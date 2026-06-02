import time
import psutil


def format_bytes(bytes_val):
    if bytes_val < 0:
        bytes_val = 0
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"


def main():
    try:
        duration = int(input("Monitoring duration (seconds) [default: 10]: ") or "10")
    except ValueError:
        print("Invalid input. Using default: 10 seconds")
        duration = 10

    old_stats = psutil.net_io_counters()
    old_rx = old_stats.bytes_recv
    old_tx = old_stats.bytes_sent

    print(f"\n Monitoring for {duration} seconds...")

    start_time = time.time()
    total_rx = 0
    total_tx = 0

    for i in range(duration):
            time.sleep(1)
            stats = psutil.net_io_counters()

            rx_diff = stats.bytes_recv - old_rx
            tx_diff = stats.bytes_sent - old_tx

            total_rx += rx_diff
            total_tx += tx_diff

            print(
                f"[{i + 1:2d}/{duration}s] ↓ RX: {format_bytes(rx_diff):>10}/s  |  ↑ TX: {format_bytes(tx_diff):>10}/s")

            old_rx = stats.bytes_recv
            old_tx = stats.bytes_sent


    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print(f"Time monitored:    {time.time() - start_time:.1f} seconds")
    print(f"Received (RX):     {format_bytes(total_rx)}")
    print(f"Sent (TX):         {format_bytes(total_tx)}")


if __name__ == "__main__":
    main()
