import os
import socket
import sys


def start_client():
    if len(sys.argv) != 4:
        print("Usage: <client.exe> server_host server_port filename")
        return
    host = sys.argv[1]
    port = int(sys.argv[2])
    filename = sys.argv[3]
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    if not filename.startswith('/'):
        filename = '/' + filename

    try:
        client_socket.connect((host, port))
        print(f"Server started on {host}:{port}")

        request = f"GET {filename} HTTP/1.1\r\n"
        request += f"Host: {host}\r\n"
        request += "Connection: close\r\n"
        request += "\r\n"
        client_socket.sendall(request.encode())
        response = b""
        while True:
            data = client_socket.recv(4096)
            if not data:
                break
            response += data
        print("Server's reply")
        print(response.decode())

    except ConnectionRefusedError:
        print("Can't connect to server")
    except Exception as e:
        print(f"Error {e}")
    finally:
        client_socket.close()


if __name__ == "__main__":
    start_client()