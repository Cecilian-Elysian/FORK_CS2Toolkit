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
            with open(conf_path, 'w', encoding='utf-8') as f:
                f.write(conf_content)
        except Exception as e:
            raise Exception(f"创建fonts.conf文件失败: {str(e)}")
    
    def update_global_conf(self, conf_path, font_name):
        # 更新42-repl-global.conf文件
        try:
            conf_content = self.config_manager.generate_global_conf(font_name)
            with open(conf_path, 'w', encoding='utf-8') as f:
                f.write(conf_content)
        except Exception as e:
            raise Exception(f"更新42-repl-global.conf文件失败: {str(e)}")
    
    def extract_font_name(self, font_path):
        # 从字体文件路径提取字体名称（去掉扩展名）
        filename = os.path.basename(font_path)
        font_name = os.path.splitext(filename)[0]
        return font_name
    
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