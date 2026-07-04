import json
import os
import shutil
import sys
import zipfile
import uuid

class ConfigManager:
    # 统一的配置管理器。
    # - 管理CS2Toolkit工作目录。
    # - 将所有预设（视频、音效、字体）保存在一个 preconfig.json 文件中。
    def __init__(self, directory_name="CS2Toolkit"):
        self.directory_name = directory_name
        self.work_dir = self._resolve_work_dir(directory_name)
        self.presets_file = os.path.join(self.work_dir, "preconfig.json")
        self.thumbnails_dir = os.path.join(self.work_dir, "thumbnails")
        self.configs_dir = os.path.join(self.work_dir, "configs")
        
        self.config = {
            "video_presets": [],
            "sound_presets": [],
            "font_presets": [],
            "gsi_sound_presets": [],
            "gsi_events": [],
            "go_pet": {
                "enabled": False,
                "display_mode": "game",
                "size": 200,
                "offset_x": 50,
                "offset_y": 50,
                "events": []
            },
            "theme": "Auto",               # Auto, Light, Dark
            "close_behavior": "prompt",    # prompt, tray, exit
            "hide_close_prompt": False,
            "auto_start": False
        }

        self._ensure_directories()
        self._migrate_legacy_work_dir()
        self.load_config()

    def _resolve_work_dir(self, directory_name):
        exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        parent_dir = os.path.dirname(exe_dir)
        
        # Check for path override file (e.g. if user moved the data directory)
        for d in [exe_dir, parent_dir]:
            override_file = os.path.join(d, "cs2toolkit_data_path.txt")
            if os.path.isfile(override_file):
                try:
                    with open(override_file, 'r', encoding='utf-8') as f:
                        custom_path = f.read().strip()
                        if custom_path and os.path.isabs(custom_path):
                            # Try to ensure the custom directory exists
                            os.makedirs(custom_path, exist_ok=True)
                            return custom_path
                except Exception as e:
                    print(f"无法读取或创建自定义数据路径: {e}")

        # Default to LOCALAPPDATA
        local_appdata = os.environ.get("LOCALAPPDATA")
        if not local_appdata:
            local_appdata = os.path.join(os.path.expanduser("~"), "AppData", "Local")
        return os.path.join(local_appdata, directory_name)

    def change_work_dir(self, new_dir):
        """将当前数据迁移到新目录，并写入重定向文件"""
        if not new_dir or not os.path.isabs(new_dir):
            return False, "新路径必须是有效的绝对路径。"
            
        if os.path.abspath(new_dir) == os.path.abspath(self.work_dir):
            return False, "新路径与当前路径相同。"

        # 1. 尝试复制所有文件到新目录
        try:
            os.makedirs(new_dir, exist_ok=True)
            for item in os.listdir(self.work_dir):
                src_path = os.path.join(self.work_dir, item)
                dst_path = os.path.join(new_dir, item)
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                else:
                    shutil.copy2(src_path, dst_path)
        except OSError as e:
            return False, f"复制数据到新目录失败，可能是空间不足或权限受限: {e}"

        # 2. 写入重定向文件
        exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        if os.path.basename(exe_dir).lower() == "runtime":
            write_dir = os.path.dirname(exe_dir)
        else:
            write_dir = exe_dir
            
        override_file = os.path.join(write_dir, "cs2toolkit_data_path.txt")
        try:
            with open(override_file, 'w', encoding='utf-8') as f:
                f.write(os.path.abspath(new_dir))
        except OSError as e:
            return False, f"无法写入路径配置文件: {e}"

        # 3. 迁移成功（不自动删除旧目录，以防万一，用户可手动删除）
        return True, "数据目录迁移成功！为了确保所有组件正常工作，请重新启动本软件。"

    def _candidate_legacy_work_dirs(self):
        seen = set()
        candidates = []

        def add_candidate(path):
            if not path:
                return
            normalized = os.path.abspath(path)
            if normalized == os.path.abspath(self.work_dir):
                return
            if normalized in seen:
                return
            seen.add(normalized)
            if os.path.isdir(normalized):
                candidates.append(normalized)

        cwd = os.path.abspath(os.getcwd())
        exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

        add_candidate(os.path.join(cwd, self.directory_name))
        add_candidate(os.path.join(exe_dir, self.directory_name))

        parent_dirs = {
            os.path.dirname(cwd),
            os.path.dirname(exe_dir),
        }
        for parent_dir in parent_dirs:
            if not parent_dir or not os.path.isdir(parent_dir):
                continue
            try:
                for entry in os.scandir(parent_dir):
                    if not entry.is_dir():
                        continue
                    add_candidate(os.path.join(entry.path, self.directory_name))
            except OSError:
                continue

        return candidates

    def _find_legacy_work_dir(self):
        best_candidate = ""
        best_mtime = -1.0

        for candidate in self._candidate_legacy_work_dirs():
            candidate_preset = os.path.join(candidate, "preconfig.json")
            if not os.path.isfile(candidate_preset):
                continue
            try:
                candidate_mtime = os.path.getmtime(candidate_preset)
            except OSError:
                candidate_mtime = 0.0
            if candidate_mtime > best_mtime:
                best_candidate = candidate
                best_mtime = candidate_mtime

        return best_candidate

    def _migrate_legacy_work_dir(self):
        if os.path.exists(self.presets_file):
            return

        legacy_work_dir = self._find_legacy_work_dir()
        if not legacy_work_dir:
            return

        try:
            for entry in os.scandir(legacy_work_dir):
                src = entry.path
                dst = os.path.join(self.work_dir, entry.name)
                if entry.is_dir():
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                elif not os.path.exists(dst):
                    shutil.copy2(src, dst)
        except OSError as e:
            print(f"迁移旧版配置目录失败: {e}")

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
                    loaded_config.pop("analytics", None)
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
            "go_pet": {
                "enabled": False,
                "display_mode": "game",
                "size": 200,
                "offset_x": 50,
                "offset_y": 50,
                "events": []
            },
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
            selections = {"bg": True, "video": True, "sound": True, "font": True, "visual": True, "gsi": True, "go_pet": True}
            
        export_data = copy.deepcopy(self.config)
        included_resources = []
        
        try:
            with zipfile.ZipFile(export_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                file_map = {} # path -> relative_name
                
                # 剔除纯本地偏好设置（保留 theme，剔除 auto_start 和 close_behavior 等）
                local_keys = ['auto_start', 'close_behavior', 'hide_close_prompt', 'steam_path', 'gsi_port', 'gsi_sound_presets']
                for key in local_keys:
                    export_data.pop(key, None)
                
                def _add_path(abs_path, category):
                    if not abs_path or not os.path.exists(abs_path):
                        return ""
                    if abs_path in file_map:
                        return file_map[abs_path]

                    basename = os.path.basename(abs_path.rstrip("\\/")) or category
                    if os.path.isdir(abs_path):
                        rel_dir = f"resources/{category}/{basename}"
                        wrote_file = False
                        for root, _, files in os.walk(abs_path):
                            for file_name in files:
                                source = os.path.join(root, file_name)
                                relative_sub_path = os.path.relpath(source, abs_path).replace("\\", "/")
                                zipf.write(source, f"{rel_dir}/{relative_sub_path}")
                                wrote_file = True
                        if not wrote_file:
                            zipf.writestr(f"{rel_dir}/.keep", "")
                        file_map[abs_path] = rel_dir
                        return rel_dir

                    rel_name = f"resources/{category}/{basename}"
                    zipf.write(abs_path, rel_name)
                    file_map[abs_path] = rel_name
                    return rel_name
                    
                # 1. video_presets
                if selections.get("video"):
                    included_resources.append("开屏动画预设及配置")
                    for p in export_data.get("video_presets", []):
                        p["video_path"] = _add_path(p.get("video_path"), "video")
                        p["thumbnail_path"] = _add_path(p.get("thumbnail_path"), "thumb")
                    if export_data.get("current_video_path"):
                        export_data["current_video_path"] = _add_path(export_data.get("current_video_path"), "video")
                else:
                    export_data.pop("video_presets", None)
                    export_data.pop("current_video", None)
                    export_data.pop("current_video_path", None)
                    
                # 2. sound_presets
                if selections.get("sound"):
                    included_resources.append("启动音效预设及配置")
                    for p in export_data.get("sound_presets", []):
                        p["sound_path"] = _add_path(p.get("sound_path"), "sound")
                    if export_data.get("current_sound_path"):
                        export_data["current_sound_path"] = _add_path(export_data.get("current_sound_path"), "sound")
                else:
                    export_data.pop("sound_presets", None)
                    export_data.pop("current_sound", None)
                    export_data.pop("current_sound_path", None)
                    
                # 3. font_presets
                if selections.get("font"):
                    included_resources.append("全局字体预设及配置")
                    for p in export_data.get("font_presets", []):
                        p["font_path"] = _add_path(p.get("font_path"), "font")
                    if export_data.get("current_font_path"):
                        export_data["current_font_path"] = _add_path(export_data.get("current_font_path"), "font")
                else:
                    export_data.pop("font_presets", None)
                    export_data.pop("current_font", None)
                    export_data.pop("current_font_path", None)
                    
                # 4. gsi_events
                if selections.get("gsi"):
                    included_resources.append("游戏内实时音效配置")
                    for e in export_data.get("gsi_events", []):
                        e["sound"] = _add_path(e.get("sound"), "gsi")
                        if "sounds_1_5" in e:
                            for s in e["sounds_1_5"]:
                                s["path"] = _add_path(s.get("path"), "gsi")
                else:
                    export_data.pop("gsi_events", None)
                            
                # 5. visual
                if selections.get("visual"):
                    included_resources.append("游戏内视觉效果配置")
                    visual = export_data.get("visual", {})
                    if "flash_path" in visual:
                        visual["flash_path"] = _add_path(visual.get("flash_path"), "flash")
                    if "death_media_path" in visual:
                        visual["death_media_path"] = _add_path(visual.get("death_media_path"), "death")
                    if "kill_icon_path" in visual:
                        visual["kill_icon_path"] = _add_path(visual.get("kill_icon_path"), "kill_icon")
                    if "kill_icons_1_5" in visual:
                        for k in visual["kill_icons_1_5"]:
                            k["path"] = _add_path(k.get("path"), "kill_icon")
                    export_data["visual"] = visual
                else:
                    export_data.pop("visual", None)

                # 6. go_pet
                if selections.get("go_pet"):
                    included_resources.append("GO桌宠配置与资源")
                    go_pet = dict(export_data.get("go_pet", {}))
                    go_pet.pop("offset_x", None)
                    go_pet.pop("offset_y", None)
                    events = go_pet.get("events", [])
                    if isinstance(events, list):
                        for event in events:
                            if not isinstance(event, dict):
                                continue
                            event["image"] = _add_path(event.get("image"), "go_pet/image")
                            event["sound"] = _add_path(event.get("sound"), "go_pet/sound")
                    export_data["go_pet"] = go_pet
                else:
                    export_data.pop("go_pet", None)
                
                # 7. bg_path
                if selections.get("bg"):
                    if export_data.get("bg_path"):
                        included_resources.append("自定义软件背景")
                        export_data["bg_path"] = _add_path(export_data.get("bg_path"), "bg")
                else:
                    export_data.pop("bg_path", None)
                    
                # 8. current selected items validation
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

            # 6. go_pet
            go_pet_defaults = {
                "enabled": False,
                "display_mode": "game",
                "size": 200,
                "offset_x": 50,
                "offset_y": 50,
                "events": []
            }
            go_pet = imported_config.get("go_pet")
            if isinstance(go_pet, dict):
                normalized_go_pet = dict(go_pet_defaults)
                go_pet.pop("streamer_mode", None)
                normalized_go_pet.update(go_pet)
                events = go_pet.get("events", [])
                if isinstance(events, list):
                    for event in events:
                        if not isinstance(event, dict):
                            continue
                        event["image"] = _resolve_path(event.get("image"))
                        event["sound"] = _resolve_path(event.get("sound"))
                    normalized_go_pet["events"] = events
                imported_config["go_pet"] = normalized_go_pet
            else:
                imported_config["go_pet"] = dict(go_pet_defaults)
                
            # 7. bg_path
            if imported_config.get("bg_path"):
                imported_config["bg_path"] = _resolve_path(imported_config.get("bg_path"))
                
            # 过滤掉不应被覆盖的纯本地设置
            local_keys_to_protect = ['auto_start', 'close_behavior', 'hide_close_prompt', 'steam_path', 'gsi_port', 'gsi_sound_presets']
            for key in local_keys_to_protect:
                imported_config.pop(key, None)
                
            # Update config
            for key in imported_config:
                self.config[key] = imported_config[key]
                
            self.save_config()
            return True, "导入成功"
        except Exception as e:
            return False, f"导入失败: {str(e)}"
