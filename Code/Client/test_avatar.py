from PySide6.QtWidgets import QApplication
from avatar_utils import generate_default_avatar #import hàm generate_default_avatar từ avatar_utils.py

app = QApplication([])

avatar = generate_default_avatar("kienpham")
avatar.save("test.png")

print("Đã tạo test.png")