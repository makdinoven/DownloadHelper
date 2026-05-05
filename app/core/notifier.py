"""Системные уведомления через QSystemTrayIcon."""

from PyQt6.QtWidgets import QSystemTrayIcon, QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer


class Notifier:
    """Показывает Windows toast-уведомления."""

    def __init__(self):
        self._tray: QSystemTrayIcon | None = None
        self._init_tray()

    def _init_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self._tray = QSystemTrayIcon()
        # Используем иконку приложения, если есть
        app = QApplication.instance()
        if app and not app.windowIcon().isNull():
            self._tray.setIcon(app.windowIcon())
        else:
            # Стандартная иконка
            self._tray.setIcon(
                app.style().standardIcon(app.style().StandardPixmap.SP_ArrowDown)
                if app else QIcon()
            )
        self._tray.setToolTip("Download Helper")
        self._tray.show()

    def notify(self, title: str, message: str, success: bool = True):
        """Показать системное уведомление."""
        if not self._tray:
            return
        icon = (
            QSystemTrayIcon.MessageIcon.Information if success
            else QSystemTrayIcon.MessageIcon.Warning
        )
        self._tray.showMessage(title, message, icon, 5000)

    def cleanup(self):
        if self._tray:
            self._tray.hide()
