import socket

HOST = ''
PORT = 8989


def start_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((HOST, PORT))

    print(f"Client listening on port {PORT}")

    try:
        while True:
            data, addr = sock.recvfrom(1024)
            message = data.decode('utf-8')
            print(f"[RECV from {addr}] {message}")
    except KeyboardInterrupt:
        print("\nClient stopped")
    finally:
        sock.close()


if __name__ == "__main__":
    start_client()