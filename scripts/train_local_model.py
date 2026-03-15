from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from behavior_system import DeviceRuntime


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device-id", default="trainer-device")
    parser.add_argument("--secret", default="demo-shared-secret")
    parser.add_argument("--output", default=str(ROOT / "data" / "device_model.pt"))
    args = parser.parse_args()

    runtime = DeviceRuntime(device_id=args.device_id, shared_secret=args.secret)
    runtime.bootstrap(windows=40, seconds_per_window=45)
    runtime.save_model(args.output)
    print(f"Saved model to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())