"""Виджет ввода команды с кнопкой Разобрать."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel


class CommandInput(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        hint = QLabel(
            'Команду запуска можно получить, если отправить System Log(JSON) '
            'боту в Telegram <a href="https://t.me/kinpro_bot">@kinpro_bot</a>'
        )
        hint.setWordWrap(True)
        hint.setOpenExternalLinks(True)
        hint.setStyleSheet("color: gray; font-size: 11px; margin-bottom: 4px;")
        layout.addWidget(hint)

        label = QLabel("Команда:")
        layout.addWidget(label)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Вставьте команду N_m3u8DL-RE сюда...")
        self.text_edit.setMaximumHeight(100)
        layout.addWidget(self.text_edit)

        btn_layout = QHBoxLayout()
        self.parse_btn = QPushButton("Разобрать команду")
        btn_layout.addWidget(self.parse_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def get_text(self) -> str:
        return self.text_edit.toPlainText().strip()

    def set_text(self, text: str):
        self.text_edit.setPlainText(text)
