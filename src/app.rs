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
    status_color: Color32,
    logs: Vec<String>,
    tray: Option<Tray>,
    quit_requested: bool,
    gsi_bound_port: u16,
    gsi_packets: u64,
    last_health: Option<i32>,
    last_phase: String,
    last_spectating: bool,
    last_saved_target: String,
    target_dirty_since: Option<Instant>,
}

impl DeathSwitchApp {
    pub fn new(cc: &eframe::CreationContext<'_>) -> Self {
        let font_source = crate::fonts::install(&cc.egui_ctx);
        let config = config::load();
        let (sender, state_receiver) = mpsc::channel();
        let running = Arc::new(AtomicBool::new(true));
        let tray = Tray::new().ok();
        let mut app = Self {
            config: config.clone(),
            detector: DeathDetector::default(),
            state_receiver,
            gsi_running: running.clone(),
            gsi_thread: None,
            pending_switch: None,
            target_active: false,
            status: "正在启动 GSI 监听".to_owned(),
            status_color: Color32::from_rgb(70, 170, 110),
            logs: Vec::new(),
            tray,
            quit_requested: false,
            gsi_bound_port: 0,
            gsi_packets: 0,
            last_health: None,
            last_phase: String::new(),
            last_spectating: false,
            last_saved_target: config.target.clone(),
            target_dirty_since: None,
        };
        match font_source {
            Some(source) => app.log(format!("已加载中文字体：{source}")),
            None => app.log("未找到系统中文字体，中文可能显示为方块"),
        }
        match gsi::start(app.config.gsi_port, sender, running) {
            Ok(handle) => {
                app.gsi_bound_port = handle.bound_port;
                app.gsi_thread = Some(handle.thread);
                app.status = format!("正在监听 127.0.0.1:{} · 等待数据", handle.bound_port);
                if handle.bound_port != app.config.gsi_port {
                    app.status_color = Color32::from_rgb(220, 140, 60);
                    app.log(format!(
                        "端口 {} 已被占用，已切换到 {}。请重新生成 GSI 配置使 CS2 指向新端口。",
                        app.config.gsi_port, handle.bound_port
                    ));
                }
            }
            Err(error) => {
                app.status = format!("GSI 监听启动失败：{error}");
                app.status_color = Color32::from_rgb(220, 80, 80);
            }
        }
        if app.tray.is_none() {
            app.log("系统托盘不可用，托盘功能已禁用".to_owned());
        }
        app
    }

    fn log(&mut self, message: impl Into<String>) {
        self.logs.push(message.into());
        if self.logs.len() > 6 {
            self.logs.remove(0);
        }
    }

    fn save(&mut self) {
        match config::save(&self.config) {
            Ok(()) => {
                self.log("配置已保存");
                self.last_saved_target = self.config.target.clone();
                self.target_dirty_since = None;
            }
            Err(error) => self.log(format!("保存配置失败：{error}")),
        }
    }

    fn maybe_auto_save(&mut self) {
        if self.config.target == self.last_saved_target {
            self.target_dirty_since = None;
            return;
        }
        let started = *self.target_dirty_since.get_or_insert_with(Instant::now);
        if started.elapsed() >= Duration::from_millis(800) {
            self.save();
        }
    }

    fn refresh_status(&mut self) {
        if self.gsi_bound_port == 0 {
            return;
        }
        // Only nag about the cfg/port mismatch while we have not seen any GSI
        // packets. Once packets are flowing we know CS2 is talking to us on
        // whatever port we ended up bound to, and showing the running counter
        // is more useful than the persistent warning.
        if self.gsi_bound_port != self.config.gsi_port && self.gsi_packets == 0 {
            self.status_color = Color32::from_rgb(220, 140, 60);
            self.status = format!(
                "已绑定到备用端口 {}（配置端口 {} 已被占用）。点「生成 GSI 配置」同步到 CS2。",
                self.gsi_bound_port, self.config.gsi_port
            );
            return;
        }
        self.status_color = if self.gsi_packets == 0 {
            Color32::from_rgb(170, 170, 90)
        } else {
            Color32::from_rgb(70, 170, 110)
        };
        let health = match self.last_health {
            Some(value) => value.to_string(),
            None => "—".to_owned(),
        };
        let phase = if self.last_phase.is_empty() {
            "—"
        } else {
            self.last_phase.as_str()
        };
        let observing = if self.last_spectating { "观战中" } else { "本机" };
        self.status = format!(
            "正在监听 127.0.0.1:{} · 收到 {} 包 · 血量 {} · 阶段 {} · {}",
            self.gsi_bound_port, self.gsi_packets, health, phase, observing
        );
    }

    fn handle_gsi(&mut self) {
        while let Ok(game_state) = self.state_receiver.try_recv() {
            self.gsi_packets = self.gsi_packets.saturating_add(1);
            self.last_health = game_state.player.state.health;
            self.last_phase.clone_from(&game_state.round.phase);
            self.last_spectating = is_spectating(&game_state);
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
        // Always minimize CS2 first, mirroring the original CS2Toolkit, so the
        // target window can actually surface even when we reuse an existing
        // browser.
        system::minimize_cs2();
        let reuse_existing_browser = self.target_active
            && self.config.target_type == TargetType::Url
            && system::activate_existing_browser();
        let result = if reuse_existing_browser {
            Ok("已激活现有浏览器窗口".to_owned())
        } else {
            match self.config.target_type {
                TargetType::Url => system::open_url(&self.config.target),
                TargetType::App => system::open_app(&self.config.target),
            }
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
        // If we ended up on a fallback port, sync the config so the cfg file
        // points at the right place.
        if self.gsi_bound_port != 0 && self.gsi_bound_port != self.config.gsi_port {
            self.config.gsi_port = self.gsi_bound_port;
        }
        let path = PathBuf::from(&self.config.cs2_path);
        match steam::write_gsi_config(&path, self.config.gsi_port) {
            Ok(path) => {
                self.log(format!(
                    "已写入 {}（端口 {}）。记得重启 CS2。",
                    path.display(),
                    self.config.gsi_port
                ));
                self.save();
            }
            Err(error) => self.log(format!("写入 GSI 配置失败：{error}")),
        }
    }
}

fn is_spectating(state: &GameState) -> bool {
    let player = &state.player;
    (!state.provider.steamid.is_empty()
        && !player.steamid.is_empty()
        && state.provider.steamid != player.steamid)
        || player.spectarget.is_some()
        || player.activity == "spectating"
        || !matches!(player.team.as_str(), "T" | "CT")
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
        self.maybe_auto_save();
        self.refresh_status();
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
            ui.label(RichText::new(&self.status).color(self.status_color));
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