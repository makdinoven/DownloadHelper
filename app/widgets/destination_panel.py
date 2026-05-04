"""Панель выбора назначения: Локально / S3 с выбором профиля."""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QRadioButton, QLineEdit,
    QPushButton, QFileDialog, QButtonGroup, QCheckBox, QComboBox,
)


class DestinationPanel(QWidget):
    def __init__(self, default_local_path: str = "", parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._btn_group = QButtonGroup(self)

        # Локальная строка
        local_row = QHBoxLayout()
        self.local_radio = QRadioButton("Локально")
        self.local_radio.setChecked(True)
        self._btn_group.addButton(self.local_radio)
        local_row.addWidget(self.local_radio)

        self.local_path_edit = QLineEdit(default_local_path)
        self.local_path_edit.setPlaceholderText("/путь/к/директории")
        local_row.addWidget(self.local_path_edit, 1)

        self.browse_btn = QPushButton("Обзор...")
        local_row.addWidget(self.browse_btn)
        layout.addLayout(local_row)

        # S3 строка
        s3_row = QHBoxLayout()
        self.s3_radio = QRadioButton("S3")
        self._btn_group.addButton(self.s3_radio)
        s3_row.addWidget(self.s3_radio)

        self.s3_profile_combo = QComboBox()
        self.s3_profile_combo.setMinimumWidth(140)
        self.s3_profile_combo.setEnabled(False)
        s3_row.addWidget(self.s3_profile_combo)

        self.s3_path_edit = QLineEdit()
        self.s3_path_edit.setPlaceholderText("/путь/в/бакете")
        self.s3_path_edit.setEnabled(False)
        s3_row.addWidget(self.s3_path_edit, 1)

        self.s3_settings_btn = QPushButton("Настройки")
        self.s3_settings_btn.setEnabled(False)
        s3_row.addWidget(self.s3_settings_btn)
        layout.addLayout(s3_row)

        # Чекбокс удаления локальной копии после загрузки в S3
        self.delete_local_cb = QCheckBox("Удалить локальную копию после загрузки в S3")
        self.delete_local_cb.setChecked(True)
        self.delete_local_cb.setEnabled(False)
        layout.addWidget(self.delete_local_cb)

        # Переключение состояния
        self.local_radio.toggled.connect(self._on_toggle)
        self.browse_btn.clicked.connect(self._on_browse)

    def _on_toggle(self, local_checked: bool):
        self.local_path_edit.setEnabled(local_checked)
        self.browse_btn.setEnabled(local_checked)
        self.s3_profile_combo.setEnabled(not local_checked)
        self.s3_path_edit.setEnabled(not local_checked)
        self.s3_settings_btn.setEnabled(not local_checked)
        self.delete_local_cb.setEnabled(not local_checked)

    def _on_browse(self):
        path = QFileDialog.getExistingDirectory(self, "Выберите папку для загрузки")
        if path:
            self.local_path_edit.setText(path)

    def load_s3_profiles(self, names: list[str], active: str = ""):
        """Загрузить список профилей S3 в комбо-бокс."""
        self.s3_profile_combo.clear()
        if not names:
            return
        self.s3_profile_combo.addItems(names)
        if active and active in names:
            self.s3_profile_combo.setCurrentText(active)

    def get_selected_s3_profile(self) -> str:
        return self.s3_profile_combo.currentText()

    def is_local(self) -> bool:
        return self.local_radio.isChecked()

    def should_delete_local(self) -> bool:
        return self.delete_local_cb.isChecked()

    def get_local_path(self) -> str:
        return self.local_path_edit.text().strip()

    def get_s3_path(self) -> str:
        return self.s3_path_edit.text().strip()

    def set_s3_path(self, path: str):
        self.s3_path_edit.setText(path)
