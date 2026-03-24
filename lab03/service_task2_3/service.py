import os
import socket
import sys
import threading

def one_client(connect_socket):
    request = connect_socket.recv(1024).decode()
    if not request:
        connect_socket.close()
        return
    try:
        filename = request.split()[1].lstrip("/")
    except IndexError:
        connect_socket.close()
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
        error_response = "HTTP/1.1 404 Not Found\r\n\r\n"
        error_response += "Content-Type: text/html; charset=utf-8\r\n\r\n"
        error_response += "<html><body><h1>404 Not Found</h1></body></html>"
        connect_socket.sendall(error_response.encode())
    finally:
        connect_socket.close()

def start_server():
    if len(sys.argv) != 2:
        print("Usage: <server.exe> server_port")
        return
    port = int(sys.argv[1])
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", port))
    server_socket.listen(1)
    print(f"Server started on localhost:{port}")
    try:
        while(True):
            connect_socket, _ = server_socket.accept()
            thread = threading.Thread(target=one_client, args=(connect_socket,))
            thread.daemon = True
            thread.start()
    except:
        pass
    finally:
        server_socket.close()
    


if __name__ == "__main__":
    start_server()