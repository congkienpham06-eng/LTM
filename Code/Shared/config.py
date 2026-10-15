"""Cau hinh mang: khong hard-code IP/port, cho phep override qua tham so dong lenh."""
import argparse

DEFAULT_HOST = "0.0.0.0"       # Server lang nghe tren tat ca network interface
DEFAULT_PORT = 5555
DEFAULT_CLIENT_HOST = "127.0.0.1"  # gia tri goi y san tren GUI, nguoi dung co the sua

HEARTBEAT_TIMEOUT = 60   # giay khong nhan duoc gi tu client -> Server gui PING tham do
HEARTBEAT_GRACE = 90     # tong so giay khong nhan duoc gi (ke ca sau khi PING) -> coi la mat ket noi


def parse_server_args():
    parser = argparse.ArgumentParser(description="Chat TCP Server")
    parser.add_argument("--host", default=DEFAULT_HOST,
                         help="Dia chi IP server lang nghe (mac dinh 0.0.0.0 - moi interface)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                         help="Port server lang nghe")
    return parser.parse_args()
