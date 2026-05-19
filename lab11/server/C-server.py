import socket

HOST = '::1'
PORT = 12345

def to_upper_server():
    server_sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen()
    print(f"Server on [{HOST}]:{PORT}")

    try:
        while True:
            conn, addr = server_sock.accept()
            with conn:
                print(f"Added client: {addr}")
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    message = data.decode('utf-8')
                    print(f"Received: {message}")
                    response = message.upper()
                    conn.sendall(response.encode('utf-8'))
                    print(f"Sent: {response}")
                print(f"Client {addr} off")
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    finally:
        server_sock.close()
        print("Server socket closed")

if __name__ == '__main__':
    to_upper_server()