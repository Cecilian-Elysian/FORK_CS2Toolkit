from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QListWidgetItem
from PySide6.QtCore import Qt
from qfluentwidgets import (SubtitleLabel, TitleLabel, BodyLabel, PushButton, 
                           ListWidget, PrimaryPushButton, InfoBar, SwitchButton,
                           InfoBarPosition)
import os
from ..components import EventConfigWidget
from ..event_dialog import AddEventDialog
from ...logic.sound_player import SoundPlayer


class GSIPage(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.sound_player = SoundPlayer()
        self.previous_weapon_states = {}  # 存储之前的武器状态，格式: {"weapon_name:event_type": state}
        self._setup_ui()
        self._connect_signals()
        self.load_events()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(15)

        layout.addWidget(TitleLabel("实时音效播放"))
        
        server_control_layout = QHBoxLayout()
        server_control_layout.addWidget(SubtitleLabel("监听服务"))
        self.gsi_switch = SwitchButton()
        self.gsi_switch.setText("关闭")
        server_control_layout.addWidget(self.gsi_switch)
        server_control_layout.addStretch()
        layout.addLayout(server_control_layout)

        self.gsi_status_label = BodyLabel("服务已停止。")
        layout.addWidget(self.gsi_status_label)

        cfg_layout = QHBoxLayout()
        cfg_layout.addWidget(BodyLabel("启用GSI:"))
        self.create_cfg_btn = PushButton("生成配置文件")
        cfg_layout.addWidget(self.create_cfg_btn)
        cfg_layout.addStretch()
        layout.addLayout(cfg_layout)
        
        layout.addSpacing(20)

        layout.addWidget(SubtitleLabel("事件配置"))
        
        self.event_list = ListWidget()
        layout.addWidget(self.event_list)
        
        add_event_layout = QHBoxLayout()
        self.save_events_btn = PushButton("保存配置")
        self.add_event_btn = PrimaryPushButton("添加新事件")
        add_event_layout.addStretch()
        add_event_layout.addWidget(self.save_events_btn)
        add_event_layout.addWidget(self.add_event_btn)
        layout.addLayout(add_event_layout)
        
        layout.addStretch()
        
    def _connect_signals(self):
        self.gsi_switch.checkedChanged.connect(self.toggle_gsi_server)
        self.create_cfg_btn.clicked.connect(self.create_gsi_config_file)
        self.add_event_btn.clicked.connect(self.show_add_event_dialog)
        self.save_events_btn.clicked.connect(self.save_events)

    def toggle_gsi_server(self, checked):
        if checked:
            self.gsi_switch.setText("运行中")
            self.gsi_status_label.setText("服务正在启动...")
            self.parent.gsi_manager.start_server()
        else:
            self.gsi_switch.setText("关闭")
            self.gsi_status_label.setText("服务已停止。")
            self.parent.gsi_manager.stop_server()

    def create_gsi_config_file(self):
        cs2_path = self.parent.steam_path
        if not cs2_path:
            InfoBar.warning("路径缺失", "请先在主页设置CS2路径。", parent=self)
            return
        
        self.parent.gsi_manager.set_cs2_path(cs2_path)
        success, message = self.parent.gsi_manager.create_gsi_cfg()
        if success:
            InfoBar.success("成功", message, parent=self)
        else:
            InfoBar.error("失败", message, parent=self)

    def show_add_event_dialog(self):
        """显示添加事件的对话框"""
        dialog = AddEventDialog(self)
        if dialog.exec():
            config = dialog.get_config()
            self.add_new_event_widget(config)
            self.save_events()
    
    def add_new_event_widget(self, config=None):
        item = QListWidgetItem(self.event_list)
        widget = EventConfigWidget(
            on_delete=lambda widget=None: self.delete_event_widget(item),
            on_change=None
        )
        
        if config:
            widget.set_config(config)
            
        item.setSizeHint(widget.sizeHint())
        self.event_list.addItem(item)
        self.event_list.setItemWidget(item, widget)
        

    def delete_event_widget(self, item):
        row = self.event_list.row(item)
        self.event_list.takeItem(row)
        self.save_events()

    def save_events(self):
        events = []
        for i in range(self.event_list.count()):
            item = self.event_list.item(i)
            widget = self.event_list.itemWidget(item)
            config = widget.get_config()
            if config.get("weapon") and config.get("sound"):
                events.append(config)
        self.parent.config_manager.config['gsi_events'] = events
        self.parent.config_manager.save_config()
        
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
        self.event_list.clear()
        events = self.parent.config_manager.config.get('gsi_events', [])
        for event_config in events:
            self.add_new_event_widget(event_config)
            
    def process_game_state(self, game_state: dict):
        player = game_state.get('player', {})
        if not player: return

        if player.get('activity') != 'playing':
            return

        self._process_weapon_events(game_state, player)
        
        self._process_bomb_and_kill_events(game_state, player)
    
    def _process_weapon_events(self, game_state: dict, player: dict):
        # 处理武器相关的事件（切枪、换弹）
        weapons = player.get('weapons', {}).values()
        
        for i in range(self.event_list.count()):
            item = self.event_list.item(i)
            widget = self.event_list.itemWidget(item)
            config = widget.get_config()
            
            weapon_name = config.get('weapon')
            event_type = config.get('event')
            sound_path = config.get('sound')

            # 只处理武器相关事件
            if event_type not in ['active', 'reloading']:
                continue
                
            if not all([weapon_name, event_type, sound_path]):
                continue

            # 查找当前武器状态
            current_weapon = None
            for weapon in weapons:
                if weapon.get('name') == weapon_name:
                    current_weapon = weapon
                    break
            
            if not current_weapon:
                continue
                
            current_state = current_weapon.get('state')
            
            # 使用武器名称和事件类型的组合作为状态键，避免不同事件类型互相干扰
            state_key = f"{weapon_name}:{event_type}"
            
            # 从存储中获取之前的状态
            previous_state = self.previous_weapon_states.get(state_key)
            
            # 检查状态转换逻辑
            should_trigger = False
            
            # 添加调试信息
            print(f"[GSI音效] 武器: {weapon_name}, 事件类型: {event_type}")
            print(f"[GSI音效] 当前状态: {current_state}, 之前状态: {previous_state}")
            print(f"[GSI音效] 音效路径: {sound_path}")
            print(f"[GSI音效] 状态键: {state_key}")
            
            if event_type == 'active':
                # 只有当武器从holstered状态转变为active状态时才触发
                if current_state == 'active' and previous_state == 'holstered':
                    should_trigger = True
                    print(f"[GSI音效] 触发切枪音效: {weapon_name}")
            elif event_type == 'reloading':
                # 只有当武器从非reloading状态转变为reloading状态时才触发
                if current_state == 'reloading' and previous_state != 'reloading':
                    should_trigger = True
                    print(f"[GSI音效] 触发换弹音效: {weapon_name}")
            
            if should_trigger:
                if os.path.exists(sound_path):
                    volume = config.get('volume', 50)  # 获取音量设置，默认50%
                    print(f"[GSI音效] 播放音效: {sound_path}, 音量: {volume}%")
                    self.sound_player.play_sound(sound_path, volume)
                else:
                    print(f"[GSI音效] 错误: 音效文件不存在: {sound_path}")
            
            self.previous_weapon_states[state_key] = current_state
    
    def _process_bomb_and_kill_events(self, game_state: dict, player: dict):
        # 检查击杀事件
        match_stats = player.get('match_stats', {})
        current_kills = match_stats.get('kills', 0)
        round_info = game_state.get('round', {})
        current_round_phase = round_info.get('phase', '')
        
        observer_slot = player.get('observer_slot')
        
        # 初始化
        if not hasattr(self, 'previous_kills'):
            self.previous_kills = current_kills
        if not hasattr(self, 'previous_round_phase'):
            self.previous_round_phase = current_round_phase
        if not hasattr(self, 'previous_observing_state'):
            self.previous_observing_state = False
        if not hasattr(self, 'previous_observer_slot'):
            self.previous_observer_slot = observer_slot
            
        # 检测回合重置
        if (current_round_phase == 'freezetime' and 
            self.previous_round_phase != 'freezetime'):
            print(f"[GSI音效] 检测到新回合开始，重置击杀数跟踪: {self.previous_kills} -> {current_kills}")
            self.previous_kills = current_kills
            self.previous_round_phase = current_round_phase
            return  # 直接返回，避免在回合重置时触发音效
        
        # 安全检查
        player_state = player.get('state', {})
        player_team = player.get('team', '')
        round_info = game_state.get('round', {})
        
        # 检查玩家是否有有效的队伍和在正确的回合阶段
        has_valid_team = player_team in ['T', 'CT']
        valid_round_phases = ['live', 'freezetime', 'unknown']
        current_phase = round_info.get('phase', 'unknown')
        is_in_round = current_phase in valid_round_phases
        is_alive = player_state.get('health', 0) > 0  # 保留用于调试
        
        # 添加回合状态调试信息
        print(f"[GSI音效] 回合状态检测: 当前阶段='{current_phase}', 有效阶段={valid_round_phases}, 在回合中={is_in_round}")
        
        # 检查是否在观战状态
        spectarget = player.get('spectarget')
        activity = player.get('activity', '')
        
        is_observing = (
            spectarget is not None or  # 正在观战
            activity == 'spectating' or  # 活动状态为观战
            (not is_alive and observer_slot is not None)  # 死亡后的观战状态
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
            self.previous_observer_slot = observer_slot
            self.previous_round_phase = current_round_phase
            self.previous_observing_state = is_observing
            return  # 直接返回，避免在观察位置切换时触发音效
        
        # 检测观战状态变化：当观战状态发生变化时，重置击杀数跟踪
        if is_observing != self.previous_observing_state:
            print(f"[GSI音效] 检测到观战状态变化: {self.previous_observing_state} -> {is_observing}，重置击杀数跟踪")
            self.previous_kills = current_kills
            self.previous_round_phase = current_round_phase
            self.previous_observing_state = is_observing
            return  # 直接返回，避免在观战状态切换时触发音效
        
        # 添加调试信息
        if current_kills > self.previous_kills:
            print(f"[GSI音效] 击杀数变化: {self.previous_kills} -> {current_kills}")
            print(f"[GSI音效] 玩家存活: {is_alive}, 有效队伍: {has_valid_team}, 回合状态: {is_in_round}")
            print(f"[GSI音效] 观战状态: {is_observing}, 观战位置: {observer_slot}, 观战目标: {spectarget}, 活动: {activity}")
            print(f"[GSI音效] 玩家血量: {player_state.get('health', 0)}, 队伍: {player_team}, 回合阶段: {round_info.get('phase', 'unknown')}")
        
        # 只有在有有效队伍、在回合中、不在观战状态且击杀数增加时才触发音效
        if (current_kills > self.previous_kills and 
            has_valid_team and is_in_round and not is_observing):
            print(f"[GSI音效] 确认击杀事件，开始播放音效")
            # 发生击杀，获取当前武器信息
            weapons = player.get('weapons', {})
            current_weapon = None
            for weapon_slot, weapon_info in weapons.items():
                if weapon_info.get('state') == 'active':
                    current_weapon = weapon_info.get('name', '')
                    break
            
            is_knife_kill = False
            if current_weapon and ('knife' in current_weapon.lower() or 'bayonet' in current_weapon.lower()):
                is_knife_kill = True
                print(f"[GSI音效] 检测到刀杀: {current_weapon}")
            
            # 查找音效配置
            played_sound = False
            knife_kill_config = None
            weapon_kill_config = None
            global_kill_config = None
            
            # 遍历所有事件配置，查找各种击杀音效
            for i in range(self.event_list.count()):
                item = self.event_list.item(i)
                widget = self.event_list.itemWidget(item)
                config = widget.get_config()
                
                event_type = config.get('event')
                weapon_name = config.get('weapon', '')
                
                # 收集不同类型的击杀音效配置
                if event_type == 'knife_kill':
                    knife_kill_config = config
                elif event_type == 'weapon_kill' and current_weapon and weapon_name == current_weapon:
                    weapon_kill_config = config
                elif event_type == 'kill':
                    global_kill_config = config
            
            # 按优先级播放音效：刀杀 > 特定武器击杀 > 全局击杀
            if is_knife_kill and knife_kill_config:
                sound_path = knife_kill_config.get('sound')
                if sound_path and os.path.exists(sound_path):
                    volume = knife_kill_config.get('volume', 50)
                    self.sound_player.play_sound(sound_path, volume)
                    print(f"[GSI音效] 触发刀杀音效: {current_weapon}, 音量: {volume}%")
                    played_sound = True
            
            if not played_sound and weapon_kill_config:
                sound_path = weapon_kill_config.get('sound')
                if sound_path and os.path.exists(sound_path):
                    volume = weapon_kill_config.get('volume', 50)
                    self.sound_player.play_sound(sound_path, volume)
                    print(f"[GSI音效] 触发武器击杀音效: {current_weapon}, 音量: {volume}%")
                    played_sound = True
            
            if not played_sound and global_kill_config:
                sound_path = global_kill_config.get('sound')
                if sound_path and os.path.exists(sound_path):
                    volume = global_kill_config.get('volume', 50)
                    self.sound_player.play_sound(sound_path, volume)
                    print(f"[GSI音效] 触发全局击杀音效, 音量: {volume}%")
                    played_sound = True
        
        self.previous_kills = current_kills
        self.previous_round_phase = current_round_phase
        self.previous_observing_state = is_observing