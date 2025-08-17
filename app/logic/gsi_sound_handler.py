import json
import os
from .sound_player import SoundPlayer

class GSISoundHandler:
    """GSI音效事件处理器 - 处理游戏状态变化并播放相应音效"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.sound_player = SoundPlayer()
        self.current_gsi_pack = None
        self.last_game_state = {}
        self.volume = 50  # 默认音量50%
        
    def set_gsi_sound_pack(self, pack_path):
        """设置当前使用的GSI音效包"""
        if not os.path.exists(pack_path):
            print(f"GSI音效包路径不存在: {pack_path}")
            return False
            
        pack_info_file = os.path.join(pack_path, "pack.json")
        if not os.path.exists(pack_info_file):
            pack_info_file = os.path.join(pack_path, "pack_info.json")
            
        if not os.path.exists(pack_info_file):
            print(f"GSI音效包配置文件不存在: {pack_info_file}")
            return False
            
        try:
            with open(pack_info_file, 'r', encoding='utf-8') as f:
                pack_info = json.load(f)
                
            if pack_info.get('type') != 'gsi_sound':
                print(f"不是有效的GSI音效包类型: {pack_info.get('type')}")
                return False
                
            self.current_gsi_pack = {
                'path': pack_path,
                'info': pack_info
            }
            print(f"已设置GSI音效包: {pack_info.get('name')}")
            return True
            
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"读取GSI音效包配置失败: {e}")
            return False
    
    def set_volume(self, volume):
        """设置音效音量 (0-100)"""
        self.volume = max(0, min(100, volume))
        
    def handle_gsi_data(self, gsi_data_bytes):
        """处理GSI数据并触发相应音效"""
        if not self.current_gsi_pack:
            return
            
        try:
            # 尝试多种编码方式解码数据
            gsi_data_str = None
            for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
                try:
                    gsi_data_str = gsi_data_bytes.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if gsi_data_str is None:
                # 如果所有编码都失败，使用错误处理方式
                gsi_data_str = gsi_data_bytes.decode('utf-8', errors='ignore')
                print("警告: GSI数据包含无法解码的字符，已忽略部分内容")
            
            gsi_data = json.loads(gsi_data_str)
            
            # 检查炸弹事件
            self._check_bomb_events(gsi_data)
            
            # 检查玩家死亡事件
            self._check_death_events(gsi_data)

            # 检查击杀事件
            self._check_kill_events(gsi_data)
            
            # 更新上一次的游戏状态
            self.last_game_state = gsi_data.copy()
            
        except json.JSONDecodeError as e:
            print(f"解析GSI JSON数据失败: {e}")
        except Exception as e:
            print(f"处理GSI数据时发生未知错误: {e}")
    
    def _check_bomb_events(self, gsi_data):
        """检查炸弹相关事件"""
        bomb_data = gsi_data.get('bomb', {})
        last_bomb_data = self.last_game_state.get('bomb', {})
        
        # 检查炸弹安装事件
        current_state = bomb_data.get('state')
        last_state = last_bomb_data.get('state')
        
        if current_state == 'planted' and last_state != 'planted':
            self._play_sound('bomb_planted')
            
        # 检查炸弹拆除事件
        if current_state == 'defused' and last_state != 'defused':
            self._play_sound('bomb_defused')
    
    def _check_death_events(self, gsi_data):
        """检查玩家死亡事件"""
        player_data = gsi_data.get('player', {})
        player_state = player_data.get('state', {})
        
        last_player_data = self.last_game_state.get('player', {})
        last_player_state = last_player_data.get('state', {})
        
        # 检查玩家死亡
        current_health = player_state.get('health', 100)
        last_health = last_player_state.get('health', 100)
        
        if current_health == 0 and last_health > 0:
            self._play_sound('death')

    def _check_kill_events(self, gsi_data):
        """检查击杀事件"""
        player_data = gsi_data.get('player', {})
        match_stats = player_data.get('match_stats', {})
        current_kills = match_stats.get('kills', 0)

        last_player_data = self.last_game_state.get('player', {})
        last_match_stats = last_player_data.get('match_stats', {})
        last_kills = last_match_stats.get('kills', 0)

        if current_kills > last_kills:
            # 获取当前武器信息
            current_weapon = None
            weapons = player_data.get('weapons', {})
            for weapon_info in weapons.values():
                if weapon_info.get('state') == 'active':
                    current_weapon = weapon_info.get('name')
                    break
            
            # 检查是否是刀杀
            is_knife_kill = False
            if current_weapon and ('knife' in current_weapon.lower() or 'bayonet' in current_weapon.lower()):
                is_knife_kill = True
            
            # 优先级：刀杀 > 特定武器击杀 > 全局击杀
            if is_knife_kill:
                self._play_sound('knife_kill')
            elif current_weapon:
                self._play_sound('weapon_kill')
            else:
                self._play_sound('kill')
    

    
    def _play_sound(self, sound_type):
        """播放指定类型的音效"""
        if not self.current_gsi_pack:
            return
            
        pack_info = self.current_gsi_pack['info']
        pack_path = self.current_gsi_pack['path']
        
        # 从pack.json获取文件映射
        files = pack_info.get('files', {})
        
        # 尝试不同的文件名格式
        sound_file = None
        possible_keys = [
            sound_type,
            f"{sound_type}_file",
            sound_type.replace('_', '')
        ]
        
        for key in possible_keys:
            if key in files:
                sound_file = files[key]
                break
        
        # 如果在files中没找到，尝试直接从pack_info中获取
        if not sound_file:
            sound_file_key = f"{sound_type}_file"
            sound_file = pack_info.get(sound_file_key)
        
        if not sound_file:
            print(f"未找到音效文件配置: {sound_type}")
            return
            
        sound_path = os.path.join(pack_path, sound_file)
        
        if not os.path.exists(sound_path):
            print(f"音效文件不存在: {sound_path}")
            return
            
        print(f"播放GSI音效: {sound_type} -> {sound_file}")
        self.sound_player.play_sound(sound_path, self.volume)
    
    def test_sound(self, sound_type):
        """测试播放指定类型的音效"""
        self._play_sound(sound_type)
    
    def get_available_sounds(self):
        """获取当前音效包中可用的音效列表"""
        if not self.current_gsi_pack:
            return []
            
        pack_info = self.current_gsi_pack['info']
        files = pack_info.get('files', {})
        
        # 标准GSI音效类型
        gsi_sound_types = ['bomb_planted', 'bomb_defused', 'kill', 'death']
        available_sounds = []
        
        for sound_type in gsi_sound_types:
            # 检查是否有对应的音效文件
            if any(key.startswith(sound_type) for key in files.keys()):
                available_sounds.append(sound_type)
        
        return available_sounds
    
    def get_current_pack_info(self):
        """获取当前音效包信息"""
        if not self.current_gsi_pack:
            return None
        return self.current_gsi_pack['info']