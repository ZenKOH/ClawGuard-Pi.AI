from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class VirtualGPIO:
    pins: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    def read_sensor(self, sensor: str = "moisture", pin: int | None = None) -> dict[str, Any]:
        values = {
            "moisture": {"value": 41, "unit": "%"},
            "temperature": {"value": 28.4, "unit": "°C"},
            "distance": {"value": 72, "unit": "cm"},
            "tolerance": {"value": 3, "unit": "review-scale"},
        }
        payload = values.get(sensor, {"value": 1, "unit": "state"})
        return {"sensor": sensor, "pin": pin, **payload, "mode": "simulator"}

    def write_output(self, channel: str, state: str, duration_seconds: float | None = None) -> dict[str, Any]:
        self.pins[channel] = state
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "channel": channel,
            "state": state,
            "duration_seconds": duration_seconds,
            "mode": "simulator",
        }
        self.events.append(event)
        return event


virtual_gpio = VirtualGPIO()
