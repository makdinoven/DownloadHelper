"""QProcess обёртка для запуска N_m3u8DL-RE."""

import os
import shutil
import sys
from dataclasses import dataclass

from PyQt6.QtCore import QObject, QProcess, pyqtSignal

# Утилиты, необходимые для работы
REQUIRED_TOOLS = ["N_m3u8DL-RE", "ffmpeg", "mp4decrypt"]


@dataclass
class ToolStatus:
    """Результат поиска одного инструмента."""
    name: str
    found: bool
    path: str = ""


def _app_dir() -> str:
    """Директория рядом с exe (или рядом со скриптом)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(sys.argv[0]))


def find_tool(name: str) -> ToolStatus:
    """Ищет утилиту в PATH, затем рядом с приложением."""
    # 1. PATH
    found = shutil.which(name)
    if found:
        return ToolStatus(name=name, found=True, path=found)

    # 2. Рядом с exe
    app = _app_dir()
    for suffix in ("", ".exe"):
        candidate = os.path.join(app, name + suffix)
        if os.path.isfile(candidate):
            return ToolStatus(name=name, found=True, path=candidate)

    return ToolStatus(name=name, found=False)


def check_all_tools() -> list[ToolStatus]:
    """Проверяет наличие всех необходимых утилит."""
    return [find_tool(name) for name in REQUIRED_TOOLS]


def find_executable() -> str | None:
    """Найти N_m3u8DL-RE (обратная совместимость)."""
    status = find_tool("N_m3u8DL-RE")
    return status.path if status.found else None


def format_tool_check_log(statuses: list[ToolStatus]) -> str:
    """Форматирует результат проверки утилит для вывода в лог."""
    lines = ["Проверка утилит:"]
    all_ok = True
    for s in statuses:
        if s.found:
            lines.append(f"  [OK] {s.name} -> {s.path}")
        else:
            lines.append(f"  [НЕ НАЙДЕН] {s.name}")
            all_ok = False

    if not all_ok:
        lines.append("")
        lines.append(
            "Отсутствующие утилиты необходимо поместить в одну папку "
            "с приложением или добавить в системный PATH."
        )
    lines.append("")
    return "\n".join(lines)


class Downloader(QObject):
    output_received = pyqtSignal(str)
    finished = pyqtSignal(int)  # код выхода

    def __init__(self, parent=None):
        super().__init__(parent)
        self._process = QProcess(self)
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._on_output)
        self._process.finished.connect(self._on_finished)

    def start(self, args: list[str]):
        """Запустить N_m3u8DL-RE. args[0] — путь к исполняемому файлу."""
        exe = args[0]
        self._process.start(exe, args[1:])

    def stop(self):
        if self._process.state() != QProcess.ProcessState.NotRunning:
            self._process.kill()
            self._process.waitForFinished(3000)

    def is_running(self) -> bool:
        return self._process.state() != QProcess.ProcessState.NotRunning

    def _on_output(self):
        data = self._process.readAllStandardOutput().data()
        try:
            text = data.decode("utf-8", errors="replace")
        except Exception:
            text = str(data)
        # Обработка \r строк прогресса: оставляем только последний сегмент
        if "\r" in text:
            lines = text.split("\r")
            text = lines[-1] if lines[-1] else (lines[-2] if len(lines) > 1 else text)
            if not text.endswith("\n"):
                text += "\n"
        self.output_received.emit(text)

    def _on_finished(self, exit_code, _exit_status):
        self.finished.emit(exit_code)
