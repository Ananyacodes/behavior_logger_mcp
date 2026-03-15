from __future__ import annotations

import argparse
import json
import socketserver
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from behavior_system import DeviceCoordinator, DeviceReport


COORDINATOR = DeviceCoordinator()


class CoordinatorHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        try:
            raw = self.rfile.readline().decode("utf-8").strip()
            if not raw:
                return
            request = json.loads(raw)
            command = request.get("command")

            if command == "register":
                COORDINATOR.register_device(request["device_id"], request["secret"])
                response = {"status": "ok", "registered": request["device_id"]}
            elif command == "report":
                report = DeviceReport.from_wire(request["report"])
                accepted = COORDINATOR.receive_report(report)
                response = {"status": "ok" if accepted else "rejected", "accepted": accepted}
            elif command == "summary":
                response = {"status": "ok", "summary": COORDINATOR.summary()}
            elif command == "save":
                COORDINATOR.save_state()
                response = {"status": "ok", "saved": True}
            elif command == "health":
                response = {"status": "ok", "service": "coordinator", "ready": True}
            else:
                response = {"status": "error", "message": f"unknown command: {command}"}
        except json.JSONDecodeError as error:
            response = {"status": "error", "message": f"invalid json: {error}"}
        except KeyError as error:
            response = {"status": "error", "message": f"missing field: {error}"}
        except Exception as error:
            response = {"status": "error", "message": f"internal error: {error}"}

        self.wfile.write((json.dumps(response) + "\n").encode("utf-8"))


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True


def main() -> int:
    global COORDINATOR
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--state-file",
        default=str(ROOT / "data" / "coordinator_state.json"),
        help="Path to a JSON file where coordinator state is persisted.",
    )
    args = parser.parse_args()
    COORDINATOR = DeviceCoordinator(state_path=args.state_file)

    with ThreadedTCPServer((args.host, args.port), CoordinatorHandler) as server:
        print(f"Coordinator listening on {args.host}:{args.port} (state: {args.state_file})")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            COORDINATOR.save_state()
            print("Coordinator stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())