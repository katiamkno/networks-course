import os
import socket
import sys
import threading

def one_client(connect_socket, semaphore):
    try:
        request = connect_socket.recv(1024).decode()
        if not request:
            return
        try:
            parts = request.split()
            if len(parts) < 2:
                return
            filename = parts[1].lstrip("/")
        except IndexError:
            return

        try:
            if not filename:
                raise FileNotFoundError

            with open(filename, 'rb') as f:
                content = f.read()

            header = "HTTP/1.1 200 OK\r\n"
            header += "Content-Type: text/html; charset=utf-8\r\n"
            header += f"Content-Length: {len(content)}\r\n"
            header += "Connection: close\r\n\r\n"

            connect_socket.sendall(header.encode('utf-8'))
            connect_socket.sendall(content)
            print("Sended content:", content)

        except FileNotFoundError:
            error_response = "HTTP/1.1 404 Not Found\r\n"
            error_response += "Content-Type: text/html; charset=utf-8\r\n\r\n"
            error_response += "<html><body><h1>404 Not Found</h1></body></html>"
            connect_socket.sendall(error_response.encode())

    except Exception as e:
        print(f"error {e}")
    finally:
        connect_socket.close()
        semaphore.release()


def start_server():
    if len(sys.argv) != 3:
        print("Usage: python server.py <port> <concurrency_level>")
        return

    port = int(sys.argv[1])
    concurrency_level = int(sys.argv[2])
    semaphore = threading.Semaphore(concurrency_level)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", port))
    server_socket.listen(5)

    print(f"Server started on localhost:{port}")

    try:
        while True:
            connect_socket, addr = server_socket.accept()
            semaphore.acquire()
            thread = threading.Thread(target=one_client, args=(connect_socket, semaphore))
            thread.daemon = True
            thread.start()
    except:
        pass
    finally:
        server_socket.close()


if __name__ == "__main__":
    start_server()