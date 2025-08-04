from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt
from qfluentwidgets import (SubtitleLabel, TitleLabel, BodyLabel, ToolButton, FluentIcon)
from ..components import ActionCard


class HomePage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 30)
        layout.setSpacing(20)

        welcome_layout = QVBoxLayout()
        welcome_title = TitleLabel("欢迎使用 CS2 工具箱")
        welcome_subtitle = SubtitleLabel("一款专为CS2设计的多功能软件")
        welcome_layout.addWidget(welcome_title, 0, Qt.AlignCenter)
        welcome_layout.addWidget(welcome_subtitle, 0, Qt.AlignCenter)
        layout.addLayout(welcome_layout)

        quick_actions_layout = QVBoxLayout()
        quick_actions_title = SubtitleLabel("快速操作")
        quick_actions_layout.addWidget(quick_actions_title)

        # 第一行卡片
        actions_grid_1 = QHBoxLayout()
        
        steam_card = ActionCard("🔍", "检测CS2路径", "检测CS2安装位置", self.parent.quick_detect_steam)
        actions_grid_1.addWidget(steam_card)
        
        video_card = ActionCard("🎬", "开屏替换", "替换游戏开屏动画",
                               lambda: self.parent.stackedWidget.setCurrentWidget(self.parent.video_tab))
        actions_grid_1.addWidget(video_card)
        
        sound_card = ActionCard("🔊", "音效替换", "替换游戏启动音效",
                               lambda: self.parent.stackedWidget.setCurrentWidget(self.parent.sound_tab))
        actions_grid_1.addWidget(sound_card)
        
        font_card = ActionCard("🔤", "字体替换", "替换游戏字体文件",
                               lambda: self.parent.stackedWidget.setCurrentWidget(self.parent.font_tab))
        actions_grid_1.addWidget(font_card)
        
        # 第二行卡片
        actions_grid_2 = QHBoxLayout()
        
        gsi_sound_card = ActionCard("🎵", "游戏内音效", "实时播放音效",
                                   lambda: self.parent.stackedWidget.setCurrentWidget(self.parent.gsi_tab))
        actions_grid_2.addWidget(gsi_sound_card)
    
        spacer = QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Minimum)
        actions_grid_2.addItem(spacer)
        
        quick_actions_layout.addLayout(actions_grid_1)
        quick_actions_layout.addLayout(actions_grid_2)
        layout.addLayout(quick_actions_layout)

        recent_layout = QVBoxLayout()
        recent_title = SubtitleLabel("最近活动")
        recent_layout.addWidget(recent_title)
        
        self.recent_activity_label = BodyLabel("无")
        recent_layout.addWidget(self.recent_activity_label)
        layout.addLayout(recent_layout)

        status_layout = QVBoxLayout()
        status_title = SubtitleLabel("系统状态")
        status_layout.addWidget(status_title)
        
        steam_status_layout = QHBoxLayout()
        self.steam_status_label = BodyLabel("CS2路径: 未检测")
        self.browse_steam_btn = ToolButton()
        self.browse_steam_btn.setIcon(FluentIcon.FOLDER)
        self.browse_steam_btn.setToolTip("手动选择CS2路径")
        self.browse_steam_btn.clicked.connect(self.parent.browse_steam)
        
        steam_status_layout.addWidget(self.steam_status_label)
        steam_status_layout.addWidget(self.browse_steam_btn)
        steam_status_layout.addStretch()
        
        self.video_count_label = BodyLabel(f"视频预设: {len(self.parent.config_manager.get_presets('video'))} 个")
        self.sound_count_label = BodyLabel(f"音效预设: {len(self.parent.config_manager.get_presets('sound'))} 个")
        self.font_count_label = BodyLabel(f"字体预设: {len(self.parent.config_manager.get_presets('font'))} 个")
        
        status_layout.addLayout(steam_status_layout)
        status_layout.addWidget(self.video_count_label)
        status_layout.addWidget(self.sound_count_label)
        status_layout.addWidget(self.font_count_label)
        layout.addLayout(status_layout)

        layout.addStretch()