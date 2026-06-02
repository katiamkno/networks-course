import socket
import struct
import os
import sys
import time
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed


def checksum(data):
    if len(data) % 2:
        data += b'\x00'
    s = 0
    for i in range(0, len(data), 2):
        s += (data[i] << 8) + data[i + 1]
    s = (s >> 16) + (s & 0xffff)
    s += s >> 16
    return ~s & 0xffff


def icmp_ping(ip_str, timeout=1.0):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        sock.settimeout(timeout)
        pid = os.getpid() & 0xffff
        header = struct.pack('!BBHHH', 8, 0, 0, pid, 1)
        payload = b'scan'
        chk = checksum(header + payload)
        packet = struct.pack('!BBHHH', 8, 0, chk, pid, 1) + payload
        sock.sendto(packet, (ip_str, 0))
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                raw, addr = sock.recvfrom(1024)
                if addr[0] == ip_str:
                    sock.close()
                    return True
            except socket.timeout:
                break
        sock.close()
    except Exception:
        pass
    return False

def get_ifaces():
    import subprocess
    ifaces = {}
    try:
        out = subprocess.check_output('ipconfig /all', shell=True, encoding='cp866', errors='replace')
        current_name = None
        current = {}
        for line in out.splitlines():
            if line and not line.startswith(' '):
                if current_name and current.get('ip'):
                    ifaces[current_name] = current
                current_name = line.strip().rstrip(':')
                current = {}
            line = line.strip()
            if 'IPv4' in line and ':' in line:
                import re
                ip = line.split(':', 1)[1].strip()
                ip = re.sub(r'\(.*?\)', '', ip).strip()
                current['ip'] = ip
            if ('Subnet Mask' in line or 'Маска' in line) and ':' in line:
                current['mask'] = line.split(':', 1)[1].strip()
            if ('Physical Address' in line or 'Физический адрес' in line) and ':' in line:
                mac = line.split(':', 1)[1].strip().replace('-', ':').upper()
                current['mac'] = mac
        if current_name and current.get('ip'):
            ifaces[current_name] = current
    except Exception as e:
        print(f"ipconfig error: {e}")
    for name in ifaces:
        ifaces[name].setdefault('mask', '255.255.255.0')
        ifaces[name].setdefault('mac', '??:??:??:??:??:??')
    return ifaces


def get_mac_arp(ip):
    if sys.platform == 'win32':
        try:
            import subprocess
            out = subprocess.check_output(f'arp -a {ip}', shell=True,
                                          encoding='cp866', errors='replace')
            for line in out.splitlines():
                if ip in line:
                    parts = line.split()
                    for p in parts:
                        if '-' in p and len(p) == 17:
                            return p.replace('-', ':').upper()
        except Exception:
            pass
    else:
        try:
            with open('/proc/net/arp') as f:
                for line in f.readlines()[1:]:
                    parts = line.split()
                    if parts[0] == ip and parts[2] == '0x2':
                        return parts[3].upper()
        except Exception:
            pass
    return '??:??:??:??:??:??'


def get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return ip


def scan_host(ip_str):
    if icmp_ping(ip_str):
        return {
            'ip': ip_str,
            'mac': get_mac_arp(ip_str),
            'hostname': get_hostname(ip_str),
        }
    return None


def main():
    ifaces = get_ifaces()
    if not ifaces:
        print("Нет доступных интерфейсов.")
        sys.exit(1)

    iface_list = list(ifaces.items())
    print("Интерфейсы:")
    for i, (name, info) in enumerate(iface_list):
        print(f"  [{i}] {name}  IP: {info['ip']}  Маска: {info['mask']}  MAC: {info['mac']}")

    choice = input("Выберите интерфейс [0]: ").strip()
    idx = int(choice) if choice.isdigit() and int(choice) < len(iface_list) else 0
    iface_name, local = iface_list[idx]

    network = ipaddress.IPv4Network(f"{local['ip']}/{local['mask']}", strict=False)
    print(f"\nСканирование {network} ...\n")

    local_entry = {
        'ip': local['ip'],
        'mac': local['mac'],
        'hostname': socket.gethostname(),
    }

    hosts_to_scan = [str(h) for h in network.hosts() if str(h) != local['ip']]
    total = len(hosts_to_scan)
    found = []

    with ThreadPoolExecutor(max_workers=64) as executor:
        futures = {executor.submit(scan_host, ip): ip for ip in hosts_to_scan}
        done = 0
        for future in as_completed(futures):
            done += 1
            print(f"\r  Проверено: {done}/{total}", end='', flush=True)
            result = future.result()
            if result:
                found.append(result)

    found.sort(key=lambda h: ipaddress.IPv4Address(h['ip']))

    print(f"\n\n{'IP-адрес':<18} {'MAC-адрес':<20} Имя хоста")
    print('-' * 65)
    print(f"{local_entry['ip']:<18} {local_entry['mac']:<20} {local_entry['hostname']}  (этот компьютер)")
    for h in found:
        print(f"{h['ip']:<18} {h['mac']:<20} {h['hostname']}")
    print(f"\nНайдено хостов: {len(found) + 1}")


if __name__ == '__main__':
    main()