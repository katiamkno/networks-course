import socket
import struct
import time
import select
import sys
import os

ICMP_ECHO_REQUEST = 8
ICMP_ECHO_REPLY   = 0
TIMEOUT           = 1.0
ICMP_TIME_EXCEEDED = 11

def compute_checksum(data):
    i = 0
    total = 0
    n = len(data)
    while i + 1 < n:
        word = (data[i] << 8) | data[i + 1]
        total += word
        total = (total & 0xFFFF) + (total >> 16)
        i += 2

    if i < n:
        word = data[i] << 8
        total += word
        total = (total & 0xFFFF) + (total >> 16)
    return (~total) & 0xFFFF


def build_packet(seq, pid):
    header = struct.pack("!BBHHH", ICMP_ECHO_REQUEST, 0, 0, pid, seq)
    data   = struct.pack("!d", time.time()) + b"TraceData"
    csum   = compute_checksum(header + data)
    header = struct.pack("!BBHHH", ICMP_ECHO_REQUEST, 0, csum, pid, seq)
    return header + data

def parse_reply(packet, pid):
    if len(packet) < 28:
        return None
    icmp_header = packet[20:28]
    icmp_type, icmp_code, _, recv_pid, recv_seq = struct.unpack("!BBHHH", icmp_header)

    if icmp_type == ICMP_ECHO_REPLY and recv_pid == pid:
        if len(packet) < 36:
            return None
        send_time = struct.unpack("!d", packet[28 : 36])[0]
        return ("reply", recv_seq, send_time, icmp_type, icmp_code)

    if icmp_type == ICMP_TIME_EXCEEDED:
        if len(packet) < 56:
            return None
        inner_icmp = packet[48 : 56]
        _, _, _, inner_pid, inner_seq = struct.unpack("!BBHHH", inner_icmp)
        if inner_pid == pid:
            return ("time_exceeded", inner_seq, None, icmp_type, icmp_code)
    return None

def traceroute(host, probes=3, max_ttl=30, timeout=TIMEOUT, resolve=True):
    try:
        dest_ip = socket.gethostbyname(host)
    except socket.gaierror as e:
        print(f"Cannot resolve {host}: {e}")
        sys.exit(1)

    pid = os.getpid() & 0xFFFF
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    sock.settimeout(timeout)

    print(f"traceroute to {host} ({dest_ip}), {max_ttl} hops max, {probes} probes per hop")

    for ttl in range(1, max_ttl + 1):
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
        print(f"{ttl:2d}  ", end='', flush=True)
        responses = []

        for probe in range(probes):
            seq = ttl * 100 + probe
            packet = build_packet(seq, pid)
            send_time = time.time()
            try:
                sock.sendto(packet, (dest_ip, 0))
            except socket.error as e:
                print(f"Send error: {e}")
                continue
            got_response = False
            while True:
                remaining = timeout - (time.time() - send_time)
                if remaining <= 0:
                    break
                ready = select.select([sock], [], [], remaining)
                if not ready[0]:
                    break
                try:
                    raw, addr = sock.recvfrom(1024)
                except socket.timeout:
                    break
                recv_time = time.time()

                result = parse_reply(raw, pid)
                if result is None:
                    continue
                kind, recv_seq, send_ts, icmp_type, icmp_code = result
                if kind == "reply":
                    rtt = (recv_time - send_ts) * 1000
                    responses.append((addr[0], rtt))
                    got_response = True
                elif kind == "time_exceeded" and recv_seq == seq:
                    rtt = (recv_time - send_time) * 1000
                    responses.append((addr[0], rtt))
                    got_response = True
                    break

            if not got_response:
                responses.append(None)
        unique_ips = []
        for r in responses:
            if r is not None and r[0] not in [ip for ip, _ in unique_ips]:
                unique_ips.append(r)

        if not unique_ips:
            print("* * *")
        else:
            for ip, first_rtt in unique_ips:
                rtts = [r[1] for r in responses if r is not None and r[0] == ip]
                times_str = "  ".join(f"{v:.3f} ms" for v in rtts)
                if resolve:
                    try:
                        name = socket.gethostbyaddr(ip)[0]
                    except socket.herror:
                        name = ip
                else:
                    name = ip
                print(f"{name} ({ip})  {times_str}")

        if any(r is not None and r[0] == dest_ip for r in responses):
            break
    sock.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: sudo python3 {sys.argv[0]} <host> [-q probes] [-m max_ttl] [-w timeout] [-n]")
        sys.exit(1)

    host = sys.argv[1]
    probes = 3
    max_ttl = 30
    timeout = TIMEOUT
    resolve = True

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "-q" and i + 1 < len(args):
            probes = int(args[i + 1])
            i += 2
        elif args[i] == "-m" and i + 1 < len(args):
            max_ttl = int(args[i + 1])
            i += 2
        elif args[i] == "-w" and i + 1 < len(args):
            timeout = float(args[i + 1])
            i += 2
        elif args[i] == "-n":
            resolve = False
            i += 1
        else:
            i += 1

    traceroute(host, probes, max_ttl, timeout, resolve)