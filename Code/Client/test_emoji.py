
import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from emoji_picker import EmojiPicker  # Đổi thành tên file Python của bạn

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("Test Emoji Picker")
window.resize(300, 150)

layout = QVBoxLayout(window)

label = QLabel("Emoji đã chọn: Chưa có")
layout.addWidget(label)

open_btn = QPushButton("Chọn Emoji")
layout.addWidget(open_btn)

picker = EmojiPicker(window)

# Bấm nút để mở popup chọn emoji
open_btn.clicked.connect(picker.show)

# Hiển thị emoji vừa chọn lên giao diện
picker.emoji_selected.connect(
    lambda emoji: label.setText(f"Emoji đã chọn: {emoji}")
)

window.show()
sys.exit(app.exec())
