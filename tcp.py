"""TCP port scanner functions for ai-cli."""
import socket
import concurrent.futures
from typing import List, Tuple

def scan_port(host: str, port: int, timeout: float = 1.0) -> Tuple[int, bool]:
    """Return (port, True) if open, else (port, False)."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return port, True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return port, False

def tcp_scan(
    host: str,
    ports: List[int],
    timeout: float = 1.0,
    max_workers: int = 100
) -> List[int]:
    """Scan a list of ports using threads. Returns sorted list of open ports."""
    open_ports = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_port = {
            executor.submit(scan_port, host, port, timeout): port
            for port in ports
        }
        for future in concurrent.futures.as_completed(future_to_port):
            port, is_open = future.result()
            if is_open:
                open_ports.append(port)
    return sorted(open_ports)

def parse_ports(port_spec: str) -> List[int]:
    """Parse port specification like '80', '1-1024', '80,443,8080-8100'."""
    ports = []
    for part in port_spec.split(","):
        part = part.strip()
        if "-" in part:
            start, end = map(int, part.split("-"))
            if start > end or start < 1 or end > 65535:
                raise ValueError(f"Invalid port range: {part}")
            ports.extend(range(start, end + 1))
        else:
            port = int(part)
            if not 1 <= port <= 65535:
                raise ValueError(f"Port out of range: {port}")
            ports.append(port)
    return sorted(set(ports))
