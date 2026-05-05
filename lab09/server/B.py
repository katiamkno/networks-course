import socket
import sys


def is_port_free(ip, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        result = s.connect_ex((ip, port))
        return result != 0


def scan_ports(ip, start_port, end_port):
    for port in range(start_port, end_port + 1):
        if is_port_free(ip, port):
            print(f"Port {port} is free")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python scan.py <IP> <start_port> <end_port>")
        sys.exit(1)

    ip = sys.argv[1]
    start_port = int(sys.argv[2])
    end_port = int(sys.argv[3])

    scan_ports(ip, start_port, end_port)