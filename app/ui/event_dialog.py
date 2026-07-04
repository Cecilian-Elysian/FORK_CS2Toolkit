from PySide6.QtWidgets import QWidget, QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QFileDialog, QDialogButtonBox, QGroupBox, QGridLayout, QCompleter
from PySide6.QtCore import Qt
from qfluentwidgets import (
    TitleLabel, SubtitleLabel, BodyLabel, LineEdit, ComboBox, 
    PushButton, Slider, MessageBox, CheckBox, EditableComboBox, MessageBoxBase
)
import os



class AddEventDialog(MessageBoxBase):
    # 添加GSI事件的对话框
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sound_path = ""

        # Remove the TitleLabel we previously added since we use MessageBoxBase's title now
        self.titleLabel = SubtitleLabel('添加新的事件', self)
        self.viewLayout.addWidget(self.titleLabel)

        self._setup_ui()
        self.widget.setMinimumWidth(500)
        
        # Override the button texts from MessageBoxBase
        self.yesButton.setText('确定')
        self.cancelButton.setText('取消')
        
    def _setup_ui(self):
        # 表单布局
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # 事件类型选择
        self.event_type_combo = ComboBox()
        # 分类添加事件类型
        event_items = [
            "--- 全局音效 ---",
            "全局击杀",
            "C4安装", 
            "C4拆除",
            "玩家死亡",
            "--- 其他音效 ---",
            "切换到",
            "换弹", 
            "使用武器击杀",
            "道具投出"
        ]
        self.event_type_combo.addItems(event_items)
        self.event_type_combo.currentIndexChanged.connect(self._on_event_type_changed)
        form_layout.addRow(BodyLabel("事件类型:"), self.event_type_combo)
        
        # 武器名称输入
        self.weapon_name_input = EditableComboBox()
        self.weapon_name_input.setPlaceholderText("选择或输入武器名称")
        
        # 武器名称中文映射
        weapon_names_cn = [
            "所有枪械",
            "AK-47", "M4A4", "M4A1-S消音版", "AWP",
            "沙漠之鹰", "R8 左轮", "格洛克18", "USP消音版", "P250",
            "Five-SeveN", "Tec-9", "CZ75-Auto", "P2000",
            "双持贝瑞塔", "P90", "PP-Bizon", "MAC-10",
            "MP7", "MP9", "MP5-SD", "UMP-45", "XM1014",
            "短管霰弹枪", "新星", "MAG-7", "内格夫",
            "M249", "加利尔AR", "法玛斯", "SG 553",
            "AUG", "SCAR-20", "G3SG1", "SSG 08",
            "电击枪 (Zeus x27)", "默认刀", "T方默认刀", "刺刀", "海豹短刀", "折叠刀",
            "穿肠刀", "爪子刀", "M9刺刀", "猎杀者匕首", "弯刀",
            "鲍伊猎刀", "蝴蝶刀", "暗影双匕", "系绳匕首", "求生匕首",
            "熊刀", "折刀", "流浪者匕首", "短剑", "锯齿爪刀",
            "骷髅匕首", "廓尔喀刀"
        ]
        
        # 对应的英文武器名称（用于配置保存）
        weapon_names_en = [
            "all_weapons",
            "weapon_ak47", "weapon_m4a1", "weapon_m4a1_silencer", "weapon_awp",
            "weapon_deagle", "weapon_revolver", "weapon_glock", "weapon_usp_silencer", "weapon_p250",
            "weapon_fiveseven", "weapon_tec9", "weapon_cz75a", "weapon_p2000",
            "weapon_elite", "weapon_p90", "weapon_bizon", "weapon_mac10",
            "weapon_mp7", "weapon_mp9", "weapon_mp5sd", "weapon_ump45", "weapon_xm1014",
            "weapon_sawedoff", "weapon_nova", "weapon_mag7", "weapon_negev",
            "weapon_m249", "weapon_galilar", "weapon_famas", "weapon_sg556",
            "weapon_aug", "weapon_scar20", "weapon_g3sg1", "weapon_ssg08",
            "weapon_taser", "weapon_knife", "weapon_knife_t", "weapon_bayonet", "weapon_knife_css", "weapon_knife_flip",
            "weapon_knife_gut", "weapon_knife_karambit", "weapon_knife_m9_bayonet", "weapon_knife_huntsman", "weapon_knife_falchion",
            "weapon_knife_survival_bowie", "weapon_knife_butterfly", "weapon_knife_push", "weapon_knife_cord", "weapon_knife_tactical",
            "weapon_knife_ursus", "weapon_knife_gypsy_jackknife", "weapon_knife_nomad", "weapon_knife_stiletto", "weapon_knife_widowmaker",
            "weapon_knife_skeleton", "weapon_knife_kukri"
        ]
        
        self.grenade_names_cn = [
            "所有道具", "闪光弹", "烟雾弹", "高爆手雷", "燃烧弹/燃烧瓶", "诱饵弹"
        ]
        self.grenade_names_en = [
            "all_grenades", "weapon_flashbang", "weapon_smokegrenade", "weapon_hegrenade", "weapon_molotov", "weapon_decoy"
        ]
        
        # 创建中英文映射字典
        self.weapon_cn_to_en = dict(zip(weapon_names_cn, weapon_names_en))
        self.weapon_en_to_cn = dict(zip(weapon_names_en, weapon_names_cn))
        self.weapon_cn_to_en.update(dict(zip(self.grenade_names_cn, self.grenade_names_en)))
        self.weapon_en_to_cn.update(dict(zip(self.grenade_names_en, self.grenade_names_cn)))
        
        # 保留原有的列表以供切换
        self.weapon_names_cn_list = weapon_names_cn
        
        self.weapon_name_input.addItems(weapon_names_cn)
        
        # 添加搜索/自动补全功能
        self.completer = QCompleter(weapon_names_cn, self)
        self.completer.setFilterMode(Qt.MatchContains)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.weapon_name_input.setCompleter(self.completer)
        
        self.weapon_name_label = BodyLabel("武器名称:")
        form_layout.addRow(self.weapon_name_label, self.weapon_name_input)
        
        # 连杀配置选项 (仅在击杀事件时显示)
        self.advanced_checkbox = CheckBox("启用连杀音效配置 (分别为1杀到5杀设置不同音效)")
        self.advanced_checkbox.stateChanged.connect(self._on_advanced_changed)
        self.advanced_checkbox.hide()
        form_layout.addRow(self.advanced_checkbox)
        
        # 基础音效配置容器
        self.basic_container = QWidget()
        basic_layout = QFormLayout(self.basic_container)
        basic_layout.setContentsMargins(0, 0, 0, 0)
        
        # 音效文件选择
        sound_layout = QHBoxLayout()
        self.sound_path_input = LineEdit()
        self.sound_path_input.setPlaceholderText("选择音效文件")
        self.sound_path_input.setReadOnly(True)
        self.browse_sound_btn = PushButton("浏览")
        self.browse_sound_btn.clicked.connect(self._browse_sound_file)
        sound_layout.addWidget(self.sound_path_input)
        sound_layout.addWidget(self.browse_sound_btn)
        basic_layout.addRow(BodyLabel("音效文件:"), sound_layout)
        
        # 音量控制
        volume_layout = QHBoxLayout()
        self.volume_slider = Slider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setFixedWidth(200)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        self.volume_label = BodyLabel("50%")
        self.volume_label.setFixedWidth(40)
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_label)
        volume_layout.addStretch()
        basic_layout.addRow(BodyLabel("音量:"), volume_layout)
        
        form_layout.addRow(self.basic_container)
        
        # 连杀配置容器
        self.advanced_container = QWidget()
        advanced_layout = QFormLayout(self.advanced_container)
        advanced_layout.setContentsMargins(0, 0, 0, 0)
        self.advanced_inputs = []
        
        for i in range(1, 6):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            
            path_input = LineEdit()
            path_input.setPlaceholderText(f"选择 {i}杀 音效")
            path_input.setReadOnly(True)
            
            browse_btn = PushButton("浏览")
            # 捕获循环变量
            browse_btn.clicked.connect(lambda checked, idx=i-1: self._browse_advanced_sound(idx))
            
            vol_slider = Slider(Qt.Horizontal)
            vol_slider.setRange(0, 100)
            vol_slider.setValue(50)
            vol_slider.setFixedWidth(100)
            
            vol_label = BodyLabel("50%")
            vol_label.setFixedWidth(35)
            
            vol_slider.valueChanged.connect(lambda val, lbl=vol_label: lbl.setText(f"{val}%"))
            
            row_layout.addWidget(path_input, 1)
            row_layout.addWidget(browse_btn)
            row_layout.addWidget(BodyLabel("音量:"))
            row_layout.addWidget(vol_slider)
            row_layout.addWidget(vol_label)
            
            advanced_layout.addRow(BodyLabel(f"{i} 杀:"), row_widget)
            
            self.advanced_inputs.append({
                "path_input": path_input,
                "vol_slider": vol_slider,
                "path": ""
            })
            
        self.advanced_container.hide()
        form_layout.addRow(self.advanced_container)
        
        self.viewLayout.addLayout(form_layout)
        self.viewLayout.addSpacing(20)
        
        # 移除QDialogButtonBox，因为MessageBoxBase已经有了
        # 验证按钮事件
        self.yesButton.clicked.disconnect()  # disconnect default
        self.yesButton.clicked.connect(self._validate_and_accept)
        
        # 初始化状态
        self.event_type_combo.setCurrentIndex(1)  # 默认选择"全局击杀"
        self._on_event_type_changed(1)
        
    def _on_advanced_changed(self, state):
        # 修正: qfluentwidgets.CheckBox 的 stateChanged 发出的 state 可能是 2 (Qt.CheckState.Checked) 或布尔值
        # 考虑到兼容性，我们可以直接检查 isChecked() 状态
        is_checked = self.advanced_checkbox.isChecked()
        if is_checked:
            self.basic_container.hide()
            self.advanced_container.show()
        else:
            self.basic_container.show()
            self.advanced_container.hide()
            
    def _browse_advanced_sound(self, idx):
        path, _ = QFileDialog.getOpenFileName(self, f"选择 {idx+1}杀 音效文件", "", "音效文件 (*.mp3 *.wav)")
        if path:
            self.advanced_inputs[idx]["path"] = path
            self.advanced_inputs[idx]["path_input"].setText(os.path.basename(path))
            self.advanced_inputs[idx]["path_input"].setToolTip(path)
            
    def _on_event_type_changed(self, index):
        # 当事件类型改变时调用
        # 防止选择分类标题
        if index in [0, 5]:  # 分类标题索引
            # 如果选择了分类标题，跳转到下一个有效选项
            if index == 0:  # 全局音效分类
                # 阻止信号触发，避免递归调用
                self.event_type_combo.blockSignals(True)
                self.event_type_combo.setCurrentIndex(1)  # 跳转到"全局击杀"
                self.event_type_combo.blockSignals(False)
                # 手动调用更新逻辑
                index = 1
            elif index == 5:  # 其他音效分类
                # 阻止信号触发，避免递归调用
                self.event_type_combo.blockSignals(True)
                self.event_type_combo.setCurrentIndex(6)  # 跳转到"切换到"
                self.event_type_combo.blockSignals(False)
                # 手动调用更新逻辑
                index = 6
        


        # 根据事件类型更新UI状态
        self._update_ui_state_for_event_type(index)
    
    def _update_ui_state_for_event_type(self, index):
        # 根据事件类型索引更新UI控件状态
        # 只有击杀类事件显示连杀配置选项
        if index in [1, 8]: # 1:全局击杀 8:使用武器击杀
            self.advanced_checkbox.show()
        else:
            self.advanced_checkbox.hide()
            self.advanced_checkbox.setChecked(False)
            
        if index in [1, 2, 3, 4]:  # 全局击杀、C4安装、C4拆除、玩家死亡（全局事件）
            self.weapon_name_input.setCurrentText("全局事件")
            self.weapon_name_label.hide()
            self.weapon_name_input.hide()
            self.browse_sound_btn.setEnabled(True)
            self.sound_path_input.setEnabled(True)
        elif index == 9: # 道具投出
            self.weapon_name_label.setText("道具名称:")
            self.weapon_name_label.show()
            self.weapon_name_input.show()
            self.weapon_name_input.setEnabled(True)
            
            # 切换为道具列表
            self.weapon_name_input.clear()
            self.weapon_name_input.addItems(self.grenade_names_cn)
            
            from PySide6.QtCore import QStringListModel
            model = QStringListModel(self.grenade_names_cn)
            self.completer.setModel(model)
        else:  # 其他事件：使用武器击杀、切换到、换弹
            self.weapon_name_label.setText("武器名称:")
            self.weapon_name_label.show()
            self.weapon_name_input.show()
            self.weapon_name_input.setEnabled(True)
            
            # 切换为武器列表
            current_text = self.weapon_name_input.currentText()
            self.weapon_name_input.clear()
            self.weapon_name_input.addItems(self.weapon_names_cn_list)
            if current_text in self.weapon_names_cn_list:
                self.weapon_name_input.setCurrentText(current_text)
            elif current_text == "全局事件" or current_text in self.grenade_names_cn:
                self.weapon_name_input.setCurrentText("")
                
            from PySide6.QtCore import QStringListModel
            model = QStringListModel(self.weapon_names_cn_list)
            self.completer.setModel(model)
    
    def _on_volume_changed(self, value):
        # 当音量滑块值改变时更新显示
        self.volume_label.setText(f"{value}%")
        self.volume_slider.setToolTip(f"音量: {value}%")
    

    
    def _browse_sound_file(self):
        # 浏览音效文件
        path, _ = QFileDialog.getOpenFileName(self, "选择音效文件", "", "音效文件 (*.mp3 *.wav)")
        if path:
            self.sound_path = path
            self.sound_path_input.setText(os.path.basename(path))
            self.sound_path_input.setToolTip(path)
    
    def _validate_and_accept(self):
        # 验证输入并接受对话框
        # 验证武器名称
        weapon_name = self.weapon_name_input.currentText().strip()
        if not weapon_name:
            MessageBox("错误", "请输入武器名称", self).exec()
            return
        
        is_advanced = self.advanced_checkbox.isChecked()
        
        if is_advanced:
            # 验证连杀音效文件（至少选择一个）
            has_any_sound = False
            for idx, item in enumerate(self.advanced_inputs):
                if item["path"]:
                    has_any_sound = True
                    if not os.path.exists(item["path"]):
                        MessageBox("错误", f"{idx+1}杀音效文件不存在", self).exec()
                        return
            if not has_any_sound:
                MessageBox("错误", "请至少为连杀配置选择一个音效文件", self).exec()
                return
        else:
            # 验证基础音效文件
            if not self.sound_path:
                MessageBox("错误", "请选择音效文件", self).exec()
                return
            
            if not os.path.exists(self.sound_path):
                MessageBox("错误", "音效文件不存在", self).exec()
                return
        
        self.accept()
    
    def get_config(self):
        # 获取配置信息
        weapon_name_cn = self.weapon_name_input.currentText().strip()
        # 将中文武器名称转换为英文（用于配置保存）
        weapon_name = self.weapon_cn_to_en.get(weapon_name_cn, weapon_name_cn)
        event_index = self.event_type_combo.currentIndex()
        
        # 使用索引映射，与components.py保持一致
        event_mapping = {
            1: "kill",           # 全局击杀
            2: "bomb_planted",   # C4安装
            3: "bomb_defused",   # C4拆除
            4: "player_death",   # 玩家死亡
            6: "active",         # 切换到
            7: "reloading",      # 换弹
            8: "weapon_kill",    # 使用武器击杀
            9: "grenade_thrown"  # 道具投出
        }
        event_type = event_mapping.get(event_index, "active")
        
        # 为全局事件设置正确的武器名称
        if event_index in [1, 2, 3, 4]:  # 全局事件
            weapon_name = "全局事件"
        
        # 为事件生成名称
        if event_index == 1:
            name = "全局击杀音效"
        elif event_index == 2:
            name = "C4安装音效"
        elif event_index == 3:
            name = "C4拆除音效"
        elif event_index == 4:
            name = "玩家死亡音效"
        else:
            name = f"{weapon_name}_{event_type}"
        
        config = {
            "name": name,
            "weapon": weapon_name,
            "event": event_type,
            "volume": self.volume_slider.value(),
            "enabled": True,
            "sound": self.sound_path,
            "is_advanced": self.advanced_checkbox.isChecked()
        }
        
        if config["is_advanced"]:
            sounds_1_5 = []
            for item in self.advanced_inputs:
                sounds_1_5.append({
                    "path": item["path"],
                    "volume": item["vol_slider"].value()
                })
            config["sounds_1_5"] = sounds_1_5
        
        return config
    
    def set_config(self, config):
        # 设置配置信息
        weapon_name = config.get("weapon", "")
        if weapon_name:
            # 将英文武器名称转换为中文显示
            weapon_name_cn = self.weapon_en_to_cn.get(weapon_name, weapon_name)
            # 查找是否在下拉列表中存在该武器名称
            index = self.weapon_name_input.findText(weapon_name_cn)
            if index >= 0:
                self.weapon_name_input.setCurrentIndex(index)
            else:
                # 如果不存在，设置为可编辑文本
                self.weapon_name_input.setCurrentText(weapon_name_cn)
        
        event_type = config.get("event", "active")
        event_index_mapping = {
            "kill": 1,           # 全局击杀
            "bomb_planted": 2,   # C4安装
            "bomb_defused": 3,   # C4拆除
            "player_death": 4,   # 玩家死亡
            "active": 6,         # 切换到
            "reloading": 7,      # 换弹
            "weapon_kill": 8,    # 使用武器击杀
            "grenade_thrown": 9  # 道具投出
        }
        event_index = event_index_mapping.get(event_type, 6)
        self.event_type_combo.setCurrentIndex(event_index)
        
        # 设置音量
        volume = config.get("volume", 100)
        self.volume_slider.setValue(volume)
        
        # 设置音效文件路径
        sound_path = config.get("sound", "")
        if sound_path:
            self.sound_path = sound_path
            self.sound_path_input.setText(os.path.basename(sound_path))
        
        # 更新UI状态
        self._update_ui_state_for_event_type(event_index)
        
        # 设置连杀配置
        is_advanced = config.get("is_advanced", False)
        self.advanced_checkbox.setChecked(is_advanced)
        if is_advanced:
            sounds_1_5 = config.get("sounds_1_5", [])
            for idx, sound_cfg in enumerate(sounds_1_5):
                if idx < len(self.advanced_inputs):
                    path = sound_cfg.get("path", "")
                    vol = sound_cfg.get("volume", 50)
                    self.advanced_inputs[idx]["path"] = path
                    if path:
                        self.advanced_inputs[idx]["path_input"].setText(os.path.basename(path))
                    self.advanced_inputs[idx]["vol_slider"].setValue(vol)
            
            # 手动触发UI切换，因为setChecked在未改变状态时可能不触发信号
            self.basic_container.hide()
            self.advanced_container.show()
        else:
            self.basic_container.show()
            self.advanced_container.hide()