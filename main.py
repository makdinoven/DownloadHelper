"""Download Helper - GUI for N_m3u8DL-RE."""

import sys

from PyQt6.QtWidgets import QApplication

from app.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Download Helper")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
