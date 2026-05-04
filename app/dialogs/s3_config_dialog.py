"""Диалог настроек S3."""

from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPushButton, QHBoxLayout, QVBoxLayout,
    QLabel,
)
from PyQt6.QtCore import QThread, pyqtSignal

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
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.endpoint_edit = QLineEdit(config.get("s3_endpoint"))
        self.endpoint_edit.setPlaceholderText("https://s3.example.com")
        form.addRow("Адрес (Endpoint):", self.endpoint_edit)

        self.region_edit = QLineEdit(config.get("s3_region"))
        self.region_edit.setPlaceholderText("us-east-1")
        form.addRow("Регион:", self.region_edit)

        self.bucket_edit = QLineEdit(config.get("s3_bucket"))
        self.bucket_edit.setPlaceholderText("my-bucket")
        form.addRow("Бакет:", self.bucket_edit)

        self.access_key_edit = QLineEdit(config.get("s3_access_key"))
        form.addRow("Ключ доступа:", self.access_key_edit)

        self.secret_key_edit = QLineEdit(config.get("s3_secret_key"))
        self.secret_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Секретный ключ:", self.secret_key_edit)

        layout.addLayout(form)

        # Кнопка проверки подключения
        test_row = QHBoxLayout()
        self._test_btn = QPushButton("Проверить подключение")
        self._test_btn.clicked.connect(self._on_test)
        test_row.addWidget(self._test_btn)

        self._test_status = QLabel("")
        test_row.addWidget(self._test_status, 1)
        layout.addLayout(test_row)

        # Кнопки сохранить/отмена
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        cancel_btn = QPushButton("Отмена")
        btn_layout.addStretch()
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        save_btn.clicked.connect(self._save)
        cancel_btn.clicked.connect(self.reject)

    def _current_s3_config(self) -> dict:
        return {
            "endpoint": self.endpoint_edit.text().strip(),
            "access_key": self.access_key_edit.text().strip(),
            "secret_key": self.secret_key_edit.text().strip(),
            "bucket": self.bucket_edit.text().strip(),
            "region": self.region_edit.text().strip(),
        }

    def _on_test(self):
        cfg = self._current_s3_config()
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
        if success:
            self._test_status.setStyleSheet("color: green;")
        else:
            self._test_status.setStyleSheet("color: red;")
        self._test_status.setText(message)
        self._test_worker = None

    def _save(self):
        cfg = self._current_s3_config()
        self._config.set_s3_config(
            endpoint=cfg["endpoint"],
            access_key=cfg["access_key"],
            secret_key=cfg["secret_key"],
            bucket=cfg["bucket"],
            region=cfg["region"],
        )
        self.accept()
