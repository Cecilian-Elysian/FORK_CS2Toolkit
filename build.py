# build.py 构建脚本
import subprocess

def build_exe():
    entry_file = "main.py"
    
    cmd = [
        "python", "-m", "nuitka",
        "--standalone",
        "--onefile",  
        "--windows-console-mode=disable", 
        "--enable-plugin=pyside6", 
        "--include-package=cv2",
        "--include-package=PySide6.QtMultimedia", 
        "--include-qt-plugins=multimedia",
        "--include-qt-plugins=platforms",
        "--assume-yes-for-downloads",
        "--output-dir=dist",         
        "--noinclude-qt-translations",
        "--enable-plugin=upx",
        "--lto=yes",
        "--windows-icon-from-ico=app_icon.ico",    
        entry_file
    ]

    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    build_exe()