import os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog
from PySide6.QtCore import Qt
from qfluentwidgets import (ScrollArea, SettingCardGroup, SwitchSettingCard, SettingCard,
                           PushSettingCard, PushButton, FluentIcon as FIF, LineEdit, MessageBoxBase, SubtitleLabel, BodyLabel, SwitchButton, Slider)

class VisualSettingCard(SettingCard):
    def __init__(self, icon, title, content=None, parent=None):
        super().__init__(icon, title, content, parent)
        
        self.setting_btn = PushButton("设置", self)
        self.switch_btn = SwitchButton("关", self)
        self.switch_btn.setOnText("开")
        self.switch_btn.setOffText("关")
        
        self.hBoxLayout.addWidget(self.setting_btn, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self.hBoxLayout.addWidget(self.switch_btn, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

class VisualConfigDialog(MessageBoxBase):
    def __init__(self, config_manager, dialog_type, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.dialog_type = dialog_type # 'flash', 'death', 'boss_key'
        self.visual_config = self.config_manager.get('visual', {})
        self._setup_ui()

    def _setup_ui(self):
        if self.dialog_type == 'flash':
            self.titleLabel = SubtitleLabel('自定义闪光图片', self)
            self.viewLayout.addWidget(self.titleLabel)
            
            # File selection
            selection_layout = QHBoxLayout()
            selection_layout.addWidget(BodyLabel("图片路径:"))
            
            path_val = self.visual_config.get('flash_path', '')
            self.path_label = BodyLabel(os.path.basename(path_val) if path_val else "未选择")
            self.path_label.setStyleSheet("color: #666666;")
            selection_layout.addWidget(self.path_label, 1)
            
            self.select_btn = PushButton("选择图片", self)
            self.select_btn.clicked.connect(self._browse_flash_image)
            selection_layout.addWidget(self.select_btn)
            self.viewLayout.addLayout(selection_layout)

        elif self.dialog_type == 'death':
            self.titleLabel = SubtitleLabel('自定义死亡画面', self)
            self.viewLayout.addWidget(self.titleLabel)
            
            selection_layout = QHBoxLayout()
            selection_layout.addWidget(BodyLabel("媒体路径:"))
            
            path_val = self.visual_config.get('death_media_path', '')
            self.path_label = BodyLabel(os.path.basename(path_val) if path_val else "未选择")
            self.path_label.setStyleSheet("color: #666666;")
            selection_layout.addWidget(self.path_label, 1)
            
            self.select_btn = PushButton("选择文件", self)
            self.select_btn.clicked.connect(self._browse_death_media)
            selection_layout.addWidget(self.select_btn)
            self.viewLayout.addLayout(selection_layout)

        elif self.dialog_type == 'boss_key':
            self.titleLabel = SubtitleLabel('网页地址', self)
            self.viewLayout.addWidget(self.titleLabel)
            
            url_layout = QHBoxLayout()
            url_layout.addWidget(BodyLabel("打开网页:"))
            self.url_input = LineEdit(self)
            self.url_input.setText(self.visual_config.get('boss_key_url', 'https://www.bilibili.com/'))
            self.url_input.textChanged.connect(self._on_url_changed)
            url_layout.addWidget(self.url_input, 1)
            self.viewLayout.addLayout(url_layout)

        self.widget.setMinimumWidth(400)

    def _browse_flash_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp)")
        if path:
            self.visual_config['flash_path'] = path
            self.path_label.setText(os.path.basename(path))
            self.config_manager.set('visual', self.visual_config)

    def _browse_death_media(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择媒体文件", "", "媒体文件 (*.png *.jpg *.mp4 *.webm *.avi)")
        if path:
            self.visual_config['death_media_path'] = path
            self.path_label.setText(os.path.basename(path))
            self.config_manager.set('visual', self.visual_config)
            
    def _on_url_changed(self, text):
        self.visual_config['boss_key_url'] = text
        self.config_manager.set('visual', self.visual_config)

class KillIconDialog(MessageBoxBase):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.visual_config = self.config_manager.get('visual', {})
        self._setup_ui()

    def _setup_ui(self):
        self.titleLabel = SubtitleLabel('配置击杀图标', self)
        self.viewLayout.addWidget(self.titleLabel)

        self.is_advanced = self.visual_config.get('kill_icon_is_advanced', False)
        
        # 基础设置
        self.basic_container = QWidget()
        basic_layout = QVBoxLayout(self.basic_container)
        basic_layout.setContentsMargins(0, 0, 0, 0)
        
        selection_layout = QHBoxLayout()
        selection_layout.addWidget(BodyLabel("全局图标路径:"))
        path_val = self.visual_config.get('kill_icon_path', '')
        self.path_label = BodyLabel(os.path.basename(path_val) if path_val else "未选择")
        self.path_label.setStyleSheet("color: #666666;")
        selection_layout.addWidget(self.path_label, 1)
        
        self.select_btn = PushButton("选择图片", self)
        self.select_btn.clicked.connect(self._browse_basic_image)
        selection_layout.addWidget(self.select_btn)
        basic_layout.addLayout(selection_layout)
        
        # 高级设置开关
        adv_switch_layout = QHBoxLayout()
        adv_switch_layout.addWidget(BodyLabel("启用 1-5 杀独立配置:"))
        self.adv_switch = SwitchButton(self)
        self.adv_switch.setOnText("开")
        self.adv_switch.setOffText("关")
        self.adv_switch.setChecked(self.is_advanced)
        self.adv_switch.checkedChanged.connect(self._on_advanced_toggled)
        adv_switch_layout.addStretch()
        adv_switch_layout.addWidget(self.adv_switch)
        basic_layout.addLayout(adv_switch_layout)

        # 图标宽度设置
        width_layout = QHBoxLayout()
        width_layout.addWidget(BodyLabel("图标宽度:"))
        self.width_slider = Slider(Qt.Horizontal, self)
        self.width_slider.setRange(50, 500)
        self.width_slider.setValue(self.visual_config.get('kill_icon_width', 120))
        
        self.width_value_label = BodyLabel(f"{self.width_slider.value()} px")
        self.width_slider.valueChanged.connect(self._on_width_changed)
        
        width_layout.addWidget(self.width_slider, 1)
        width_layout.addWidget(self.width_value_label)
        basic_layout.addLayout(width_layout)
        
        # 图标高度设置
        height_layout = QHBoxLayout()
        height_layout.addWidget(BodyLabel("图标高度:"))
        self.height_slider = Slider(Qt.Horizontal, self)
        self.height_slider.setRange(50, 500)
        self.height_slider.setValue(self.visual_config.get('kill_icon_height', 120))
        
        self.height_value_label = BodyLabel(f"{self.height_slider.value()} px")
        self.height_slider.valueChanged.connect(self._on_height_changed)
        
        height_layout.addWidget(self.height_slider, 1)
        height_layout.addWidget(self.height_value_label)
        basic_layout.addLayout(height_layout)

        self.viewLayout.addWidget(self.basic_container)

        # 高级设置容器
        self.adv_container = QWidget()
        adv_layout = QVBoxLayout(self.adv_container)
        adv_layout.setContentsMargins(0, 0, 0, 0)
        
        self.adv_labels = []
        icons_config = self.visual_config.get('kill_icons_1_5', [{} for _ in range(5)])
        
        for i in range(5):
            h_layout = QHBoxLayout()
            h_layout.addWidget(BodyLabel(f"{i+1} 杀图标:"))
            path_val = icons_config[i].get('path', '')
            label = BodyLabel(os.path.basename(path_val) if path_val else "未选择")
            label.setStyleSheet("color: #666666;")
            self.adv_labels.append(label)
            h_layout.addWidget(label, 1)
            
            btn = PushButton("选择图片", self)
            btn.clicked.connect(lambda checked=False, idx=i: self._browse_adv_image(idx))
            h_layout.addWidget(btn)
            adv_layout.addLayout(h_layout)

        self.viewLayout.addWidget(self.adv_container)
        
        self._update_visibility()
        self.widget.setMinimumWidth(450)

    def _update_visibility(self):
        if self.is_advanced:
            self.adv_container.show()
            self.basic_container.findChild(QHBoxLayout).setEnabled(False) # 只是视觉上，实际用 hide 更简单但影响布局
        else:
            self.adv_container.hide()

    def _on_advanced_toggled(self, checked):
        self.is_advanced = checked
        self.visual_config['kill_icon_is_advanced'] = checked
        self._update_visibility()
        self.config_manager.set('visual', self.visual_config)

    def _on_width_changed(self, value):
        self.width_value_label.setText(f"{value} px")
        self.visual_config['kill_icon_width'] = value
        self.config_manager.set('visual', self.visual_config)

    def _on_height_changed(self, value):
        self.height_value_label.setText(f"{value} px")
        self.visual_config['kill_icon_height'] = value
        self.config_manager.set('visual', self.visual_config)

    def _browse_basic_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择击杀图标", "", "媒体文件 (*.png *.jpg *.jpeg *.bmp *.gif *.mp4 *.webm)")
        if path:
            self.visual_config['kill_icon_path'] = path
            self.path_label.setText(os.path.basename(path))
            self.config_manager.set('visual', self.visual_config)

    def _browse_adv_image(self, index):
        path, _ = QFileDialog.getOpenFileName(self, f"选择 {index+1} 杀图标", "", "媒体文件 (*.png *.jpg *.jpeg *.bmp *.gif *.mp4 *.webm)")
        if path:
            icons = self.visual_config.get('kill_icons_1_5', [{} for _ in range(5)])
            icons[index]['path'] = path
            self.visual_config['kill_icons_1_5'] = icons
            self.adv_labels[index].setText(os.path.basename(path))
            self.config_manager.set('visual', self.visual_config)

class VisualPage(ScrollArea):
    def __init__(self, config_manager, parent=None):
        super().__init__(parent=parent)
        self.config_manager = config_manager
        self.parent_window = parent
        
        self.view = QWidget(self)
        self.view.setObjectName("view")
        self.layout = QVBoxLayout(self.view)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)
        self.layout.setAlignment(Qt.AlignTop)
        
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setObjectName("visualPage")
        self.setStyleSheet("QScrollArea {background: transparent; border: none;} #view {background: transparent;}")
        
        self._init_config()
        self._setup_ui()
        
    def _init_config(self):
        self.visual_config = self.config_manager.get('visual', {
            'flash_enabled': False,
            'flash_path': '',
            'death_media_enabled': False,
            'death_media_path': '',
            'boss_key_enabled': False,
            'boss_key_url': 'https://www.bilibili.com/',
            'kill_icon_enabled': False,
            'kill_icon_is_advanced': False,
            'kill_icon_width': 120,
            'kill_icon_height': 120,
            'kill_icon_path': '',
            'kill_icons_1_5': [{} for _ in range(5)]
        })

    def _update_ui_from_config(self):
        self._init_config()
        self.flash_card.switch_btn.blockSignals(True)
        self.flash_card.switch_btn.setChecked(self.visual_config.get('flash_enabled', False))
        self.flash_card.switch_btn.blockSignals(False)
        
        self.kill_icon_card.switch_btn.blockSignals(True)
        self.kill_icon_card.switch_btn.setChecked(self.visual_config.get('kill_icon_enabled', False))
        self.kill_icon_card.switch_btn.blockSignals(False)
        
        self.death_card.switch_btn.blockSignals(True)
        self.death_card.switch_btn.setChecked(self.visual_config.get('death_media_enabled', False))
        self.death_card.switch_btn.blockSignals(False)
        
        self.boss_key_card.switch_btn.blockSignals(True)
        self.boss_key_card.switch_btn.setChecked(self.visual_config.get('boss_key_enabled', False))
        self.boss_key_card.switch_btn.blockSignals(False)
        
    def _save_config(self):
        self.config_manager.set('visual', self.visual_config)
        
    def _setup_ui(self):
        self.practical_group = SettingCardGroup("实用功能", self.view)
        
        # 1. 闪光弹设置
        self.flash_card = VisualSettingCard(
            icon=FIF.PHOTO,
            title="自定义闪光效果",
            content="当被闪白时，在屏幕上叠加自定义图片",
            parent=self.practical_group
        )
        self.flash_card.switch_btn.setChecked(self.visual_config.get('flash_enabled', False))
        self.flash_card.switch_btn.checkedChanged.connect(self._on_flash_switch_changed)
        self.flash_card.setting_btn.clicked.connect(lambda: self._open_settings('flash'))
        self.practical_group.addSettingCard(self.flash_card)
        
        # 2. 击杀图标设置
        self.kill_icon_card = VisualSettingCard(
            icon=FIF.GAME,
            title="击杀图标显示",
            content="在击杀敌人时，在屏幕下方显示击杀图标（支持1-5杀高阶配置）",
            parent=self.practical_group
        )
        self.kill_icon_card.switch_btn.setChecked(self.visual_config.get('kill_icon_enabled', False))
        self.kill_icon_card.switch_btn.checkedChanged.connect(self._on_kill_icon_switch_changed)
        self.kill_icon_card.setting_btn.clicked.connect(lambda: self._open_settings('kill_icon'))
        self.practical_group.addSettingCard(self.kill_icon_card)
        
        self.layout.addWidget(self.practical_group)

        self.entertainment_group = SettingCardGroup("娱乐功能", self.view)
        
        # 3. 死亡画面设置
        self.death_card = VisualSettingCard(
            icon=FIF.VIDEO,
            title="自定义死亡画面",
            content="死亡时在屏幕上播放指定的图片或视频",
            parent=self.entertainment_group
        )
        self.death_card.switch_btn.setChecked(self.visual_config.get('death_media_enabled', False))
        self.death_card.switch_btn.checkedChanged.connect(self._on_death_switch_changed)
        self.death_card.setting_btn.clicked.connect(lambda: self._open_settings('death'))
        self.entertainment_group.addSettingCard(self.death_card)
        
        # 4. 死亡一键切屏 (老板键)
        self.boss_key_card = VisualSettingCard(
            icon=FIF.HIDE,
            title="死亡一键切屏",
            content="死亡后自动最小化游戏并打开指定网页，新回合开始时自动切回",
            parent=self.entertainment_group
        )
        self.boss_key_card.switch_btn.setChecked(self.visual_config.get('boss_key_enabled', False))
        self.boss_key_card.switch_btn.checkedChanged.connect(self._on_boss_key_switch_changed)
        self.boss_key_card.setting_btn.clicked.connect(lambda: self._open_settings('boss_key'))
        self.entertainment_group.addSettingCard(self.boss_key_card)

        self.layout.addWidget(self.entertainment_group)

    def _open_settings(self, type):
        if type == 'kill_icon':
            dialog = KillIconDialog(self.config_manager, self)
        else:
            dialog = VisualConfigDialog(self.config_manager, type, self)
        dialog.exec()
        
    def _on_flash_switch_changed(self, is_checked):
        self.visual_config['flash_enabled'] = is_checked
        self._save_config()
        if hasattr(self.parent_window, 'home_tab'):
            self.parent_window.home_tab.flash_switch_card.switchButton.blockSignals(True)
            self.parent_window.home_tab.flash_switch_card.switchButton.setChecked(is_checked)
            self.parent_window.home_tab.flash_switch_card.switchButton.blockSignals(False)
            
    def _on_kill_icon_switch_changed(self, is_checked):
        self.visual_config['kill_icon_enabled'] = is_checked
        self._save_config()
        if hasattr(self.parent_window, 'home_tab'):
            self.parent_window.home_tab.kill_icon_switch_card.switchButton.blockSignals(True)
            self.parent_window.home_tab.kill_icon_switch_card.switchButton.setChecked(is_checked)
            self.parent_window.home_tab.kill_icon_switch_card.switchButton.blockSignals(False)
            
    def _on_death_switch_changed(self, is_checked):
        self.visual_config['death_media_enabled'] = is_checked
        self._save_config()
        if hasattr(self.parent_window, 'home_tab'):
            self.parent_window.home_tab.death_switch_card.switchButton.blockSignals(True)
            self.parent_window.home_tab.death_switch_card.switchButton.setChecked(is_checked)
            self.parent_window.home_tab.death_switch_card.switchButton.blockSignals(False)
            
    def _on_boss_key_switch_changed(self, is_checked):
        self.visual_config['boss_key_enabled'] = is_checked
        self._save_config()
        if hasattr(self.parent_window, 'home_tab'):
            self.parent_window.home_tab.boss_key_switch_card.switchButton.blockSignals(True)
            self.parent_window.home_tab.boss_key_switch_card.switchButton.setChecked(is_checked)
            self.parent_window.home_tab.boss_key_switch_card.switchButton.blockSignals(False)
