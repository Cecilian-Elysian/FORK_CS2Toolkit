from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QSlider, QGroupBox, QGridLayout, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import (
    FluentIcon as FIF, PushButton, ComboBox, Slider, 
    TitleLabel, SubtitleLabel, BodyLabel, InfoBar, InfoBarPosition
)
import os

class GSISoundPage(QWidget):
    """GSI音效设置页面"""
    
    # 信号
    sound_pack_changed = Signal(str)  # 音效包改变
    volume_changed = Signal(float)    # 音量改变
    test_sound_requested = Signal(str)  # 测试音效请求
    
    def __init__(self, gsi_manager=None, config_manager=None, parent=None):
        super().__init__(parent)
        self.gsi_manager = gsi_manager
        self.config_manager = config_manager
        self.current_pack_path = None
        
        self.init_ui()
        self.load_sound_packs()
        self.load_settings()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # 标题
        title = TitleLabel("GSI音效设置")
        layout.addWidget(title)
        
        # 音效包选择组
        pack_group = self.create_pack_selection_group()
        layout.addWidget(pack_group)
        
        # 音量控制组
        volume_group = self.create_volume_control_group()
        layout.addWidget(volume_group)
        
        # 音效测试组
        test_group = self.create_sound_test_group()
        layout.addWidget(test_group)
        
        # 状态信息
        self.status_label = BodyLabel("请选择GSI音效包")
        self.status_label.setStyleSheet("color: #666666;")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
    
    def create_pack_selection_group(self):
        """创建音效包选择组"""
        group = QGroupBox("音效包选择")
        layout = QVBoxLayout(group)
        
        # 说明文字
        desc_label = BodyLabel("选择要使用的GSI音效包，包含炸弹安装、拆除和死亡音效")
        desc_label.setStyleSheet("color: #666666;")
        layout.addWidget(desc_label)
        
        # 音效包选择
        pack_layout = QHBoxLayout()
        pack_layout.addWidget(QLabel("音效包:"))
        
        self.pack_combo = ComboBox()
        self.pack_combo.setMinimumWidth(300)
        self.pack_combo.currentTextChanged.connect(self.on_pack_changed)
        pack_layout.addWidget(self.pack_combo)
        
        # 刷新按钮
        self.refresh_btn = PushButton("刷新", self)
        self.refresh_btn.setIcon(FIF.SYNC)
        self.refresh_btn.clicked.connect(self.load_sound_packs)
        pack_layout.addWidget(self.refresh_btn)
        
        pack_layout.addStretch()
        layout.addLayout(pack_layout)
        
        return group
    
    def create_volume_control_group(self):
        """创建音量控制组"""
        group = QGroupBox("音量控制")
        layout = QVBoxLayout(group)
        
        # 音量滑块
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("音量:"))
        
        self.volume_slider = Slider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50)
        self.volume_slider.setMinimumWidth(200)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        volume_layout.addWidget(self.volume_slider)
        
        self.volume_label = QLabel("50%")
        self.volume_label.setMinimumWidth(40)
        volume_layout.addWidget(self.volume_label)
        
        volume_layout.addStretch()
        layout.addLayout(volume_layout)
        
        return group
    
    def create_sound_test_group(self):
        """创建音效测试组"""
        group = QGroupBox("音效测试")
        layout = QGridLayout(group)
        
        # 测试按钮
        test_buttons = [
            ("炸弹安装", "bomb_planted", 0, 0),
            ("炸弹拆除", "bomb_defused", 0, 1),
            ("玩家死亡", "player_death", 1, 0),
            ("敌人死亡", "enemy_death", 1, 1)
        ]
        
        for text, sound_type, row, col in test_buttons:
            btn = PushButton(f"测试{text}音效", self)
            btn.setIcon(FIF.PLAY)
            btn.clicked.connect(lambda checked, st=sound_type: self.test_sound(st))
            layout.addWidget(btn, row, col)
        
        return group
    
    def load_sound_packs(self):
        """加载GSI音效包列表"""
        self.pack_combo.clear()
        self.pack_combo.addItem("无", None)
        
        if not self.config_manager:
            return
        
        # 获取GSI音效预设
        gsi_presets = self.config_manager.get_presets('gsi_sound')
        for preset in gsi_presets:
            name = preset.get('name', '未知音效包')
            pack_path = preset.get('pack_path', '')
            self.pack_combo.addItem(name, pack_path)
    
    def load_settings(self):
        """加载设置"""
        # 这里可以从配置文件加载上次的设置
        pass
    
    def on_pack_changed(self, text):
        """音效包改变事件"""
        if text == "无":
            self.current_pack_path = None
            self.status_label.setText("未选择GSI音效包")
        else:
            # 获取选中的音效包路径
            index = self.pack_combo.currentIndex()
            pack_path = self.pack_combo.itemData(index)
            
            if pack_path and os.path.exists(pack_path):
                self.current_pack_path = pack_path
                self.status_label.setText(f"已选择: {text}")
                
                # 设置GSI音效包
                if self.gsi_manager:
                    success = self.gsi_manager.set_gsi_sound_pack(pack_path)
                    if success:
                        InfoBar.success(
                            title="成功",
                            content=f"已应用GSI音效包: {text}",
                            orient=Qt.Orientation.Horizontal,
                            isClosable=True,
                            position=InfoBarPosition.TOP,
                            duration=2000,
                            parent=self
                        )
                    else:
                        InfoBar.error(
                            title="错误",
                            content="应用GSI音效包失败",
                            orient=Qt.Orientation.Horizontal,
                            isClosable=True,
                            position=InfoBarPosition.TOP,
                            duration=3000,
                            parent=self
                        )
                
                self.sound_pack_changed.emit(pack_path)
            else:
                self.current_pack_path = None
                self.status_label.setText("音效包路径无效")
    
    def on_volume_changed(self, value):
        """音量改变事件"""
        self.volume_label.setText(f"{value}%")
        volume = value / 100.0
        
        # 设置GSI音效音量
        if self.gsi_manager:
            self.gsi_manager.set_gsi_sound_volume(volume)
        
        self.volume_changed.emit(volume)
    
    def test_sound(self, sound_type):
        """测试音效"""
        if not self.current_pack_path:
            InfoBar.warning(
                title="提示",
                content="请先选择GSI音效包",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return
        
        if self.gsi_manager:
            self.gsi_manager.test_gsi_sound(sound_type)
            
            sound_names = {
                "bomb_planted": "炸弹安装",
                "bomb_defused": "炸弹拆除", 
                "player_death": "玩家死亡",
                "enemy_death": "敌人死亡"
            }
            
            InfoBar.info(
                title="测试音效",
                content=f"正在播放{sound_names.get(sound_type, sound_type)}音效",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=1500,
                parent=self
            )
        
        self.test_sound_requested.emit(sound_type)
    
    def get_current_pack_path(self):
        """获取当前选中的音效包路径"""
        return self.current_pack_path
    
    def get_current_volume(self):
        """获取当前音量"""
        return self.volume_slider.value() / 100.0