from __future__ import annotations

import hashlib
import hmac
import os

from .schemas import FeatureWindow, PrivacyProof


class ProofManager:
    def __init__(self, shared_secret: str) -> None:
        self._secret = shared_secret.encode("utf-8")

    def build_proof(
        self,
        device_id: str,
        window: FeatureWindow,
        feature_digest: str,
        anomaly_score: float,
        model_digest: str,
    ) -> PrivacyProof:
        nonce = os.urandom(16).hex()
        commitment = self._commit(
            device_id=device_id,
            timestamp=window.timestamp,
            window_seconds=window.window_seconds,
            feature_digest=feature_digest,
            anomaly_score=anomaly_score,
            model_digest=model_digest,
            nonce=nonce,
        )
        return PrivacyProof(
            device_id=device_id,
            timestamp=window.timestamp,
            window_seconds=window.window_seconds,
            feature_digest=feature_digest,
            anomaly_score=round(float(anomaly_score), 6),
            model_digest=model_digest,
            nonce=nonce,
            commitment=commitment,
        )

    def verify_proof(self, proof: PrivacyProof) -> bool:
        expected = self._commit(
            device_id=proof.device_id,
            timestamp=proof.timestamp,
            window_seconds=proof.window_seconds,
            feature_digest=proof.feature_digest,
            anomaly_score=proof.anomaly_score,
            model_digest=proof.model_digest,
            nonce=proof.nonce,
        )
        return hmac.compare_digest(expected, proof.commitment)

    def _commit(
        self,
        device_id: str,
        timestamp: float,
        window_seconds: int,
        feature_digest: str,
        anomaly_score: float,
        model_digest: str,
        nonce: str,
    ) -> str:
        message = "|".join(
            [
                device_id,
                f"{timestamp:.6f}",
                str(window_seconds),
                feature_digest,
                f"{anomaly_score:.6f}",
                model_digest,
                nonce,
            ]
        ).encode("utf-8")
        return hmac.new(self._secret, message, hashlib.sha256).hexdigest()

    @staticmethod
    def digest_model_update(model_update: list[float]) -> str:
        payload = ",".join(f"{value:.6f}" for value in model_update).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()