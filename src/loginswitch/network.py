from __future__ import annotations

import socket


def tcp_check(server: str, timeout_sec: float = 1.0) -> bool:
    host, _, port = server.partition(":")
    if not port.isdigit():
        return False
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout_sec)
        return s.connect_ex((host, int(port))) == 0
