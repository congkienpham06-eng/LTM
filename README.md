# Chat TCP - [Mã đề tài: điền sau]

Ứng dụng chat Client–Server qua TCP, toàn bộ thao tác qua GUI, hỗ trợ reply, forward, avatar và emoji.

**Video demo:** [điền link YouTube Public/Unlisted ở đây]

## Thành viên nhóm

| MSSV | Họ tên | Vai trò |
|---|---|---|
| | | |
| | | |

## Kiến trúc

- Mô hình **Client–Server** qua TCP socket thuần (module `socket` của Python, không dùng framework web).
- Mỗi Client là 1 tiến trình GUI riêng (PySide6); Server là 1 tiến trình nền, mỗi Client kết nối được xử lý trên 1 thread riêng.
- Giao thức ứng dụng tự định nghĩa, đóng khung bằng 4 byte độ dài + payload JSON (xem chi tiết bên dưới).
- GUI chạy mạng trên `QThread` riêng, không block giao diện khi chờ dữ liệu.

## Giao thức (Protocol)

- Framing: `[4 byte length (big-endian)][JSON payload UTF-8]`.
- Loại message: `LOGIN, ACK, ERROR, TEXT, REPLY, FORWARD, PING, PONG, DISCONNECT, USER_JOINED, USER_LEFT`.
- Cấu trúc message: xem `Code/Shared/protocol.py` (hàm `make_message`, `validate_message`).
- Quy trình: Client connect TCP → gửi `LOGIN` (username + avatar base64) → Server validate → trả `ACK` (kèm danh sách contact đang online) hoặc `ERROR` → sau đó trao đổi `TEXT/REPLY/FORWARD`; Server gửi `PING` định kỳ nếu Client im lặng quá lâu, Client phải trả `PONG`; kết thúc bằng `DISCONNECT` chủ động hoặc Server tự phát hiện khi socket đóng/timeout.

## Yêu cầu môi trường

- Python 3.10+ (đã test với Python 3.13).
- Cài thư viện: `pip install -r Code/requirements.txt` (chỉ cần `PySide6`).

## Cấu hình

- **Server**: IP/port cấu hình qua tham số dòng lệnh, không hard-code:
  ```
  python Code/Server/server.py --host 0.0.0.0 --port 5555
  ```
- **Client**: nhập Server IP/Port ngay trên màn hình kết nối của GUI (không hard-code).

## Hướng dẫn chạy

1. Cài thư viện: `pip install -r Code/requirements.txt`
2. Chạy Server (1 cửa sổ terminal):
   ```
   python Code/Server/server.py
   ```
3. Chạy Client (mở nhiều terminal/process khác nhau để test nhiều người dùng):
   ```
   python Code/Client/main.py
   ```
4. Trên màn hình kết nối của mỗi Client: nhập Server IP (`127.0.0.1` nếu cùng máy, hoặc IP LAN của máy chạy Server nếu khác máy), Port, Tên hiển thị, có thể chọn ảnh đại diện → bấm **Kết nối**.
5. Dùng chuột phải trên 1 tin nhắn để **Reply** hoặc **Forward**; nút 😊 để mở bảng chọn emoji.

### Chạy thử nhiều Client cùng lúc (demo 2 tiến trình trở lên)

Có thể chạy toàn bộ trên 1 máy (2 process Client riêng, đúng yêu cầu "nếu chạy cùng máy vẫn phải là 2 tiến trình riêng") hoặc trên 2 máy khác nhau cùng mạng LAN (nhập IP LAN của máy chạy Server, nhớ cho phép Server qua Windows Firewall ở lần chạy đầu tiên).

## Kiểm thử

- Script test tải: `python Extra/stress_test.py --host 127.0.0.1 --port 5555 --clients 10 --duration 15` (chạy với 2 mức `--clients` khác nhau để lấy số liệu throughput/tỷ lệ lỗi).
- Log Server: `Code/Server/server.log` (không commit — đã có trong `.gitignore`).
- Kết quả kiểm thử, ảnh/video minh chứng: lưu trong `Extra/`.

## Hạn chế / phạm vi không thực hiện

- [Điền các giới hạn thực tế của sản phẩm trước khi nộp, ví dụ: chưa hỗ trợ gửi file, chưa mã hoá đường truyền (chưa dùng TLS), chưa lưu lịch sử chat khi server restart, v.v.]
