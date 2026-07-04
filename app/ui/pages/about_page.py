import os
import sys

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from qfluentwidgets import TitleLabel, BodyLabel, PushButton, MessageBoxBase, SubtitleLabel


class SponsorshipDialog(MessageBoxBase):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)

        self.titleLabel = SubtitleLabel("赞赏支持", self)
        self.viewLayout.addWidget(self.titleLabel)

        self.textLabel = BodyLabel(
            "如果这个项目对你有帮助，欢迎自愿赞赏支持后续维护。\n"
            "赞赏仅代表对作者的支持，不对应任何功能、授权、更新承诺或专属服务。",
            self
        )
        self.textLabel.setWordWrap(True)
        self.viewLayout.addWidget(self.textLabel)

        self.imageLabel = QLabel(self)
        self.imageLabel.setAlignment(Qt.AlignCenter)
        self.viewLayout.addWidget(self.imageLabel)

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            self.imageLabel.setText("未能加载赞赏码图片，请检查 sponsorship.jpg 是否存在。")
        else:
            self.imageLabel.setPixmap(
                pixmap.scaled(320, 320, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )

        self.widget.setMinimumWidth(380)
        self.yesButton.setText("关闭")
        self.cancelButton.hide()


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
这是一个为CS2设计的多功能软件，可自定义开屏动画、音效、游戏字体与实时播放音效，其他功能还在积极开发中，敬请期待！(｡･ω･｡)<br><br>
<b>版本: {version}</b><br>
作者: Moon4Quartz<br>
作者主页: <a href="https://space.bilibili.com/3537124972300357">https://space.bilibili.com/3537124972300357</a><br>
开源地址: <a href="{repo_url}">{repo_url}</a><br>
许可证: GPLv3<br>
免责: 本项目按现状提供，不附带任何担保<br>
声明: 本项目与 Valve 无关联，相关商标归其各自权利人所有<br>
""".format(version=self.parent.version, repo_url=self.parent.repo_url))
        about_text.setOpenExternalLinks(True)
        layout.addWidget(about_text, 0, Qt.AlignTop)
        
        self.check_update_btn = PushButton("检查更新")
        layout.addWidget(self.check_update_btn, 0, Qt.AlignTop)

        self.sponsorship_btn = None
        if os.path.isfile(self._get_sponsorship_image_path()):
            self.sponsorship_btn = PushButton("赞赏支持")
            layout.addWidget(self.sponsorship_btn, 0, Qt.AlignTop)

        layout.addStretch()
        self._connect_signals()

    def _get_sponsorship_image_path(self):
        return os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "sponsorship.jpg")

    def _show_sponsorship_dialog(self):
        dialog = SponsorshipDialog(self._get_sponsorship_image_path(), self)
        dialog.exec()

    def _connect_signals(self):
        self.check_update_btn.clicked.connect(self.parent.check_for_updates)
        if self.sponsorship_btn is not None:
            self.sponsorship_btn.clicked.connect(self._show_sponsorship_dialog)
