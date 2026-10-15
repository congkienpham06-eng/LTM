"""Giao thuc chung giua Server va Client: dinh dang message va framing qua TCP.

TCP la giao thuc stream (khong co khai niem "1 goi tin"), nen moi message duoc
dong khung bang 4 byte do dai (big-endian) + payload JSON UTF-8, de ben nhan biet
chinh xac can doc bao nhieu byte cho 1 message hoan chinh.
"""
import json
import struct
import time
import uuid

HEADER_SIZE = 4
MAX_MESSAGE_SIZE = 5 * 1024 * 1024  # gioi han 5MB / message (avatar base64 tinh luon)

MSG_LOGIN = "LOGIN"
MSG_ACK = "ACK"
MSG_ERROR = "ERROR"
MSG_TEXT = "TEXT"
MSG_REPLY = "REPLY"
MSG_FORWARD = "FORWARD"
MSG_PING = "PING"
MSG_PONG = "PONG"
MSG_DISCONNECT = "DISCONNECT"
MSG_USER_JOINED = "USER_JOINED"
MSG_USER_LEFT = "USER_LEFT"

ALL_TYPES = {
    MSG_LOGIN, MSG_ACK, MSG_ERROR, MSG_TEXT, MSG_REPLY, MSG_FORWARD,
    MSG_PING, MSG_PONG, MSG_DISCONNECT, MSG_USER_JOINED, MSG_USER_LEFT,
}

CONTENT_TYPES = {MSG_TEXT, MSG_REPLY, MSG_FORWARD}

MAX_USERNAME_LEN = 32
MAX_CONTENT_LEN = 10_000
MAX_AVATAR_LEN = 2_000_000


class ProtocolError(Exception):
    pass


def make_message(msg_type, sender="", to="", content="", reply_to=None,
                  forward_from=None, extra=None):
    msg = {
        "type": msg_type,
        "msg_id": str(uuid.uuid4()),
        "from": sender,
        "to": to,
        "timestamp": time.time(),
        "content": content,
        "reply_to": reply_to,
        "forward_from": forward_from,
    }
    if extra:
        msg.update(extra)
    return msg


def _recv_exact(sock, n):
    chunks = []
    remaining = n
    while remaining > 0:
        chunk = sock.recv(remaining)
        if chunk == b"":
            return None
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def send_message(sock, message):
    payload = json.dumps(message, ensure_ascii=False).encode("utf-8")
    if len(payload) > MAX_MESSAGE_SIZE:
        raise ProtocolError("Message vuot qua kich thuoc toi da cho phep")
    header = struct.pack("!I", len(payload))
    sock.sendall(header + payload)


def recv_message(sock):
    """Tra ve dict message, hoac None neu peer dong ket noi binh thuong.
    Nem socket.timeout / OSError neu mat ket noi bat thuong, ProtocolError neu du lieu sai dinh dang.
    """
    header = _recv_exact(sock, HEADER_SIZE)
    if header is None:
        return None
    (length,) = struct.unpack("!I", header)
    if length > MAX_MESSAGE_SIZE:
        raise ProtocolError("Kich thuoc message khai bao vuot gioi han cho phep")
    payload = _recv_exact(sock, length)
    if payload is None:
        return None
    try:
        return json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ProtocolError(f"Du lieu JSON khong hop le: {e}")


def validate_message(message):
    """Tra ve (True, "") neu hop le, (False, ly_do) neu khong hop le."""
    if not isinstance(message, dict):
        return False, "Message phai la JSON object"

    msg_type = message.get("type")
    if msg_type not in ALL_TYPES:
        return False, f"Loai message khong hop le: {msg_type!r}"

    if not isinstance(message.get("from", ""), str):
        return False, "Truong 'from' phai la chuoi"

    if msg_type == MSG_LOGIN:
        username = message.get("from", "").strip()
        if not username:
            return False, "Username khong duoc rong"
        if len(username) > MAX_USERNAME_LEN:
            return False, f"Username qua dai (toi da {MAX_USERNAME_LEN} ky tu)"
        avatar = message.get("content", "")
        if avatar and len(avatar) > MAX_AVATAR_LEN:
            return False, "Du lieu avatar qua lon"

    elif msg_type in CONTENT_TYPES:
        if not message.get("to"):
            return False, "Thieu truong 'to' (nguoi nhan)"
        content = message.get("content", "")
        if not isinstance(content, str) or not content.strip():
            return False, "Noi dung tin nhan khong duoc rong"
        if len(content) > MAX_CONTENT_LEN:
            return False, f"Noi dung tin nhan qua dai (toi da {MAX_CONTENT_LEN} ky tu)"
        if msg_type == MSG_REPLY and not message.get("reply_to"):
            return False, "Tin nhan REPLY phai co 'reply_to'"
        if msg_type == MSG_FORWARD and not message.get("forward_from"):
            return False, "Tin nhan FORWARD phai co 'forward_from'"

    return True, ""
