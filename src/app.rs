use crate::{
    config::{self, Config, TargetType},
    detector::{DeathDetector, Event, GameState},
    gsi, steam, system,
    tray::{Tray, TrayAction},
};
use eframe::egui::{self, Color32, RichText};
use std::{
    path::PathBuf,
    sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
        mpsc::{self, Receiver},
    },
    thread::JoinHandle,
    time::{Duration, Instant},
};

pub struct DeathSwitchApp {
    config: Config,
    detector: DeathDetector,
    state_receiver: Receiver<GameState>,
    gsi_running: Arc<AtomicBool>,
    gsi_thread: Option<JoinHandle<()>>,
    pending_switch: Option<Instant>,
    target_active: bool,
    status: String,
    logs: Vec<String>,
    tray: Option<Tray>,
    quit_requested: bool,
}

impl DeathSwitchApp {
    pub fn new(cc: &eframe::CreationContext<'_>) -> Self {
        let font_source = crate::fonts::install(&cc.egui_ctx);
        let config = config::load();
        let (sender, state_receiver) = mpsc::channel();
        let running = Arc::new(AtomicBool::new(true));
        let tray = Tray::new().ok();
        let mut app = Self {
            config,
            detector: DeathDetector::default(),
            state_receiver,
            gsi_running: running.clone(),
            gsi_thread: None,
            pending_switch: None,
            target_active: false,
            status: "正在启动 GSI 监听".to_owned(),
            logs: Vec::new(),
            tray,
            quit_requested: false,
        };
        match font_source {
            Some(source) => app.log(format!("已加载中文字体：{source}")),
            None => app.log("未找到系统中文字体，中文可能显示为方块"),
        }
        match gsi::start(app.config.gsi_port, sender, running) {
            Ok(thread) => {
                app.gsi_thread = Some(thread);
                app.status = format!("正在监听 127.0.0.1:{}", app.config.gsi_port);
            }
            Err(error) => app.status = format!("GSI 监听启动失败：{error}"),
        }
        if app.tray.is_none() {
            app.log("系统托盘不可用，托盘功能已禁用".to_owned());
        }
        app
    }

    fn log(&mut self, message: impl Into<String>) {
        self.logs.push(message.into());
        if self.logs.len() > 5 {
            self.logs.remove(0);
        }
    }

    fn save(&mut self) {
        match config::save(&self.config) {
            Ok(()) => self.log("配置已保存"),
            Err(error) => self.log(format!("保存配置失败：{error}")),
        }
    }

    fn handle_gsi(&mut self) {
        while let Ok(game_state) = self.state_receiver.try_recv() {
            match self.detector.process(&game_state) {
                Event::Died if self.config.enabled => {
                    self.pending_switch = Some(
                        Instant::now() + Duration::from_secs(self.config.delay_seconds.into()),
                    );
                    self.log("检测到死亡，已计划切换");
                }
                Event::Returned => self.return_to_game(),
                _ => {}
            }
        }
        if self.pending_switch.is_some_and(|at| Instant::now() >= at) {
            self.pending_switch = None;
            self.switch_away();
        }
    }

    fn handle_tray(&mut self, ctx: &egui::Context) {
        let action = self.tray.as_ref().and_then(Tray::poll);
        match action {
            Some(TrayAction::Toggle) => {
                self.config.enabled = !self.config.enabled;
                self.save();
                self.log(if self.config.enabled {
                    "已启用切换"
                } else {
                    "已暂停切换"
                });
            }
            Some(TrayAction::Show) => ctx.send_viewport_cmd(egui::ViewportCommand::Visible(true)),
            Some(TrayAction::Quit) => {
                self.quit_requested = true;
                ctx.send_viewport_cmd(egui::ViewportCommand::Close);
            }
            None => {}
        }
    }

    fn switch_away(&mut self) {
        if self.config.target.trim().is_empty() {
            self.log("已跳过切换：未设置目标");
            return;
        }
        let result = if self.target_active
            && self.config.target_type == TargetType::Url
            && system::activate_existing_browser()
        {
            Ok("已激活现有浏览器窗口".to_owned())
        } else {
            system::switch_away(&self.config)
        };
        match result {
            Ok(message) => {
                self.target_active = true;
                self.log(message);
            }
            Err(error) => self.log(error),
        }
    }

    fn return_to_game(&mut self) {
        self.pending_switch = None;
        if !self.target_active {
            return;
        }
        if self.config.pause_media_on_return {
            if let Err(error) = system::pause_current_media() {
                self.log(format!("暂停媒体失败：{error}"));
            }
        }
        system::return_to_cs2();
        self.target_active = false;
        self.log("已返回 CS2");
    }

