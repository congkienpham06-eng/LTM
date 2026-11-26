"""Man hinh chat chinh: danh sach lien he, khung chat bubble, reply, forward, emoji."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Shared.protocol import (
    MSG_ERROR, MSG_FORWARD, MSG_REPLY, MSG_TEXT, MSG_USER_JOINED, MSG_USER_LEFT,
    make_message,
)

from avatar_utils import base64_to_pixmap, generate_default_avatar, make_circle_pixmap
from chat_bubble import ChatBubble
from emoji_picker import EmojiPicker

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QMenu, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)


class ForwardDialog(QDialog):
    def __init__(self, contacts, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Chuyển tiếp tin nhắn tới...")
        self.selected = None

        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        self.list_widget.addItem("Tất cả (all)")
        for name in contacts:
            self.list_widget.addItem(name)
        layout.addWidget(self.list_widget)

        btn = QPushButton("Chuyển tiếp")
        btn.clicked.connect(self.accept_selection)
        layout.addWidget(btn)

    def accept_selection(self):
        item = self.list_widget.currentItem()
        if item:
            text = item.text()
            self.selected = "all" if text.startswith("Tất cả") else text
            self.accept()


class ChatWindow(QWidget):
    def __init__(self, client_thread, username, contacts):
        super().__init__()
        self.client_thread = client_thread
        self.username = username
        self.contacts = dict(contacts)   # username -> avatar_b64
        self.messages_by_id = {}         # msg_id -> message (tra cuu khi hien thi reply-quote)
        self.reply_target = None

        self.setWindowTitle(f"Chat TCP - {username}")
        self.resize(820, 560)

        self._build_ui()
        self._refresh_contact_list()

        self.client_thread.message_received.connect(self.on_message_received)
        self.client_thread.status_changed.connect(self.on_status_changed)

    def _build_ui(self):
        root = QHBoxLayout(self)

        left = QVBoxLayout()
        left.addWidget(QLabel("<b>Đang online</b>"))
        self.contact_list = QListWidget()
        self.contact_list.setFixedWidth(200)
        left.addWidget(self.contact_list)
        root.addLayout(left)

        right = QVBoxLayout()

        self.status_label = QLabel("Đã kết nối")
        self.status_label.setStyleSheet("color:green; font-weight:bold;")
        right.addWidget(self.status_label)

        self.chat_list = QListWidget()
        self.chat_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.chat_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.chat_list.customContextMenuRequested.connect(self.show_message_menu)
        right.addWidget(self.chat_list, stretch=1)

        self.reply_bar = QFrame()
        self.reply_bar.setVisible(False)
        reply_bar_layout = QHBoxLayout(self.reply_bar)
        reply_bar_layout.setContentsMargins(6, 2, 6, 2)
        self.reply_bar_label = QLabel()
        reply_bar_layout.addWidget(self.reply_bar_label, stretch=1)
        cancel_reply_btn = QPushButton("x")
        cancel_reply_btn.setFixedWidth(24)
        cancel_reply_btn.clicked.connect(self.cancel_reply)
        reply_bar_layout.addWidget(cancel_reply_btn)
        right.addWidget(self.reply_bar)

        input_row = QHBoxLayout()
        input_row.addWidget(QLabel("Gửi tới:"))

        self.target_combo = QComboBox()
        self.target_combo.addItem("Tất cả (all)")
        input_row.addWidget(self.target_combo)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Nhập tin nhắn...")
        self.message_input.returnPressed.connect(self.send_message)
        input_row.addWidget(self.message_input, stretch=1)

        emoji_btn = QPushButton("😊")
        emoji_btn.setFixedWidth(36)
        emoji_btn.clicked.connect(self.open_emoji_picker)
        input_row.addWidget(emoji_btn)

        send_btn = QPushButton("Gửi")
        send_btn.clicked.connect(self.send_message)
        input_row.addWidget(send_btn)

        right.addLayout(input_row)
        root.addLayout(right, stretch=1)

    def _refresh_contact_list(self):
        self.contact_list.clear()
        self.target_combo.clear()
        self.target_combo.addItem("Tất cả (all)")
        for name, avatar_b64 in self.contacts.items():
            pixmap = make_circle_pixmap(base64_to_pixmap(avatar_b64) or generate_default_avatar(name), 28)
            item = QListWidgetItem(QIcon(pixmap), f"  {name}")
            self.contact_list.addItem(item)
            self.target_combo.addItem(name)

    def send_message(self):
        content = self.message_input.text().strip()
        if not content:
            return
        target_text = self.target_combo.currentText()
        target = "all" if target_text.startswith("Tất cả") else target_text

        if self.reply_target:
            msg = make_message(MSG_REPLY, sender=self.username, to=target,
                                content=content, reply_to=self.reply_target)
        else:
            msg = make_message(MSG_TEXT, sender=self.username, to=target, content=content)

        try:
            self.client_thread.send(msg)
        except Exception as e:
            QMessageBox.warning(self, "Lỗi gửi tin", f"Không gửi được: {e}")
            return

        self.messages_by_id[msg["msg_id"]] = msg
        self._append_bubble(msg, is_own=True)
        self.message_input.clear()
        self.cancel_reply()

    def open_emoji_picker(self):
        picker = EmojiPicker(self)
        picker.emoji_selected.connect(self.insert_emoji)
        btn = self.sender()
        picker.move(btn.mapToGlobal(btn.rect().bottomLeft()))
        picker.show()

    def insert_emoji(self, emoji):
        self.message_input.insert(emoji)

    def show_message_menu(self, pos):
        item = self.chat_list.itemAt(pos)
        if not item:
            return
        bubble = self.chat_list.itemWidget(item)
        if not bubble:
            return
        msg = bubble.message

        menu = QMenu(self)
        reply_action = QAction("Reply", self)
        reply_action.triggered.connect(lambda: self.start_reply(msg))
        menu.addAction(reply_action)

        forward_action = QAction("Forward", self)
        forward_action.triggered.connect(lambda: self.start_forward(msg))
        menu.addAction(forward_action)

        menu.exec(self.chat_list.viewport().mapToGlobal(pos))

    def start_reply(self, msg):
        self.reply_target = msg["msg_id"]
        preview = msg.get("content", "")[:60]
        self.reply_bar_label.setText(f'Đang reply: "{preview}" - {msg.get("from", "?")}')
        self.reply_bar.setVisible(True)

    def cancel_reply(self):
        self.reply_target = None
        self.reply_bar.setVisible(False)

    def start_forward(self, msg):
        dialog = ForwardDialog(list(self.contacts.keys()), self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected:
            fwd = make_message(MSG_FORWARD, sender=self.username, to=dialog.selected,
                                content=msg.get("content", ""), forward_from=msg.get("from"))
            try:
                self.client_thread.send(fwd)
            except Exception as e:
                QMessageBox.warning(self, "Lỗi gửi tin", f"Không gửi được: {e}")
                return
            self.messages_by_id[fwd["msg_id"]] = fwd
            self._append_bubble(fwd, is_own=True)

    def on_message_received(self, msg):
        msg_type = msg.get("type")

        if msg_type == MSG_USER_JOINED:
            name = msg.get("content")
            if name and name != self.username:
                self.contacts[name] = msg.get("avatar", "")
                self._refresh_contact_list()
                self._append_system_note(f"{name} đã tham gia")

        elif msg_type == MSG_USER_LEFT:
            name = msg.get("content")
            if name in self.contacts:
                del self.contacts[name]
                self._refresh_contact_list()
                self._append_system_note(f"{name} đã rời đi")

        elif msg_type == MSG_ERROR:
            QMessageBox.warning(self, "Server báo lỗi", msg.get("content", ""))

        elif msg_type in (MSG_TEXT, MSG_REPLY, MSG_FORWARD):
            self.messages_by_id[msg["msg_id"]] = msg
            self._append_bubble(msg, is_own=False)

    def on_status_changed(self, state, detail):
        if state == "connected":
            self.status_label.setText("Đã kết nối")
            self.status_label.setStyleSheet("color:green; font-weight:bold;")
        elif state == "error":
            self.status_label.setText(f"Lỗi kết nối: {detail}")
            self.status_label.setStyleSheet("color:red; font-weight:bold;")
        elif state == "disconnected":
            self.status_label.setText(f"Mất kết nối: {detail}")
            self.status_label.setStyleSheet("color:red; font-weight:bold;")

    def _append_bubble(self, msg, is_own):
        reply_preview = None
        reply_to = msg.get("reply_to")
        if reply_to and reply_to in self.messages_by_id:
            original = self.messages_by_id[reply_to]
            reply_preview = f"{original.get('from', '?')}: {original.get('content', '')[:60]}"

        sender = msg.get("from", "?")
        avatar_b64 = self.contacts.get(sender) if sender != self.username else None
        base_pixmap = base64_to_pixmap(avatar_b64) if avatar_b64 else None
        if base_pixmap is None or base_pixmap.isNull():
            base_pixmap = generate_default_avatar(sender)
        pixmap = make_circle_pixmap(base_pixmap, 32)

        bubble = ChatBubble(msg, pixmap, is_own, reply_preview)
        item = QListWidgetItem()
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        item.setSizeHint(bubble.sizeHint())
        self.chat_list.addItem(item)
        self.chat_list.setItemWidget(item, bubble)
        self.chat_list.scrollToBottom()

    def _append_system_note(self, text):
        item = QListWidgetItem(f"— {text} —")
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        item.setFlags(Qt.ItemFlag.NoItemFlags)
        self.chat_list.addItem(item)
        self.chat_list.scrollToBottom()

    def closeEvent(self, event):
        self.client_thread.stop()
        self.client_thread.wait(2000)
        event.accept()
