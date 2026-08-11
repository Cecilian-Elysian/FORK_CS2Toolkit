from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
from qfluentwidgets import SegmentedWidget, TitleLabel


class GameEnhancementPage(QWidget):
    def __init__(self, sound_page, visual_page, parent=None):
        super().__init__(parent=parent)
        self.parent_window = parent
        self.sound_page = sound_page
        self.visual_page = visual_page
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 20)
        layout.setSpacing(15)

        layout.addWidget(TitleLabel("游戏增强"))

        self.pivot = SegmentedWidget(self)
        self.stacked_widget = QStackedWidget(self)

        self.add_sub_interface(self.sound_page, "soundEnhancementInterface", "游戏内音效设置")
        self.add_sub_interface(self.visual_page, "visualEnhancementInterface", "游戏内视觉设置")

        layout.addWidget(self.pivot)
        layout.addWidget(self.stacked_widget)

        self.pivot.setCurrentItem("soundEnhancementInterface")
        self.stacked_widget.setCurrentWidget(self.sound_page)

        self.pivot.currentItemChanged.connect(
            lambda key: self.stacked_widget.setCurrentWidget(self.findChild(QWidget, key))
        )

    def add_sub_interface(self, widget, object_name, text):
        widget.setObjectName(object_name)
        self.stacked_widget.addWidget(widget)
        self.pivot.addItem(
            routeKey=object_name,
            text=text,
            onClick=lambda: self.stacked_widget.setCurrentWidget(widget)
        )
