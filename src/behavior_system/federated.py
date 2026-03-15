from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import threading

from .crypto import ProofManager
from .schemas import DeviceReport


class DeviceCoordinator:
    def __init__(self, state_path: str | Path | None = None) -> None:
        self._lock = threading.Lock()
        self._state_path = Path(state_path) if state_path else None
        self._shared_secrets: dict[str, str] = {}
        self._proof_managers: dict[str, ProofManager] = {}
        self._reports: list[DeviceReport] = []
        self._updates: dict[str, list[list[float]]] = defaultdict(list)
        if self._state_path and self._state_path.exists():
            self.load_state(self._state_path)

    def register_device(self, device_id: str, shared_secret: str) -> None:
        with self._lock:
            self._shared_secrets[device_id] = shared_secret
            self._proof_managers[device_id] = ProofManager(shared_secret)
            self._persist_locked()

    def receive_report(self, report: DeviceReport) -> bool:
        with self._lock:
            manager = self._proof_managers.get(report.device_id)
            if manager is None:
                return False
            if not manager.verify_proof(report.proof):
                return False
            self._reports.append(report)
            if report.model_update:
                self._updates[report.device_id].append(report.model_update)
            self._persist_locked()
            return True

    def aggregate_model(self) -> list[float]:
        with self._lock:
            all_updates = [update for updates in self._updates.values() for update in updates]
            if not all_updates:
                return []
            width = min(len(update) for update in all_updates)
            totals = [0.0] * width
            for update in all_updates:
                for index in range(width):
                    totals[index] += float(update[index])
            return [round(value / len(all_updates), 6) for value in totals]

    def summary(self) -> dict[str, object]:
        with self._lock:
            accepted = len(self._reports)
            devices = sorted(self._proof_managers.keys())
            latest_scores: dict[str, float] = {}
            reports_by_device: dict[str, int] = defaultdict(int)
            for report in self._reports:
                latest_scores[report.device_id] = report.proof.anomaly_score
                reports_by_device[report.device_id] += 1
            aggregated = self._aggregate_model_locked()
            return {
                "accepted_reports": accepted,
                "registered_devices": len(devices),
                "devices": devices,
                "latest_scores": latest_scores,
                "reports_by_device": dict(reports_by_device),
                "aggregated_update_size": len(aggregated),
            }

    def save_state(self, path: str | Path | None = None) -> None:
        with self._lock:
            target = Path(path) if path else self._state_path
            if target is None:
                return
            target.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "shared_secrets": self._shared_secrets,
                "reports": [report.to_wire() for report in self._reports],
                "updates": self._updates,
            }
            target.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def load_state(self, path: str | Path | None = None) -> None:
        target = Path(path) if path else self._state_path
        if target is None or not target.exists():
            return
        payload = json.loads(target.read_text(encoding="utf-8"))
        with self._lock:
            self._shared_secrets = dict(payload.get("shared_secrets", {}))
            self._proof_managers = {
                device_id: ProofManager(secret)
                for device_id, secret in self._shared_secrets.items()
            }
            self._reports = [
                DeviceReport.from_wire(item) for item in payload.get("reports", [])
            ]
            updates_raw = payload.get("updates", {})
            self._updates = defaultdict(list)
            for device_id, updates in updates_raw.items():
                self._updates[device_id] = [list(update) for update in updates]

    def _persist_locked(self) -> None:
        if self._state_path is None:
            return
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "shared_secrets": self._shared_secrets,
            "reports": [report.to_wire() for report in self._reports],
            "updates": self._updates,
        }
        self._state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _aggregate_model_locked(self) -> list[float]:
        all_updates = [update for updates in self._updates.values() for update in updates]
        if not all_updates:
            return []
        width = min(len(update) for update in all_updates)
        totals = [0.0] * width
        for update in all_updates:
            for index in range(width):
                totals[index] += float(update[index])
        return [round(value / len(all_updates), 6) for value in totals]