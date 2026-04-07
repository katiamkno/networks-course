import socket
import sys

HOST = '127.0.0.1'
PORT = 8999

def send_command(command):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))
        client_socket.sendall(command.encode('utf-8'))
        response = client_socket.recv(4096).decode('utf-8')
        return response

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python client.py <command>")
        sys.exit(1)

    command = ' '.join(sys.argv[1:])
    print(f"Sending command: {command}")
    result = send_command(command)
    print(result)