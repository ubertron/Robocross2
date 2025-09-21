from __future__ import annotations
import time


def lerp_volume(self, start: int | float, end: int | float, duration_ms: int = 500, steps: int = 50):
    duration = duration_ms / 1000.0  # convert to seconds
    interval = duration / steps      # time between updates
    start_time = time.perf_counter()

    for i in range(steps + 1):
        t = (time.perf_counter() - start_time) / duration
        t = min(max(t, 0.0), 1.0)  # clamp between 0–1
        value = start + (end - start) * t
        time.sleep(interval)