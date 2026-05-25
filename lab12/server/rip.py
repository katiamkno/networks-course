import json
import random
import socket
import threading
import time

INFINITY = 16
UPDATE_INTERVAL = 2
print_lock = threading.Lock()

def random_ip():
    return ".".join(str(random.randint(1, 254)) for _ in range(4))


class Router:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.neighbors = {}
        self.routing_table = {}

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", port))

        self.lock = threading.Lock()

        self.routing_table[ip] = {
            "next_hop": ip,
            "metric": 0
        }

    def add_neighbor(self, neighbor_ip, cost):
        self.neighbors[neighbor_ip] = cost

        self.routing_table[neighbor_ip] = {
            "next_hop": neighbor_ip,
            "metric": cost
        }

    def serialize_table(self):
        return {
            dest: {
                "next_hop": info["next_hop"],
                "metric": info["metric"]
            }
            for dest, info in self.routing_table.items()
        }

    def send_updates(self, routers):
        while True:
            packet = {
                "source": self.ip,
                "table": self.serialize_table()
            }

            data = json.dumps(packet).encode()

            for neighbor_ip in self.neighbors:
                neighbor = routers[neighbor_ip]

                self.sock.sendto(
                    data,
                    ("127.0.0.1", neighbor.port)
                )

            time.sleep(UPDATE_INTERVAL)

    def receive_updates(self):
        while True:
            data, _ = self.sock.recvfrom(65535)
            packet = json.loads(data.decode())
            source_ip = packet["source"]
            received_table = packet["table"]

            with self.lock:
                for destination, info in received_table.items():
                    if destination == self.ip:
                        continue
                    new_metric = min(
                        INFINITY,
                        self.neighbors[source_ip] + info["metric"]
                    )

                    if (destination not in self.routing_table
                        or new_metric < self.routing_table[destination]["metric"]):
                        self.routing_table[destination] = {
                            "next_hop": source_ip,
                            "metric": new_metric
                        }

    def print_table(self, title="FINAL"):
        with self.lock:
            with print_lock:
                print(f"\n{title} STATE OF ROUTER {self.ip}")
                print(
                    f"{'[Source IP]':<18}"
                    f"{'[Destination IP]':<18}"
                    f"{'[Next Hop]':<18}"
                    f"{'[Metric]':<10}"
                )

                for destination, info in sorted(self.routing_table.items()):
                    print(
                        f"{self.ip:<18}"
                        f"{destination:<18}"
                        f"{info['next_hop']:<18}"
                        f"{info['metric']:<10}"
                    )


def generate_random_network(router_count=5):
    routers = {}

    base_port = 10000

    ips = [random_ip() for _ in range(router_count)]

    for i in range(router_count):
        routers[ips[i]] = Router(ips[i], base_port + i)
    for i in range(router_count - 1):
        cost = random.randint(1, 5)
        routers[ips[i]].add_neighbor(ips[i + 1], cost)
        routers[ips[i + 1]].add_neighbor(ips[i], cost)
    extra_edges = router_count

    for _ in range(extra_edges):
        a, b = random.sample(ips, 2)

        if b not in routers[a].neighbors:
            cost = random.randint(1, 5)

            routers[a].add_neighbor(b, cost)
            routers[b].add_neighbor(a, cost)

    return routers


def main():
    routers = generate_random_network(6)

    print("\n=== NETWORK TOPOLOGY ===\n")

    for router in routers.values():
        print(router.ip)

        for neighbor, cost in router.neighbors.items():
            print(f"  -> {neighbor} cost={cost}")

    threads = []

    for router in routers.values():
        t_recv = threading.Thread(
            target=router.receive_updates,
            daemon=True
        )
        t_send = threading.Thread(
            target=router.send_updates,
            args=(routers,),
            daemon=True
        )
        t_recv.start()
        t_send.start()
        threads.append(t_recv)
        threads.append(t_send)

    simulation_time = 15

    for step in range(simulation_time):
        print(f"\n================ STEP {step + 1} ================\n")

        for router in routers.values():
            router.print_table(f"SIMULATION STEP {step + 1}")

        time.sleep(1)

    print("\n================ FINAL TABLES ================\n")

    for router in routers.values():
        router.print_table()

    print("\nSimulation complete.\n")


if __name__ == "__main__":
    main()