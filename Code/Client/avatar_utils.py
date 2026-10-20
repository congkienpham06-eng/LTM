"""Tien ich xu ly avatar: resize, bo tron, sinh avatar mac dinh, encode/decode base64.
Dung toan bo PySide6 (QPixmap/QPainter) de khong can them thu vien anh ngoai (Pillow)."""
import base64

from PySide6.QtCore import QBuffer, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPixmap

AVATAR_SIZE = 96

_PALETTE = ["#E57373", "#64B5F6", "#81C784", "#FFB74D", "#BA68C8", "#4DB6AC", "#F06292"]


def pixmap_to_base64(pixmap):
    buffer = QBuffer()
    buffer.open(QBuffer.OpenModeFlag.WriteOnly)
    pixmap.save(buffer, "PNG")
    return base64.b64encode(bytes(buffer.data())).decode("ascii")


def base64_to_pixmap(b64_str):
    pixmap = QPixmap()
    if b64_str:
        try:
            pixmap.loadFromData(base64.b64decode(b64_str))
        except Exception:
            pass
    return pixmap


def _resize_cover(pixmap, size):
    scaled = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                            Qt.TransformationMode.SmoothTransformation)
    x = max(0, (scaled.width() - size) // 2)
    y = max(0, (scaled.height() - size) // 2)
    return scaled.copy(x, y, size, size)


def make_circle_pixmap(pixmap, size=AVATAR_SIZE):
    if pixmap is None or pixmap.isNull():
        return QPixmap()
    src = _resize_cover(pixmap, size)
    result = QPixmap(size, size)
    result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath()
    path.addEllipse(0, 0, size, size)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, src)
    painter.end()
    return result


def generate_default_avatar(username, size=AVATAR_SIZE):
    name = username or "?"
    color = _PALETTE[sum(ord(c) for c in name) % len(_PALETTE)]
    initials = name[:2].upper()

    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(color))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(0, 0, size, size)
    painter.setPen(QColor("white"))
    font = QFont()
    font.setPointSize(int(size * 0.35))
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, initials)
    painter.end()
    return pixmap
