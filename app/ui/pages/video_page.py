from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMenu
from PySide6.QtCore import Qt
from qfluentwidgets import (SubtitleLabel, TitleLabel, LineEdit, PushButton, 
                           RadioButton, ListWidget, PrimaryPushButton)


class VideoPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(15)

        layout.addWidget(TitleLabel("开屏动画替换"))
        layout.addSpacing(10)

        layout.addWidget(SubtitleLabel("选择视频文件 (WEBM格式)"))
        self.video_entry = LineEdit()
        self.video_entry.setPlaceholderText("选择一个webm格式的视频文件")
        self.browse_video_btn = PushButton("选择文件")
        video_layout = QHBoxLayout()
        video_layout.addWidget(self.video_entry)
        video_layout.addWidget(self.browse_video_btn)
        layout.addLayout(video_layout)

        layout.addWidget(SubtitleLabel("选择替换版本"))
        version_layout = QHBoxLayout()
        self.intl_radio = RadioButton("国际服")
        self.cn_radio = RadioButton("国服")
        self.both_radio = RadioButton("两者都替换")
        self.both_radio.setChecked(True)
        version_layout.addStretch()
        version_layout.addWidget(self.intl_radio)
        version_layout.addWidget(self.cn_radio)
        version_layout.addWidget(self.both_radio)
        version_layout.addStretch()
        layout.addLayout(version_layout)

        self.execute_btn = PrimaryPushButton("替换")
        layout.addWidget(self.execute_btn)
        
        layout.addWidget(SubtitleLabel("视频预设"))
        self.preset_list = ListWidget()
        self.preset_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.preset_list.customContextMenuRequested.connect(self.show_video_preset_context_menu)
        self.save_preset_btn = PushButton("保存当前视频为预设")
        preset_buttons_layout = QHBoxLayout()
        preset_buttons_layout.addWidget(self.save_preset_btn)
        layout.addWidget(self.preset_list)
        layout.addLayout(preset_buttons_layout)

        self._connect_signals()
    
    def _connect_signals(self):
        self.browse_video_btn.clicked.connect(self.parent.browse_video)
        self.execute_btn.clicked.connect(self.parent.execute_replace)
        self.save_preset_btn.clicked.connect(self.parent.save_preset)
        self.preset_list.itemDoubleClicked.connect(self.parent.apply_preset_from_item)
    
    def show_video_preset_context_menu(self, pos):
        item = self.preset_list.itemAt(pos)
        if not item:
            return
            
        index = self.preset_list.row(item)
        preset = self.parent.config_manager.get_presets('video')[index]
        
        menu = QMenu(self)
        open_folder_action = menu.addAction("打开文件所在位置")
        open_folder_action.triggered.connect(lambda: self.parent.open_preset_folder(preset["video_path"]))
        
        delete_action = menu.addAction("删除预设")
        delete_action.triggered.connect(lambda: self.parent.delete_preset_confirm(index))
        
        menu.exec(self.preset_list.mapToGlobal(pos))