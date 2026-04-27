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


def verify_checksum(data: bytes, checksum: int) -> bool:
    total = 0
    n = len(data)
    i = 0

    while i + 1 < n:
        word = (data[i] << 8) | data[i + 1]
        total += word
        total = (total & 0xFFFF) + (total >> 16)
        i += 2

    if i < n:
        word = data[i] << 8
        total += word
        total = (total & 0xFFFF) + (total >> 16)

    total += checksum
    total = (total & 0xFFFF) + (total >> 16)

    return total == 0xFFFF

def run_tests():
    data1 = bytes([0x12, 0x34, 0x56, 0x78])
    checksum1 = compute_checksum(data1)
    print("Test 1 (correct):",
          "OK" if verify_checksum(data1, checksum1) else "FAIL")

    data2 = bytearray(data1)
    data2[1] ^= 0x01
    print("Test 2 (bit error):",
          "OK" if not verify_checksum(data2, checksum1) else "FAIL")

    data3 = bytes([0xAA, 0xBB, 0xCC])
    checksum3 = compute_checksum(data3)
    print("Test 3 (correct - odd length):",
          "OK" if verify_checksum(data3, checksum3) else "FAIL")


if __name__ == "__main__":
    run_tests()