    fn choose_cs2(&mut self) {
        if let Some(path) = rfd::FileDialog::new().pick_folder() {
            if steam::is_cs2_root(&path) {
                self.config.cs2_path = path.display().to_string();
                self.save();
                self.log("已选择 CS2 目录");
            } else {
                self.log("所选目录中未找到 cs2.exe");
            }
        }
    }

    fn detect_cs2(&mut self) {
        match steam::detect_cs2() {
            Some(path) => {
                self.config.cs2_path = path.display().to_string();
                self.save();
                self.log("已检测到 CS2 安装目录");
            }
            None => self.log("未找到 CS2 安装目录"),
        }
    }

    fn generate_gsi(&mut self) {
        let path = PathBuf::from(&self.config.cs2_path);
        match steam::write_gsi_config(&path, self.config.gsi_port) {
            Ok(path) => self.log(format!("已写入 {}", path.display())),
            Err(error) => self.log(format!("写入 GSI 配置失败：{error}")),
        }
    }
}

impl Drop for DeathSwitchApp {
    fn drop(&mut self) {
        self.gsi_running.store(false, Ordering::Relaxed);
        if let Some(thread) = self.gsi_thread.take() {
            let _ = thread.join();
        }
    }
}

impl eframe::App for DeathSwitchApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        self.handle_tray(ctx);
        self.handle_gsi();
        ctx.request_repaint_after(Duration::from_millis(100));

        if self.config.close_to_tray
            && !self.quit_requested
            && ctx.input(|input| input.viewport().close_requested())
        {
            ctx.send_viewport_cmd(egui::ViewportCommand::CancelClose);
            ctx.send_viewport_cmd(egui::ViewportCommand::Visible(false));
        }

        egui::CentralPanel::default().show(ctx, |ui| {
            ui.heading("CS2 死亡切换");
            ui.label(RichText::new(&self.status).color(Color32::from_rgb(70, 170, 110)));
            ui.separator();

            ui.horizontal(|ui| {
                ui.checkbox(&mut self.config.enabled, "启用死亡切换");
                ui.checkbox(
                    &mut self.config.pause_media_on_return,
                    "返回时暂停媒体",
                );
                ui.checkbox(&mut self.config.close_to_tray, "关闭时最小化到托盘");
            });
            ui.add_space(8.0);
            ui.label("切换目标");
            ui.horizontal(|ui| {
                ui.selectable_value(&mut self.config.target_type, TargetType::Url, "网页");
                ui.selectable_value(
                    &mut self.config.target_type,
                    TargetType::App,
                    "本地程序",
                );
            });
            ui.horizontal(|ui| {
                let hint = if self.config.target_type == TargetType::Url {
                    "https://example.com"
                } else {
                    "C:\\Path\\to\\app.exe"
                };
                ui.add(
                    egui::TextEdit::singleline(&mut self.config.target)
                        .hint_text(hint)
                        .desired_width(380.0),
                );
                if self.config.target_type == TargetType::App && ui.button("浏览").clicked() {
                    if let Some(path) = rfd::FileDialog::new()
                        .add_filter("应用程序", &["exe", "lnk", "bat", "cmd"])
                        .pick_file()
                    {
                        self.config.target = path.display().to_string();
                    }
                }
            });
            ui.horizontal(|ui| {
                ui.label("延迟（秒）");
                ui.add(egui::DragValue::new(&mut self.config.delay_seconds).range(0..=60));
                if ui.button("保存").clicked() {
                    self.save();
                }
                if ui.button("测试切换").clicked() {
                    self.switch_away();
                }
                if ui.button("返回 CS2").clicked() {
                    self.return_to_game();
                }
                if ui.button("隐藏到托盘").clicked() {
                    ctx.send_viewport_cmd(egui::ViewportCommand::Visible(false));
                }
            });

            ui.separator();
            ui.label("CS2 集成");
            ui.horizontal(|ui| {
                ui.add(
                    egui::TextEdit::singleline(&mut self.config.cs2_path)
                        .hint_text("CS2 安装目录")
                        .desired_width(370.0),
                );
                if ui.button("选择").clicked() {
                    self.choose_cs2();
                }
            });
            ui.horizontal(|ui| {
                if ui.button("检测 CS2").clicked() {
                    self.detect_cs2();
                }
                if ui.button("生成 GSI 配置").clicked() {
                    self.generate_gsi();
                }
                ui.label(format!("端口：{}", self.config.gsi_port));
            });

            ui.separator();
            ui.label("最近活动");
            for line in &self.logs {
                ui.label(line);
            }
        });
    }
}
