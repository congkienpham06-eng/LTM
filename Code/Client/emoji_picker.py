"""Popup luoi chon emoji don gian - emoji la ky tu Unicode thuong, khong can giao thuc rieng."""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGridLayout, QPushButton, QWidget

EMOJIS = [
    "😀", "😁", "😂", "🤣", "😊", "😍", "😘", "😜", "🤔", "😎",
    "😢", "😭", "😡", "😱", "👍", "👎", "👏", "🙏", "❤️", "💔",
    "🔥", "🎉", "✅", "❌", "⭐", "💡", "👋", "🤝", "🙌", "😴",
]


class EmojiPicker(QWidget):
    emoji_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Popup)
        layout = QGridLayout(self)
        layout.setSpacing(2)
        cols = 6
        for i, emoji in enumerate(EMOJIS):
            btn = QPushButton(emoji)
            btn.setFixedSize(36, 36)
            btn.setStyleSheet("font-size: 18px;")
            btn.clicked.connect(lambda checked=False, e=emoji: self._pick(e))
            layout.addWidget(btn, i // cols, i % cols)

    def _pick(self, emoji):
        self.emoji_selected.emit(emoji)
        self.close()
