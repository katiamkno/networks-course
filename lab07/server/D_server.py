import socket
import random
import time
import threading
from collections import defaultdict

last_seen = defaultdict(float)

def monitor_clients(heartbeat_timeout=5):
    while True:
        time.sleep(2)
        current_time = time.time()
        for client_addr, last_time in list(last_seen.items()):
            if current_time - last_time > heartbeat_timeout:
                print(f"client {client_addr} stopped")


def run_server(host='127.0.0.1', port=12001, heartbeat_timeout=5):
    monitor_thread = threading.Thread(target=monitor_clients, args=(heartbeat_timeout,), daemon=True)
    monitor_thread.start()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    print(f"Run on {host}:{port}")

    while True:
        try:
            message, client_address = server_socket.recvfrom(2048)
            receive_time = time.time()
            last_seen[client_address] = receive_time
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

    server_socket.close()


if __name__ == "__main__":
    run_server()