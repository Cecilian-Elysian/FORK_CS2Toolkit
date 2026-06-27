import threading
import requests
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy, QFormLayout
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import (SubtitleLabel, TitleLabel, BodyLabel, ToolButton, FluentIcon, SimpleCardWidget, LineEdit, PrimaryPushButton, InfoBar, ScrollArea, SettingCardGroup, SwitchSettingCard)
from ..styles import UIStyles

class HomePage(ScrollArea):
    announcement_fetched = Signal(str, str)

    def __init__(self, parent):
        super().__init__(parent=parent)
        self.parent_window = parent
        
        self.view = QWidget(self)
        self.view.setObjectName("home_view")
        self.layout = QVBoxLayout(self.view)
        self.layout.setContentsMargins(30, 20, 30, 30)
        self.layout.setSpacing(20)
        
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setObjectName("homePage")
        self.setStyleSheet("QScrollArea {background: transparent; border: none;} #home_view {background: transparent;}")
        
        self.announcement_fetched.connect(self._update_announcement_ui)
        self._setup_ui()
        self._fetch_announcement()
    
    def _setup_ui(self):
        # Welcome Section
        welcome_card = SimpleCardWidget(self.view)
        UIStyles.apply_styles(welcome_card)
        welcome_card.setObjectName("customPanel")
        
        welcome_layout = QVBoxLayout(welcome_card)
        welcome_layout.setContentsMargins(20, 20, 20, 20)
        welcome_title = TitleLabel("欢迎使用 CS2 工具箱", welcome_card)
        welcome_subtitle = SubtitleLabel("一款专为CS2设计的多功能软件", welcome_card)
        welcome_subtitle.setStyleSheet("color: #666666;")
        welcome_layout.addWidget(welcome_title, 0, Qt.AlignCenter)
        welcome_layout.addWidget(welcome_subtitle, 0, Qt.AlignCenter)
        self.layout.addWidget(welcome_card)

        # Announcement Section
        self.announcement_card = SimpleCardWidget(self.view)
        UIStyles.apply_styles(self.announcement_card)
        announcement_layout = QVBoxLayout(self.announcement_card)
        announcement_layout.setContentsMargins(20, 20, 20, 20)
        announcement_layout.setSpacing(10)
        
        self.announcement_title = SubtitleLabel("公告栏", self.announcement_card)
        self.announcement_content = BodyLabel("正在获取最新公告...", self.announcement_card)
        self.announcement_content.setWordWrap(True)
        self.announcement_content.setTextFormat(Qt.RichText)
        self.announcement_content.setOpenExternalLinks(True)
        
        announcement_layout.addWidget(self.announcement_title)
        announcement_layout.addWidget(self.announcement_content)
        self.layout.addWidget(self.announcement_card)

        # Control Panel Section
        self.control_group = SettingCardGroup("快捷控制面板", self.view)
        
        # Visual - Flash
        self.flash_switch_card = SwitchSettingCard(
            icon=FluentIcon.PHOTO,
            title="自定义闪光效果",
            content="当被闪白时，在屏幕上叠加自定义图片",
            parent=self.control_group
        )
        self.flash_switch_card.switchButton.checkedChanged.connect(self._on_flash_toggled)
        self.control_group.addSettingCard(self.flash_switch_card)
        
        # Visual - Kill Icon
        self.kill_icon_switch_card = SwitchSettingCard(
            icon=FluentIcon.GAME,
            title="击杀图标显示",
            content="在击杀敌人时，在屏幕下方显示击杀图标",
            parent=self.control_group
        )
        self.kill_icon_switch_card.switchButton.checkedChanged.connect(self._on_kill_icon_toggled)
        self.control_group.addSettingCard(self.kill_icon_switch_card)

        # Visual - Death
        self.death_switch_card = SwitchSettingCard(
            icon=FluentIcon.VIDEO,
            title="自定义死亡画面",
            content="死亡时在屏幕上播放指定的图片或视频",
            parent=self.control_group
        )
        self.death_switch_card.switchButton.checkedChanged.connect(self._on_death_toggled)
        self.control_group.addSettingCard(self.death_switch_card)

        # Visual - Boss Key
        self.boss_key_switch_card = SwitchSettingCard(
            icon=FluentIcon.HIDE,
            title="死亡一键切屏",
            content="死亡后自动最小化游戏并打开指定网页",
            parent=self.control_group
        )
        self.boss_key_switch_card.switchButton.checkedChanged.connect(self._on_boss_key_toggled)
        self.control_group.addSettingCard(self.boss_key_switch_card)

        self.layout.addWidget(self.control_group)

        # System Status Section
        status_card = SimpleCardWidget(self.view)
        UIStyles.apply_styles(status_card)
        status_layout = QVBoxLayout(status_card)
        status_layout.setContentsMargins(20, 20, 20, 20)
        status_layout.setSpacing(15)

        status_title = SubtitleLabel("当前状态", status_card)
        status_layout.addWidget(status_title)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        steam_status_layout = QHBoxLayout()
        self.steam_status_label = BodyLabel("未检测", status_card)
        self.browse_steam_btn = ToolButton(status_card)
        self.browse_steam_btn.setIcon(FluentIcon.FOLDER)
        self.browse_steam_btn.setToolTip("手动选择CS2路径")
        self.browse_steam_btn.clicked.connect(self.parent_window.browse_steam)
        steam_status_layout.addWidget(self.steam_status_label)
        steam_status_layout.addWidget(self.browse_steam_btn)
        steam_status_layout.addStretch()

        form_layout.addRow(BodyLabel("CS2路径:"), steam_status_layout)
        
        self.status_gsi_server = BodyLabel("未知")
        self.video_status_label = BodyLabel("未知")
        self.sound_status_label = BodyLabel("未知")
        self.font_status_label = BodyLabel("未知")
        self.gsi_count_label = BodyLabel("0")

        form_layout.addRow(BodyLabel("游戏内服务:"), self.status_gsi_server)
        form_layout.addRow(BodyLabel("当前开屏动画:"), self.video_status_label)
        form_layout.addRow(BodyLabel("当前启动音效:"), self.sound_status_label)
        form_layout.addRow(BodyLabel("当前字体:"), self.font_status_label)
        form_layout.addRow(BodyLabel("设定游戏内音效数:"), self.gsi_count_label)

        status_layout.addLayout(form_layout)
        self.layout.addWidget(status_card)

        self.layout.addStretch()
        
        # Initial data fetch
        self.update_status()

    def update_status(self):
        # This will be called by main_window when needed
        if not self.parent_window:
            return
            
        steam_path = self.parent_window.steam_path
        if steam_path:
            self.steam_status_label.setText(steam_path)
            self.steam_status_label.setStyleSheet("color: green;")
        else:
            self.steam_status_label.setText("未检测到")
            self.steam_status_label.setStyleSheet("color: red;")
            
        if hasattr(self.parent_window, 'gsi_manager') and self.parent_window.gsi_manager.is_running():
            self.status_gsi_server.setText("运行中...")
            self.status_gsi_server.setStyleSheet("color: green;")
        else:
            self.status_gsi_server.setText("未运行")
            self.status_gsi_server.setStyleSheet("color: red;")

        # Update applied statuses from config if available
        self.video_status_label.setText(self.parent_window.config_manager.get("current_video", "未知"))
        self.sound_status_label.setText(self.parent_window.config_manager.get("current_sound", "未知"))
        self.font_status_label.setText(self.parent_window.config_manager.get("current_font", "未知"))
        
        events = self.parent_window.config_manager.get("gsi_events", [])
        self.gsi_count_label.setText(f"{len(events)} 个")
        
        # Sync switches with actual configuration/state
        # Visual Settings
        visual_config = self.parent_window.config_manager.get('visual', {})
        self.flash_switch_card.switchButton.blockSignals(True)
        self.flash_switch_card.switchButton.setChecked(visual_config.get('flash_enabled', False))
        self.flash_switch_card.switchButton.blockSignals(False)
        
        self.kill_icon_switch_card.switchButton.blockSignals(True)
        self.kill_icon_switch_card.switchButton.setChecked(visual_config.get('kill_icon_enabled', False))
        self.kill_icon_switch_card.switchButton.blockSignals(False)
        
        self.death_switch_card.switchButton.blockSignals(True)
        self.death_switch_card.switchButton.setChecked(visual_config.get('death_media_enabled', False))
        self.death_switch_card.switchButton.blockSignals(False)
        
        self.boss_key_switch_card.switchButton.blockSignals(True)
        self.boss_key_switch_card.switchButton.setChecked(visual_config.get('boss_key_enabled', False))
        self.boss_key_switch_card.switchButton.blockSignals(False)

    def _on_flash_toggled(self, is_checked):
        if hasattr(self.parent_window, 'visual_tab'):
            self.parent_window.visual_tab.flash_card.switch_btn.setChecked(is_checked)
            
    def _on_kill_icon_toggled(self, is_checked):
        if hasattr(self.parent_window, 'visual_tab'):
            self.parent_window.visual_tab.kill_icon_card.switch_btn.setChecked(is_checked)
        
    def _on_death_toggled(self, is_checked):
        if hasattr(self.parent_window, 'visual_tab'):
            self.parent_window.visual_tab.death_card.switch_btn.setChecked(is_checked)
        
    def _on_boss_key_toggled(self, is_checked):
        if hasattr(self.parent_window, 'visual_tab'):
            self.parent_window.visual_tab.boss_key_card.switch_btn.setChecked(is_checked)

    def _fetch_announcement(self):
        def fetch_task():
            try:
                proxies = {"http": None, "https": None}
                # Try fetching announcement.json
                response = requests.get("https://gitee.com/clover23333/CS2-ToolKit/raw/master/announcement.json", timeout=5, proxies=proxies)
                if response.status_code == 200:
                    data = response.json()
                    title = data.get("title", "最新公告")
                    content = data.get("content", "暂无公告内容。")
                    self.announcement_fetched.emit(title, content)
                else:
                    self.announcement_fetched.emit("公告栏", "暂无最新公告。")
            except Exception as e:
                self.announcement_fetched.emit("公告栏", f"获取公告失败。")
                
        threading.Thread(target=fetch_task, daemon=True).start()

    def _update_announcement_ui(self, title, content):
        self.announcement_title.setText(title)
        # 如果不是HTML，将换行符替换为HTML换行
        if "<" not in content and ">" not in content:
            content = content.replace("\n", "<br>")
        self.announcement_content.setText(content)