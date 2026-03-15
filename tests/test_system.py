from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from behavior_system import DeviceCoordinator, DeviceRuntime, FeatureExtractor, ProofManager


def test_feature_extraction_and_digest() -> None:
    runtime = DeviceRuntime("test-device", "test-secret")
    runtime.collector.simulate_activity(30, seed=1)
    now = time.time()
    events = runtime.collector.recent_events(30, now=now)
    window = runtime.extractor.extract("test-device", events, 30, now)
    digest = runtime.extractor.digest(window)
    assert len(window.vector()) == len(FeatureExtractor.FEATURE_NAMES)
    assert len(digest) == 64


def test_proof_generation_and_verification() -> None:
    runtime = DeviceRuntime("test-device", "test-secret")
    runtime.bootstrap(windows=8, seconds_per_window=20)
    report = runtime.simulate_round(seconds=20, seed=2)
    manager = ProofManager("test-secret")
    assert manager.verify_proof(report.proof)


def test_coordinator_accepts_valid_report() -> None:
    coordinator = DeviceCoordinator()
    coordinator.register_device("test-device", "test-secret")
    runtime = DeviceRuntime("test-device", "test-secret")
    runtime.bootstrap(windows=8, seconds_per_window=20)
    report = runtime.simulate_round(seconds=20, seed=3)
    assert coordinator.receive_report(report) is True
    assert coordinator.summary()["accepted_reports"] == 1


def test_aggregate_model_has_expected_shape() -> None:
    coordinator = DeviceCoordinator()
    coordinator.register_device("a", "secret-a")
    coordinator.register_device("b", "secret-b")
    for device_id, secret, seed in [("a", "secret-a", 10), ("b", "secret-b", 20)]:
        runtime = DeviceRuntime(device_id, secret)
        runtime.bootstrap(windows=6, seconds_per_window=15)
        report = runtime.simulate_round(seconds=15, seed=seed)
        assert coordinator.receive_report(report)
    aggregate = coordinator.aggregate_model()
    assert len(aggregate) == 32


def test_coordinator_rejects_tampered_report() -> None:
    coordinator = DeviceCoordinator()
    coordinator.register_device("test-device", "test-secret")
    runtime = DeviceRuntime("test-device", "test-secret")
    runtime.bootstrap(windows=8, seconds_per_window=20)
    report = runtime.simulate_round(seconds=20, seed=4)
    report.proof.commitment = "0" * len(report.proof.commitment)
    assert coordinator.receive_report(report) is False
    assert coordinator.summary()["accepted_reports"] == 0


def test_coordinator_state_persistence(tmp_path: Path) -> None:
    state_file = tmp_path / "coordinator_state.json"
    coordinator = DeviceCoordinator(state_path=state_file)
    coordinator.register_device("a", "secret-a")

    runtime = DeviceRuntime("a", "secret-a")
    runtime.bootstrap(windows=6, seconds_per_window=15)
    report = runtime.simulate_round(seconds=15, seed=5)
    assert coordinator.receive_report(report)

    restored = DeviceCoordinator(state_path=state_file)
    summary = restored.summary()
    assert summary["accepted_reports"] == 1
    assert "a" in summary["devices"]