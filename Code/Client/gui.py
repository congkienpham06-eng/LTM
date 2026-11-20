import sys
import argparse

from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QListWidgetItem,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QLineEdit,
    QPushButton,
    QLabel,
)

# Đổi tên file/class cho đúng với phần của bên client
from test import FakeClientForTest


class message_bridge(QObject):
    

    new_message = Signal(object)

    def insert(self, index, text):
        self.new_message.emit(text)


class chat_window(QWidget):
    def __init__(self, client):
        super().__init__()

        self.reply_to = None
        self.reply_label = QLabel()
        self.reply_label.hide()

        self.client = client

        self.setWindowTitle("Chatroom")
        self.resize(600, 500)

        self.messages = QListWidget()

      
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Write your message here.")

        self.btn_send = QPushButton("Send")
        self.btn_cancel_reply = QPushButton("X")
        self.btn_cancel_reply.hide()

        row = QHBoxLayout()
        row.addWidget(self.text_input)
        row.addWidget(self.btn_send)

        reply_row = QHBoxLayout()
        reply_row.addWidget(self.reply_label)
        reply_row.addWidget(self.btn_cancel_reply)

        layout = QVBoxLayout(self)
        layout.addWidget(self.messages)
        layout.addLayout(reply_row)
        layout.addLayout(row)

        self.text_input.returnPressed.connect(self.send)
        self.btn_send.clicked.connect(self.send)
        self.messages.itemDoubleClicked.connect(self.reply)

    def add_message(self, packet):
        sender = packet.get("from")
        content = packet.get("content")
        text = f"{sender}: {content}"
        item = QListWidgetItem()
        border = bubble_border(text)
        row = QWidget()
        
        layout = QHBoxLayout(row)
        layout.setContentsMargins(10, 5, 10, 5)

        if sender == self.client.name:
            layout.addStretch()
            layout.addWidget(border)
        else:
            layout.addWidget(border)
            layout.addStretch()

        item.setSizeHint(row.sizeHint())
        item.setData(Qt.UserRole, packet)

        self.messages.addItem(item)
        self.messages.setItemWidget(item, row)
        self.messages.scrollToBottom()

    def send(self):
        message = self.text_input.text().strip()
        self.text_input.clear()
        if not message:
            return

        if message != "/quit":
            self.add_message({"from": self.client.name, "content": message})

        self.client.send(message)

        if message == "/quit":
            self.close()

    def reply(self, item):
        packet = item.data(Qt.UserRole)
        self.reply_to = packet
        sender = packet.get("from")
        content = packet.get("content")
        self.reply_label.setText(f"Replying {sender}: {content}")
        
        self.reply_label.show()
        self.btn_cancel_reply.show()

        self.text_input.setFocus()

class bubble_border(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet(
            "background-color: darkblue;" 
            "border-radius: 15px;" 
            "padding: 10px;" 
            "color: white;")
        self.setWordWrap(True)
        self.setMaximumWidth(400)


def main(host, port):
    app = QApplication(sys.argv)

    client = FakeClientForTest(host, port)
    receive = client.start()

    window = chat_window(client)

    bridge = message_bridge()
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

