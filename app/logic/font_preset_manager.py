import json
import os

class FontPresetManager:
    # 字体预设管理器
    
    def __init__(self, presets_file="font_presets.json"):
        self.presets_file = presets_file
        self.presets = []
        self.load_presets()
    
    def load_presets(self):
        # 加载字体预设
        try:
            with open(self.presets_file, 'r', encoding='utf-8') as f:
                self.presets = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.presets = []
    
    def save_presets(self):
        # 保存字体预设
        with open(self.presets_file, 'w', encoding='utf-8') as f:
            json.dump(self.presets, f, ensure_ascii=False, indent=2)
    
    def add_preset(self, name, font_path, font_name=None):
        # 添加字体预设
        if font_name is None:
            font_name = self.extract_font_name(font_path)
        
        preset = {
            "name": name,
            "font_path": font_path,
            "font_name": font_name,
            "font_filename": os.path.basename(font_path)
        }
        
        self.presets.append(preset)
        self.save_presets()
    
    def delete_preset(self, index):
        # 删除字体预设
        if 0 <= index < len(self.presets):
            del self.presets[index]
            self.save_presets()
    
    def get_preset(self, index):
        # 获取指定索引的预设
        if 0 <= index < len(self.presets):
            return self.presets[index]
        return None
    
    def extract_font_name(self, font_path):
        # 从字体文件路径提取字体名称（去掉扩展名）
        filename = os.path.basename(font_path)
        font_name = os.path.splitext(filename)[0]
        return font_name
    
    def preset_exists(self, name):
        # 检查预设名称是否已存在
        return any(preset["name"] == name for preset in self.presets)
    
    def get_preset_names(self):
        # 获取所有预设名称列表
        return [preset["name"] for preset in self.presets]