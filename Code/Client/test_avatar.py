from PySide6.QtWidgets import QApplication
from avatar_utils import generate_default_avatar

app = QApplication([])

avatar = generate_default_avatar("kienpham")
avatar.save("avatar.png")

print("Đã tạo avatar.png")