from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
from qfluentwidgets import (ScrollArea, ExpandLayout, SettingCardGroup,
                            SettingCard, SwitchButton, ComboBox, FluentIcon as FIF,
                            setTheme, Theme, PushButton, Slider, BodyLabel, MessageBoxBase, SubtitleLabel, LineEdit, CheckBox, PrimaryPushButton)
from PySide6.QtGui import QColor
import winreg
import sys
import os

class BackgroundSettingDialog(MessageBoxBase):
    """ 自定义背景设置对话框 """
    def __init__(self, config_manager, parent_window, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.parent_window = parent_window
        
        self.titleLabel = SubtitleLabel('自定义背景设置', self)
        
        # 将组件添加到布局中
        self.viewLayout.addWidget(self.titleLabel)
        
        # 图片选择
        selection_layout = QHBoxLayout()
        selection_layout.addWidget(BodyLabel("图片路径:"))
        self.path_label = BodyLabel("未选择")
        self.path_label.setStyleSheet("color: #666666;")
        
        bg_path = self.config_manager.get("bg_path", "")
        if bg_path:
            self.path_label.setText(os.path.basename(bg_path))
            
        selection_layout.addWidget(self.path_label, 1)
        self.select_btn = PushButton("选择图片", self)
        self.select_btn.clicked.connect(self._on_select_bg)
        selection_layout.addWidget(self.select_btn)
        
        self.clear_btn = PushButton("清除", self)
        self.clear_btn.clicked.connect(self._on_clear_bg)
        selection_layout.addWidget(self.clear_btn)
        
        self.viewLayout.addLayout(selection_layout)

        # 缩放方式
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(BodyLabel("缩放方式:"))
        self.scale_combo = ComboBox()
        self.scale_combo.addItems(["等比缩放", "填充", "拉伸", "居中"])
        self.scale_combo.setCurrentIndex(self.config_manager.get("bg_scale", 0))
        self.scale_combo.currentIndexChanged.connect(self._on_bg_scale_changed)
        scale_layout.addWidget(self.scale_combo)
        scale_layout.addStretch(1)
        self.viewLayout.addLayout(scale_layout)

        # 亮度
        bright_layout = QHBoxLayout()
        bright_layout.addWidget(BodyLabel("亮度:"))
        self.bright_slider = Slider(Qt.Horizontal)
        self.bright_slider.setRange(10, 100)
        self.bright_slider.setValue(self.config_manager.get("bg_bright", 100))
        self.bright_slider.valueChanged.connect(self._on_bg_bright_changed)
        bright_layout.addWidget(self.bright_slider)
        self.viewLayout.addLayout(bright_layout)
        
        # 模糊
        blur_layout = QHBoxLayout()
        blur_layout.addWidget(BodyLabel("模糊:"))
        self.blur_slider = Slider(Qt.Horizontal)
        self.blur_slider.setRange(0, 50)
        self.blur_slider.setValue(self.config_manager.get("bg_blur", 0))
        self.blur_slider.valueChanged.connect(self._on_bg_blur_changed)
        blur_layout.addWidget(self.blur_slider)
        self.viewLayout.addLayout(blur_layout)
        
        self.widget.setMinimumWidth(360)

    def _on_select_bg(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择背景图片", "", "图片文件 (*.png *.jpg *.jpeg)")
        if path:
            self.config_manager.set("bg_path", path)
            self.path_label.setText(os.path.basename(path))
            if hasattr(self.parent_window, 'apply_custom_background'):
                self.parent_window.apply_custom_background()

    def _on_clear_bg(self):
        self.config_manager.set("bg_path", "")
        self.path_label.setText("未选择")
        if hasattr(self.parent_window, 'apply_custom_background'):
            self.parent_window.apply_custom_background()

    def _on_bg_scale_changed(self, index):
        self.config_manager.set("bg_scale", index)
        if hasattr(self.parent_window, 'apply_custom_background'):
            self.parent_window.apply_custom_background()

    def _on_bg_bright_changed(self, value):
        self.config_manager.set("bg_bright", value)
        if hasattr(self.parent_window, 'apply_custom_background'):
            self.parent_window.apply_custom_background()

    def _on_bg_blur_changed(self, value):
        self.config_manager.set("bg_blur", value)
        if hasattr(self.parent_window, 'apply_custom_background'):
            self.parent_window.apply_custom_background()

class BackgroundSettingCard(SettingCard):
    def __init__(self, icon, title, content=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.config_btn = PushButton("设置背景", self)
        self.hBoxLayout.addWidget(self.config_btn, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

class MySwitchSettingCard(SettingCard):
    def __init__(self, icon, title, content=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.switchButton = SwitchButton("关", self)
        self.switchButton.setOnText("开")
        self.switchButton.setOffText("关")
        self.hBoxLayout.addWidget(self.switchButton, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

class MyComboBoxSettingCard(SettingCard):
    def __init__(self, icon, title, content=None, texts=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.comboBox = ComboBox(self)
        if texts:
            self.comboBox.addItems(texts)
        self.hBoxLayout.addWidget(self.comboBox, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

class ExportConfigDialog(MessageBoxBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel('导出配置', self)
        self.viewLayout.addWidget(self.titleLabel)
        
        self.name_input = LineEdit(self)
        self.name_input.setPlaceholderText("请输入配置名称 (必填)")
        self.name_input.textChanged.connect(self._validate)
        self.viewLayout.addWidget(self.name_input)
        
        self.desc_input = LineEdit(self)
        self.desc_input.setPlaceholderText("请输入配置描述 (可选)")
        self.viewLayout.addWidget(self.desc_input)
        
        self.viewLayout.addWidget(BodyLabel("请选择要导出的资源 (包括预设及当前正在使用的资源):"))
        
        self.checkboxes = {}
        options = {
            "bg": "自定义软件背景",
            "video": "开屏动画",
            "sound": "启动音效",
            "font": "全局字体",
            "visual": "游戏内视觉效果 (闪白/击杀/死亡)",
            "gsi": "游戏内实时音效配置"
        }
        
        for key, label in options.items():
            cb = CheckBox(label, self)
            cb.setChecked(True)
            self.viewLayout.addWidget(cb)
            self.checkboxes[key] = cb
        
        self.widget.setMinimumWidth(350)
        self.yesButton.setDisabled(True)
        
    def _validate(self, text):
        self.yesButton.setDisabled(not bool(text.strip()))
        
    def get_data(self):
        selections = {k: cb.isChecked() for k, cb in self.checkboxes.items()}
        return self.name_input.text().strip(), self.desc_input.text().strip(), selections

class ImportConfirmDialog(MessageBoxBase):
    def __init__(self, meta, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel('确认导入配置', self)
        self.viewLayout.addWidget(self.titleLabel)
        
        name = meta.get("name", "未知")
        desc = meta.get("description", "无描述信息")
        included_resources = meta.get("included_resources", [])
        
        self.viewLayout.addWidget(BodyLabel(f"配置名称: {name}"))
        self.viewLayout.addWidget(BodyLabel(f"配置描述: {desc}"))
        
        if included_resources:
            self.viewLayout.addWidget(BodyLabel("包含以下资源:"))
            for res in included_resources:
                self.viewLayout.addWidget(BodyLabel(f" • {res}"))
        
        warning = BodyLabel("导入将覆盖当前对应的设置，是否继续？")
        warning.setStyleSheet("color: #d40000; margin-top: 10px;")
        self.viewLayout.addWidget(warning)
        
        self.widget.setMinimumWidth(350)

class QuickSwitchConfigCard(SettingCard):
    def __init__(self, icon, title, content=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.comboBox = ComboBox(self)
        self.comboBox.setMinimumWidth(150)
        self.apply_btn = PushButton("应用", self)
        self.open_folder_btn = PushButton("打开文件夹", self)
        
        self.hBoxLayout.addWidget(self.comboBox, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(8)
        self.hBoxLayout.addWidget(self.apply_btn, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(8)
        self.hBoxLayout.addWidget(self.open_folder_btn, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

class ExportImportCard(SettingCard):
    def __init__(self, icon, title, content=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.import_btn = PushButton("导入配置", self)
        self.export_btn = PushButton("导出配置", self)
        self.hBoxLayout.addWidget(self.import_btn, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addWidget(self.export_btn, 0, Qt.AlignmentFlag.AlignRight)
        self.hBoxLayout.addSpacing(16)

class SettingPage(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.parent_window = parent
        self.config_manager = parent.config_manager

        self.view = QWidget(self)
        self.expandLayout = ExpandLayout(self.view)
        
        self.setObjectName("setting_page")
        self.view.setObjectName("setting_view")
        self.setWidget(self.view)
        self.setWidgetResizable(True)
        self.setStyleSheet("QScrollArea {background: transparent; border: none;}")
        self.view.setStyleSheet("QWidget#setting_view {background: transparent;}")

        self._init_ui()

    def _init_ui(self):
        # 1. 个性化设置组
        self.personalGroup = SettingCardGroup("个性化", self.view)
        
        # 主题设置
        theme_val = self.config_manager.get("theme", "Auto")
        
        self.themeCard = MyComboBoxSettingCard(
            icon=FIF.BRIGHTNESS,
            title="应用主题",
            content="更改应用程序的外观",
            texts=["浅色", "深色", "跟随系统"],
            parent=self.personalGroup
        )
        # 初始化选中项
        idx_map = {"Light": 0, "Dark": 1, "Auto": 2}
        self.themeCard.comboBox.setCurrentIndex(idx_map.get(theme_val, 2))
        self.themeCard.comboBox.currentIndexChanged.connect(self._on_theme_changed)
        self.personalGroup.addSettingCard(self.themeCard)
        
        # 背景设置
        self.bgCard = BackgroundSettingCard(
            icon=FIF.PHOTO,
            title="自定义背景",
            content="配置软件背景图片及其显示效果",
            parent=self.personalGroup
        )
        self.bgCard.config_btn.clicked.connect(self._show_bg_dialog)
        self.personalGroup.addSettingCard(self.bgCard)
        
        # 2. 系统行为设置组
        self.systemGroup = SettingCardGroup("系统", self.view)
        
        # 关闭行为
        close_val = self.config_manager.get("close_behavior", "prompt")
        
        self.closeCard = MyComboBoxSettingCard(
            icon=FIF.CLOSE,
            title="关闭窗口行为",
            content="点击右上角关闭按钮时的动作",
            texts=["每次询问", "最小化到托盘", "完全退出"],
            parent=self.systemGroup
        )
        idx_close_map = {"prompt": 0, "tray": 1, "exit": 2}
        self.closeCard.comboBox.setCurrentIndex(idx_close_map.get(close_val, 0))
        self.closeCard.comboBox.currentIndexChanged.connect(self._on_close_behavior_changed)
        self.systemGroup.addSettingCard(self.closeCard)
        
        # 开机自启
        auto_start_val = self.config_manager.get("auto_start", False)
        self.autoStartCard = MySwitchSettingCard(
            icon=FIF.POWER_BUTTON,
            title="开机自启",
            content="在系统登录时自动运行此程序",
            parent=self.systemGroup
        )
        self.autoStartCard.switchButton.setChecked(auto_start_val)
        self.autoStartCard.switchButton.checkedChanged.connect(self._on_auto_start_changed)
        self.systemGroup.addSettingCard(self.autoStartCard)

        # 3. 配置管理组
        self.configGroup = SettingCardGroup("配置管理", self.view)
        
        self.exportImportCard = ExportImportCard(
            icon=FIF.FOLDER,
            title="导入与导出",
            content="将当前的所有设置及资源文件打包导出，或从压缩包中导入并覆盖当前配置",
            parent=self.configGroup
        )
        self.exportImportCard.export_btn.clicked.connect(self._on_export_config)
        self.exportImportCard.import_btn.clicked.connect(self._on_import_config)
        self.configGroup.addSettingCard(self.exportImportCard)

        self.quickSwitchCard = QuickSwitchConfigCard(
            icon=FIF.SYNC,
            title="快捷切换配置",
            content="快速应用已保存的配置包",
            parent=self.configGroup
        )
        self.quickSwitchCard.apply_btn.clicked.connect(self._on_quick_switch)
        self.quickSwitchCard.open_folder_btn.clicked.connect(self._on_open_config_folder)
        self.configGroup.addSettingCard(self.quickSwitchCard)

        # 4. 危险操作组
        self.dangerGroup = SettingCardGroup("高级与危险操作", self.view)
        
        self.resetCard = SettingCard(
            FIF.DELETE,
            "重置所有设置",
            "将软件设置恢复为默认，并尝试清除已替换的开屏动画、音效、字体及自定义资源",
            self.dangerGroup
        )
        self.reset_btn = PrimaryPushButton("恢复默认", self.resetCard)
        self.reset_btn.setStyleSheet("QPushButton { background-color: #c42b1c; border: 1px solid #c42b1c; border-radius: 4px; padding: 5px 15px; } QPushButton:hover { background-color: #b02719; }")
        self.resetCard.hBoxLayout.addWidget(self.reset_btn, 0, Qt.AlignmentFlag.AlignRight)
        self.resetCard.hBoxLayout.addSpacing(16)
        self.reset_btn.clicked.connect(self._on_reset_all)
        self.dangerGroup.addSettingCard(self.resetCard)

        self.expandLayout.addWidget(self.personalGroup)
        self.expandLayout.addWidget(self.systemGroup)
        self.expandLayout.addWidget(self.configGroup)
        self.expandLayout.addWidget(self.dangerGroup)
        
        self._load_quick_switch_configs()

    def _show_bg_dialog(self):
        dialog = BackgroundSettingDialog(self.config_manager, self.parent_window, self)
        dialog.exec()

    def _on_reset_all(self):
        dialog = MessageBoxBase(self.parent_window)
        dialog.titleLabel = SubtitleLabel("确认重置所有设置？", dialog)
        dialog.viewLayout.addWidget(dialog.titleLabel)
        
        warning = BodyLabel("此操作将清除您在软件内保存的所有预设、事件、自定义图片，并尝试移除游戏中已替换的视频、音效和字体。此操作不可逆！\n\n注意：如果遇到游戏资源问题，请通过 Steam 验证游戏完整性。")
        warning.setWordWrap(True)
        dialog.viewLayout.addWidget(warning)
        dialog.widget.setMinimumWidth(380)
        
        if dialog.exec():
            # 1. 恢复游戏资源
            steam_path = self.parent_window.steam_path
            if steam_path and os.path.exists(steam_path):
                from ...logic.steam_utils import SteamUtils
                steam_lib = SteamUtils.extract_steam_library_from_cs2_path(steam_path)
                
                # 恢复音效
                from ...logic.sound_replacer import SoundReplacer
                SoundReplacer(steam_path).restore_sound()
                
                if steam_lib:
                    # 恢复字体
                    from ...logic.font_replacer import FontReplacer
                    replacer = FontReplacer(steam_lib)
                    if hasattr(replacer, 'restore_font'):
                        replacer.restore_font()
                        
                    # 恢复视频
                    from ...logic.video_replacer import VideoReplacer
                    v_replacer = VideoReplacer(steam_lib)
                    if hasattr(v_replacer, 'restore_video'):
                        v_replacer.restore_video()

            # 2. 恢复软件配置
            self.config_manager.reset_all()
            
            # 3. 刷新 UI
            self.parent_window.show_success("重置成功", "所有设置已恢复为初始状态。")
            self.parent_window.load_all_presets()
            self.parent_window.update_home_status()
            self.parent_window.apply_custom_background()
            if hasattr(self.parent_window, 'integrated_sound_page'):
                self.parent_window.integrated_sound_page.load_events()
            if hasattr(self.parent_window, 'visual_tab'):
                self.parent_window.visual_tab.config_manager = self.config_manager
                self.parent_window.visual_tab._update_ui_from_config()
                
            # 刷新主题
            self.themeCard.comboBox.blockSignals(True)
            self.themeCard.comboBox.setCurrentIndex(2) # Auto
            self.themeCard.comboBox.blockSignals(False)
            self._on_theme_changed(2)

    def _on_theme_changed(self, index):
        val_map = {0: "Light", 1: "Dark", 2: "Auto"}
        theme_val = val_map.get(index, "Auto")
        self.config_manager.set("theme", theme_val)
        
        if theme_val == "Light":
            setTheme(Theme.LIGHT)
            self.parent_window.is_dark_mode = False
        elif theme_val == "Dark":
            setTheme(Theme.DARK)
            self.parent_window.is_dark_mode = True
        else:
            setTheme(Theme.AUTO)
            # Auto模式下判断实际颜色较为复杂，这里简单处理
            self.parent_window.is_dark_mode = False

    def _on_close_behavior_changed(self, index):
        val_map = {0: "prompt", 1: "tray", 2: "exit"}
        behavior = val_map.get(index, "prompt")
        self.config_manager.set("close_behavior", behavior)
        # 如果用户主动修改了这个选项，我们将 hide_close_prompt 置为 True
        if behavior != "prompt":
            self.config_manager.set("hide_close_prompt", True)
        else:
            self.config_manager.set("hide_close_prompt", False)

    def _on_auto_start_changed(self, is_checked):
        self.config_manager.set("auto_start", is_checked)
        self._set_windows_auto_start(is_checked)

    def _on_export_config(self):
        dialog = ExportConfigDialog(self)
        if dialog.exec():
            name, desc, selections = dialog.get_data()
            default_path = os.path.join(self.config_manager.configs_dir, f"{name}.zip")
            path, _ = QFileDialog.getSaveFileName(self, "导出配置", default_path, "ZIP 压缩包 (*.zip)")
            if path:
                success, msg = self.config_manager.export_config(path, name, desc, selections)
                if success:
                    # 如果用户选择保存到别的地方，我们也保存一份到 configs_dir 以便快捷切换
                    if os.path.dirname(os.path.abspath(path)) != os.path.abspath(self.config_manager.configs_dir):
                        import shutil
                        try:
                            shutil.copy2(path, os.path.join(self.config_manager.configs_dir, os.path.basename(path)))
                        except Exception:
                            pass
                    self._load_quick_switch_configs()
                    self.parent_window.show_success("导出成功", msg)
                else:
                    self.parent_window.show_error("导出失败", msg)

    def _on_import_config(self):
        path, _ = QFileDialog.getOpenFileName(self, "导入配置", "", "ZIP 压缩包 (*.zip)")
        if path:
            if not self.config_manager.is_valid_config_zip(path):
                self.parent_window.show_error("导入失败", "这不是有效的CS2Toolkit配置包。")
                return
                
            meta = self.config_manager.get_zip_meta(path)
            dialog = ImportConfirmDialog(meta, self)
            if dialog.exec():
                import shutil
                dest_path = os.path.join(self.config_manager.configs_dir, os.path.basename(path))
                if os.path.abspath(path) != os.path.abspath(dest_path):
                    try:
                        if os.path.exists(dest_path):
                            import time
                            base, ext = os.path.splitext(os.path.basename(path))
                            dest_path = os.path.join(self.config_manager.configs_dir, f"{base}_{int(time.time())}{ext}")
                        shutil.copy2(path, dest_path)
                    except Exception as e:
                        print(f"复制配置文件失败: {e}")
                        dest_path = path

                self._apply_config_zip(dest_path)
                self._load_quick_switch_configs()

    def _on_quick_switch(self):
        idx = self.quickSwitchCard.comboBox.currentIndex()
        if idx >= 0:
            zip_path = self.quickSwitchCard.comboBox.itemData(idx)
            if zip_path and os.path.exists(zip_path):
                meta = self.config_manager.get_zip_meta(zip_path)
                dialog = ImportConfirmDialog(meta, self)
                if dialog.exec():
                    self._apply_config_zip(zip_path)
            else:
                self.parent_window.show_error("错误", "配置文件不存在。")
                self._load_quick_switch_configs()

    def _apply_config_zip(self, zip_path):
        success, msg = self.config_manager.import_config(zip_path)
        if success:
            self.parent_window.show_success("导入成功", "配置导入成功，界面即将刷新。")
            
            # Apply imported current selections to game files
            current_video = self.config_manager.get("current_video")
            if current_video:
                video_path = self.config_manager.get("current_video_path")
                if video_path and os.path.exists(video_path):
                    from ...logic.video_replacer import VideoReplacer
                    from ...logic.steam_utils import SteamUtils
                    steam_lib = SteamUtils.extract_steam_library_from_cs2_path(self.parent_window.steam_path)
                    if steam_lib:
                        replacer = VideoReplacer(steam_lib)
                        replacer.replace_video(video_path)
                        
            current_sound = self.config_manager.get("current_sound")
            if current_sound:
                sound_path = self.config_manager.get("current_sound_path")
                if sound_path and os.path.exists(sound_path):
                    from ...logic.sound_replacer import SoundReplacer
                    replacer = SoundReplacer(self.parent_window.steam_path)
                    replacer.replace_sound(sound_path)
                        
            current_font = self.config_manager.get("current_font")
            if current_font:
                font_path = self.config_manager.get("current_font_path")
                if font_path and os.path.exists(font_path):
                    from ...logic.font_replacer import FontReplacer
                    from ...logic.steam_utils import SteamUtils
                    steam_lib = SteamUtils.extract_steam_library_from_cs2_path(self.parent_window.steam_path)
                    if steam_lib:
                        replacer = FontReplacer(steam_lib)
                        replacer.replace_font(font_path, lambda msg: None)
            
            self.parent_window.load_all_presets()
            self.parent_window.update_home_status()
            self.parent_window.apply_custom_background()
            if hasattr(self.parent_window, 'integrated_sound_page'):
                self.parent_window.integrated_sound_page.load_events()
            if hasattr(self.parent_window, 'visual_tab'):
                self.parent_window.visual_tab.config_manager = self.config_manager
                self.parent_window.visual_tab._update_ui_from_config()
            
            # 刷新主题
            theme_val = self.config_manager.get("theme", "Auto")
            idx_map = {"Light": 0, "Dark": 1, "Auto": 2}
            self.themeCard.comboBox.blockSignals(True)
            self.themeCard.comboBox.setCurrentIndex(idx_map.get(theme_val, 2))
            self.themeCard.comboBox.blockSignals(False)
            self._on_theme_changed(idx_map.get(theme_val, 2))
            
        else:
            self.parent_window.show_error("导入失败", msg)

    def _load_quick_switch_configs(self):
        self.quickSwitchCard.comboBox.clear()
        configs_dir = self.config_manager.configs_dir
        if not os.path.exists(configs_dir):
            return
            
        for f in os.listdir(configs_dir):
            if f.endswith('.zip'):
                zip_path = os.path.join(configs_dir, f)
                if self.config_manager.is_valid_config_zip(zip_path):
                    meta = self.config_manager.get_zip_meta(zip_path)
                    name = meta.get("name", f)
                    self.quickSwitchCard.comboBox.addItem(name, userData=zip_path)

    def _on_open_config_folder(self):
        import os
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        configs_dir = self.config_manager.configs_dir
        if not os.path.exists(configs_dir):
            os.makedirs(configs_dir, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(configs_dir))

    def _set_windows_auto_start(self, enable: bool):
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        app_name = "CS2Toolkit"
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            if enable:
                exe_path = sys.executable
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, f'"{exe_path}"')
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"设置开机自启失败: {e}")