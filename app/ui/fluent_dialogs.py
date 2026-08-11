from qfluentwidgets import BodyLabel, LineEdit, MessageBoxBase, SubtitleLabel


class TextInputDialog(MessageBoxBase):
    def __init__(self, title, content, default_text="", parent=None):
        super().__init__(parent)

        self.titleLabel = SubtitleLabel(title, self)
        self.viewLayout.addWidget(self.titleLabel)

        if content:
            self.contentLabel = BodyLabel(content, self)
            self.contentLabel.setWordWrap(True)
            self.viewLayout.addWidget(self.contentLabel)

        self.lineEdit = LineEdit(self)
        self.lineEdit.setText(default_text)
        self.lineEdit.selectAll()
        self.lineEdit.textChanged.connect(self._validate)
        self.viewLayout.addWidget(self.lineEdit)

        self.widget.setMinimumWidth(360)
        self.yesButton.setText("确定")
        self.cancelButton.setText("取消")
        self._validate()

    def _validate(self):
        self.yesButton.setEnabled(bool(self.lineEdit.text().strip()))

    def get_text(self):
        return self.lineEdit.text().strip()
