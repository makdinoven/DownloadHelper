"""Read-only log output panel."""

from PyQt6.QtWidgets import QPlainTextEdit
from PyQt6.QtGui import QFont


class LogPanel(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 9))
        self.setMaximumBlockCount(5000)

    def append_text(self, text: str):
        self.moveCursor(self.textCursor().MoveOperation.End)
        self.insertPlainText(text)
        self.moveCursor(self.textCursor().MoveOperation.End)
