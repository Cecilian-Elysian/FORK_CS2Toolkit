from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from qfluentwidgets import TitleLabel, BodyLabel, PushButton


class AboutPage(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 20, 30, 30)
        layout.setSpacing(10)
        
        layout.addWidget(TitleLabel("关于 CS2 工具箱"), 0, Qt.AlignTop)
        
        about_text = BodyLabel()
        about_text.setWordWrap(True)
        about_text.setText("""
这是一个为CS2(Counter-Strike 2)设计的多功能软件，可自定义开屏动画、音效、游戏字体与实时播放音效，其他功能还在积极开发中，敬请期待！(｡･ω･｡)<br><br>
<b>版本: {version}</b><br>
作者: Clover_233<br>
作者主页: <a href="https://cloverz.top">https://cloverz.top</a><br>
""".format(version=self.parent.version))
        about_text.setOpenExternalLinks(True)
        layout.addWidget(about_text, 0, Qt.AlignTop)
        
        self.check_update_btn = PushButton("检查更新")
        layout.addWidget(self.check_update_btn, 0, Qt.AlignTop)

        layout.addStretch()
        self._connect_signals()
        
    def _connect_signals(self):
        self.check_update_btn.clicked.connect(self.parent.check_for_updates)