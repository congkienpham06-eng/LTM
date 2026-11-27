import os
import sys
import argparse

from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Cho Python thấy thư mục Code (chứa Shared), giống client_handler.py của nhóm
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from Shared.protocol import make_message, MSG_TEXT, MSG_REPLY
except ImportError:

    import time
    import uuid

    MSG_TEXT = "TEXT"
    MSG_REPLY = "REPLY"

    def make_message(msg_type, sender="", to="", content="", reply_to=None,
                     forward_from=None, extra=None):
        msg = {
            "type": msg_type,
            "msg_id": str(uuid.uuid4()),
            "from": sender,
            "to": to,
            "timestamp": time.time(),
            "content": content,
            "reply_to": reply_to,
            "forward_from": forward_from,
        }
        if extra:
            msg.update(extra)
        return msg


from test import FakeClient


class message_bridge(QObject):

    new_message = Signal(object)

    def insert(self, index, text):
        self.new_message.emit(text)


class chat_window(QWidget):
    def __init__(self, client):
        super().__init__()

        self.reply_target = None

        self.messages_by_id = {}

        self.reply_label = QLabel()
        self.reply_label.setTextFormat(Qt.TextFormat.PlainText)
        self.reply_label.hide()

        self.client = client

        self.setWindowTitle(f"Chatroom - {self.client.name}")
        self.resize(600, 500)

        self.messages = QListWidget()
        self.messages.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Nhập tin nhắn.")

        self.btn_send = QPushButton("Gửi")
        self.btn_cancel_reply = QPushButton("X")
        self.btn_cancel_reply.setFixedWidth(24)
        self.btn_cancel_reply.hide()

        row = QHBoxLayout()
        row.addWidget(self.text_input)
        row.addWidget(self.btn_send)

        reply_row = QHBoxLayout()
        reply_row.addWidget(self.reply_label, stretch=1)
        reply_row.addWidget(self.btn_cancel_reply)

        layout = QVBoxLayout(self)
        layout.addWidget(self.messages)
        layout.addLayout(reply_row)
        layout.addLayout(row)

        self.text_input.returnPressed.connect(self.send)
        self.btn_send.clicked.connect(self.send)
        self.btn_cancel_reply.clicked.connect(self.cancel_reply)
        self.messages.itemDoubleClicked.connect(self.reply)
        self.messages.customContextMenuRequested.connect(self.show_message_menu)

    def add_message(self, packet):
        msg_id = packet.get("msg_id")
        if msg_id:
            self.messages_by_id[msg_id] = packet

        sender = packet.get("from")
        content = packet.get("content")
        text = f"{sender}: {content}"

        reply_preview = None
        reply_to = packet.get("reply_to")
        if reply_to:
            original = self.messages_by_id.get(reply_to)
            if original:
                reply_preview = "{}: {}".format(
                    original.get("from", "?"), original.get("content", "")[:60]
                )
            else:
                reply_preview = "Tin nhắn gốc không còn khả dụng"

        if reply_preview:
            text = f"> {reply_preview}\n{text}"

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

        if message == "/quit":
            self.client.send(message)
            self.close()
            return

        if self.reply_target:
            packet = make_message(MSG_REPLY, sender=self.client.name, to="all",
                                  content=message, reply_to=self.reply_target)
        else:
            packet = make_message(MSG_TEXT, sender=self.client.name, to="all",
                                  content=message)

        self.add_message(packet)
        self.client.send(packet)
        self.cancel_reply()

    def show_message_menu(self, pos):
        """Chuột phải vào tin: hiện menu Reply."""
        item = self.messages.itemAt(pos)
        if not item:
            return
        packet = item.data(Qt.ItemDataRole.UserRole)
        if not packet:
            return

        menu = QMenu(self)
        reply_action = menu.addAction("Reply")
        reply_action.triggered.connect(lambda: self.start_reply(packet))
        menu.exec(self.messages.viewport().mapToGlobal(pos))

    def reply(self, item):
        """Nhấp đúp vào tin cũng reply."""
        packet = item.data(Qt.ItemDataRole.UserRole)
        if packet:
            self.start_reply(packet)

    def start_reply(self, packet):
        msg_id = packet.get("msg_id")
        if not msg_id:
            return  

        self.reply_target = msg_id
        sender = packet.get("from", "?")
        preview = packet.get("content", "")[:60]
        self.reply_label.setText(f"Replying {sender}: {preview}")

        self.reply_label.show()
        self.btn_cancel_reply.show()
        self.text_input.setFocus()

    def cancel_reply(self):
        self.reply_target = None
        self.reply_label.hide()
        self.btn_cancel_reply.hide()


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

    client = FakeClient(host, port)
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