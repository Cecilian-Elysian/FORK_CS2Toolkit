from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QMenu
from PySide6.QtCore import Qt
from qfluentwidgets import (SubtitleLabel, TitleLabel, BodyLabel, LineEdit, PushButton, 
                           ListWidget, PrimaryPushButton)


class FontPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(15)

        layout.addWidget(TitleLabel("游戏字体替换"))
        layout.addSpacing(10)

        layout.addWidget(SubtitleLabel("选择字体文件 (TTF格式)"))
        self.font_entry = LineEdit()
        self.font_entry.setPlaceholderText("选择一个ttf格式的字体文件")
        self.browse_font_btn = PushButton("选择字体文件")
        font_file_layout = QHBoxLayout()
        font_file_layout.addWidget(self.font_entry)
        font_file_layout.addWidget(self.browse_font_btn)
        layout.addLayout(font_file_layout)

        self.font_name_label = BodyLabel("字体名称: 未选择")
        self.font_filename_label = BodyLabel("文件名: 未选择")
        layout.addWidget(self.font_name_label)
        layout.addWidget(self.font_filename_label)

        self.execute_font_btn = PrimaryPushButton("替换字体")
        layout.addWidget(self.execute_font_btn)

        layout.addWidget(SubtitleLabel("字体预设"))
        self.font_preset_list = ListWidget()
        self.font_preset_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.font_preset_list.customContextMenuRequested.connect(self.show_font_preset_context_menu)
        layout.addWidget(self.font_preset_list)

        layout.addStretch()
        
        self.save_font_preset_btn = PushButton("保存当前字体为预设")
        layout.addWidget(self.save_font_preset_btn)

        self._connect_signals()
    
    def _connect_signals(self):
        self.browse_font_btn.clicked.connect(self.parent.browse_font_file)
        self.execute_font_btn.clicked.connect(self.parent.execute_font_replace)
        self.save_font_preset_btn.clicked.connect(self.parent.save_font_preset)
        self.font_preset_list.itemDoubleClicked.connect(self.parent.apply_font_preset_from_item)
    
    def show_font_preset_context_menu(self, pos):
        item = self.font_preset_list.itemAt(pos)
        if not item:
            return
        
        index = self.font_preset_list.row(item)
        preset = self.parent.config_manager.get_presets('font')[index]
        
        menu = QMenu(self)
        open_folder_action = menu.addAction("打开文件位置")
        open_folder_action.triggered.connect(lambda: self.parent.open_preset_folder(preset["font_path"]))
        
        delete_action = menu.addAction("删除预设")
        delete_action.triggered.connect(lambda: self.parent.delete_font_preset_confirm(index))
        
        menu.exec(self.font_preset_list.mapToGlobal(pos))