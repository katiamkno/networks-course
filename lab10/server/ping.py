import socket
import struct
import time
import select
import sys
import os
import statistics

ICMP_ECHO_REQUEST = 8
ICMP_ECHO_REPLY   = 0
TIMEOUT           = 1.0

ICMP_UNREACHABLE_CODES = {
    0: "Network unreachable",
    1: "Host unreachable",
    2: "Protocol unreachable",
    3: "Port unreachable",
    4: "Fragmentation needed",
    5: "Source route failed",
    6: "Destination network unknown",
    7: "Destination host unknown",
    9: "Network administratively prohibited",
    10: "Host administratively prohibited",
    11: "Network unreachable for ToS",
    12: "Host unreachable for ToS",
    13: "Communication administratively prohibited",
}

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
    data   = struct.pack("!d", time.time()) + b"PingData"
    csum   = compute_checksum(header + data)
    header = struct.pack("!BBHHH", ICMP_ECHO_REQUEST, 0, csum, pid, seq)
    return header + data

def parse_reply(packet, pid):
    icmp_header = packet[20:28]
    icmp_type, icmp_code, _, recv_pid, recv_seq = struct.unpack("!BBHHH", icmp_header)

    if icmp_type == ICMP_ECHO_REPLY and recv_pid == pid:
        send_time = struct.unpack("!d", packet[ihl + 8: ihl + 16])[0]
        return ("reply", recv_seq, send_time, icmp_type, icmp_code)

    if icmp_type == 3:
        return ("unreachable", 0, None, icmp_type, icmp_code)

    if icmp_type == 11:
        return ("timeout_ttl", 0, None, icmp_type, icmp_code)

    return ("other", 0, None, icmp_type, icmp_code)

def ping(host, count=10):
    try:
        dest = socket.gethostbyname(host)
    except socket.gaierror as e:
        print(f"Cannot resolve {host}: {e}")
        sys.exit(1)

    pid  = os.getpid() & 0xFFFF
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    sock.settimeout(TIMEOUT)

    print(f"PING {host} ({dest})")

    rtts     = []
    sent     = 0
    received = 0

    try:
        for seq in range(1, count + 1):
            packet = build_packet(seq, pid)
            send_time = time.time()
            sock.sendto(packet, (dest, 0))
            sent += 1

            deadline = send_time + TIMEOUT
            got_reply = False

            while True:
                now  = time.time()
                left = deadline - now
                if left <= 0:
                    break

                ready = select.select([sock], [], [], left)
                if not ready[0]:
                    break

                raw, addr = sock.recvfrom(1024)
                result    = parse_reply(raw, pid)
                kind      = result[0]

                if kind == "reply":
                    _, recv_seq, send_ts, _, _ = result
                    if recv_seq != seq:
                        continue
                    rtt = (time.time() - send_ts) * 1000
                    rtts.append(rtt)
                    received += 1
                    got_reply = True
                    print(f"bytes from {addr[0]}: icmp_seq={seq} ttl=64 time={rtt:.3f} ms"
                          f"  |  min={min(rtts):.3f} max={max(rtts):.3f} "
                          f"avg={sum(rtts)/len(rtts):.3f} ms  "
                          f"loss={100*(sent-received)/sent:.1f}%")
                    break

                elif kind == "unreachable":
                    _, _, _, icmp_type, icmp_code = result
                    desc = ICMP_UNREACHABLE_CODES.get(icmp_code, f"code {icmp_code}")
                    print(f"From {addr[0]}: Destination Unreachable — {desc}")
                    got_reply = True
                    break

                elif kind == "timeout_ttl":
                    print(f"From {addr[0]}: Time Exceeded (TTL expired in transit)")
                    got_reply = True
                    break

                else:
                    _, _, _, icmp_type, icmp_code = result
                    print(f"From {addr[0]}: ICMP type={icmp_type} code={icmp_code}")
                    got_reply = True
                    break

            if not got_reply:
                loss = 100 * (sent - received) / sent
                print(f"Request timeout for icmp_seq={seq}  |  loss={loss:.1f}%")

            elapsed = time.time() - send_time
            if elapsed < 1.0:
                time.sleep(1.0 - elapsed)

    except KeyboardInterrupt:
        pass
    finally:
        sock.close()

    print(f"\n--- {host} ping statistics ---")
    print(f"{sent} packets transmitted, {received} received, "
          f"{100*(sent-received)/sent:.1f}% packet loss")
    if rtts:
        print(f"rtt min/avg/max/stddev = "
              f"{min(rtts):.3f}/{sum(rtts)/len(rtts):.3f}/"
              f"{max(rtts):.3f}/{statistics.stdev(rtts) if len(rtts)>1 else 0:.3f} ms")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: sudo python3 {sys.argv[0]} <host> [count]")
        sys.exit(1)
    host  = sys.argv[1]
    count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    ping(host, count)