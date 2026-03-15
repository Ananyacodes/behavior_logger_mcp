from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class BehaviorEvent:
    event_type: str
    timestamp: float
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FeatureWindow:
    device_id: str
    timestamp: float
    window_seconds: int
    feature_names: list[str]
    feature_values: list[float]
    event_count: int

    def vector(self) -> list[float]:
        return self.feature_values

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PrivacyProof:
    device_id: str
    timestamp: float
    window_seconds: int
    feature_digest: str
    anomaly_score: float
    model_digest: str
    nonce: str
    commitment: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DeviceReport:
    device_id: str
    timestamp: float
    proof: PrivacyProof
    model_update: list[float] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_wire(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["proof"] = self.proof.to_dict()
        return payload

    @classmethod
    def from_wire(cls, payload: dict[str, Any]) -> "DeviceReport":
        proof = PrivacyProof(**payload["proof"])
        return cls(
            device_id=payload["device_id"],
            timestamp=payload["timestamp"],
            proof=proof,
            model_update=list(payload.get("model_update", [])),
            metadata=dict(payload.get("metadata", {})),
        )