"""Панель прогресса загрузки с прогресс-баром."""

import re

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QProgressBar, QLabel


# Префиксы потоков N_m3u8DL-RE (видео важнее аудио важнее субтитров)
_STREAM_PRIORITY = {"vid": 3, "aud": 2, "sub": 1}


class ProgressPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        bar_row = QHBoxLayout()
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setTextVisible(True)
        bar_row.addWidget(self._progress_bar, 1)

        self._status_label = QLabel("")
        bar_row.addWidget(self._status_label)
        layout.addLayout(bar_row)

        self._info_label = QLabel("")
        self._info_label.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(self._info_label)

        # Прогресс каждого потока: {"vid": 45, "aud": 80, "sub": 0}
        self._stream_progress: dict[str, int] = {}

        # Регулярки для N_m3u8DL-RE
        self._stream_re = re.compile(r"^(Vid|Aud|Sub)\b", re.IGNORECASE)
        self._pct_re = re.compile(r"(\d+(?:\.\d+)?)%")
        self._fraction_re = re.compile(r"(\d+)/(\d+)")
        self._speed_re = re.compile(
            r"(\d+(?:\.\d+)?\s*(?:Ki?B|Mi?B|Gi?B|[KMG]?B|B)(?:ps|/s))", re.IGNORECASE
        )
        self._time_re = re.compile(r"(\d{1,2}:\d{2}(?::\d{2})?)")

    def reset(self):
        self._progress_bar.setValue(0)
        self._status_label.setText("")
        self._info_label.setText("")
        self._stream_progress.clear()

    def set_progress(self, value: int):
        self._progress_bar.setValue(min(value, 100))

    def set_status(self, text: str):
        self._status_label.setText(text)

    def set_info(self, text: str):
        self._info_label.setText(text)

    def parse_output(self, text: str):
        """Парсит строку прогресса N_m3u8DL-RE и обновляет бар."""
        # Определяем процент из строки
        pct = -1
        pct_match = self._pct_re.search(text)
        if pct_match:
            pct = int(float(pct_match.group(1)))
        elif (frac := self._fraction_re.search(text)):
            done, total = int(frac.group(1)), int(frac.group(2))
            if total > 0:
                pct = int(done * 100 / total)

        if pct >= 0:
            # Определяем поток (Vid/Aud/Sub) или "unknown"
            stream_match = self._stream_re.match(text.strip())
            stream = stream_match.group(1).lower() if stream_match else "unknown"
            self._stream_progress[stream] = pct

            # Прогресс-бар показывает поток с наивысшим приоритетом
            best_pct = self._get_primary_progress()
            self._progress_bar.setValue(best_pct)

        # Информация (скорость, время)
        info_parts = []
        speed_match = self._speed_re.search(text)
        if speed_match:
            info_parts.append(f"Скорость: {speed_match.group(1)}")

        time_matches = self._time_re.findall(text)
        if time_matches:
            info_parts.append(f"Осталось: {time_matches[-1]}")

        if info_parts:
            self._info_label.setText("  |  ".join(info_parts))

    def _get_primary_progress(self) -> int:
        """Возвращает прогресс самого приоритетного потока."""
        if not self._stream_progress:
            return 0
        best_stream = max(
            self._stream_progress,
            key=lambda s: _STREAM_PRIORITY.get(s, 0),
        )
        return self._stream_progress[best_stream]

    def set_finished(self, success: bool):
        if success:
            self._progress_bar.setValue(100)
            self._status_label.setText("Готово")
            self._info_label.setText("")
        else:
            self._status_label.setText("Ошибка")
