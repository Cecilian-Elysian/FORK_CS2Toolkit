import json
import os
from typing import Dict, List, Optional

class GSISoundPresetManager:
    # GSI音效预设管理器
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.presets_file = os.path.join(config_manager.work_dir, "gsi_sound_presets.json")
        self.presets = self._load_presets()
    
    def _load_presets(self) -> Dict:
        # 加载GSI音效预设
        if os.path.exists(self.presets_file):
            try:
                with open(self.presets_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载GSI音效预设失败: {e}")
        return {}
    
    def save_presets(self):
        # 保存GSI音效预设
        try:
            with open(self.presets_file, 'w', encoding='utf-8') as f:
                json.dump(self.presets, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存GSI音效预设失败: {e}")
    
    def add_preset(self, name: str, pack_path: str, description: str = "", 
                   author: str = "", version: str = "1.0") -> bool:
        # 添加GSI音效预设
        # Args:
        #     name: 预设名称
        #     pack_path: 音效包路径
        #     description: 描述
        #     author: 作者
        #     version: 版本
        # Returns:
        #     是否添加成功
        try:
            # 检查音效包配置文件
            pack_config_path = os.path.join(pack_path, "pack.json")
            if not os.path.exists(pack_config_path):
                return False
            
            with open(pack_config_path, 'r', encoding='utf-8') as f:
                pack_config = json.load(f)
            
            preset_id = f"gsi_sound_{len(self.presets) + 1}"
            self.presets[preset_id] = {
                "name": name,
                "pack_path": pack_path,
                "description": description,
                "author": author,
                "version": version,
                "pack_config": pack_config
            }
            
            self.save_presets()
            return True
        except Exception as e:
            print(f"添加GSI音效预设失败: {e}")
            return False
    
    def remove_preset(self, preset_id: str) -> bool:
        # 删除GSI音效预设
        if preset_id in self.presets:
            del self.presets[preset_id]
            self.save_presets()
            return True
        return False
    
    def get_preset(self, preset_id: str) -> Optional[Dict]:
        # 获取指定的GSI音效预设
        return self.presets.get(preset_id)
    
    def get_all_presets(self) -> Dict:
        # 获取所有GSI音效预设
        return self.presets.copy()
    
    def get_preset_names(self) -> List[str]:
        # 获取所有预设名称
        return [preset["name"] for preset in self.presets.values()]
    
    def get_preset_by_name(self, name: str) -> Optional[Dict]:
        # 根据名称获取预设
        for preset_id, preset in self.presets.items():
            if preset["name"] == name:
                return {"id": preset_id, **preset}
        return None
    
    def update_preset(self, preset_id: str, **kwargs) -> bool:
        # 更新预设信息
        if preset_id not in self.presets:
            return False
        
        for key, value in kwargs.items():
            if key in ["name", "pack_path", "description", "author", "version"]:
                self.presets[preset_id][key] = value
        
        self.save_presets()
        return True