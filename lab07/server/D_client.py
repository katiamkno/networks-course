import socket
import time
import threading

running = True
heartbeat_seq = 0

def send_heartbeat(sock, server_address, interval=2):
    global running, heartbeat_seq
    while running:
        heartbeat_seq += 1
        send_time = time.time()
        message = f"Hi {heartbeat_seq} {send_time}"
        try:
            sock.sendto(message.encode(), server_address)
            print(f"Sent {send_time} to {server_address}")
        except Exception as e:
            print(f"error - {e}")
        time.sleep(interval)


def run_client(host='127.0.0.1', port=12001, ping_count=10, ping_timeout=1, heartbeat_interval=2):
    global running

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(ping_timeout)
    server_address = (host, port)
    heartbeat_thread = threading.Thread(target=send_heartbeat, args=(client_socket, server_address, heartbeat_interval),
                                        daemon=True)
    heartbeat_thread.start()
    print(f"Heartbeat runs")

    time.sleep(1)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Client stopped")
        running = False
        client_socket.close()


if __name__ == "__main__":
    run_client()