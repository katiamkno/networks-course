import socket
import struct
import random
import os

TIMEOUT = 2.0
BUFFER_SIZE = 4096
PACKET_SIZE = 1024
TYPE_DATA = b'D'
TYPE_ACK = b'A'


def calculate_checksum(data):
    checksum = 0
    for byte in data:
        checksum ^= byte
    return checksum

def create_packet(packet_type, seq, data=b''):
    length = len(data)
    header = packet_type + bytes([seq]) + struct.pack('!H', length)
    checksum = calculate_checksum(header + data)
    full_header = header + struct.pack('!H', checksum)
    return full_header + data

def parse_packet(packet):
    if len(packet) < 6:
        return None, None, None, None
    packet_type = packet[0:1]
    seq = packet[1]
    length = struct.unpack('!H', packet[2:4])[0]
    checksum_received = struct.unpack('!H', packet[4:6])[0]
    data = packet[6:6 + length]

    expected_checksum = calculate_checksum(packet[0:4] + packet[6:6 + length])
    if checksum_received != expected_checksum:
        print(f"Checksum mismatch")
        return None, None, None, None
    return packet_type, seq, length, data

def receive_file(sock, output_filename):
    expected_seq = 0
    with open(output_filename, 'wb') as f:
        while True:
            try:
                packet, addr = sock.recvfrom(BUFFER_SIZE)
                if random.random() < 0.3:
                    print("[LOSS] Packet lost")
                    continue
                packet_type, seq, length, data = parse_packet(packet)
                if packet_type is None:
                    print("[ERROR] Invalid packet")
                    continue
                if packet_type == TYPE_DATA:
                    print(f"[RECV] DATA{seq}")
                    if seq == expected_seq:
                        ack_seq = seq
                    else:
                        ack_seq = 1 - expected_seq
                    ack_packet = create_packet(TYPE_ACK, ack_seq)
                    if random.random() < 0.3:
                        print(f"[LOSS] ACK{ack_seq}")
                    else:
                        sock.sendto(ack_packet, addr)
                        print(f"[SEND] ACK{ack_seq}")
                    if seq == expected_seq:
                        if length == 0:
                            print("End marker received")
                        f.write(data)
                        f.flush()
                        expected_seq = 1 - expected_seq
                    else:
                        print(f"Seq {seq}, expected {expected_seq}")

                elif packet_type == TYPE_ACK:
                    print(f"ACK{seq}")
            except KeyboardInterrupt:
                print("\nServer stopped")
                break
            except Exception as e:
                print(f"Error: {e}")


def send_file(filename = 'file_to_send.txt', host='127.0.0.1', port=12002, timeout=TIMEOUT):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(timeout)
    server_addr = (host, port)

    if not os.path.exists(filename):
        print(f"File '{filename}' not found")
        return
    with open(filename, 'rb') as f:
        file_data = f.read()

    packets = []
    for i in range(0, len(file_data), PACKET_SIZE):
        packets.append(file_data[i:i + PACKET_SIZE])
    packets.append(b'')
    total_packets = len(packets)

    seq = 0
    packet_index = 0

    while packet_index < total_packets:
        data = packets[packet_index]
        packet = create_packet(TYPE_DATA, seq, data)

        packet_acked = False
        attempt = 0

        while not packet_acked:
            attempt += 1
            if random.random() < 0.3:
                print(f"DATA{seq} lost during transmission (attempt {attempt})")
                continue
            client_socket.sendto(packet, server_addr)
            print(f"DATA{seq}, len={len(data)} bytes (attempt {attempt})")

            try:
                ack_packet, _ = client_socket.recvfrom(BUFFER_SIZE)
                if random.random() < 0.3:
                    print(f"ACK for DATA{seq} lost on receive (attempt {attempt})")
                    continue

                ack_type, ack_seq, _, _ = parse_packet(ack_packet)

                if ack_type == TYPE_ACK and ack_seq == seq:
                    print(f"ACK{ack_seq} - OK, (attempt {attempt})")
                    packet_acked = True
                else:
                    print(f"Wrong ACK{ack_seq}, expected ACK{seq}")

            except socket.timeout:
                print(f"[TIMEOUT] No ACK for DATA{seq} after {timeout}s (attempt {attempt})")
        seq = 1 - seq
        packet_index += 1
    client_socket.close()

if __name__ == "__main__":
    TIMEOUT = int(input("enter timeout in seconds: "))
    PACKET_SIZE = int(input("enter packet size in bytes: "))
    send_file()