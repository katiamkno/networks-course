from collections import defaultdict
import socket

try:
    from scapy.all import sniff, IP, TCP, UDP
except ImportError:
    import os
    os.system("pip install scapy")
    from scapy.all import sniff, IP, TCP, UDP


def format_bytes(n):
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def get_local_ips():
    ips = set()
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None):
            ips.add(info[4][0])
    except Exception:
        pass
    ips.add("127.0.0.1")
    return ips


local_ips = get_local_ips()
rx = defaultdict(int)
tx = defaultdict(int)


def handle_packet(pkt):
    if IP not in pkt:
        return
    size = len(pkt)
    src = pkt[IP].src
    dst = pkt[IP].dst

    if TCP in pkt:
        sport, dport = pkt[TCP].sport, pkt[TCP].dport
    elif UDP in pkt:
        sport, dport = pkt[UDP].sport, pkt[UDP].dport
    else:
        return

    if dst in local_ips:
        rx[dport] += size
    elif src in local_ips:
        tx[dport] += size


try:
    duration = int(input("Monitoring duration (seconds) [default: 10]: ") or "10")
except ValueError:
    print("Invalid input. Using default: 10 seconds")
    duration = 10
print(f"\n Monitoring for {duration} seconds...")
sniff(timeout=duration, prn=handle_packet, store=False)

all_ports = set(rx) | set(tx)
rows = sorted(all_ports, key=lambda p: rx[p] + tx[p], reverse=True)

print(f"{'PORT':<8} {'RX (incoming)':<18} {'TX (outgoing)':<18} {'TOTAL'}")
print("-" * 70)
for port in rows:
    total = rx[port] + tx[port]
    print(f"{port:<8}{format_bytes(rx[port]):<18} {format_bytes(tx[port]):<18} {format_bytes(total)}")

print("-" * 70)
total_rx = sum(rx.values())
total_tx = sum(tx.values())
print(
    f"{'TOTAL':<8} {'':<14} {format_bytes(total_rx):<18} {format_bytes(total_tx):<18} {format_bytes(total_rx + total_tx)}")
