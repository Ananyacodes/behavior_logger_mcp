from __future__ import annotations

import argparse
import json
import socket
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from behavior_system import DeviceRuntime


def send_json(host: str, port: int, payload: dict) -> dict:
    with socket.create_connection((host, port), timeout=5) as connection:
        connection.sendall((json.dumps(payload) + "\n").encode("utf-8"))
        return json.loads(connection.recv(65536).decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device-id", required=True)
    parser.add_argument("--secret", required=True)
    parser.add_argument("--coordinator-host", default="127.0.0.1")
    parser.add_argument("--coordinator-port", type=int, default=8765)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--window-seconds", type=int, default=60)
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    runtime = DeviceRuntime(device_id=args.device_id, shared_secret=args.secret)
    runtime.bootstrap(windows=12, seconds_per_window=30)

    register_response = send_json(
        args.coordinator_host,
        args.coordinator_port,
        {"command": "register", "device_id": args.device_id, "secret": args.secret},
    )
    print(f"Registered: {register_response}")

    if args.live:
        runtime.start_live_capture()

    try:
        for round_index in range(args.rounds):
            if args.simulate or not args.live:
                report = runtime.simulate_round(seconds=args.window_seconds, seed=round_index)
            else:
                time.sleep(args.window_seconds)
                report = runtime.generate_report(window_seconds=args.window_seconds)
            response = send_json(
                args.coordinator_host,
                args.coordinator_port,
                {"command": "report", "report": report.to_wire()},
            )
            print(
                json.dumps(
                    {
                        "round": round_index + 1,
                        "device_id": report.device_id,
                        "anomaly_score": report.proof.anomaly_score,
                        "accepted": response.get("accepted"),
                    }
                )
            )
    finally:
        if args.live:
            runtime.stop_live_capture()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())