"""JSON config manager for application settings."""

import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".downloader_helper"
CONFIG_PATH = CONFIG_DIR / "config.json"

_DEFAULTS = {
    "save_path": str(Path.home() / "Downloads"),
    "s3_endpoint": "",
    "s3_access_key": "",
    "s3_secret_key": "",
    "s3_bucket": "",
    "s3_region": "",
    "s3_default_path": "/",
}


class ConfigManager:
    def __init__(self):
        self._data: dict = {}
        self._load()

    def _load(self):
        if CONFIG_PATH.exists():
            try:
                self._data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._data = {}
        else:
            self._data = {}

    def get(self, key: str, default=None):
        return self._data.get(key, _DEFAULTS.get(key, default))

    def set(self, key: str, value):
        self._data[key] = value

    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def get_s3_config(self) -> dict:
        return {
            "endpoint": self.get("s3_endpoint"),
            "access_key": self.get("s3_access_key"),
            "secret_key": self.get("s3_secret_key"),
            "bucket": self.get("s3_bucket"),
            "region": self.get("s3_region"),
        }

    def set_s3_config(self, endpoint: str, access_key: str, secret_key: str,
                      bucket: str, region: str):
        self.set("s3_endpoint", endpoint)
        self.set("s3_access_key", access_key)
        self.set("s3_secret_key", secret_key)
        self.set("s3_bucket", bucket)
        self.set("s3_region", region)
        self.save()
