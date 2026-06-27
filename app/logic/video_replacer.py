# 视频替换功能模块
# 处理开屏动画视频文件的替换

import os
import shutil
from .steam_utils import SteamUtils


class VideoReplacer:
    # 视频替换器
    
    def __init__(self, steam_library_path):
        self.steam_library_path = steam_library_path
    
    def validate_paths(self, video_path):
        # 验证路径有效性
        
        if not os.path.isdir(self.steam_library_path):
            raise ValueError("Steam库路径无效！")
        
        # 直接构建CS2路径
        cs2_path = os.path.join(self.steam_library_path, "steamapps", "common", "Counter-Strike Global Offensive")
        if not os.path.exists(cs2_path):
            raise ValueError("CS2安装路径不存在！请检查CS2是否已安装。")
        
        target_dir = os.path.join(cs2_path, "game", "csgo", "panorama", "videos")
        if not os.path.exists(target_dir):
            raise ValueError("CS2视频文件夹不存在！")
        
        if not video_path or not os.path.isfile(video_path):
            raise ValueError("请选择有效的视频文件！")
        
        if not video_path.lower().endswith('.webm'):
            raise ValueError("只支持WEBM格式的视频文件！")
        
        return True
    
    def get_target_directory(self):
        # 获取目标视频目录
        cs2_path = os.path.join(self.steam_library_path, "steamapps", "common", "Counter-Strike Global Offensive")
        if not os.path.exists(cs2_path):
            return None
        return os.path.join(cs2_path, "game", "csgo", "panorama", "videos")
    
    def get_target_filenames(self, version_type):
        # 根据版本类型获取目标文件名列表
        if version_type == "intl":
            return [
                "intro.webm",
                "intro720p.webm"
            ]
        elif version_type == "cn":
            return [
                "intro-perfectworld.webm",
                "intro-perfectworld720p.webm"
            ]
        else:
            return [
                "intro.webm",
                "intro720p.webm",
                "intro-perfectworld.webm",
                "intro-perfectworld720p.webm"
            ]
    
    def replace_video(self, video_path, version_type="both", progress_callback=None):
        # 执行视频替换
        
        self.validate_paths(video_path)
        
        target_dir = self.get_target_directory()
        filenames = self.get_target_filenames(version_type)
        
        try:
            if progress_callback:
                progress_callback("开始替换视频文件...")
            
            
            for i, filename in enumerate(filenames):
                if progress_callback:
                    progress_callback(f"正在替换 {filename}... ({i+1}/{len(filenames)})")
                
                dest = os.path.join(target_dir, filename)
                shutil.copy2(video_path, dest)
            
            if progress_callback:
                progress_callback("视频替换完成！")
            
            return {
                "success": True,
                "replaced_count": len(filenames),
                "filenames": filenames
            }
            
        except Exception as e:
            if progress_callback:
                progress_callback("操作失败")
            return {
                "success": False,
                "error": str(e)
            }
            
    def restore_video(self):
        try:
            target_dir = self.get_target_directory()
            if not target_dir:
                return {"success": False, "error": "无法获取视频目录"}
            filenames = self.get_target_filenames("both")
            for filename in filenames:
                dest = os.path.join(target_dir, filename)
                if os.path.exists(dest):
                    os.remove(dest)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_version_display_name(self, version_type):
        # 获取版本类型的显示名称
        version_names = {
            "intl": "国际服",
            "cn": "国服",
            "both": "国际服和国服"
        }
        return version_names.get(version_type, "未知版本")