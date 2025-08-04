from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QSlider, QGroupBox, QGridLayout, QMessageBox,
    QListWidgetItem, QMenu
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from qfluentwidgets import (
    FluentIcon as FIF, PushButton, ComboBox, Slider, 
    TitleLabel, SubtitleLabel, BodyLabel, InfoBar, InfoBarPosition,
    SwitchButton, ListWidget, PrimaryPushButton
)
import os
from .components import EventConfigWidget
from .event_dialog import AddEventDialog
from ..logic.sound_player import SoundPlayer

class IntegratedSoundPage(QWidget):
    # 音效管理页面 - 实时音效配置
    
    # 信号
    sound_pack_changed = Signal(str)  # 音效包改变
    volume_changed = Signal(float)    # 音量改变
    test_sound_requested = Signal(str)  # 测试音效请求
    
    def __init__(self, gsi_manager=None, config_manager=None, parent=None):
        super().__init__(parent)
        self.gsi_manager = gsi_manager
        self.config_manager = config_manager
        self.parent = parent
        self.sound_player = SoundPlayer()
        self.previous_weapon_states = {}  # 存储之前的武器状态
        self.current_pack_path = None
        
        # 观战状态跟踪变量
        self.previous_observing_state = False
        self.previous_observer_slot = None
        self.previous_round_phase = None
        
        # 初始化状态跟踪变量
        self.previous_kills = 0
        self.previous_deaths = 0
        self.previous_bomb_state = ''
        self.previous_health = 100
        self.previous_is_alive = True
        
        # 连杀数跟踪
        self.round_kills = 0  # 当前回合的击杀数
        self.previous_round_kills = 0  # 上一次记录的回合击杀数
        
        self.init_ui()
        self._connect_signals()
        self.load_events()
    
    def init_ui(self):
        # 初始化用户界面
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(20)
        
        # 页面标题
        layout.addWidget(TitleLabel("实时音效管理"))
        
        # 实时音效配置板块
        self.create_realtime_sound_section(layout)
    
    def create_realtime_sound_section(self, parent_layout):
        # 创建实时音效配置板块
        # 实时音效组
        realtime_group = QGroupBox("实时音效配置")
        realtime_layout = QVBoxLayout(realtime_group)
        realtime_layout.setSpacing(15)
        
        # 服务控制
        server_control_layout = QHBoxLayout()
        server_control_layout.addWidget(SubtitleLabel("监听服务"))
        self.gsi_switch = SwitchButton()
        self.gsi_switch.setText("关闭")
        server_control_layout.addWidget(self.gsi_switch)
        server_control_layout.addStretch()
        realtime_layout.addLayout(server_control_layout)
        
        self.gsi_status_label = BodyLabel("服务已停止。")
        realtime_layout.addWidget(self.gsi_status_label)
        
        # GSI配置文件生成
        cfg_layout = QHBoxLayout()
        cfg_layout.addWidget(BodyLabel("启用GSI:"))
        self.create_cfg_btn = PushButton("生成配置文件")
        cfg_layout.addWidget(self.create_cfg_btn)
        cfg_layout.addStretch()
        realtime_layout.addLayout(cfg_layout)
        
        # 事件配置
        realtime_layout.addWidget(SubtitleLabel("事件配置"))
        
        self.event_list = ListWidget()
        realtime_layout.addWidget(self.event_list)
        
        # 事件操作按钮
        add_event_layout = QHBoxLayout()
        self.save_events_btn = PushButton("保存配置")
        self.add_event_btn = PrimaryPushButton("添加新事件")
        add_event_layout.addStretch()
        add_event_layout.addWidget(self.save_events_btn)
        add_event_layout.addWidget(self.add_event_btn)
        realtime_layout.addLayout(add_event_layout)
        
        parent_layout.addWidget(realtime_group)
    

    
    def _connect_signals(self):
        # 连接信号
        # 实时音效信号
        self.gsi_switch.checkedChanged.connect(self.toggle_gsi_server)
        self.create_cfg_btn.clicked.connect(self.create_gsi_config_file)
        self.add_event_btn.clicked.connect(self.show_add_event_dialog)
        self.save_events_btn.clicked.connect(self.save_events)
    
    # ==================== 实时音效相关方法 ====================
    
    def toggle_gsi_server(self, checked):
        # 切换GSI服务器状态
        if checked:
            self.gsi_switch.setText("运行中")
            self.gsi_status_label.setText("服务正在启动...")
            if self.gsi_manager:
                self.gsi_manager.start_server()
        else:
            self.gsi_switch.setText("关闭")
            self.gsi_status_label.setText("服务已停止。")
            if self.gsi_manager:
                self.gsi_manager.stop_server()
    
    def create_gsi_config_file(self):
        # 创建GSI配置文件
        if not self.parent or not hasattr(self.parent, 'steam_path'):
            InfoBar.warning("路径缺失", "请先在主页设置CS2路径。", parent=self)
            return
            
        cs2_path = self.parent.steam_path
        if not cs2_path:
            InfoBar.warning("路径缺失", "请先在主页设置CS2路径。", parent=self)
            return
        
        if self.gsi_manager:
            self.gsi_manager.set_cs2_path(cs2_path)
            success, message = self.gsi_manager.create_gsi_cfg()
            if success:
                InfoBar.success("成功", message, parent=self)
            else:
                InfoBar.error("失败", message, parent=self)
    
    def show_add_event_dialog(self):
        # 显示添加事件对话框
        dialog = AddEventDialog(self)
        if dialog.exec() == QMessageBox.Accepted:
            config = dialog.get_config()
            if config:
                # 保存新事件配置到config_manager
                events = self.config_manager.config.get('gsi_events', [])
                events.append(config)
                self.config_manager.config['gsi_events'] = events
                self.config_manager.save_config()
                
                # 重新加载事件列表以正确分类新事件
                self.load_events()
                
                InfoBar.success(
                    title="添加成功",
                    content="新事件已添加",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
    
    def add_new_event_widget(self, config=None, enable_change_callback=True):
        # 添加新的事件配置组件
        if config is None:
            config = {}
        
        item = QListWidgetItem()
        # 根据参数决定是否设置on_change回调
        on_change = self._on_event_config_changed if enable_change_callback else None
        widget = EventConfigWidget(parent=None, on_delete=self.delete_event_widget, on_change=on_change)
        if config:
            widget.set_config(config)
        item.setSizeHint(widget.sizeHint())
        self.event_list.addItem(item)
        self.event_list.setItemWidget(item, widget)
    
    def delete_event_widget(self, widget):
        # 删除事件配置组件
        # 遍历列表找到对应的QListWidgetItem
        for i in range(self.event_list.count()):
            item = self.event_list.item(i)
            if self.event_list.itemWidget(item) == widget:
                self.event_list.takeItem(i)
                break
        self.save_events()
        # 重新加载事件列表以更新分类显示
        self.load_events()
    
    def save_events(self):
        # 保存事件配置
        if not self.config_manager:
            return
            
        events = []
        for i in range(self.event_list.count()):
            item = self.event_list.item(i)
            widget = self.event_list.itemWidget(item)
            # 跳过分类标题（QLabel对象）
            if hasattr(widget, 'get_config'):
                config = widget.get_config()
                # 保存所有有武器名称的配置，不再强制要求音效文件
                if config.get("weapon"):
                    events.append(config)
        
        self.config_manager.config['gsi_events'] = events
        self.config_manager.save_config()
        
        InfoBar.success(
            title="保存成功",
            content=f"已保存 {len(events)} 个音效事件配置",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
    
    def load_events(self):
        # 加载事件配置
        if not self.config_manager:
            return
            
        self.event_list.clear()
        events = self.config_manager.config.get('gsi_events', [])
        
        # 检查并修复配置
        config_updated = False
        
        # 修复现有的武器击杀事件：将 event='kill' 改为 event='weapon_kill'
        # 但排除全局事件（武器名称为"全局事件"的情况）
        for event in events:
            weapon_name = event.get('weapon', '')
            event_type = event.get('event', '')
            # 只有当武器名称不是"全局事件"且事件类型是'kill'时，才转换为'weapon_kill'
            # 这样可以保护真正的全局击杀事件不被错误转换
            if (weapon_name != '全局事件' and 
                event_type == 'kill' and
                weapon_name.startswith('weapon_')):
                event['event'] = 'weapon_kill'
                config_updated = True
        
        # 如果配置有更新，保存配置
        if config_updated:
            self.config_manager.config['gsi_events'] = events
            self.config_manager.save_config()
        
        # 按事件类型分类
        global_events = []  # 全局音效
        other_events = []   # 其他音效
        
        for event_config in events:
            event_type = event_config.get('event', '')
            weapon_name = event_config.get('weapon', '')
            
            # 全局音效：事件类型为全局事件或武器名称为"全局事件"
            if (event_type in ['kill', 'bomb_planted', 'bomb_defused', 'player_death', 'knife_kill'] or 
                weapon_name == '全局事件'):
                global_events.append(event_config)
            else:
                other_events.append(event_config)
        
        # 只在有事件时显示分类标题
        if global_events:
            self._add_category_header("全局音效")
            for event_config in global_events:
                self.add_new_event_widget(event_config, enable_change_callback=False)
        
        if other_events:
            self._add_category_header("其他音效")
            for event_config in other_events:
                self.add_new_event_widget(event_config, enable_change_callback=False)
        
        # 如果没有任何事件，显示提示信息
        if not global_events and not other_events:
            self._add_empty_hint()
        else:
            # 加载完成后，为所有事件组件启用回调
            self._enable_all_event_callbacks()
    
    def _add_category_header(self, category_name):
        # 添加分类标题
        from PySide6.QtWidgets import QLabel
        from PySide6.QtCore import Qt
        
        item = QListWidgetItem()
        header_label = QLabel(f"--- {category_name} ---")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                color: #0078d4;
                padding: 8px;
                background-color: #f5f5f5;
                border-radius: 4px;
                margin: 4px 0px;
            }
        """)
        
        item.setSizeHint(header_label.sizeHint())
        self.event_list.addItem(item)
        self.event_list.setItemWidget(item, header_label)
        
        # 设置分类标题不可选择
        item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
    
    def _add_empty_hint(self):
        # 添加空状态提示信息
        from PySide6.QtWidgets import QLabel
        from PySide6.QtCore import Qt
        
        item = QListWidgetItem()
        hint_label = QLabel("暂无事件配置，点击上方'添加新事件'按钮开始配置")
        hint_label.setAlignment(Qt.AlignCenter)
        hint_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #999;
                padding: 20px;
                background-color: #fafafa;
                border: 1px dashed #ddd;
                border-radius: 4px;
                margin: 10px;
            }
        """)
        
        item.setSizeHint(hint_label.sizeHint())
        self.event_list.addItem(item)
        self.event_list.setItemWidget(item, hint_label)
        
        # 设置提示信息不可选择
        item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
    
    def _enable_all_event_callbacks(self):
        # 为所有事件组件启用回调
        for i in range(self.event_list.count()):
            item = self.event_list.item(i)
            widget = self.event_list.itemWidget(item)
            # 只为EventConfigWidget启用回调
            if hasattr(widget, 'set_on_change'):
                widget.set_on_change(self._on_event_config_changed)
    
    def _on_event_config_changed(self):
        # 当事件配置改变时调用，只保存配置不重新加载列表
        # 静默保存配置，不重新加载列表以避免重置用户正在编辑的状态
        if not self.config_manager:
            return
            
        events = []
        for i in range(self.event_list.count()):
            item = self.event_list.item(i)
            widget = self.event_list.itemWidget(item)
            # 跳过分类标题（QLabel对象）
            if hasattr(widget, 'get_config'):
                config = widget.get_config()
                # 保存所有有武器名称的配置，不再强制要求音效文件
                if config.get("weapon"):
                    events.append(config)
        
        self.config_manager.config['gsi_events'] = events
        self.config_manager.save_config()
        
        # 注释掉重新加载，避免重置用户正在编辑的状态
        # self.load_events()
    
    def process_game_state(self, game_state: dict):
        """处理游戏状态数据"""
        player = game_state.get('player', {})
        if not player: 
            return

        if player.get('activity') != 'playing':
            return

        # 处理武器相关事件
        self._process_weapon_events(game_state, player)
        
        # 处理C4和击杀事件
        self._process_bomb_and_kill_events(game_state, player)
    
    def _process_weapon_events(self, game_state: dict, player: dict):
        """处理武器相关事件"""
        weapons = player.get('weapons', {})
        if not weapons:
            return
        
        for i in range(self.event_list.count()):
            item = self.event_list.item(i)
            widget = self.event_list.itemWidget(item)
            
            # 跳过分类标题（QLabel），只处理 EventConfigWidget
            if not hasattr(widget, 'get_config'):
                continue
                
            config = widget.get_config()
            
            weapon_name = config.get('weapon')
            event_type = config.get('event')
            sound_path = config.get('sound')
            
            if not all([weapon_name, event_type, sound_path]):
                continue
            
            # 查找匹配的武器
            weapon_data = None
            for weapon_key, weapon_info in weapons.items():
                if weapon_info.get('name') == weapon_name:
                    weapon_data = weapon_info
                    break
            
            if not weapon_data:
                continue
            
            current_state = weapon_data.get('state')
            state_key = f"{weapon_name}:{event_type}"
            previous_state = self.previous_weapon_states.get(state_key)
            
            should_trigger = False
            
            if event_type == 'active':
                if current_state == 'active' and previous_state == 'holstered':
                    should_trigger = True
            elif event_type == 'reloading':
                if current_state == 'reloading' and previous_state != 'reloading':
                    should_trigger = True
            
            if should_trigger:
                if os.path.exists(sound_path):
                    volume = config.get('volume', 50)
                    self.sound_player.play_sound(sound_path, volume)
                
            self.previous_weapon_states[state_key] = current_state
    
    def _process_bomb_and_kill_events(self, game_state: dict, player: dict):
        """处理炸弹、击杀和死亡事件"""
        # 初始化之前的状态
        if not hasattr(self, 'previous_kills'):
            self.previous_kills = player.get('match_stats', {}).get('kills', 0)
        if not hasattr(self, 'previous_deaths'):
            self.previous_deaths = player.get('match_stats', {}).get('deaths', 0)
        if not hasattr(self, 'previous_bomb_state'):
            self.previous_bomb_state = game_state.get('round', {}).get('bomb', '')
        
        # 获取当前状态信息
        current_kills = player.get('match_stats', {}).get('kills', 0)
        current_deaths = player.get('match_stats', {}).get('deaths', 0)
        observer_slot = player.get('observer_slot')
        current_round_phase = game_state.get('round', {}).get('phase', 'unknown')
        player_state = player.get('state', {})
        player_team = player.get('team', '')
        round_info = game_state.get('round', {})
        current_health = player_state.get('health', 0)
        
        # 检查玩家是否有有效的队伍和在正确的回合阶段
        has_valid_team = player_team in ['T', 'CT']
        valid_round_phases = ['live', 'freezetime', 'unknown']
        current_phase = round_info.get('phase', 'unknown')
        is_in_round = current_phase in valid_round_phases
        is_alive = player_state.get('health', 0) > 0
        
        # 检查是否在观战状态（更精确的检测）
        spectarget = player.get('spectarget')
        activity = player.get('activity', '')
        
        # 观战检测逻辑：
        # 1. 有观战目标 或
        # 2. 活动状态为观战 或  
        # 3. 活动状态不是游玩 或
        # 4. 没有有效队伍（可能是观战者）
        # 注意：不要将死亡状态直接判断为观战，因为死亡时仍需要触发死亡音效
        is_observing = (
            spectarget is not None or  # 正在观战某个玩家
            activity == 'spectating' or  # 活动状态为观战
            activity != 'playing' or  # 活动状态不是游玩
            not has_valid_team  # 没有有效队伍（可能是观战者）
        )
        
        # 添加详细的观战状态调试信息
        print(f"[GSI音效] 观战状态详细信息:")
        print(f"  - spectarget: {spectarget}")
        print(f"  - activity: {activity}")
        print(f"  - observer_slot: {observer_slot}")
        print(f"  - is_alive: {is_alive}")
        print(f"  - 计算出的观战状态: {is_observing}")
        print(f"  - 上次观战状态: {self.previous_observing_state}")
        print(f"  - 击杀数: {current_kills}, 上次击杀数: {self.previous_kills}")
        
        # 检测观察位置变化：当observer_slot发生变化时，重置击杀数跟踪
        if observer_slot != self.previous_observer_slot:
            print(f"[GSI音效] 检测到观察位置变化: {self.previous_observer_slot} -> {observer_slot}，重置击杀数跟踪")
            self.previous_kills = current_kills
            self.previous_deaths = current_deaths
            self.previous_observer_slot = observer_slot
            self.previous_round_phase = current_round_phase
            self.previous_observing_state = is_observing
            self.previous_health = current_health
            self.previous_is_alive = is_alive
            return  # 直接返回，避免在观察位置切换时触发音效
        
        # 检测观战状态变化：当观战状态发生变化时，重置击杀数跟踪
        if is_observing != self.previous_observing_state:
            print(f"[GSI音效] 检测到观战状态变化: {self.previous_observing_state} -> {is_observing}，重置击杀数跟踪")
            self.previous_kills = current_kills
            self.previous_deaths = current_deaths
            self.previous_round_phase = current_round_phase
            self.previous_observing_state = is_observing
            self.previous_health = current_health
            self.previous_is_alive = is_alive
            return  # 直接返回，避免在观战状态切换时触发音效
        
        # 如果当前在观战状态，只处理死亡音效，跳过其他音效
        skip_non_death_events = is_observing
        if skip_non_death_events:
            print(f"[GSI音效] 当前在观战状态，只处理死亡音效")
            
        # 添加事件配置调试信息（只在第一次或配置变化时显示）
        if not hasattr(self, 'debug_events_shown'):
            self.debug_events_shown = True
            print(f"[GSI音效] 当前配置的事件列表:")
            for i in range(self.event_list.count()):
                item = self.event_list.item(i)
                widget = self.event_list.itemWidget(item)
                
                # 跳过分类标题（QLabel），只处理 EventConfigWidget
                if not hasattr(widget, 'get_config'):
                    continue
                    
                config = widget.get_config()
                event_type = config.get('event')
                weapon_name = config.get('weapon', '')
                sound_path = config.get('sound')
                volume = config.get('volume', 50)
                
                print(f"  - 事件类型: {event_type}, 武器: {weapon_name}, 音效文件: {sound_path}, 音量: {volume}%")
                
            if self.event_list.count() == 0:
                print(f"  - 没有配置任何事件")
        
        # 添加血量和死亡数的调试信息
        if not hasattr(self, 'previous_health'):
            self.previous_health = current_health
        if not hasattr(self, 'previous_is_alive'):
            self.previous_is_alive = is_alive
            
        # 检查血量变化（用于死亡检测）
        if current_health != self.previous_health:
            print(f"[GSI音效] 血量变化: {self.previous_health} -> {current_health}")
            
        # 检查存活状态变化（主要的死亡检测方式）
        if is_alive != self.previous_is_alive:
            print(f"[GSI音效] 存活状态变化: {self.previous_is_alive} -> {is_alive}")
            
        # 检查死亡数变化
        if current_deaths != self.previous_deaths:
            print(f"[GSI音效] 死亡数变化: {self.previous_deaths} -> {current_deaths}")
            print(f"[GSI音效] 玩家存活: {is_alive}, 有效队伍: {has_valid_team}, 回合状态: {is_in_round}")
            print(f"[GSI音效] 观战状态: {is_observing}, 观战位置: {observer_slot}, 观战目标: {spectarget}, 活动: {activity}")
            print(f"[GSI音效] 玩家血量: {current_health}, 队伍: {player_team}, 回合阶段: {round_info.get('phase', 'unknown')}")
            
        # 检查基于存活状态的死亡事件（从存活变为死亡）
        if not is_alive and self.previous_is_alive:
            print(f"[GSI音效] 检测到基于存活状态的死亡事件: 存活状态从 {self.previous_is_alive} 变为 {is_alive}")
            # 玩家死亡时重置击杀数
            print(f"[GSI音效] 玩家死亡，重置连杀数: {self.round_kills} -> 0")
            self.round_kills = 0
            
            # 触发基于存活状态的死亡音效
            death_sound_found = False
            for i in range(self.event_list.count()):
                item = self.event_list.item(i)
                widget = self.event_list.itemWidget(item)
                
                # 跳过分类标题（QLabel），只处理 EventConfigWidget
                if not hasattr(widget, 'get_config'):
                    continue
                    
                config = widget.get_config()
                
                event_type = config.get('event')
                sound_path = config.get('sound')
                
                if event_type == 'player_death' and sound_path and os.path.exists(sound_path):
                    volume = config.get('volume', 50)
                    self.sound_player.play_sound(sound_path, volume)
                    print(f"[GSI音效] 触发基于存活状态的死亡音效, 音量: {volume}%")
                    death_sound_found = True
                    break
            
            if not death_sound_found:
                print(f"[GSI音效] 未找到可用的死亡音效配置（基于存活状态检测）")
        
        # 检查玩家死亡事件
        if current_deaths > self.previous_deaths:
            print(f"[GSI音效] 确认死亡事件，开始查找死亡音效")
            # 玩家死亡时重置击杀数
            print(f"[GSI音效] 玩家死亡，重置连杀数: {self.round_kills} -> 0")
            self.round_kills = 0
            
            # 触发玩家死亡音效
            death_sound_found = False
            for i in range(self.event_list.count()):
                item = self.event_list.item(i)
                widget = self.event_list.itemWidget(item)
                
                # 跳过分类标题（QLabel），只处理 EventConfigWidget
                if not hasattr(widget, 'get_config'):
                    continue
                    
                config = widget.get_config()
                
                event_type = config.get('event')
                sound_path = config.get('sound')
                
                print(f"[GSI音效] 检查事件配置: event_type={event_type}, sound_path={sound_path}")
                
                if event_type == 'player_death' and sound_path and os.path.exists(sound_path):
                    volume = config.get('volume', 50)
                    self.sound_player.play_sound(sound_path, volume)
                    print(f"[GSI音效] 触发玩家死亡音效, 音量: {volume}%")
                    death_sound_found = True
                    break
            
            if not death_sound_found:
                print(f"[GSI音效] 未找到可用的死亡音效配置")
        
        # 检查击杀事件（观战状态下跳过）
        if current_kills > self.previous_kills and not skip_non_death_events:
            # 计算连杀数（每次击杀+1）
            kill_increment = current_kills - self.previous_kills
            self.round_kills += kill_increment
            
            print(f"[GSI音效] 击杀事件: 总击杀数 {self.previous_kills} -> {current_kills}, 本次击杀增量: {kill_increment}, 当前回合连杀数: {self.round_kills}")
            
            # 获取当前武器信息
            current_weapon = None
            weapons = player.get('weapons', {})
            for weapon_info in weapons.values():
                if weapon_info.get('state') == 'active':
                    current_weapon = weapon_info.get('name')
                    break
            
            # 检查是否是刀杀
            is_knife_kill = False
            if current_weapon and ('knife' in current_weapon.lower() or 'bayonet' in current_weapon.lower()):
                is_knife_kill = True
                print(f"[GSI音效] 检测到刀杀: {current_weapon}")
            
            # 优先级：刀杀 > 特定武器击杀 > 全局击杀
            played_sound = False
            
            # 1. 尝试播放刀杀音效
            if is_knife_kill:
                played_sound = self._play_kill_sound('knife_kill', '全局事件', self.round_kills)
            
            # 2. 如果没有播放刀杀音效，尝试播放特定武器击杀音效
            if not played_sound and current_weapon:
                played_sound = self._play_kill_sound('weapon_kill', current_weapon, self.round_kills)
            
            # 3. 如果都没有播放，则播放全局击杀音效
            if not played_sound:
                self._play_kill_sound('kill', '全局事件', self.round_kills)
        
        # 处理C4事件
        self._handle_bomb_events(game_state, skip_non_death_events)
        
        # 检查回合重置（新回合开始时重置连杀数）
        round_data = game_state.get('round', {})
        current_round_phase = round_data.get('phase', '')
        if current_round_phase != self.previous_round_phase:
            if current_round_phase in ['live', 'freezetime']:
                print(f"[GSI音效] 回合阶段变化: {self.previous_round_phase} -> {current_round_phase}, 重置连杀数")
                self.round_kills = 0
        
        # 更新状态
        self.previous_kills = current_kills
        self.previous_deaths = current_deaths
        self.previous_bomb_state = game_state.get('round', {}).get('bomb', '')
        self.previous_observing_state = is_observing
        self.previous_observer_slot = observer_slot
        self.previous_round_phase = current_round_phase
        self.previous_health = current_health
        self.previous_is_alive = is_alive
    
    def _play_kill_sound(self, event_type, weapon_name, kill_count):
        """播放击杀音效，支持高级连杀配置"""
        played = False
        
        for i in range(self.event_list.count()):
            item = self.event_list.item(i)
            widget = self.event_list.itemWidget(item)
            
            # 跳过分类标题（QLabel），只处理 EventConfigWidget
            if not hasattr(widget, 'get_config'):
                continue
                
            config = widget.get_config()
            
            config_event = config.get('event')
            config_weapon = config.get('weapon')
            
            # 检查事件类型和武器匹配
            # 对于全局击杀事件，只检查事件类型，不检查武器名称
            if config_event == event_type and (event_type == 'kill' or config_weapon == weapon_name):
                print(f"[GSI音效] 找到匹配的配置!")
                sound_path = config.get('sound')
                if sound_path and os.path.exists(sound_path):
                    volume = config.get('volume', 50)
                    self.sound_player.play_sound(sound_path, volume)
                    print(f"[GSI音效] 触发击杀音效: {weapon_name}, 连杀数: {kill_count}, 音量: {volume}%")
                    played = True
                    break
                else:
                    print(f"[GSI音效] 击杀音效文件不存在: {sound_path}")
        
        if not played:
            print(f"[GSI音效] 未找到匹配的击杀音效: {event_type}, {weapon_name}, 连杀数: {kill_count}")
        
        return played
    
    def _handle_bomb_events(self, game_state, skip_non_death_events):
        """处理C4相关事件"""
        # 检查C4事件（观战状态下跳过）
        round_data = game_state.get('round', {})
        current_bomb_state = round_data.get('bomb', '')
        
        if current_bomb_state != self.previous_bomb_state and not skip_non_death_events:
            if current_bomb_state == 'planted':
                # 触发C4安装音效
                for i in range(self.event_list.count()):
                    item = self.event_list.item(i)
                    widget = self.event_list.itemWidget(item)
                    
                    # 跳过分类标题（QLabel），只处理 EventConfigWidget
                    if not hasattr(widget, 'get_config'):
                        continue
                        
                    config = widget.get_config()
                    
                    event_type = config.get('event')
                    sound_path = config.get('sound')
                    
                    if event_type == 'bomb_planted' and sound_path and os.path.exists(sound_path):
                        volume = config.get('volume', 50)
                        self.sound_player.play_sound(sound_path, volume)
                        print(f"[GSI音效] 触发C4安装音效, 音量: {volume}%")
                        break
            elif current_bomb_state == 'defused' or (self.previous_bomb_state == 'planted' and current_bomb_state == ''):
                # 触发C4拆除音效（当状态为defused或从planted变为空时）
                for i in range(self.event_list.count()):
                    item = self.event_list.item(i)
                    widget = self.event_list.itemWidget(item)
                    
                    # 跳过分类标题（QLabel），只处理 EventConfigWidget
                    if not hasattr(widget, 'get_config'):
                        continue
                        
                    config = widget.get_config()
                    
                    event_type = config.get('event')
                    sound_path = config.get('sound')
                    
                    if event_type == 'bomb_defused' and sound_path and os.path.exists(sound_path):
                        volume = config.get('volume', 50)
                        self.sound_player.play_sound(sound_path, volume)
                        print(f"[GSI音效] 触发C4拆除音效, 音量: {volume}%")
                        break