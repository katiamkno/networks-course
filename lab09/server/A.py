import psutil

for interface, addrs in psutil.net_if_addrs().items():
    for addr in addrs:
        if addr.family == 2:
            print(f"Interface: {interface}")
            print(f"IP Address: {addr.address}")
            print(f"Netmask: {addr.netmask}")
            print()