# Steam工具模块
# 处理Steam路径检测和相关功能

import os
import winreg
import re


class SteamUtils:
    # Steam工具类
    
    @staticmethod
    def auto_detect_steam_path():
        # 自动检测Steam安装路径
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
            path, _ = winreg.QueryValueEx(key, "SteamPath")
            steam_path = path.replace("/", "\\")
            winreg.CloseKey(key)
            if os.path.isdir(steam_path):
                return steam_path
        except (FileNotFoundError, OSError, winreg.error):
            pass
        
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam")
            path, _ = winreg.QueryValueEx(key, "InstallPath")
            steam_path = path.replace("/", "\\")
            winreg.CloseKey(key)
            if os.path.isdir(steam_path):
                return steam_path
        except (FileNotFoundError, OSError, winreg.error):
            pass
        
        default_paths = [
            r"C:\Program Files (x86)\Steam",
            r"C:\Program Files\Steam",
            r"D:\Steam",
            r"E:\Steam"
        ]
        
        for path in default_paths:
            if os.path.isdir(path):
                return path
        
        return None
    
    @staticmethod
    def get_steam_library_folders(steam_path):
        # 获取Steam所有库文件夹路径
        library_folders = []
        if steam_path and os.path.isdir(steam_path):
            library_folders.append(steam_path)
        
        vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
        if not os.path.exists(vdf_path):
            return library_folders
        
        try:
            with open(vdf_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            path_pattern = r'"path"\s*"([^"]+)"'
            matches = re.findall(path_pattern, content)
            
            for match in matches:
                path = match.replace('\\\\', '\\').replace('/', '\\')
                if os.path.isdir(path) and path not in library_folders:
                    library_folders.append(path)
        except Exception as e:
            print(f"读取libraryfolders.vdf失败: {e}")
        
        return library_folders
    
    @staticmethod
    def find_cs2_in_libraries(steam_path):
        # 在所有Steam库中查找CS2安装路径
        library_folders = SteamUtils.get_steam_library_folders(steam_path)
        for library_path in library_folders:
            cs2_path = os.path.join(library_path, "steamapps\\common\\Counter-Strike Global Offensive")
            if os.path.exists(cs2_path):
                return cs2_path
        return None
    
    @staticmethod
    def validate_steam_path(steam_path):
        # 验证Steam路径是否有效
        if not steam_path or not os.path.isdir(steam_path):
            return False
        steam_exe = os.path.join(steam_path, "Steam.exe")
        if not os.path.exists(steam_exe):
            return False
        return True
    
    @staticmethod
    def get_cs2_path(steam_path):
        # 获取CS2游戏路径
        if not SteamUtils.validate_steam_path(steam_path):
            return None
        cs2_path = os.path.join(steam_path, "steamapps\\common\\Counter-Strike Global Offensive")
        if os.path.exists(cs2_path):
            return cs2_path
        return SteamUtils.find_cs2_in_libraries(steam_path)
    
    @staticmethod
    def get_cs2_video_path(steam_path):
        # 获取CS2视频文件路径
        cs2_path = SteamUtils.get_cs2_path(steam_path)
        if not cs2_path:
            return None
        video_path = os.path.join(cs2_path, "game\\csgo\\panorama\\videos")
        if os.path.exists(video_path):
            return video_path
        return None
    
    @staticmethod
    def get_cs2_font_path(steam_path):
        # 获取CS2字体文件路径
        cs2_path = SteamUtils.get_cs2_path(steam_path)
        if not cs2_path:
            return None
        font_path = os.path.join(cs2_path, "game\\csgo\\panorama\\fonts")
        return font_path
    
    @staticmethod
    def get_cs2_font_config_path(steam_path):
        # 获取CS2字体配置文件路径
        cs2_path = SteamUtils.get_cs2_path(steam_path)
        if not cs2_path:
            return None
        config_path = os.path.join(cs2_path, "game\\core\\panorama\\fonts\\conf.d\\42-repl-global.conf")
        return config_path
    
    @staticmethod
    def validate_cs2_installation(steam_path):
        # 验证CS2是否正确安装
        cs2_path = SteamUtils.get_cs2_path(steam_path)
        if not cs2_path:
            return False, "CS2未安装或路径不正确"
        game_exe = os.path.join(cs2_path, "game\\bin\\win64\\cs2.exe")
        if not os.path.exists(game_exe):
            return False, "CS2游戏文件不完整"
        return True, "CS2安装正常"

    @staticmethod
    def find_steam_userdata_folders():
        # 查找所有Steam userdata文件夹
        steam_path = SteamUtils.auto_detect_steam_path()
        if not steam_path:
            return []
        
        userdata_path = os.path.join(steam_path, "userdata")
        if not os.path.isdir(userdata_path):
            return []
        
        user_folders = []
        for item in os.listdir(userdata_path):
            full_path = os.path.join(userdata_path, item)
            # 用户文件夹是数字格式的 (好友代码)
            if os.path.isdir(full_path) and item.isdigit():
                cs2_cfg_path = os.path.join(full_path, "730", "local", "cfg")
                if os.path.isdir(cs2_cfg_path):
                    user_folders.append(full_path)
        
        return user_folders

    @staticmethod
    def find_cs2_install_path():
        # 一个便捷函数，用于自动检测并返回CS2的完整路径。
        steam_path = SteamUtils.auto_detect_steam_path()
        if steam_path:
            return SteamUtils.get_cs2_path(steam_path)
        return None

    @staticmethod
    def extract_steam_library_from_cs2_path(cs2_path):
        # 从CS2完整路径中提取Steam库路径
        if not cs2_path:
            return None
        normalized_path = cs2_path.replace('/', '\\')
        cs2_folder_patterns = [
            "\\steamapps\\common\\Counter-Strike Global Offensive",
            "\\steamapps\\common\\Counter-Strike Global Offensive\\",
            "\\SteamApps\\common\\Counter-Strike Global Offensive",
            "\\SteamApps\\common\\Counter-Strike Global Offensive\\",
        ]
        for pattern in cs2_folder_patterns:
            if pattern in normalized_path:
                library_path = normalized_path.replace(pattern, "")
                library_path = library_path.rstrip('\\')
                return library_path
        parts = normalized_path.split('\\')
        if len(parts) >= 4 and parts[-1] == "Counter-Strike Global Offensive" and parts[-2] == "common" and parts[-3] == "steamapps":
            library_parts = parts[:-3]
            library_path = '\\'.join(library_parts)
            return library_path
        return None


class PathValidator:
    # 路径验证器
    
    @staticmethod
    def validate_video_file(file_path):
        # 验证视频文件
        if not file_path or not os.path.isfile(file_path):
            return False, "请选择有效的视频文件"
        if not file_path.lower().endswith('.webm'):
            return False, "只支持WEBM格式的视频文件"
        return True, "视频文件有效"
    
    @staticmethod
    def validate_font_file(file_path):
        # 验证字体文件
        if not file_path or not os.path.isfile(file_path):
            return False, "请选择有效的字体文件"
        if not file_path.lower().endswith('.ttf'):
            return False, "只支持TTF格式的字体文件"
        return True, "字体文件有效"
    
    @staticmethod
    def validate_directory(dir_path, description="目录"):
        # 验证目录
        if not dir_path or not os.path.isdir(dir_path):
            return False, f"{description}路径无效"
        return True, f"{description}路径有效"