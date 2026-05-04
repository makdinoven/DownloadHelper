"""Диалог управления S3 профилями."""

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout,
    QLabel, QListWidget, QMessageBox, QInputDialog, QSplitter, QWidget,
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt

from app.core.config import ConfigManager


class _S3TestWorker(QThread):
    """Проверка подключения к S3 в фоне."""
    result = pyqtSignal(bool, str)

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self._config = config

    def run(self):
        try:
            import boto3
            from botocore.config import Config as BotoConfig

            kwargs = {
                "aws_access_key_id": self._config["access_key"],
                "aws_secret_access_key": self._config["secret_key"],
            }
            if self._config.get("endpoint"):
                kwargs["endpoint_url"] = self._config["endpoint"]
            if self._config.get("region"):
                kwargs["region_name"] = self._config["region"]
                kwargs["config"] = BotoConfig(s3={"addressing_style": "path"})

            client = boto3.client("s3", **kwargs)
            client.head_bucket(Bucket=self._config["bucket"])
            self.result.emit(True, "Подключение успешно!")
        except Exception as e:
            self.result.emit(False, f"Ошибка: {e}")


class S3ConfigDialog(QDialog):
    def __init__(self, config: ConfigManager, parent=None):
        super().__init__(parent)
        self._config = config
        self._test_worker: _S3TestWorker | None = None
        self.setWindowTitle("Настройки S3")
        self.setMinimumSize(600, 400)

        main_layout = QHBoxLayout(self)

        # ── Левая панель: список профилей ────────────────────────
        left = QVBoxLayout()
        left.addWidget(QLabel("Профили:"))

        self._profile_list = QListWidget()
        self._profile_list.currentRowChanged.connect(self._on_profile_selected)
        left.addWidget(self._profile_list, 1)

        list_btns_top = QHBoxLayout()
        add_btn = QPushButton("+")
        add_btn.setToolTip("Добавить профиль")
        add_btn.setFixedWidth(32)
        add_btn.clicked.connect(self._on_add_profile)
        self._del_btn = QPushButton("−")
        self._del_btn.setToolTip("Удалить профиль")
        self._del_btn.setFixedWidth(32)
        self._del_btn.clicked.connect(self._on_delete_profile)
        self._rename_btn = QPushButton("Переименовать")
        self._rename_btn.clicked.connect(self._on_rename_profile)
        list_btns_top.addWidget(add_btn)
        list_btns_top.addWidget(self._del_btn)
        list_btns_top.addStretch()
        left.addLayout(list_btns_top)
        left.addWidget(self._rename_btn)

        left_widget = QWidget()
        left_widget.setLayout(left)
        left_widget.setFixedWidth(180)
        main_layout.addWidget(left_widget)

        # ── Правая панель: редактирование профиля ────────────────
        right = QVBoxLayout()

        self._form_container = QWidget()
        form = QFormLayout(self._form_container)

        self._endpoint_edit = QLineEdit()
        self._endpoint_edit.setPlaceholderText("https://s3.example.com")
        form.addRow("Адрес (Endpoint):", self._endpoint_edit)

        self._region_edit = QLineEdit()
        self._region_edit.setPlaceholderText("us-east-1")
        form.addRow("Регион:", self._region_edit)

        self._bucket_edit = QLineEdit()
        self._bucket_edit.setPlaceholderText("my-bucket")
        form.addRow("Бакет:", self._bucket_edit)

        self._access_key_edit = QLineEdit()
        form.addRow("Ключ доступа:", self._access_key_edit)

        self._secret_key_edit = QLineEdit()
        self._secret_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Секретный ключ:", self._secret_key_edit)

        right.addWidget(self._form_container, 1)

        # Проверка подключения
        test_row = QHBoxLayout()
        self._test_btn = QPushButton("Проверить подключение")
        self._test_btn.clicked.connect(self._on_test)
        test_row.addWidget(self._test_btn)
        self._test_status = QLabel("")
        test_row.addWidget(self._test_status, 1)
        right.addLayout(test_row)

        # Кнопки сохранить / закрыть
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._save_btn = QPushButton("Сохранить профиль")
        self._save_btn.clicked.connect(self._on_save)
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(self._save_btn)
        btn_row.addWidget(close_btn)
        right.addLayout(btn_row)

        main_layout.addLayout(right, 1)

        # Загрузить список профилей
        self._reload_list()
        self._update_form_enabled()

    # ── Загрузка списка ──────────────────────────────────────────

    def _reload_list(self):
        self._profile_list.clear()
        names = self._config.get_s3_profile_names()
        self._profile_list.addItems(names)
        active = self._config.get_active_s3_profile()
        if active in names:
            self._profile_list.setCurrentRow(names.index(active))
        elif names:
            self._profile_list.setCurrentRow(0)
        self._update_form_enabled()

    def _update_form_enabled(self):
        has_profiles = self._profile_list.count() > 0
        self._form_container.setEnabled(has_profiles)
        self._test_btn.setEnabled(has_profiles)
        self._save_btn.setEnabled(has_profiles)
        self._rename_btn.setEnabled(has_profiles)
        self._del_btn.setEnabled(has_profiles)

    # ── Выбор профиля ────────────────────────────────────────────

    def _on_profile_selected(self, row: int):
        self._test_status.setText("")
        if row < 0:
            return
        name = self._profile_list.item(row).text()
        profile = self._config.get_s3_profile(name)
        if not profile:
            return
        self._endpoint_edit.setText(profile.get("endpoint", ""))
        self._region_edit.setText(profile.get("region", ""))
        self._bucket_edit.setText(profile.get("bucket", ""))
        self._access_key_edit.setText(profile.get("access_key", ""))
        self._secret_key_edit.setText(profile.get("secret_key", ""))

    # ── Добавить / переименовать / удалить ───────────────────────

    def _on_add_profile(self):
        name, ok = QInputDialog.getText(
            self, "Новый профиль", "Название профиля:"
        )
        if not ok or not name.strip():
            return
        name = name.strip()
        if name in self._config.get_s3_profile_names():
            QMessageBox.warning(self, "Ошибка", f"Профиль «{name}» уже существует.")
            return
        self._config.save_s3_profile({
            "name": name, "endpoint": "", "region": "",
            "bucket": "", "access_key": "", "secret_key": "",
        })
        self._reload_list()
        # Выбрать новый
        names = self._config.get_s3_profile_names()
        self._profile_list.setCurrentRow(names.index(name))

    def _on_rename_profile(self):
        row = self._profile_list.currentRow()
        if row < 0:
            return
        old_name = self._profile_list.item(row).text()
        new_name, ok = QInputDialog.getText(
            self, "Переименовать", "Новое название:", text=old_name
        )
        if not ok or not new_name.strip() or new_name.strip() == old_name:
            return
        new_name = new_name.strip()
        if new_name in self._config.get_s3_profile_names():
            QMessageBox.warning(self, "Ошибка", f"Профиль «{new_name}» уже существует.")
            return
        self._config.rename_s3_profile(old_name, new_name)
        self._reload_list()

    def _on_delete_profile(self):
        row = self._profile_list.currentRow()
        if row < 0:
            return
        name = self._profile_list.item(row).text()
        reply = QMessageBox.question(
            self, "Удаление", f"Удалить профиль «{name}»?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._config.delete_s3_profile(name)
            self._reload_list()

    # ── Сохранение ───────────────────────────────────────────────

    def _on_save(self):
        row = self._profile_list.currentRow()
        if row < 0:
            return
        name = self._profile_list.item(row).text()
        profile = {
            "name": name,
            "endpoint": self._endpoint_edit.text().strip(),
            "region": self._region_edit.text().strip(),
            "bucket": self._bucket_edit.text().strip(),
            "access_key": self._access_key_edit.text().strip(),
            "secret_key": self._secret_key_edit.text().strip(),
        }
        self._config.save_s3_profile(profile)
        self._config.set_active_s3_profile(name)
        self._test_status.setStyleSheet("color: green;")
        self._test_status.setText("Сохранено")

    # ── Проверка подключения ─────────────────────────────────────

    def _current_form_config(self) -> dict:
        return {
            "endpoint": self._endpoint_edit.text().strip(),
            "access_key": self._access_key_edit.text().strip(),
            "secret_key": self._secret_key_edit.text().strip(),
            "bucket": self._bucket_edit.text().strip(),
            "region": self._region_edit.text().strip(),
        }

    def _on_test(self):
        cfg = self._current_form_config()
        if not cfg["bucket"]:
            self._test_status.setStyleSheet("color: red;")
            self._test_status.setText("Укажите бакет")
            return

        self._test_btn.setEnabled(False)
        self._test_status.setStyleSheet("color: gray;")
        self._test_status.setText("Проверка...")

        self._test_worker = _S3TestWorker(cfg, self)
        self._test_worker.result.connect(self._on_test_result)
        self._test_worker.start()

    def _on_test_result(self, success: bool, message: str):
        self._test_btn.setEnabled(True)
        self._test_status.setStyleSheet("color: green;" if success else "color: red;")
        self._test_status.setText(message)
        self._test_worker = None
