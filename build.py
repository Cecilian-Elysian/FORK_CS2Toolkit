# build.py 构建脚本
import subprocess
import sys

def build_exe():
    entry_file = "main.py"
    
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--onefile",
        "--windows-console-mode=disable",
        "--enable-plugin=pyside6",
        "--include-package=PySide6.QtMultimedia",
        "--include-qt-plugins=multimedia",
        "--include-qt-plugins=platforms",
        "--assume-yes-for-downloads",
        "--output-dir=dist",
        "--noinclude-qt-translations",
        "--windows-icon-from-ico=app_icon.ico",

        "--mingw64",
        "--onefile-no-compression",
        "--enable-plugin=upx",
        "--nofollow-import-to=cv2",
        "--nofollow-import-to=tkinter",
        "--nofollow-import-to=idlelib",
        "--nofollow-import-to=pkg_resources",
        entry_file
    ]

    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    build_exe()