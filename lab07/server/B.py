import socket
import time


def run_client(host='127.0.0.1', port=12000, timeout=1, count=10):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(timeout)

    for seq in range(1, count + 1):
        send_time = time.time()
        message = f"Ping {seq} {send_time}"

        try:
            client_socket.sendto(message.encode(), (host, port))
            response, server_address = client_socket.recvfrom(2048)
            recv_time = time.time()

            rtt = recv_time - send_time
            print(f"Answer from {server_address}: {response.decode()}, RTT = {rtt:.6f} с")

        except socket.timeout:
            print("Request timed out")
        except Exception as e:
            print(f"{seq}: error - {e}")

    client_socket.close()


if __name__ == "__main__":
    run_client()