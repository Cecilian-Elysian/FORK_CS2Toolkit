import json
import os
import shutil
import zipfile
import uuid

class ConfigManager:
    # 统一的配置管理器。
    # - 管理CS2Toolkit工作目录。
    # - 将所有预设（视频、音效、字体）保存在一个 preconfig.json 文件中。
    def __init__(self, directory_name="CS2Toolkit"):
        self.work_dir = os.path.join(os.getcwd(), directory_name)
        self.presets_file = os.path.join(self.work_dir, "preconfig.json")
        self.thumbnails_dir = os.path.join(self.work_dir, "thumbnails")
        self.configs_dir = os.path.join(self.work_dir, "configs")
        
        self.config = {
            "video_presets": [],
            "sound_presets": [],
            "font_presets": [],
            "gsi_sound_presets": [],
            "gsi_events": [],
            "theme": "Auto",               # Auto, Light, Dark
            "close_behavior": "prompt",    # prompt, tray, exit
            "hide_close_prompt": False,
            "auto_start": False
        }
        
        self._ensure_directories()
        self.load_config()

    def _ensure_directories(self):
        # 确保工作目录和缩略图目录存在
        os.makedirs(self.work_dir, exist_ok=True)
        os.makedirs(self.thumbnails_dir, exist_ok=True)
        os.makedirs(self.configs_dir, exist_ok=True)

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
                    # 加载新的键（防止后续新增键丢失）
                    for key in loaded_config:
                        if key not in self.config:
                            self.config[key] = loaded_config[key]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"配置文件加载失败或不存在，将创建新的配置: {e}")
            self.save_config()

    def save_config(self):
        # 将当前配置保存到 preconfig.json
        with open(self.presets_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()

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

    def reset_all(self):
        # 重置所有配置到默认状态
        self.config = {
            "video_presets": [],
            "sound_presets": [],
            "font_presets": [],
            "gsi_sound_presets": [],
            "gsi_events": [],
            "theme": "Auto",               
            "close_behavior": "prompt",    
            "hide_close_prompt": False,
            "auto_start": False
        }
        self.save_config()
        
        # 清理缩略图
        if os.path.exists(self.thumbnails_dir):
            for file in os.listdir(self.thumbnails_dir):
                try:
                    os.remove(os.path.join(self.thumbnails_dir, file))
                except:
                    pass

    def is_valid_config_zip(self, zip_path):
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                return ".cs2toolkit_profile" in zipf.namelist()
        except Exception:
            return False

    def get_zip_meta(self, zip_path):
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                if "meta.json" in zipf.namelist():
                    meta_bytes = zipf.read("meta.json")
                    return json.loads(meta_bytes.decode('utf-8'))
        except Exception:
            pass
        return {"name": os.path.basename(zip_path), "description": "无描述信息"}

    def export_config(self, export_zip_path, name, description="", selections=None):
        import copy
        if selections is None:
            selections = {"bg": True, "video": True, "sound": True, "font": True, "visual": True, "gsi": True}
            
        export_data = copy.deepcopy(self.config)
        included_resources = []
        
        try:
            with zipfile.ZipFile(export_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                file_map = {} # path -> relative_name
                
                def _add_file(abs_path, category):
                    if not abs_path or not os.path.exists(abs_path):
                        return ""
                    if abs_path in file_map:
                        return file_map[abs_path]
                    
                    basename = os.path.basename(abs_path)
                    rel_name = f"resources/{category}/{basename}"
                    zipf.write(abs_path, rel_name)
                    file_map[abs_path] = rel_name
                    return rel_name
                    
                # 1. video_presets
                if selections.get("video"):
                    included_resources.append("开屏动画预设及配置")
                    for p in export_data.get("video_presets", []):
                        p["video_path"] = _add_file(p.get("video_path"), "video")
                        p["thumbnail_path"] = _add_file(p.get("thumbnail_path"), "thumb")
                    if export_data.get("current_video_path"):
                        export_data["current_video_path"] = _add_file(export_data.get("current_video_path"), "video")
                else:
                    export_data["video_presets"] = []
                    export_data["current_video"] = ""
                    export_data["current_video_path"] = ""
                    
                # 2. sound_presets
                if selections.get("sound"):
                    included_resources.append("启动音效预设及配置")
                    for p in export_data.get("sound_presets", []):
                        p["sound_path"] = _add_file(p.get("sound_path"), "sound")
                    if export_data.get("current_sound_path"):
                        export_data["current_sound_path"] = _add_file(export_data.get("current_sound_path"), "sound")
                else:
                    export_data["sound_presets"] = []
                    export_data["current_sound"] = ""
                    export_data["current_sound_path"] = ""
                    
                # 3. font_presets
                if selections.get("font"):
                    included_resources.append("全局字体预设及配置")
                    for p in export_data.get("font_presets", []):
                        p["font_path"] = _add_file(p.get("font_path"), "font")
                    if export_data.get("current_font_path"):
                        export_data["current_font_path"] = _add_file(export_data.get("current_font_path"), "font")
                else:
                    export_data["font_presets"] = []
                    export_data["current_font"] = ""
                    export_data["current_font_path"] = ""
                    
                # 4. gsi_events
                if selections.get("gsi"):
                    included_resources.append("游戏内实时音效配置")
                    for e in export_data.get("gsi_events", []):
                        e["sound"] = _add_file(e.get("sound"), "gsi")
                        if "sounds_1_5" in e:
                            for s in e["sounds_1_5"]:
                                s["path"] = _add_file(s.get("path"), "gsi")
                else:
                    export_data["gsi_events"] = []
                            
                # 5. visual
                if selections.get("visual"):
                    included_resources.append("游戏内视觉效果配置")
                    visual = export_data.get("visual", {})
                    if "flash_path" in visual:
                        visual["flash_path"] = _add_file(visual.get("flash_path"), "flash")
                    if "death_media_path" in visual:
                        visual["death_media_path"] = _add_file(visual.get("death_media_path"), "death")
                    if "kill_icon_path" in visual:
                        visual["kill_icon_path"] = _add_file(visual.get("kill_icon_path"), "kill_icon")
                    if "kill_icons_1_5" in visual:
                        for k in visual["kill_icons_1_5"]:
                            k["path"] = _add_file(k.get("path"), "kill_icon")
                    export_data["visual"] = visual
                else:
                    export_data["visual"] = {}
                
                # 6. bg_path
                if selections.get("bg"):
                    if export_data.get("bg_path"):
                        included_resources.append("自定义软件背景")
                        export_data["bg_path"] = _add_file(export_data.get("bg_path"), "bg")
                else:
                    export_data["bg_path"] = ""
                    
                # 7. current selected items validation
                current_video = export_data.get("current_video")
                if current_video and not export_data.get("current_video_path"):
                    for p in export_data.get("video_presets", []):
                        if p.get("name") == current_video:
                            export_data["current_video_path"] = p.get("video_path")
                            break
                    else:
                        export_data["current_video"] = ""

                current_sound = export_data.get("current_sound")
                if current_sound and not export_data.get("current_sound_path"):
                    for p in export_data.get("sound_presets", []):
                        if p.get("name") == current_sound:
                            export_data["current_sound_path"] = p.get("sound_path")
                            break
                    else:
                        export_data["current_sound"] = ""
                        
                current_font = export_data.get("current_font")
                if current_font and not export_data.get("current_font_path"):
                    for p in export_data.get("font_presets", []):
                        if p.get("name") == current_font:
                            export_data["current_font_path"] = p.get("font_path")
                            break
                    else:
                        export_data["current_font"] = ""
                    
                # write config.json
                zipf.writestr("config.json", json.dumps(export_data, ensure_ascii=False, indent=4))
                
                # write meta.json
                meta = {
                    "name": name,
                    "description": description,
                    "included_resources": included_resources
                }
                zipf.writestr("meta.json", json.dumps(meta, ensure_ascii=False, indent=4))
                zipf.writestr(".cs2toolkit_profile", "CS2Toolkit Configuration Profile")
                
            return True, "导出成功"
        except Exception as e:
            return False, f"导出失败: {str(e)}"

    def import_config(self, import_zip_path):
        extract_dir = os.path.join(self.work_dir, "imported", uuid.uuid4().hex[:8])
        os.makedirs(extract_dir, exist_ok=True)
        
        try:
            with zipfile.ZipFile(import_zip_path, 'r') as zipf:
                zipf.extractall(extract_dir)
                
            config_file = os.path.join(extract_dir, "config.json")
            if not os.path.exists(config_file):
                return False, "压缩包内没有 config.json，格式不正确。"
                
            with open(config_file, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
                
            def _resolve_path(rel_path):
                if not rel_path: return ""
                rel_path = rel_path.replace("/", os.sep)
                abs_path = os.path.join(extract_dir, rel_path)
                return abs_path if os.path.exists(abs_path) else ""
                
            # 1. video_presets
            for p in imported_config.get("video_presets", []):
                p["video_path"] = _resolve_path(p.get("video_path"))
                p["thumbnail_path"] = _resolve_path(p.get("thumbnail_path"))
            if imported_config.get("current_video_path"):
                imported_config["current_video_path"] = _resolve_path(imported_config.get("current_video_path"))
                
            # 2. sound_presets
            for p in imported_config.get("sound_presets", []):
                p["sound_path"] = _resolve_path(p.get("sound_path"))
            if imported_config.get("current_sound_path"):
                imported_config["current_sound_path"] = _resolve_path(imported_config.get("current_sound_path"))
                
            # 3. font_presets
            for p in imported_config.get("font_presets", []):
                p["font_path"] = _resolve_path(p.get("font_path"))
            if imported_config.get("current_font_path"):
                imported_config["current_font_path"] = _resolve_path(imported_config.get("current_font_path"))
                
            # 4. gsi_events
            for e in imported_config.get("gsi_events", []):
                e["sound"] = _resolve_path(e.get("sound"))
                if "sounds_1_5" in e:
                    for s in e["sounds_1_5"]:
                        s["path"] = _resolve_path(s.get("path"))
                        
            # 5. visual
            visual = imported_config.get("visual", {})
            if "flash_path" in visual:
                visual["flash_path"] = _resolve_path(visual.get("flash_path"))
            if "death_media_path" in visual:
                visual["death_media_path"] = _resolve_path(visual.get("death_media_path"))
            if "kill_icon_path" in visual:
                visual["kill_icon_path"] = _resolve_path(visual.get("kill_icon_path"))
            if "kill_icons_1_5" in visual:
                for k in visual["kill_icons_1_5"]:
                    k["path"] = _resolve_path(k.get("path"))
            imported_config["visual"] = visual
                
            # 6. bg_path
            if imported_config.get("bg_path"):
                imported_config["bg_path"] = _resolve_path(imported_config.get("bg_path"))
                
            # Update config
            for key in imported_config:
                self.config[key] = imported_config[key]
                
            self.save_config()
            return True, "导入成功"
        except Exception as e:
            return False, f"导入失败: {str(e)}"