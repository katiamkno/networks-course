import socket

SERVER_HOST = '::1'
SERVER_PORT = 12345

def run_client():
    with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as client_sock:
        client_sock.connect((SERVER_HOST, SERVER_PORT))
        print("Enter messages (empty string - exit):")
        while True:
            message = input("> ")
            if message == "":
                break
            client_sock.sendall(message.encode('utf-8'))
            data = client_sock.recv(1024)
            print(f"Answer: {data.decode('utf-8')}")

if __name__ == '__main__':
    run_client()