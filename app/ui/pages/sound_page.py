from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMenu
from PySide6.QtCore import Qt
from qfluentwidgets import (SubtitleLabel, TitleLabel, BodyLabel, LineEdit, PushButton, 
                           ListWidget, PrimaryPushButton, SimpleCardWidget)
from ..styles import UIStyles


class SoundPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(15)

        layout.addWidget(TitleLabel("启动音效替换"))
        layout.addSpacing(10)

        # 音效文件选择与操作 (Card)
        file_card = SimpleCardWidget(self)
        UIStyles.apply_styles(file_card)
        file_layout = QVBoxLayout(file_card)
        file_layout.setContentsMargins(20, 20, 20, 20)
        file_layout.setSpacing(10)

        file_layout.addWidget(SubtitleLabel("选择音效文件 (vsnd_c格式) 与 替换"))
        self.sound_entry = LineEdit()
        self.sound_entry.setPlaceholderText("选择音效文件路径")
        self.browse_sound_btn = PushButton("浏览文件")
        sound_layout = QHBoxLayout()
        sound_layout.addWidget(self.sound_entry)
        sound_layout.addWidget(self.browse_sound_btn)
        file_layout.addLayout(sound_layout)

        info_layout = QHBoxLayout()
        self.sound_name_label = BodyLabel("音效名称: 未选择")
        self.sound_name_label.setStyleSheet("color: #666666;")
        self.sound_filename_label = BodyLabel("文件名: 未选择")
        self.sound_filename_label.setStyleSheet("color: #666666;")
        info_layout.addWidget(self.sound_name_label)
        info_layout.addWidget(self.sound_filename_label)
        
        self.execute_btn = PrimaryPushButton("替换启动音效")
        self.restore_btn = PushButton("还原默认音效")
        self.tutorial_btn = PushButton("替换教程")
        
        info_layout.addStretch()
        info_layout.addWidget(self.execute_btn)
        info_layout.addWidget(self.restore_btn)
        info_layout.addWidget(self.tutorial_btn)
        
        file_layout.addLayout(info_layout)
        layout.addWidget(file_card)

        # 音效预设 (Card)
        preset_card = SimpleCardWidget(self)
        UIStyles.apply_styles(preset_card)
        preset_layout = QVBoxLayout(preset_card)
        preset_layout.setContentsMargins(20, 20, 20, 20)
        preset_layout.setSpacing(10)

        preset_layout.addWidget(SubtitleLabel("音效预设"))
        self.sound_preset_list = ListWidget()
        self.sound_preset_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.sound_preset_list.customContextMenuRequested.connect(self.show_sound_preset_context_menu)
        preset_layout.addWidget(self.sound_preset_list)
        
        self.save_sound_preset_btn = PushButton("保存当前音效为预设")
        preset_layout.addWidget(self.save_sound_preset_btn)
        layout.addWidget(preset_card)

        self._connect_signals()

    def _connect_signals(self):
        self.browse_sound_btn.clicked.connect(self.parent.browse_sound_file)
        self.execute_btn.clicked.connect(self.parent.execute_sound_replace)
        self.restore_btn.clicked.connect(self.parent.restore_sound)
        self.tutorial_btn.clicked.connect(self.parent.open_sound_tutorial)
        self.save_sound_preset_btn.clicked.connect(self.parent.save_sound_preset)
        self.sound_preset_list.itemDoubleClicked.connect(self.parent.apply_sound_preset_from_item)

    def show_sound_preset_context_menu(self, pos):
        item = self.sound_preset_list.itemAt(pos)
        if not item:
            return
        
        index = self.sound_preset_list.row(item)
        preset = self.parent.config_manager.get_presets('sound')[index]
        
        menu = QMenu(self)
        open_folder_action = menu.addAction("打开文件位置")
        open_folder_action.triggered.connect(lambda: self.parent.open_preset_folder(preset["sound_path"]))
        
        delete_action = menu.addAction("删除预设")
        delete_action.triggered.connect(lambda: self.parent.delete_sound_preset_confirm(index))
        
        menu.exec(self.sound_preset_list.mapToGlobal(pos))