"""Xu ly 1 client: moi client chay tren 1 thread rieng, loi o client nay
khong duoc lam anh huong client khac hay lam sap Server."""
import logging
import socket
import threading

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Shared.protocol import (
    send_message, recv_message, make_message, validate_message, ProtocolError,
    MSG_LOGIN, MSG_ACK, MSG_ERROR, MSG_PONG, MSG_DISCONNECT,
    MSG_USER_JOINED, MSG_USER_LEFT, CONTENT_TYPES,
)
from Shared.config import HEARTBEAT_TIMEOUT, HEARTBEAT_GRACE

logger = logging.getLogger("ChatServer")


class ServerState:
    def __init__(self):
        self.lock = threading.Lock()
        self.clients = {}  # username -> {"sock": socket, "avatar": base64 str}

    def add_client(self, username, sock, avatar):
        with self.lock:
            self.clients[username] = {"sock": sock, "avatar": avatar}

    def remove_client(self, username):
        with self.lock:
            self.clients.pop(username, None)

    def get_socket(self, username):
        with self.lock:
            entry = self.clients.get(username)
            return entry["sock"] if entry else None

    def contacts_snapshot(self):
        with self.lock:
            return {u: c["avatar"] for u, c in self.clients.items()}


def _safe_send(sock, message, label="?"):
    try:
        send_message(sock, message)
        return True
    except (OSError, ProtocolError) as e:
        logger.warning("Khong gui duoc toi %s: %s", label, e)
        return False


def broadcast(state, message, exclude_username=None):
    with state.lock:
        targets = [(u, c["sock"]) for u, c in state.clients.items() if u != exclude_username]
    for username, sock in targets:
        _safe_send(sock, message, username)


def handle_client(conn, addr, state):
    username = None
    registered = False
    conn.settimeout(HEARTBEAT_TIMEOUT)
    try:
        login_msg = recv_message(conn)
        if login_msg is None:
            logger.info("Dia chi %s ngat ket noi truoc khi login", addr)
            return

        ok, err = validate_message(login_msg)
        if ok and login_msg.get("type") != MSG_LOGIN:
            ok, err = False, "Yeu cau dau tien sau khi ket noi phai la LOGIN"

        username = login_msg.get("from", "").strip() if ok else None
        avatar = login_msg.get("content", "") if ok else None

        if ok:
            with state.lock:
                if username in state.clients:
                    ok, err = False, f"Username '{username}' da duoc su dung"

        if not ok:
            _safe_send(conn, make_message(MSG_ERROR, sender="server", content=err))
            logger.info("Login that bai tu %s: %s", addr, err)
            return

        contacts = state.contacts_snapshot()
        state.add_client(username, conn, avatar)
        registered = True
        logger.info("Client '%s' (%s) da dang nhap", username, addr)

        _safe_send(conn, make_message(
            MSG_ACK, sender="server", to=username, content="Dang nhap thanh cong",
            extra={"contacts": contacts},
        ), username)

        broadcast(state, make_message(
            MSG_USER_JOINED, sender=username, to="all", content=username,
            extra={"avatar": avatar},
        ), exclude_username=username)

        missed_heartbeats = 0
        while True:
            try:
                msg = recv_message(conn)
            except socket.timeout:
                missed_heartbeats += 1
                if missed_heartbeats * HEARTBEAT_TIMEOUT >= HEARTBEAT_GRACE:
                    logger.info("Client '%s' khong phan hoi qua %ss, ngat ket noi", username, HEARTBEAT_GRACE)
                    break
                _safe_send(conn, make_message(MSG_PING, sender="server", to=username), username)
                continue
            except (OSError, ProtocolError) as e:
                logger.info("Loi doc du lieu tu '%s': %s", username, e)
                break

            if msg is None:
                logger.info("Client '%s' da dong ket noi", username)
                break

            missed_heartbeats = 0
            ok, err = validate_message(msg)
            if not ok:
                _safe_send(conn, make_message(MSG_ERROR, sender="server", to=username, content=err), username)
                logger.warning("Du lieu khong hop le tu '%s': %s", username, err)
                continue

            msg_type = msg.get("type")

            if msg_type == MSG_DISCONNECT:
                logger.info("Client '%s' chu dong ngat ket noi", username)
                break

            elif msg_type == MSG_PONG:
                continue

            elif msg_type in CONTENT_TYPES:
                msg["from"] = username  # khong cho client gia mao nguoi gui khac
                target = msg.get("to")
                if target == "all":
                    broadcast(state, msg, exclude_username=username)
                    logger.info("'%s' -> all [%s]", username, msg_type)
                else:
                    target_sock = state.get_socket(target)
                    if target_sock is None:
                        _safe_send(conn, make_message(
                            MSG_ERROR, sender="server", to=username,
                            content=f"Nguoi dung '{target}' khong online",
                        ), username)
                        logger.info("'%s' -> '%s' [%s] that bai: nguoi nhan khong online", username, target, msg_type)
                    else:
                        _safe_send(target_sock, msg, target)
                        logger.info("'%s' -> '%s' [%s]", username, target, msg_type)
            else:
                _safe_send(conn, make_message(
                    MSG_ERROR, sender="server", to=username,
                    content=f"Server chua ho tro loai message '{msg_type}'",
                ), username)

    except Exception:
        logger.exception("Loi khong mong muon voi client %s (%s)", addr, username)
    finally:
        if registered:
            state.remove_client(username)
            broadcast(state, make_message(MSG_USER_LEFT, sender=username, to="all", content=username))
            logger.info("Da don dep tai nguyen cho '%s'", username)
        try:
            conn.close()
        except OSError:
            pass
