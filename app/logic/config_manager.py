import json
import os

class ConfigManager:
    # 统一的配置管理器。
    # - 管理CS2Toolkit工作目录。
    # - 将所有预设（视频、音效、字体）保存在一个 preconfig.json 文件中。
    def __init__(self, directory_name="CS2Toolkit"):
        self.work_dir = os.path.join(os.getcwd(), directory_name)
        self.presets_file = os.path.join(self.work_dir, "preconfig.json")
        self.thumbnails_dir = os.path.join(self.work_dir, "thumbnails")
        
        self.config = {
            "video_presets": [],
            "sound_presets": [],
            "font_presets": [],
            "gsi_sound_presets": [],
            "gsi_events": []
        }
        
        self._ensure_directories()
        self.load_config()

    def _ensure_directories(self):
        # 确保工作目录和缩略图目录存在
        os.makedirs(self.work_dir, exist_ok=True)
        os.makedirs(self.thumbnails_dir, exist_ok=True)

    def load_config(self):
        # 从 preconfig.json 加载配置
        try:
            if os.path.exists(self.presets_file):
                with open(self.presets_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 确保所有键都存在
                    for key in self.config:
                        if key in loaded_config:
                            self.config[key] = loaded_config[key]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"配置文件加载失败或不存在，将创建新的配置: {e}")
            self.save_config()

    def save_config(self):
        # 将当前配置保存到 preconfig.json
        with open(self.presets_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

    def get_presets(self, preset_type):
        # 获取指定类型的预设. 'video', 'sound', 'font'
        return self.config.get(f"{preset_type}_presets", [])

    def add_preset(self, preset_type, **kwargs):
        # 添加一个预设到指定类型.
        # 例如: add_preset('video', name="MyVideo", video_path="path/to/vid")
        key = f"{preset_type}_presets"
        if key in self.config:
            self.config[key].append(kwargs)
            self.save_config()

    def delete_preset(self, preset_type, index):
        # 删除指定类型的预设
        key = f"{preset_type}_presets"
        if key in self.config and 0 <= index < len(self.config[key]):
            # 如果是视频预设，则额外删除缩略图文件
            if preset_type == 'video':
                preset = self.config[key][index]
                if "thumbnail_path" in preset and os.path.exists(preset["thumbnail_path"]):
                    try:
                        os.remove(preset["thumbnail_path"])
                    except OSError as e:
                        print(f"删除缩略图失败 {preset['thumbnail_path']}: {e}")

            del self.config[key][index]
            self.save_config()

    def get_thumbnail_dir(self):
        # 获取缩略图文件夹路径
        return self.thumbnails_dir