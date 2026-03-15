from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import torch
from torch import nn


class Autoencoder(nn.Module):
    def __init__(self, input_dim: int) -> None:
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(8, 16),
            nn.ReLU(),
            nn.Linear(16, input_dim),
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        encoded = self.encoder(inputs)
        return self.decoder(encoded)


class NeuralAnomalyDetector:
    def __init__(self, input_dim: int, model_path: str | None = None) -> None:
        self.input_dim = input_dim
        self.model = Autoencoder(input_dim)
        self.model_path = Path(model_path) if model_path else None
        self.mean = np.zeros(input_dim, dtype=np.float32)
        self.std = np.ones(input_dim, dtype=np.float32)
        self.trained = False
        if self.model_path and self.model_path.exists():
            self.load(self.model_path)

    def fit(self, windows: list[list[float]], epochs: int = 40, lr: float = 1e-3) -> None:
        matrix = np.asarray(windows, dtype=np.float32)
        if matrix.ndim != 2 or matrix.shape[1] != self.input_dim:
            raise ValueError("Training windows must match detector input dimension")
        self.mean = matrix.mean(axis=0)
        self.std = np.where(matrix.std(axis=0) < 1e-6, 1.0, matrix.std(axis=0))
        normalized = (matrix - self.mean) / self.std
        tensor = torch.tensor(normalized, dtype=torch.float32)
        optimizer = torch.optim.Adam(self.model.parameters(), lr=lr)
        loss_fn = nn.MSELoss()
        self.model.train()
        for _ in range(epochs):
            optimizer.zero_grad()
            reconstructed = self.model(tensor)
            loss = loss_fn(reconstructed, tensor)
            loss.backward()
            optimizer.step()
        self.trained = True

    def score(self, features: list[float]) -> float:
        vector = np.asarray(features, dtype=np.float32)
        normalized = (vector - self.mean) / self.std
        tensor = torch.tensor(normalized, dtype=torch.float32).unsqueeze(0)
        self.model.eval()
        with torch.no_grad():
            reconstructed = self.model(tensor).cpu().numpy()[0]
        error = float(np.mean(np.square(reconstructed - normalized)))
        return float(np.clip(error / (1.0 + error), 0.0, 1.0))

    def export_update(self, limit: int = 32) -> list[float]:
        flat: list[float] = []
        for parameter in self.model.parameters():
            flat.extend(parameter.detach().cpu().view(-1).tolist())
            if len(flat) >= limit:
                break
        if len(flat) < limit:
            flat.extend([0.0] * (limit - len(flat)))
        return [round(float(value), 6) for value in flat[:limit]]

    def model_digest(self) -> str:
        update = self.export_update(limit=64)
        payload = ",".join(f"{value:.6f}" for value in update).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def save(self, path: str | Path) -> None:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "state_dict": self.model.state_dict(),
                "mean": self.mean,
                "std": self.std,
                "input_dim": self.input_dim,
                "trained": self.trained,
            },
            target,
        )

    def load(self, path: str | Path) -> None:
        payload = torch.load(Path(path), map_location="cpu")
        self.model = Autoencoder(int(payload["input_dim"]))
        self.model.load_state_dict(payload["state_dict"])
        self.mean = np.asarray(payload["mean"], dtype=np.float32)
        self.std = np.asarray(payload["std"], dtype=np.float32)
        self.trained = bool(payload.get("trained", True))