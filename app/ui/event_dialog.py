from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QFileDialog, QDialogButtonBox, QGroupBox, QGridLayout
from PySide6.QtCore import Qt
from qfluentwidgets import (
    TitleLabel, SubtitleLabel, BodyLabel, LineEdit, ComboBox, 
    PushButton, Slider, MessageBox, CheckBox
)
import os



class AddEventDialog(QDialog):
    # 添加GSI事件的对话框
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.sound_path = ""

        self.setWindowTitle("添加新事件")
        self.setFixedSize(600, 600)
        self.setModal(True)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title = TitleLabel("添加新的事件")
        layout.addWidget(title)
        
        # 说明文字
        info_text = BodyLabel("说明：配置各种游戏事件的音效，包括C4安装/拆除、玩家死亡、武器切换、换弹和特定武器击杀等。")
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: #666; padding: 5px; background-color: #f5f5f5; border-radius: 4px;")
        layout.addWidget(info_text)
        
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
            "刀杀",
            "--- 其他音效 ---",
            "切换到",
            "换弹", 
            "使用武器击杀"
        ]
        self.event_type_combo.addItems(event_items)
        self.event_type_combo.currentIndexChanged.connect(self._on_event_type_changed)
        form_layout.addRow(BodyLabel("事件类型:"), self.event_type_combo)
        
        # 武器名称输入
        self.weapon_name_input = ComboBox()
        self.weapon_name_input.setPlaceholderText("选择或输入武器名称")
        
        # 武器名称中文映射
        weapon_names_cn = [
            "AK-47", "M4A4", "M4A1-S消音版", "AWP",
            "沙漠之鹰", "格洛克18", "USP消音版", "P250",
            "Five-SeveN", "Tec-9", "CZ75-Auto", "P2000",
            "双持贝瑞塔", "P90", "PP-野牛", "MAC-10",
            "MP7", "MP9", "UMP-45", "XM1014",
            "短管霰弹枪", "新星", "MAG-7", "内格夫",
            "M249", "加利尔AR", "法玛斯", "SG 553",
            "AUG", "SCAR-20", "G3SG1", "SSG 08",
            "默认刀", "T方默认刀", "刺刀", "海豹短刀", "折叠刀",
            "穿肠刀", "爪子刀", "M9刺刀", "猎杀者匕首", "弯刀",
            "鲍伊猎刀", "蝴蝶刀", "暗影双匕", "系绳匕首", "求生匕首",
            "熊刀", "折刀", "流浪者匕首", "短剑", "锯齿爪刀",
            "骷髅匕首", "廓尔喀刀"
        ]
        
        # 对应的英文武器名称（用于配置保存）
        weapon_names_en = [
            "weapon_ak47", "weapon_m4a1", "weapon_m4a1_silencer", "weapon_awp",
            "weapon_deagle", "weapon_glock", "weapon_usp_silencer", "weapon_p250",
            "weapon_fiveseven", "weapon_tec9", "weapon_cz75a", "weapon_p2000",
            "weapon_elite", "weapon_p90", "weapon_bizon", "weapon_mac10",
            "weapon_mp7", "weapon_mp9", "weapon_ump45", "weapon_xm1014",
            "weapon_sawedoff", "weapon_nova", "weapon_mag7", "weapon_negev",
            "weapon_m249", "weapon_galilar", "weapon_famas", "weapon_sg556",
            "weapon_aug", "weapon_scar20", "weapon_g3sg1", "weapon_ssg08",
            "weapon_knife", "weapon_knife_t", "weapon_bayonet", "weapon_knife_css", "weapon_knife_flip",
            "weapon_knife_gut", "weapon_knife_karambit", "weapon_knife_m9_bayonet", "weapon_knife_huntsman", "weapon_knife_falchion",
            "weapon_knife_survival_bowie", "weapon_knife_butterfly", "weapon_knife_push", "weapon_knife_cord", "weapon_knife_tactical",
            "weapon_knife_ursus", "weapon_knife_gypsy_jackknife", "weapon_knife_nomad", "weapon_knife_stiletto", "weapon_knife_widowmaker",
            "weapon_knife_skeleton", "weapon_knife_kukri"
        ]
        
        # 创建中英文映射字典
        self.weapon_cn_to_en = dict(zip(weapon_names_cn, weapon_names_en))
        self.weapon_en_to_cn = dict(zip(weapon_names_en, weapon_names_cn))
        
        self.weapon_name_input.addItems(weapon_names_cn)
        form_layout.addRow(BodyLabel("武器名称:"), self.weapon_name_input)
        
        # 音效文件选择
        sound_layout = QHBoxLayout()
        self.sound_path_input = LineEdit()
        self.sound_path_input.setPlaceholderText("选择音效文件")
        self.sound_path_input.setReadOnly(True)
        self.browse_sound_btn = PushButton("浏览")
        self.browse_sound_btn.clicked.connect(self._browse_sound_file)
        sound_layout.addWidget(self.sound_path_input)
        sound_layout.addWidget(self.browse_sound_btn)
        form_layout.addRow(BodyLabel("音效文件:"), sound_layout)
        
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
        form_layout.addRow(BodyLabel("音量:"), volume_layout)
        
        layout.addLayout(form_layout)
        layout.addSpacing(20)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # 初始化状态
        self.event_type_combo.setCurrentIndex(1)  # 默认选择"全局击杀"
        self._on_event_type_changed(1)
        
    def _on_event_type_changed(self, index):
        # 当事件类型改变时调用
        # 防止选择分类标题
        if index in [0, 6]:  # 分类标题索引
            # 如果选择了分类标题，跳转到下一个有效选项
            if index == 0:  # 全局音效分类
                # 阻止信号触发，避免递归调用
                self.event_type_combo.blockSignals(True)
                self.event_type_combo.setCurrentIndex(1)  # 跳转到"全局击杀"
                self.event_type_combo.blockSignals(False)
                # 手动调用更新逻辑
                index = 1
            elif index == 6:  # 其他音效分类
                # 阻止信号触发，避免递归调用
                self.event_type_combo.blockSignals(True)
                self.event_type_combo.setCurrentIndex(7)  # 跳转到"切换到"
                self.event_type_combo.blockSignals(False)
                # 手动调用更新逻辑
                index = 6
        


        # 根据事件类型更新UI状态
        self._update_ui_state_for_event_type(index)
    
    def _update_ui_state_for_event_type(self, index):
        # 根据事件类型索引更新UI控件状态
        if index in [1, 2, 3, 4]:  # 全局击杀、C4安装、C4拆除、玩家死亡（全局事件）
            self.weapon_name_input.setCurrentText("全局事件")
            self.weapon_name_input.setEnabled(False)
            self.browse_sound_btn.setEnabled(True)
            self.sound_path_input.setEnabled(True)
        elif index == 5:  # 刀杀（全局事件）
            self.weapon_name_input.setCurrentText("全局事件")
            self.weapon_name_input.setEnabled(False)
            self.browse_sound_btn.setEnabled(True)
            self.sound_path_input.setEnabled(True)
        elif index == 9:  # 使用武器击杀
            self.weapon_name_input.setEnabled(True)
            if self.weapon_name_input.currentText() == "全局事件":
                self.weapon_name_input.setCurrentText("")
        else:  # 切换到、换弹
            self.weapon_name_input.setEnabled(True)
            if self.weapon_name_input.currentText() == "全局事件":
                self.weapon_name_input.setCurrentText("")
    
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
        
        # 验证音效文件
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
            5: "knife_kill",     # 刀杀
            7: "active",         # 切换到
            8: "reloading",      # 换弹
            9: "weapon_kill"     # 使用武器击杀
        }
        event_type = event_mapping.get(event_index, "active")
        
        # 为全局事件设置正确的武器名称
        if event_index in [1, 2, 3, 4, 5]:  # 全局事件
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
        elif event_index == 5:
            name = "刀杀音效"
        else:
            name = f"{weapon_name}_{event_type}"
        
        config = {
            "name": name,
            "weapon": weapon_name,
            "event": event_type,
            "volume": self.volume_slider.value(),
            "enabled": True,
            "sound": self.sound_path,
            "is_advanced": False
        }
        
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
            "knife_kill": 5,     # 刀杀
            "active": 7,         # 切换到
            "reloading": 8,      # 换弹
            "weapon_kill": 9     # 使用武器击杀
        }
        event_index = event_index_mapping.get(event_type, 7)
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