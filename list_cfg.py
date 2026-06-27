import os
import sys
sys.path.insert(0, r"c:\Users\Clove\Desktop\壹点灵 - 副本 - 副本 - 副本\CS2Toolkit")
from app.logic.steam_utils import SteamUtils

def list_cfg():
    cs2_path = SteamUtils.find_cs2_install_path()
    cfg_dir = os.path.join(cs2_path, "game", "csgo", "cfg")
    print(f"Listing {cfg_dir}:")
    for f in os.listdir(cfg_dir):
        if f.endswith(".cfg"):
            print(f)
            
    autoexec_path = os.path.join(cfg_dir, "autoexec.cfg")
    if os.path.exists(autoexec_path):
        print("\n--- autoexec.cfg ---")
        with open(autoexec_path, "r", encoding="utf-8") as f:
            print(f.read())
            
list_cfg()