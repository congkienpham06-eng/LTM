"""Script do tai: spawn N client gia lap gui tin nhan lien tuc toi Server qua TCP that.

Vi du chay 2 muc tai de lam performance test theo yeu cau do an:
    python stress_test.py --host 127.0.0.1 --port 5555 --clients 10 --duration 15
    python stress_test.py --host 127.0.0.1 --port 5555 --clients 50 --duration 15
"""
import argparse
import os
import socket
import sys
import threading
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "Code"))
from Shared.protocol import MSG_ACK, MSG_LOGIN, MSG_TEXT, make_message, recv_message, send_message

results_lock = threading.Lock()
results = {"sent": 0, "errors": 0}


def fake_client(index, host, port, duration):
    username = f"loadtest_{index}_{int(time.time() * 1000) % 100000}"
    try:
        sock = socket.create_connection((host, port), timeout=5)
        sock.settimeout(5)
        send_message(sock, make_message(MSG_LOGIN, sender=username, content=""))
        resp = recv_message(sock)
        if resp is None or resp.get("type") != MSG_ACK:
            with results_lock:
                results["errors"] += 1
            return

        end_time = time.time() + duration
        while time.time() < end_time:
            msg = make_message(MSG_TEXT, sender=username, to="all", content=f"hello from {username}")
            send_message(sock, msg)
            with results_lock:
                results["sent"] += 1
            time.sleep(0.2)

        sock.close()
    except Exception:
        with results_lock:
            results["errors"] += 1


def main():
    parser = argparse.ArgumentParser(description="Stress/performance test cho Chat Server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5555)
    parser.add_argument("--clients", type=int, default=10)
    parser.add_argument("--duration", type=int, default=10)
    args = parser.parse_args()

    threads = []
    start = time.time()
    for i in range(args.clients):
        t = threading.Thread(target=fake_client, args=(i, args.host, args.port, args.duration))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    elapsed = time.time() - start

    print(f"So client gia lap     : {args.clients}")
    print(f"Thoi gian chay        : {elapsed:.2f}s")
    print(f"Tong message da gui   : {results['sent']}")
    print(f"Throughput            : {results['sent'] / elapsed:.2f} message/giay")
    print(f"So loi (ket noi/gui)  : {results['errors']}")


if __name__ == "__main__":
    main()
