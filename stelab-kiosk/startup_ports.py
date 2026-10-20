"""Check real port conflicts while allowing TCP TIME_WAIT after a kiosk restart."""
import argparse
import socket
import time


def available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(('127.0.0.1', port))
        except OSError:
            return False
    return True


def check_ports(ports: list[int], timeout: float = 10) -> list[int]:
    deadline = time.monotonic() + timeout
    while True:
        occupied = [port for port in set(ports) if not available(port)]
        if not occupied or time.monotonic() >= deadline:
            return occupied
        time.sleep(min(0.2, max(0, deadline - time.monotonic())))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('ports', type=int, nargs='+')
    args = parser.parse_args()
    occupied = check_ports(args.ports)
    if occupied:
        print(f'Ports still occupied: {occupied}. Check for another kiosk/service; none was stopped automatically.')
        raise SystemExit(1)
