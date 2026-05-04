"""Редактор имени файла с кнопкой Нормализовать."""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton


class FileNameEdit(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel("Имя файла:"))
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("Имя файла (без расширения)")
        layout.addWidget(self.line_edit, 1)

        self.normalize_btn = QPushButton("Нормализовать")
        layout.addWidget(self.normalize_btn)

    def get_name(self) -> str:
        return self.line_edit.text().strip()

    def set_name(self, name: str):
        self.line_edit.setText(name)
