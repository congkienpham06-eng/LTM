import sys
import argparse

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QLineEdit,
    QPushButton,
)

# Đổi tên file/class cho đúng với phần của bên client
from test import FakeClient


class MessageBridge(QObject):
    

    new_message = Signal(str)

    def insert(self, index, text):
        self.new_message.emit(text)


class ChatWindow(QWidget):
    def __init__(self, client):
        super().__init__()
        self.client = client

        self.setWindowTitle("Chatroom")
        self.resize(600, 500)

       
        self.messages = QListWidget()

      
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Write your message here.")
        self.btn_send = QPushButton("Send")

        row = QHBoxLayout()
        row.addWidget(self.text_input)
        row.addWidget(self.btn_send)

        layout = QVBoxLayout(self)
        layout.addWidget(self.messages)
        layout.addLayout(row)

    
        self.text_input.returnPressed.connect(self.send)
        self.btn_send.clicked.connect(self.send)

    def add_message(self, text):
        self.messages.addItem(text)
        self.messages.scrollToBottom()

    def send(self):
        message = self.text_input.text().strip()
        self.text_input.clear()
        if not message:
            return

       
        if message != "/quit":
            self.add_message("{}: {}".format(self.client.name, message))

       
        self.client.send(message)

        if message == "/quit":
            self.close()


def main(host, port):
    app = QApplication(sys.argv)

    client = FakeClient(host, port)
    receive = client.start()

    window = ChatWindow(client)

    bridge = MessageBridge()
    bridge.new_message.connect(window.add_message)
    client.messages = bridge
    receive.messages = bridge

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chatroom GUI")
    parser.add_argument("host", help="Địa chỉ server")
    parser.add_argument("-p", metavar="PORT", type=int, default=1060, help="Cổng TCP (mặc định 1060)")
    args = parser.parse_args()

    main(args.host, args.p)