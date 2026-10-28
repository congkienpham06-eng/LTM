import json
import socket

from PySide6.QtCore import QThread, Signal

class NetworkClient(QThread):
    # Giao diện.connect() vào các tín hiệu này để biết khi nào cần cập nhật.
    status_changed = Signal(str)          #trạng thái
    message_received = Signal(str, str)   #(người gửi, nội dung)
    online_updated = Signal(list)         #danh sách tên người đang online

    def __init__(self, host, port, name):
        super().__init__()
        self.host = host
        self.port = port
        self.name = name
        self.sock = None

    # run() chạy ở luồng riêng.
    def run(self):
        #kết nối server
        try:
            self.sock = socket.create_connection((self.host, self.port), timeout=5)
            self.sock.settimeout(None)  #sau khi nối thì chờ tin vô thời hạn
        except OSError as e:
            self.status_changed.emit(f"Không kết nối được: {e}")
            return

        self.status_changed.emit("Đã kết nối")

        #gửi tin đăng nhập
        self.send({"type": "login", "name": self.name})

        #vòn lặp nhận tin, mỗi vòng 1 dòng
        try:
            reader = self.sock.makefile("r", encoding="utf-8")
            for line in reader:
                self.handle(line)
        except (OSError, ValueError):
            pass  #socket đóng, thoát vòng lặp

        self.status_changed.emit("Đã ngắt kết nối")

    def handle(self, line):
        try:
            data = json.loads(line)
        except ValueError:
            return  #dòng hỏng thì bỏ qua

        kind = data.get("type")
        if kind == "msg":
            self.message_received.emit(data.get("from", "?"), data.get("text", ""))
        elif kind == "online":git 
        self.online_updated.emit(data.get("users", []))

    # Các hàm được gọi từ bên ngoài (giao diện / terminal)
    def send(self, data):
        if self.sock is None:
            return
        try:
            self.sock.sendall((json.dumps(data) + "\n").encode("utf-8"))
        except OSError:
            self.status_changed.emit("Gửi thất bại")

    def send_message(self, text):
        self.send({"type": "msg", "text": text})

    def stop(self):
        if self.sock is not None:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.sock.close()