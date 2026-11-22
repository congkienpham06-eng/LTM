"""Entry point cua Chat Client (GUI). Chay: python main.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from ui_connect import ConnectWindow


def main():
    app = QApplication(sys.argv)
    window = ConnectWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()