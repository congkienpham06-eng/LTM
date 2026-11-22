"""Lop bao boc socket client, chay tren QThread rieng de khong treo GUI khi cho mang."""
import os
import socket
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Shared.protocol import (
    MSG_DISCONNECT, MSG_ERROR, MSG_LOGIN, MSG_PING, MSG_PONG,
    ProtocolError, make_message, recv_message, send_message,
)

from PySide6.QtCore import QThread, Signal

CONNECT_TIMEOUT = 8
RECV_TIMEOUT = 30
MAX_MISSED_BEFORE_ERROR = 3


class ClientThread(QThread):
    status_changed = Signal(str, str)       # state: connecting/connected/error/disconnected
    login_result = Signal(bool, str, dict)  # success, error_message, contacts
    message_received = Signal(dict)

    def __init__(self, host, port, username, avatar_b64):
        super().__init__()
        self.host = host
        self.port = port
        self.username = username
        self.avatar_b64 = avatar_b64
        self.sock = None
        self._running = False
        self._send_lock = threading.Lock()

    def run(self):
        try:
            self.status_changed.emit("connecting", "")
            self.sock = socket.create_connection((self.host, self.port), timeout=CONNECT_TIMEOUT)
            self.sock.settimeout(RECV_TIMEOUT)

            send_message(self.sock, make_message(MSG_LOGIN, sender=self.username, content=self.avatar_b64))
            resp = recv_message(self.sock)

            if resp is None:
                self.login_result.emit(False, "Server dong ket noi trong luc dang nhap", {})
                return
            if resp.get("type") == MSG_ERROR:
                self.login_result.emit(False, resp.get("content", "Dang nhap that bai"), {})
                return

            self._running = True
            contacts = resp.get("contacts", {})
            self.login_result.emit(True, "", contacts)
            self.status_changed.emit("connected", "")

            missed = 0
            while self._running:
                try:
                    msg = recv_message(self.sock)
                except socket.timeout:
                    missed += 1
                    if missed >= MAX_MISSED_BEFORE_ERROR:
                        self.status_changed.emit("error", "Mat ket noi toi server (timeout)")
                        break
                    continue
                except (OSError, ProtocolError) as e:
                    self.status_changed.emit("error", str(e))
                    break

                if msg is None:
                    self.status_changed.emit("disconnected", "Server da dong ket noi")
                    break

                missed = 0
                if msg.get("type") == MSG_PING:
                    try:
                        self.send(make_message(MSG_PONG, sender=self.username, to="server"))
                    except Exception:
                        break
                    continue

                self.message_received.emit(msg)
        except (ConnectionRefusedError, socket.timeout, socket.gaierror, OSError) as e:
            self.login_result.emit(False, f"Khong the ket noi: {e}", {})
            self.status_changed.emit("error", str(e))
        except ProtocolError as e:
            self.status_changed.emit("error", f"Loi giao thuc: {e}")
        finally:
            self._running = False
            if self.sock:
                try:
                    self.sock.close()
                except OSError:
                    pass

    def send(self, message):
        if not self.sock:
            raise ConnectionError("Chua ket noi toi server")
        with self._send_lock:
            send_message(self.sock, message)

    def stop(self):
        self._running = False
        try:
            if self.sock:
                with self._send_lock:
                    send_message(self.sock, make_message(MSG_DISCONNECT, sender=self.username, to="server"))
        except Exception:
            pass
        try:
            if self.sock:
                self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass