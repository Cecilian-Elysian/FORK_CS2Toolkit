# 字体替换功能模块
# 处理字体文件的复制和配置文件的生成

import os
import shutil
from .font_config import FontConfigManager
from .steam_utils import SteamUtils


class FontReplacer:
    # 字体替换器

    def __init__(self, steam_library_path):
        self.steam_library_path = steam_library_path
        self.config_manager = FontConfigManager()

    def validate_paths(self, font_path):
        # 验证路径有效性

        if not os.path.isdir(self.steam_library_path):
            raise ValueError("Steam库路径无效！")

        # 直接构建CS2路径
        cs2_game_path = os.path.join(self.steam_library_path, "steamapps", "common", "Counter-Strike Global Offensive")
        if not os.path.exists(cs2_game_path):
            raise ValueError("CS2安装路径不存在！请检查CS2是否已安装。")

        cs2_game_dir = os.path.join(cs2_game_path, "game")
        if not os.path.exists(cs2_game_dir):
            raise ValueError("CS2游戏文件不完整！")

        if not font_path or not os.path.isfile(font_path):
            raise ValueError("请选择有效的字体文件！")

        if not font_path.lower().endswith('.ttf'):
            raise ValueError("只支持TTF格式的字体文件！")

        return True

    def get_fonts_directory(self):
        # 获取fonts目录路径
        cs2_path = os.path.join(self.steam_library_path, "steamapps", "common", "Counter-Strike Global Offensive")
        if not os.path.exists(cs2_path):
            return None
        return os.path.join(cs2_path, "game", "csgo", "panorama", "fonts")

    def get_global_conf_path(self):
        # 获取全局配置文件路径
        cs2_path = os.path.join(self.steam_library_path, "steamapps", "common", "Counter-Strike Global Offensive")
        if not os.path.exists(cs2_path):
            return None
        return os.path.join(cs2_path, "game", "core", "panorama", "fonts", "conf.d", "42-repl-global.conf")

    def clear_fonts_directory(self, fonts_dir):
        # 清空fonts目录
        try:
            if os.path.exists(fonts_dir):
                for filename in os.listdir(fonts_dir):
                    file_path = os.path.join(fonts_dir, filename)
                    if os.path.isfile(file_path):
                        os.remove(file_path)
            else:

                os.makedirs(fonts_dir, exist_ok=True)
        except Exception as e:
            raise Exception(f"清空fonts目录失败: {str(e)}")

    def copy_font_file(self, src_path, dest_dir):
        # 复制字体文件到目标目录
        try:
            filename = os.path.basename(src_path)
            dest_path = os.path.join(dest_dir, filename)
            shutil.copy2(src_path, dest_path)
            return filename
        except Exception as e:
            raise Exception(f"复制字体文件失败: {str(e)}")

    def create_fonts_conf(self, fonts_dir, font_name, font_filename):
        # 生成fonts.conf文件
        try:
            conf_content = self.config_manager.generate_fonts_conf(font_name, font_filename)
            conf_path = os.path.join(fonts_dir, "fonts.conf")
            os.makedirs(fonts_dir, exist_ok=True)
            with open(conf_path, 'w', encoding='utf-8') as f:
                f.write(conf_content)
        except Exception as e:
            raise Exception(f"创建fonts.conf文件失败: {str(e)}")

    def update_global_conf(self, conf_path, font_name):
        # 更新42-repl-global.conf文件
        try:
            conf_content = self.config_manager.generate_global_conf(font_name)
            os.makedirs(os.path.dirname(conf_path), exist_ok=True)
            with open(conf_path, 'w', encoding='utf-8') as f:
                f.write(conf_content)
        except Exception as e:
            raise Exception(f"更新42-repl-global.conf文件失败: {str(e)}")

    def is_font_replacement_intact(self, font_path):
        if not font_path or not os.path.isfile(font_path):
            return False

        fonts_dir = self.get_fonts_directory()
        global_conf_path = self.get_global_conf_path()
        if not fonts_dir or not global_conf_path:
            return False

        font_filename = os.path.basename(font_path)
        expected_font_path = os.path.join(fonts_dir, font_filename)
        fonts_conf_path = os.path.join(fonts_dir, "fonts.conf")

        return (
            os.path.isfile(expected_font_path)
            and os.path.isfile(fonts_conf_path)
            and os.path.isfile(global_conf_path)
        )

    def ensure_font_replaced(self, font_path, progress_callback=None):
        if self.is_font_replacement_intact(font_path):
            return {"success": True, "repaired": False}

        result = self.replace_font(font_path, progress_callback)
        if result.get("success"):
            result["repaired"] = True
        return result

    def restore_font(self):
        try:
            fonts_dir = self.get_fonts_directory()
            if fonts_dir and os.path.exists(fonts_dir):
                self.clear_fonts_directory(fonts_dir)

            global_conf_path = self.get_global_conf_path()
            if global_conf_path and os.path.exists(global_conf_path):
                os.remove(global_conf_path)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def extract_font_name(self, font_path):
        # 尝试从 TTF 文件中提取真实的字体 Family Name
        # 如果提取失败，则回退到使用文件名
        try:
            with open(font_path, 'rb') as f:
                f.seek(4)
                num_tables = int.from_bytes(f.read(2), 'big')
                f.seek(12)
                for _ in range(num_tables):
                    tag = f.read(4)
                    _checksum = f.read(4)
                    offset = int.from_bytes(f.read(4), 'big')
                    _length = int.from_bytes(f.read(4), 'big')
                    if tag == b'name':
                        f.seek(offset)
                        _format = int.from_bytes(f.read(2), 'big')
                        num_records = int.from_bytes(f.read(2), 'big')
                        string_offset = int.from_bytes(f.read(2), 'big')

                        font_names = {}
                        for _ in range(num_records):
                            platform_id = int.from_bytes(f.read(2), 'big')
                            encoding_id = int.from_bytes(f.read(2), 'big')
                            _lang_id = int.from_bytes(f.read(2), 'big')
                            name_id = int.from_bytes(f.read(2), 'big')
                            length = int.from_bytes(f.read(2), 'big')
                            record_offset = int.from_bytes(f.read(2), 'big')

                            if name_id == 1: # 1: Font Family Name
                                pos = f.tell()
                                f.seek(offset + string_offset + record_offset)
                                name_bytes = f.read(length)
                                if platform_id == 3 and encoding_id in (0, 1): # Windows
                                    font_names['win'] = name_bytes.decode('utf-16-be', errors='ignore')
                                elif platform_id == 1 and encoding_id == 0: # Mac
                                    font_names['mac'] = name_bytes.decode('mac_roman', errors='ignore')
                                f.seek(pos)

                        if 'win' in font_names:
                            return font_names['win']
                        elif 'mac' in font_names:
                            return font_names['mac']
                        break
        except Exception as e:
            print(f"解析TTF字体名称失败: {e}")

        # 回退到使用文件名
        filename = os.path.basename(font_path)
        return os.path.splitext(filename)[0]

    def replace_font(self, font_path, progress_callback=None):
        # 执行字体替换
        # 验证路径
        self.validate_paths(font_path)

        font_name = self.extract_font_name(font_path)
        font_filename = os.path.basename(font_path)

        # 定义路径
        fonts_dir = self.get_fonts_directory()
        global_conf_path = self.get_global_conf_path()

        try:
            # 步骤1: 清空fonts目录
            if progress_callback:
                progress_callback("清空fonts目录...")
            self.clear_fonts_directory(fonts_dir)

            # 步骤2: 复制字体文件
            if progress_callback:
                progress_callback("复制字体文件...")
            self.copy_font_file(font_path, fonts_dir)

            # 步骤3: 创建fonts.conf文件
            if progress_callback:
                progress_callback("创建fonts.conf文件...")
            self.create_fonts_conf(fonts_dir, font_name, font_filename)

            # 步骤4: 更新42-repl-global.conf文件
            if progress_callback:
                progress_callback("更新全局配置文件...")
            self.update_global_conf(global_conf_path, font_name)

            if progress_callback:
                progress_callback("字体替换完成！")

            return {
                "success": True,
                "font_name": font_name,
                "font_filename": font_filename
            }

        except Exception as e:
            if progress_callback:
                progress_callback("操作失败")
            return {
                "success": False,
                "error": str(e)
            }
