import socket
import random


def run_server(host='127.0.0.1', port=12000):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    print(f"Run on {host}:{port}")

    while True:
        try:
            message, client_address = server_socket.recvfrom(2048)
            if random.random() < 0.2:
                print(f"Lost sth from {client_address}")
                continue
            response = message.upper()
            server_socket.sendto(response, client_address)
            print(f"{client_address}: {message.decode()} -> {response.decode()}")

        except KeyboardInterrupt:
            print("\nStop")
            break
        except Exception as e:
            print(f"Error {e}")


if __name__ == "__main__":
    run_server()