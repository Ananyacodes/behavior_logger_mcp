from __future__ import annotations

import math
import random
import threading
import time
from collections import deque
from typing import Optional

import psutil

from .schemas import BehaviorEvent

try:
    from pynput import keyboard, mouse
except Exception:
    keyboard = None
    mouse = None


class BehaviorCollector:
    def __init__(self, max_events: int = 5000) -> None:
        self._events: deque[BehaviorEvent] = deque(maxlen=max_events)
        self._lock = threading.Lock()
        self._pressed_keys: dict[str, float] = {}
        self._last_mouse_position: Optional[tuple[int, int, float]] = None
        self._keyboard_listener = None
        self._mouse_listener = None

    def record_keystroke(self, duration_ms: float, timestamp: Optional[float] = None) -> None:
        self._append(
            BehaviorEvent(
                event_type="keystroke",
                timestamp=timestamp or time.time(),
                payload={"duration_ms": float(duration_ms)},
            )
        )

    def record_mouse_move(self, distance_px: float, speed_px_s: float, timestamp: Optional[float] = None) -> None:
        self._append(
            BehaviorEvent(
                event_type="mouse_move",
                timestamp=timestamp or time.time(),
                payload={
                    "distance_px": float(distance_px),
                    "speed_px_s": float(speed_px_s),
                },
            )
        )

    def record_mouse_click(self, button: str = "left", timestamp: Optional[float] = None) -> None:
        self._append(
            BehaviorEvent(
                event_type="mouse_click",
                timestamp=timestamp or time.time(),
                payload={"button": button},
            )
        )

    def record_app_switch(self, app_name: str, timestamp: Optional[float] = None) -> None:
        self._append(
            BehaviorEvent(
                event_type="app_switch",
                timestamp=timestamp or time.time(),
                payload={"app_name": app_name},
            )
        )

    def collect_system_snapshot(self, timestamp: Optional[float] = None) -> None:
        at = timestamp or time.time()
        self._append(
            BehaviorEvent(
                event_type="system",
                timestamp=at,
                payload={
                    "cpu_percent": float(psutil.cpu_percent(interval=None)),
                    "memory_percent": float(psutil.virtual_memory().percent),
                    "process_count": float(len(psutil.pids())),
                },
            )
        )

    def recent_events(self, window_seconds: int, now: Optional[float] = None) -> list[BehaviorEvent]:
        cutoff = (now or time.time()) - window_seconds
        with self._lock:
            return [event for event in self._events if event.timestamp >= cutoff]

    def start_live_capture(self) -> None:
        if keyboard is None or mouse is None:
            raise RuntimeError("pynput is required for live capture")
        if self._keyboard_listener or self._mouse_listener:
            return

        def on_press(key) -> None:
            self._pressed_keys[str(key)] = time.time()

        def on_release(key) -> None:
            key_name = str(key)
            started = self._pressed_keys.pop(key_name, None)
            if started is None:
                return
            self.record_keystroke((time.time() - started) * 1000.0)

        def on_move(x, y) -> None:
            now = time.time()
            if self._last_mouse_position is None:
                self._last_mouse_position = (x, y, now)
                return
            last_x, last_y, last_t = self._last_mouse_position
            delta_t = max(now - last_t, 1e-6)
            distance = math.hypot(x - last_x, y - last_y)
            speed = distance / delta_t
            self._last_mouse_position = (x, y, now)
            self.record_mouse_move(distance, speed, timestamp=now)

        def on_click(x, y, button, pressed) -> None:
            if pressed:
                self.record_mouse_click(str(button))

        self._keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self._mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click)
        self._keyboard_listener.start()
        self._mouse_listener.start()

    def stop_live_capture(self) -> None:
        if self._keyboard_listener:
            self._keyboard_listener.stop()
            self._keyboard_listener = None
        if self._mouse_listener:
            self._mouse_listener.stop()
            self._mouse_listener = None

    def simulate_activity(self, seconds: int, seed: Optional[int] = None) -> None:
        rng = random.Random(seed)
        start = time.time() - seconds
        apps = ["editor", "browser", "terminal", "mail"]
        for offset in range(seconds):
            current = start + offset
            keystrokes = rng.randint(0, 5)
            for _ in range(keystrokes):
                self.record_keystroke(rng.uniform(40.0, 160.0), timestamp=current + rng.random())
            moves = rng.randint(1, 4)
            for _ in range(moves):
                distance = rng.uniform(10.0, 800.0)
                speed = rng.uniform(50.0, 1400.0)
                self.record_mouse_move(distance, speed, timestamp=current + rng.random())
            if rng.random() < 0.35:
                self.record_mouse_click(timestamp=current + rng.random())
            if rng.random() < 0.08:
                self.record_app_switch(rng.choice(apps), timestamp=current + rng.random())
            self._append(
                BehaviorEvent(
                    event_type="system",
                    timestamp=current,
                    payload={
                        "cpu_percent": rng.uniform(5.0, 45.0),
                        "memory_percent": rng.uniform(25.0, 75.0),
                        "process_count": float(rng.randint(90, 180)),
                    },
                )
            )

    def _append(self, event: BehaviorEvent) -> None:
        with self._lock:
            self._events.append(event)