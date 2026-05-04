"""QThread обёртка для загрузки файлов в S3 через boto3."""

import os

from PyQt6.QtCore import QThread, pyqtSignal


class S3Uploader(QThread):
    progress = pyqtSignal(int)  # процент 0-100
    upload_finished = pyqtSignal(bool, str)  # успех, сообщение
    log_message = pyqtSignal(str)

    def __init__(self, local_path: str, s3_key: str, s3_config: dict,
                 delete_local: bool = False, parent=None):
        super().__init__(parent)
        self._local_path = local_path
        self._s3_key = s3_key.lstrip("/")
        self._s3_config = s3_config
        self._delete_local = delete_local

    def run(self):
        try:
            import boto3
            from botocore.config import Config as BotoConfig

            self.log_message.emit(f"Подключение к S3: {self._s3_config['endpoint']}\n")

            kwargs = {
                "aws_access_key_id": self._s3_config["access_key"],
                "aws_secret_access_key": self._s3_config["secret_key"],
            }
            if self._s3_config.get("endpoint"):
                kwargs["endpoint_url"] = self._s3_config["endpoint"]
            if self._s3_config.get("region"):
                kwargs["region_name"] = self._s3_config["region"]
                kwargs["config"] = BotoConfig(s3={"addressing_style": "path"})

            client = boto3.client("s3", **kwargs)
            bucket = self._s3_config["bucket"]
            file_size = os.path.getsize(self._local_path)

            self.log_message.emit(
                f"Загрузка {self._local_path} -> s3://{bucket}/{self._s3_key} "
                f"({file_size / 1024 / 1024:.1f} МБ)\n"
            )

            uploaded = 0

            def callback(bytes_transferred):
                nonlocal uploaded
                uploaded += bytes_transferred
                pct = int(uploaded * 100 / file_size) if file_size > 0 else 100
                self.progress.emit(min(pct, 100))

            client.upload_file(
                self._local_path,
                bucket,
                self._s3_key,
                Callback=callback,
            )
            self.log_message.emit("Загрузка в S3 завершена.\n")

            if self._delete_local:
                try:
                    os.remove(self._local_path)
                    self.log_message.emit(f"Локальная копия удалена: {self._local_path}\n")
                except OSError as e:
                    self.log_message.emit(f"Не удалось удалить локальную копию: {e}\n")

            self.upload_finished.emit(True, "Загрузка в S3 успешна")

        except Exception as e:
            self.log_message.emit(f"Ошибка загрузки в S3: {e}\n")
            self.upload_finished.emit(False, str(e))
