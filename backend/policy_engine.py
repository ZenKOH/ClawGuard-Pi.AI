from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DecisionStatus(str, Enum):
    APPROVED = "approved"
    NEEDS_APPROVAL = "needs_approval"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class ActionSpec:
    name: str
    risk: str
    description: str
    allowed: bool = True
    requires_approval: bool = False
    max_duration_seconds: int | None = None
    simulator_only: bool = False
    allowed_parameters: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class PolicyDecision:
    status: DecisionStatus
    reason: str
    action: str
    risk: str = "unknown"
    rule_id: str = "unknown"
    requires_approval: bool = False


DANGEROUS_PARAMETER_KEYS = {
    "command", "shell", "exec", "password", "passwd", "secret", "token",
    "api_key", "apikey", "private_key", "credential", "credentials", "cookie", "session"
}

PROMPT_INJECTION_MARKERS = (
    "ignore previous instructions", "ignore all previous", "developer mode",
    "disable safety", "bypass policy", "run shell", "exfiltrate",
    "send credentials", "reveal secrets", "do not tell the user"
)

DEFAULT_ACTIONS: dict[str, ActionSpec] = {
    "capture_camera_frame": ActionSpec("capture_camera_frame", "low", "Capture a simulated or Pi camera frame.", allowed_parameters={"reason", "camera", "label"}),
    "run_camera_detection": ActionSpec("run_camera_detection", "low", "Run a simulated camera detection pass.", allowed_parameters={"model", "threshold", "reason"}),
    "read_sensor": ActionSpec("read_sensor", "low", "Read a named virtual or GPIO-backed sensor.", allowed_parameters={"pin", "sensor", "unit"}),
    "set_led": ActionSpec("set_led", "low", "Set a safe LED output through the adapter.", max_duration_seconds=60, allowed_parameters={"channel", "state", "duration_seconds"}),
    "send_notification": ActionSpec("send_notification", "medium", "Send or simulate a local notification.", requires_approval=True, allowed_parameters={"message", "channel", "severity"}),
    "export_rehab_session_summary": ActionSpec("export_rehab_session_summary", "medium", "Export a clinician-reviewable rehab session summary.", requires_approval=True, allowed_parameters={"case_id", "format", "include_raw_events"}),
    "activate_relay": ActionSpec("activate_relay", "high", "Simulator-only relay activation with strict duration limit.", requires_approval=True, max_duration_seconds=3, simulator_only=True, allowed_parameters={"relay", "duration_seconds", "reason"}),
    "start_mock_pump": ActionSpec("start_mock_pump", "high", "Simulator-only pump activation for demos.", requires_approval=True, max_duration_seconds=3, simulator_only=True, allowed_parameters={"duration_seconds", "reason"}),
    "scan_network": ActionSpec("scan_network", "high", "Network scanning is blocked in v0.1; use mock events only.", allowed=False, requires_approval=True, allowed_parameters={"cidr", "reason"}),
    "send_email": ActionSpec("send_email", "high", "Direct email sending is blocked in v0.1.", allowed=False, requires_approval=True, allowed_parameters={"to", "subject", "body"}),
    "raw_shell": ActionSpec("raw_shell", "critical", "Raw shell execution is always blocked.", allowed=False),
    "delete_file": ActionSpec("delete_file", "critical", "Arbitrary file deletion is always blocked.", allowed=False, allowed_parameters={"path"}),
}


class PolicyEngine:
    def __init__(self, actions: dict[str, ActionSpec] | None = None, mode: str = "simulator") -> None:
        self.actions = actions or DEFAULT_ACTIONS
        self.mode = mode

    def evaluate(self, action: str, parameters: dict[str, Any] | None = None, *, approved_by_human: bool = False, source_text: str = "") -> PolicyDecision:
        parameters = parameters or {}
        spec = self.actions.get(action)
        if not spec:
            return PolicyDecision(DecisionStatus.BLOCKED, f"Action '{action}' is not registered.", action, rule_id="unknown-action")
        if not spec.allowed:
            return PolicyDecision(DecisionStatus.BLOCKED, f"Action '{action}' is explicitly blocked in v0.1.", action, spec.risk, "blocked-action", spec.requires_approval)
        dangerous_key = self._find_dangerous_parameter_key(parameters)
        if dangerous_key:
            return PolicyDecision(DecisionStatus.BLOCKED, f"Parameter '{dangerous_key}' is prohibited.", action, spec.risk, "dangerous-parameter", spec.requires_approval)
        unknown = sorted(set(parameters) - spec.allowed_parameters)
        if unknown:
            return PolicyDecision(DecisionStatus.BLOCKED, f"Unregistered parameter(s): {', '.join(unknown)}.", action, spec.risk, "unknown-parameter", spec.requires_approval)
        if self._looks_like_prompt_injection(source_text, parameters):
            return PolicyDecision(DecisionStatus.BLOCKED, "Request contains prompt-injection or bypass markers.", action, spec.risk, "prompt-injection-marker", spec.requires_approval)
        duration = self._duration(parameters)
        if spec.max_duration_seconds is not None and duration is not None and duration > spec.max_duration_seconds:
            return PolicyDecision(DecisionStatus.BLOCKED, f"Requested duration {duration}s exceeds max {spec.max_duration_seconds}s.", action, spec.risk, "duration-limit", spec.requires_approval)
        if spec.simulator_only and self.mode != "simulator":
            return PolicyDecision(DecisionStatus.BLOCKED, f"Action '{action}' is simulator-only in v0.1.", action, spec.risk, "simulator-only", spec.requires_approval)
        if spec.requires_approval and not approved_by_human:
            return PolicyDecision(DecisionStatus.NEEDS_APPROVAL, f"Action '{action}' is {spec.risk}-risk and requires human approval.", action, spec.risk, "human-approval-required", True)
        return PolicyDecision(DecisionStatus.APPROVED, f"Action '{action}' is allowed by policy.", action, spec.risk, "allowlisted-action", spec.requires_approval)

    @staticmethod
    def _duration(parameters: dict[str, Any]) -> float | None:
        value = parameters.get("duration_seconds")
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _find_dangerous_parameter_key(value: Any) -> str | None:
        if isinstance(value, dict):
            for key, nested in value.items():
                if str(key).lower() in DANGEROUS_PARAMETER_KEYS:
                    return str(key)
                found = PolicyEngine._find_dangerous_parameter_key(nested)
                if found:
                    return found
        elif isinstance(value, list):
            for item in value:
                found = PolicyEngine._find_dangerous_parameter_key(item)
                if found:
                    return found
        return None

    @staticmethod
    def _looks_like_prompt_injection(source_text: str, parameters: dict[str, Any]) -> bool:
        haystack = f"{source_text} {parameters}".lower()
        return any(marker in haystack for marker in PROMPT_INJECTION_MARKERS)
