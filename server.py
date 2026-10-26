"""Entry point cua Chat Server. Chay: python server.py [--host 0.0.0.0] [--port 5555]"""
import logging
import os
import socket
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Shared.config import parse_server_args
from client_handler import ServerState, handle_client


def setup_logging():
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main():
    setup_logging()
    logger = logging.getLogger("ChatServer")
    args = parse_server_args()

    state = ServerState()

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((args.host, args.port))
    server_sock.listen(50)
    logger.info("Chat server dang lang nghe tai %s:%s", args.host, args.port)

    try:
        while True:
            conn, addr = server_sock.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr, state), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        logger.info("Dang tat server (Ctrl+C)...")
    finally:
        server_sock.close()


if __name__ == "__main__":
    main()
