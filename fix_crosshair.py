import os
import sys

# add CS2Toolkit to sys.path so we can import SteamUtils
sys.path.insert(0, r"c:\Users\Clove\Desktop\壹点灵 - 副本 - 副本 - 副本\CS2Toolkit")
from app.logic.steam_utils import SteamUtils

def fix_crosshair():
    cs2_path = SteamUtils.find_cs2_install_path()
    if not cs2_path:
        print("未找到 CS2 路径。")
        return
        
    cfg_dir = os.path.join(cs2_path, "game", "csgo", "cfg")
    if not os.path.exists(cfg_dir):
        print(f"找不到 CFG 目录: {cfg_dir}")
        return
        
    # 1. 清理 autoexec.cfg 以及其他可能被执行的 cfg (如完美平台的 pwa_userconfig)
    for file in os.listdir(cfg_dir):
        if file.endswith(".cfg") and file != "op.cfg":
            filepath = os.path.join(cfg_dir, file)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                
                new_lines = []
                cleaned = 0
                for line in lines:
                    stripped = line.strip().lower()
                    if stripped.startswith("cl_crosshair"):
                        cleaned += 1
                        continue
                    if stripped.startswith("exec crosshair"):
                        cleaned += 1
                        continue
                    new_lines.append(line)
                    
                if cleaned > 0:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.writelines(new_lines)
                    print(f"已从 {file} 清理 {cleaned} 行准星配置。")
            except Exception as e:
                print(f"处理 {file} 失败: {e}")
            
    # 2. 删除可能存在的 crosshair.cfg
    for file in os.listdir(cfg_dir):
        if file.startswith("crosshair") and file.endswith(".cfg"):
            file_path = os.path.join(cfg_dir, file)
            try:
                os.remove(file_path)
                print(f"已删除残留文件: {file}")
            except Exception as e:
                print(f"删除 {file} 失败: {e}")

if __name__ == "__main__":
    fix_crosshair()