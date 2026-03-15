from __future__ import annotations

import time
from pathlib import Path

from .collector import BehaviorCollector
from .crypto import ProofManager
from .features import FeatureExtractor
from .neural import NeuralAnomalyDetector
from .schemas import DeviceReport


class DeviceRuntime:
    def __init__(self, device_id: str, shared_secret: str, model_path: str | None = None) -> None:
        self.device_id = device_id
        self.collector = BehaviorCollector()
        self.extractor = FeatureExtractor()
        self.detector = NeuralAnomalyDetector(len(self.extractor.FEATURE_NAMES), model_path=model_path)
        self.proofs = ProofManager(shared_secret)

    def bootstrap(self, windows: int = 30, seconds_per_window: int = 60) -> None:
        samples: list[list[float]] = []
        for seed in range(windows):
            self.collector.simulate_activity(seconds_per_window, seed=seed)
            now = time.time()
            recent = self.collector.recent_events(seconds_per_window, now=now)
            window = self.extractor.extract(self.device_id, recent, seconds_per_window, now)
            samples.append(window.vector())
        self.detector.fit(samples)

    def generate_report(self, window_seconds: int = 60) -> DeviceReport:
        now = time.time()
        self.collector.collect_system_snapshot(now)
        events = self.collector.recent_events(window_seconds, now=now)
        window = self.extractor.extract(self.device_id, events, window_seconds, now)
        feature_digest = self.extractor.digest(window)
        anomaly_score = self.detector.score(window.vector())
        model_update = self.detector.export_update()
        model_digest = self.detector.model_digest()
        proof = self.proofs.build_proof(
            device_id=self.device_id,
            window=window,
            feature_digest=feature_digest,
            anomaly_score=anomaly_score,
            model_digest=model_digest,
        )
        return DeviceReport(
            device_id=self.device_id,
            timestamp=now,
            proof=proof,
            model_update=model_update,
            metadata={
                "event_count": window.event_count,
                "window_seconds": window_seconds,
            },
        )

    def simulate_round(self, seconds: int = 60, seed: int | None = None) -> DeviceReport:
        self.collector.simulate_activity(seconds, seed=seed)
        return self.generate_report(window_seconds=seconds)

    def start_live_capture(self) -> None:
        self.collector.start_live_capture()

    def stop_live_capture(self) -> None:
        self.collector.stop_live_capture()

    def save_model(self, path: str | Path) -> None:
        self.detector.save(path)