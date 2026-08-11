from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from qfluentwidgets import SegmentedWidget, TitleLabel

from .video_page import VideoPage
from .sound_page import SoundPage
from .font_page import FontPage

class CustomizePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.parent_window = parent
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(15)

        layout.addWidget(TitleLabel("个性化"))

        self.pivot = SegmentedWidget(self)
        self.stacked_widget = QStackedWidget(self)

        self.video_page = VideoPage(self.parent_window)
        self.sound_page = SoundPage(self.parent_window)
        self.font_page = FontPage(self.parent_window)

        # Remove titles from child pages to avoid duplicate titles
        # Since we use TitleLabel, we can just hide the first widget if it is a TitleLabel
        for page in [self.video_page, self.sound_page, self.font_page]:
            child_layout = page.layout()
            if child_layout and child_layout.count() > 0:
                first_item = child_layout.itemAt(0).widget()
                if isinstance(first_item, TitleLabel):
                    first_item.hide()

        self.addSubInterface(self.video_page, 'videoInterface', '开屏动画')
        self.addSubInterface(self.sound_page, 'soundInterface', '启动音效')
        self.addSubInterface(self.font_page, 'fontInterface', '全局字体')

        layout.addWidget(self.pivot)
        layout.addWidget(self.stacked_widget)

        self.pivot.setCurrentItem('videoInterface')
        self.stacked_widget.setCurrentIndex(0)

        # Connect pivot changes to stacked widget
        self.pivot.currentItemChanged.connect(
            lambda k: self.stacked_widget.setCurrentWidget(self.findChild(QWidget, k))
        )

    def addSubInterface(self, widget, objectName, text):
        widget.setObjectName(objectName)
        self.stacked_widget.addWidget(widget)
        self.pivot.addItem(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stacked_widget.setCurrentWidget(widget)
        )
