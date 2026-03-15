from __future__ import annotations

import hashlib
import json
import statistics
from typing import Iterable

from .schemas import BehaviorEvent, FeatureWindow


class FeatureExtractor:
    FEATURE_NAMES = [
        "activity_density",
        "keystroke_rate",
        "keystroke_interval_mean",
        "keystroke_interval_std",
        "keystroke_duration_mean",
        "mouse_speed_mean",
        "mouse_speed_std",
        "mouse_click_rate",
        "app_switch_rate",
        "cpu_mean",
        "memory_mean",
        "process_count_mean",
    ]

    def extract(self, device_id: str, events: Iterable[BehaviorEvent], window_seconds: int, now: float) -> FeatureWindow:
        ordered = sorted(events, key=lambda item: item.timestamp)
        keystrokes = [event for event in ordered if event.event_type == "keystroke"]
        mouse_moves = [event for event in ordered if event.event_type == "mouse_move"]
        mouse_clicks = [event for event in ordered if event.event_type == "mouse_click"]
        app_switches = [event for event in ordered if event.event_type == "app_switch"]
        system_samples = [event for event in ordered if event.event_type == "system"]

        intervals = []
        for earlier, later in zip(keystrokes, keystrokes[1:]):
            intervals.append((later.timestamp - earlier.timestamp) * 1000.0)

        feature_values = [
            round(len(ordered) / max(window_seconds, 1), 6),
            round(len(keystrokes) / max(window_seconds, 1), 6),
            self._mean(intervals),
            self._std(intervals),
            self._mean([event.payload.get("duration_ms", 0.0) for event in keystrokes]),
            self._mean([event.payload.get("speed_px_s", 0.0) for event in mouse_moves]),
            self._std([event.payload.get("speed_px_s", 0.0) for event in mouse_moves]),
            round(len(mouse_clicks) / max(window_seconds, 1), 6),
            round(len(app_switches) / max(window_seconds, 1), 6),
            self._mean([event.payload.get("cpu_percent", 0.0) for event in system_samples]),
            self._mean([event.payload.get("memory_percent", 0.0) for event in system_samples]),
            self._mean([event.payload.get("process_count", 0.0) for event in system_samples]),
        ]

        return FeatureWindow(
            device_id=device_id,
            timestamp=now,
            window_seconds=window_seconds,
            feature_names=self.FEATURE_NAMES[:],
            feature_values=feature_values,
            event_count=len(ordered),
        )

    @staticmethod
    def digest(window: FeatureWindow) -> str:
        payload = json.dumps(window.to_dict(), sort_keys=True).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def _mean(values: list[float]) -> float:
        if not values:
            return 0.0
        return round(float(statistics.fmean(values)), 6)

    @staticmethod
    def _std(values: list[float]) -> float:
        if len(values) < 2:
            return 0.0
        return round(float(statistics.pstdev(values)), 6)