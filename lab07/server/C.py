import socket
import time


def run_client_advanced(host='127.0.0.1', port=12000, timeout=1, count=10):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(timeout)

    rtt_list = []
    lost = 0

    for seq in range(1, count + 1):
        send_time = time.time()
        message = f"Ping {seq} {send_time}"

        try:
            client_socket.sendto(message.encode(), (host, port))
            response, server_address = client_socket.recvfrom(2048)
            recv_time = time.time()

            rtt = recv_time - send_time
            rtt_list.append(rtt)
            print(f"{len(response)} bytes from {server_address[0]}: seq={seq} time={rtt * 1000:.3f} ms")

        except socket.timeout:
            lost += 1
            print("Request timed out")

    client_socket.close()

    print("\n--- Ping statistics ---")

    if rtt_list:
        rtt_min = min(rtt_list)
        rtt_max = max(rtt_list)
        rtt_avg = sum(rtt_list) / len(rtt_list)
        print(f"min/avg/max = {rtt_min * 1000:.3f}/{rtt_avg * 1000:.3f}/{rtt_max * 1000:.3f} ms")
    else:
        print("No successful responses")

    sent = count
    received = count - lost
    loss_percent = (lost / sent) * 100
    print(f"{sent} packets transmitted, {received} packets received, {loss_percent:.1f}% packet loss")


if __name__ == "__main__":
    run_client_advanced()