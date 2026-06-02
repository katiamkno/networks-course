import struct
import random

POLYNOMIAL = 0x1021
CRC_INIT = 0xFFFF


def crc16(data: bytes) -> int:
    crc = CRC_INIT
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ POLYNOMIAL
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc


PACKET_DATA_SIZE = 5


def make_packet(index: int, payload: bytes) -> bytes:
    padded = payload.ljust(PACKET_DATA_SIZE, b'\x00')
    header = bytes([index & 0xFF])
    body = header + padded
    checksum = crc16(body)
    return body + struct.pack('>H', checksum)


def parse_packet(packet: bytes):
    index = packet[0]
    payload = packet[1:1 + PACKET_DATA_SIZE]
    stored_crc = struct.unpack('>H', packet[-2:])[0]
    computed_crc = crc16(packet[:-2])
    ok = stored_crc == computed_crc
    return index, payload, stored_crc, computed_crc, ok


def corrupt_packet(packet: bytes, bit_positions: list[int]) -> bytes:
    data = bytearray(packet)
    for bit_pos in bit_positions:
        byte_idx = 1 + bit_pos // 8
        bit_idx = 7 - (bit_pos % 8)
        if byte_idx < len(data) - 2:
            data[byte_idx] ^= (1 << bit_idx)
    return bytes(data)


def generate_random_errors(num_packets: int, error_rate: float = 0.3) -> dict:
    errors = {}
    for i in range(num_packets):
        if random.random() < error_rate:
            num_bits = random.choice([1, 2, 3])
            bit_positions = random.sample(range(40), num_bits)
            errors[i] = bit_positions
    return errors


def main():
    text = ("CRC-16 packet integrity check demonstration. Some packets will be corrupted.")

    random.seed(42)

    raw = text.encode('utf-8')
    chunks = [raw[i:i + PACKET_DATA_SIZE] for i in range(0, len(raw), PACKET_DATA_SIZE)]

    errors = generate_random_errors(len(chunks), error_rate=0.25)

    packets_info = []
    for idx, chunk in enumerate(chunks):
        pkt = make_packet(idx, chunk)
        corrupt_bits = errors.get(idx)
        if corrupt_bits:
            sent = corrupt_packet(pkt, corrupt_bits)
            packets_info.append((pkt, sent, True, corrupt_bits))
        else:
            packets_info.append((pkt, pkt, False, None))

    print(f"TEXT: {text}")
    print(f"TOTAL PACKETS: {len(chunks)}")
    print(f"ERRORS IN PACKETS: {sorted(errors.keys())}")
    print("=" * 70)

    errors_found = 0
    for idx, (orig, sent, corrupted, bits) in enumerate(packets_info):
        _, payload, stored_crc, computed_crc, ok = parse_packet(sent)

        raw_text = payload.rstrip(b'\x00')
        try:
            text_repr = raw_text.decode('utf-8')[:25]
        except:
            text_repr = str(raw_text)[:25]

        status = "OK" if ok else "ERROR"
        if not ok:
            errors_found += 1

        print(f"\nPACKET #{idx:02d} | {status}")
        print(f"  Data: \"{text_repr}\"")
        print(f"  CRC: stored=0x{stored_crc:04X} | computed=0x{computed_crc:04X}")
        if bits:
            print(f"  Corrupted bits: {sorted(bits)}")
    print()
    print(f"RESULT: {errors_found} errors detected out of {len(errors)} injected")
    print(f"STATUS: {'ALL ERRORS DETECTED' if errors_found == len(errors) else 'SOME ERRORS MISSED'}")


if __name__ == '__main__':
    main()