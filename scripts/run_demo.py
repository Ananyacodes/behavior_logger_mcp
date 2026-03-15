from __future__ import annotations

import json
import socket
import socketserver
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from behavior_system import DeviceRuntime
from coordinator_server import COORDINATOR, CoordinatorHandler, ThreadedTCPServer


def send_json(host: str, port: int, payload: dict) -> dict:
    with socket.create_connection((host, port), timeout=5) as connection:
        connection.sendall((json.dumps(payload) + "\n").encode("utf-8"))
        return json.loads(connection.recv(65536).decode("utf-8"))


def main() -> int:
    host, port = "127.0.0.1", 8876
    with ThreadedTCPServer((host, port), CoordinatorHandler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        devices = [
            ("laptop-a", "demo-shared-secret-a"),
            ("laptop-b", "demo-shared-secret-b"),
        ]

        for device_id, secret in devices:
            send_json(host, port, {"command": "register", "device_id": device_id, "secret": secret})

        for index, (device_id, secret) in enumerate(devices):
            runtime = DeviceRuntime(device_id=device_id, shared_secret=secret)
            runtime.bootstrap(windows=10, seconds_per_window=30)
            for round_index in range(2):
                report = runtime.simulate_round(seconds=45, seed=index * 10 + round_index)
                send_json(host, port, {"command": "report", "report": report.to_wire()})

        summary = send_json(host, port, {"command": "summary"})
        print(json.dumps(summary["summary"], indent=2))
        server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())