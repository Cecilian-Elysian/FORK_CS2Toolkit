from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMenu
from PySide6.QtCore import Qt
from qfluentwidgets import (SubtitleLabel, TitleLabel, BodyLabel, LineEdit, PushButton, 
                           ListWidget, PrimaryPushButton)


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

        layout.addWidget(SubtitleLabel("选择音效文件 (vsnd_c格式)"))
        self.sound_entry = LineEdit()
        self.sound_entry.setPlaceholderText("选择音效文件路径")
        self.browse_sound_btn = PushButton("浏览文件")
        sound_layout = QHBoxLayout()
        sound_layout.addWidget(self.sound_entry)
        sound_layout.addWidget(self.browse_sound_btn)
        layout.addLayout(sound_layout)

        self.sound_name_label = BodyLabel("音效名称: 未选择")
        self.sound_filename_label = BodyLabel("文件名: 未选择")
        layout.addWidget(self.sound_name_label)
        layout.addWidget(self.sound_filename_label)

        buttons_layout = QHBoxLayout()
        self.execute_btn = PrimaryPushButton("替换启动音效")
        self.restore_btn = PushButton("还原默认音效")
        buttons_layout.addWidget(self.execute_btn)
        buttons_layout.addWidget(self.restore_btn)
        layout.addLayout(buttons_layout)

        tutorial_layout = QHBoxLayout()
        self.tutorial_btn = PushButton("替换教程")
        self.tutorial_btn.setToolTip("点击查看音效替换教程")
        tutorial_layout.addStretch()
        tutorial_layout.addWidget(self.tutorial_btn)
        tutorial_layout.addStretch()
        layout.addLayout(tutorial_layout)
        layout.addSpacing(10)

        layout.addWidget(SubtitleLabel("音效预设"))
        self.sound_preset_list = ListWidget()
        self.sound_preset_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.sound_preset_list.customContextMenuRequested.connect(self.show_sound_preset_context_menu)
        layout.addWidget(self.sound_preset_list)

        layout.addStretch()
        
        self.save_sound_preset_btn = PushButton("保存当前音效为预设")
        layout.addWidget(self.save_sound_preset_btn)

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