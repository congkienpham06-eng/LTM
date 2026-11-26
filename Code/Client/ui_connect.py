"""Man hinh ket noi: nhap Server IP / Port / Username, chon avatar, hien 4 trang thai ket noi."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Shared.config import DEFAULT_CLIENT_HOST, DEFAULT_PORT

from avatar_utils import generate_default_avatar, make_circle_pixmap, pixmap_to_base64
from network_client import ClientThread

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QVBoxLayout, QWidget,
)


class ConnectWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat TCP - Ket noi")
        self.resize(360, 340)

        self.client_thread = None
        self.avatar_pixmap = None
        self.chat_window = None

        layout = QVBoxLayout(self)

        self.avatar_preview = QLabel()
        self.avatar_preview.setFixedSize(80, 80)
        self.avatar_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.avatar_preview, alignment=Qt.AlignmentFlag.AlignHCenter)

        pick_avatar_btn = QPushButton("Chon avatar...")
        pick_avatar_btn.clicked.connect(self.pick_avatar)
        layout.addWidget(pick_avatar_btn)

        form = QFormLayout()
        self.host_input = QLineEdit(DEFAULT_CLIENT_HOST)
        self.port_input = QLineEdit(str(DEFAULT_PORT))
        self.username_input = QLineEdit()
        form.addRow("Server IP:", self.host_input)
        form.addRow("Port:", self.port_input)
        form.addRow("Ten hien thi:", self.username_input)
        layout.addLayout(form)

        self.status_label = QLabel("Chua ket noi")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.connect_btn = QPushButton("Ket noi")
        self.connect_btn.clicked.connect(self.try_connect)
        layout.addWidget(self.connect_btn)

        self.username_input.textChanged.connect(self.update_avatar_preview)
        self.update_avatar_preview()

    def update_avatar_preview(self):
        source = self.avatar_pixmap or generate_default_avatar(self.username_input.text().strip() or "?")
        self.avatar_preview.setPixmap(make_circle_pixmap(source, 80))

    def pick_avatar(self):
        path, _ = QFileDialog.getOpenFileName(self, "Chon anh avatar", "", "Images (*.png *.jpg *.jpeg)")
        if not path:
            return
        pixmap = QPixmap(path)
        if pixmap.isNull():
            QMessageBox.warning(self, "Loi", "Khong doc duoc file anh da chon")
            return
        self.avatar_pixmap = pixmap
        self.update_avatar_preview()

    def set_status(self, text, color="black"):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color:{color};")

    def try_connect(self):
        host = self.host_input.text().strip()
        port_text = self.port_input.text().strip()
        username = self.username_input.text().strip()

        if not host:
            self.set_status("Vui long nhap Server IP", "red")
            return
        if not port_text.isdigit():
            self.set_status("Port phai la so", "red")
            return
        if not username:
            self.set_status("Vui long nhap ten hien thi", "red")
            return

        port = int(port_text)
        avatar_source = self.avatar_pixmap or generate_default_avatar(username)
        avatar_b64 = pixmap_to_base64(make_circle_pixmap(avatar_source))

        self.connect_btn.setEnabled(False)
        self.set_status("Dang ket noi...", "#B8860B")

        self.client_thread = ClientThread(host, port, username, avatar_b64)
        self.client_thread.status_changed.connect(self.on_status_changed)
        self.client_thread.login_result.connect(self.on_login_result)
        self.client_thread.start()

    def on_status_changed(self, state, detail):
        if state == "connecting":
            self.set_status("Dang ket noi...", "#B8860B")
        elif state == "error":
            self.set_status(f"That bai: {detail}", "red")
            self.connect_btn.setEnabled(True)
        elif state == "disconnected":
            self.set_status(f"Mat ket noi: {detail}", "red")
            self.connect_btn.setEnabled(True)

    def on_login_result(self, success, error_message, contacts):
        if not success:
            self.set_status(f"That bai: {error_message}", "red")
            self.connect_btn.setEnabled(True)
            return

        self.set_status("Ket noi thanh cong", "green")

        from ui_chat import ChatWindow
        username = self.username_input.text().strip()
        self.chat_window = ChatWindow(self.client_thread, username, contacts)
        self.chat_window.show()
        self.close()

    def closeEvent(self, event):
        if self.client_thread and self.client_thread.isRunning() and not self.chat_window:
            self.client_thread.stop()
            self.client_thread.wait(1000)
        event.accept()
