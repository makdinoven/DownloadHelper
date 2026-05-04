"""Панель прогресса загрузки с прогресс-баром."""

import re

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QProgressBar, QLabel


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

        # Регулярки для N_m3u8DL-RE
        # Формат: "Vid 1080 | ... 50/100 45.12% 12.3 MiB/s 00:01:23"
        self._pct_re = re.compile(r"(\d+(?:\.\d+)?)%")
        # Формат N/M (e.g. "50/100") — вычисляем процент из дроби
        self._fraction_re = re.compile(r"(\d+)/(\d+)")
        self._speed_re = re.compile(
            r"(\d+(?:\.\d+)?\s*(?:Ki?B|Mi?B|Gi?B|[KMG]?B|B)(?:ps|/s))", re.IGNORECASE
        )
        # Время формата HH:MM:SS или MM:SS
        self._time_re = re.compile(r"(\d{1,2}:\d{2}(?::\d{2})?)")

    def reset(self):
        self._progress_bar.setValue(0)
        self._status_label.setText("")
        self._info_label.setText("")

    def set_progress(self, value: int):
        self._progress_bar.setValue(min(value, 100))

    def set_status(self, text: str):
        self._status_label.setText(text)

    def set_info(self, text: str):
        self._info_label.setText(text)

    def parse_output(self, text: str):
        """Парсит строку прогресса N_m3u8DL-RE и обновляет бар."""
        pct_match = self._pct_re.search(text)
        if pct_match:
            pct = float(pct_match.group(1))
            self._progress_bar.setValue(int(pct))
        elif (frac := self._fraction_re.search(text)):
            done, total = int(frac.group(1)), int(frac.group(2))
            if total > 0:
                self._progress_bar.setValue(int(done * 100 / total))

        info_parts = []
        speed_match = self._speed_re.search(text)
        if speed_match:
            info_parts.append(f"Скорость: {speed_match.group(1)}")

        # Берём последнее совпадение времени (обычно это оставшееся время)
        time_matches = self._time_re.findall(text)
        if time_matches:
            info_parts.append(f"Осталось: {time_matches[-1]}")

        if info_parts:
            self._info_label.setText("  |  ".join(info_parts))

    def set_finished(self, success: bool):
        if success:
            self._progress_bar.setValue(100)
            self._status_label.setText("Готово")
            self._info_label.setText("")
        else:
            self._status_label.setText("Ошибка")
