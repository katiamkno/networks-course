import socket
import time
import datetime

HOST = ''
PORT = 8989
BROADCAST_ADDR = '<broadcast>'


def start_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    print(f"Broadcast server started on port {PORT}")

    try:
        while True:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"Server time: {current_time}"

            sock.sendto(message.encode('utf-8'), (BROADCAST_ADDR, PORT))
            print(f"[SENT] {message}")

            time.sleep(1)
    except KeyboardInterrupt:
        print("\nServer stopped")
    finally:
        sock.close()


if __name__ == "__main__":
    start_server()