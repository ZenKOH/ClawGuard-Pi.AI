from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from simulator.virtual_gpio import virtual_gpio


class ActionRegistry:
    """Named safe actions that can be executed only after policy approval."""

    def __init__(self, mode: str = "simulator") -> None:
        self.mode = mode
        self._actions: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
            "capture_camera_frame": self.capture_camera_frame,
            "run_camera_detection": self.run_camera_detection,
            "read_sensor": self.read_sensor,
            "set_led": self.set_led,
            "send_notification": self.send_notification,
            "export_rehab_session_summary": self.export_rehab_session_summary,
            "activate_relay": self.activate_relay,
            "start_mock_pump": self.start_mock_pump,
        }

    def list_actions(self) -> list[str]:
        return sorted(self._actions)

    def execute(self, action: str, parameters: dict[str, Any] | None = None) -> dict[str, Any]:
        parameters = parameters or {}
        handler = self._actions.get(action)
        if handler is None:
            raise ValueError(f"Action '{action}' has no registered executor.")
        return handler(parameters)

    @staticmethod
    def _stamp(payload: dict[str, Any]) -> dict[str, Any]:
        return {"executed_at": datetime.now(timezone.utc).isoformat(), **payload}

    def capture_camera_frame(self, parameters: dict[str, Any]) -> dict[str, Any]:
        return self._stamp({
            "action": "capture_camera_frame",
            "mode": self.mode,
            "frame_path": "simulator/frame_0001.jpg",
            "note": "Simulated frame capture. Replace with a deliberate Pi Camera or AI Camera adapter.",
            "parameters": parameters,
        })

    def run_camera_detection(self, parameters: dict[str, Any]) -> dict[str, Any]:
        threshold = float(parameters.get("threshold", 0.55))
        detections = [
            {"label": "parcel", "confidence": 0.87, "bbox": [128, 88, 244, 210]},
            {"label": "person", "confidence": 0.64, "bbox": [32, 42, 90, 220]},
        ]
        return self._stamp({
            "action": "run_camera_detection",
            "mode": self.mode,
            "model": parameters.get("model", "simulated-imx500-mobilenet-ssd"),
            "detections": [d for d in detections if d["confidence"] >= threshold],
        })

    def read_sensor(self, parameters: dict[str, Any]) -> dict[str, Any]:
        return self._stamp({
            "action": "read_sensor",
            "reading": virtual_gpio.read_sensor(sensor=str(parameters.get("sensor", "moisture")), pin=parameters.get("pin")),
        })

    def set_led(self, parameters: dict[str, Any]) -> dict[str, Any]:
        return self._stamp({
            "action": "set_led",
            "result": virtual_gpio.write_output(
                str(parameters.get("channel", "status")),
                str(parameters.get("state", "on")),
                parameters.get("duration_seconds"),
            ),
        })

    def send_notification(self, parameters: dict[str, Any]) -> dict[str, Any]:
        return self._stamp({
            "action": "send_notification",
            "mode": "simulated-notification",
            "channel": parameters.get("channel", "dashboard"),
            "severity": parameters.get("severity", "info"),
            "message": parameters.get("message", "ClawGuard notification"),
        })

    def export_rehab_session_summary(self, parameters: dict[str, Any]) -> dict[str, Any]:
        case_id = str(parameters.get("case_id", "case-demo-01"))
        include_raw = bool(parameters.get("include_raw_events", False))
        summary = {
            "case_id": case_id,
            "active_minutes": 24,
            "rest_breaks": 3,
            "task_attempts": 42,
            "quality_rating": 3,
            "fatigue": 5,
            "carryover_prompt": "Clinician should confirm whether task transferred into the home routine.",
            "clinician_review_required": True,
            "not_medical_device": True,
        }
        if include_raw:
            summary["raw_events"] = [
                {"t": 0, "event": "session_started"},
                {"t": 420, "event": "rest_break"},
                {"t": 1440, "event": "session_completed"},
            ]
        return self._stamp({"action": "export_rehab_session_summary", "summary": summary})

    def activate_relay(self, parameters: dict[str, Any]) -> dict[str, Any]:
        relay = str(parameters.get("relay", "relay-1"))
        duration = float(parameters.get("duration_seconds", 1))
        return self._stamp({"action": "activate_relay", "result": virtual_gpio.write_output(relay, "on", duration)})

    def start_mock_pump(self, parameters: dict[str, Any]) -> dict[str, Any]:
        duration = float(parameters.get("duration_seconds", 1))
        return self._stamp({"action": "start_mock_pump", "result": virtual_gpio.write_output("mock-pump", "on", duration)})
