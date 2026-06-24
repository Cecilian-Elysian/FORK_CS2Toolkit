import sys
from PySide6.QtWidgets import QApplication

try:
    from ctypes import windll
    myappid = 'clover.cs2.toolkit'
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    from app.main_window import CS2Tool
    window = CS2Tool()
    window.show()
    sys.exit(app.exec())