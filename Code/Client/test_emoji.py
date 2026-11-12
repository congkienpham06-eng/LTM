
import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from emoji_picker import EmojiPicker  # Đổi thành tên file Python của bạn

app = QApplication(sys.argv)

window = QWidget()
window.setWindowTitle("Test Emoji Picker")
window.resize(300, 250)

layout = QVBoxLayout(window)

label = QLabel("Emoji đã chọn: Chưa có")
layout.addWidget(label)

open_btn = QPushButton("Chọn Emoji")
layout.addWidget(open_btn)

picker = EmojiPicker(window)
layout.addWidget(picker)
picker.hide()

# Bấm nút để ẩn/hiện bảng emoji ngay trong cửa sổ, không bật popup rời
def toggle_picker():
    showing = not picker.isVisible()
    picker.setVisible(showing)
    open_btn.setText("Hủy" if showing else "Chọn Emoji")

open_btn.clicked.connect(toggle_picker)

# Chọn emoji xong thì ẩn bảng và trả nút về trạng thái ban đầu
picker.emoji_selected.connect(lambda emoji: open_btn.setText("Chọn Emoji"))

# Hiển thị emoji vừa chọn lên giao diện
picker.emoji_selected.connect(
    lambda emoji: label.setText(f"Emoji đã chọn: {emoji}")
)

window.show()
sys.exit(app.exec())
