from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.action_registry import ActionRegistry
from backend.audit_log import AuditLog
from backend.policy_engine import DEFAULT_ACTIONS, DecisionStatus, PolicyEngine

APP_ROOT = Path(__file__).resolve().parents[1]
FRONTEND = APP_ROOT / "frontend"
MODE = os.getenv("CLAWGUARD_MODE", "simulator").strip().lower() or "simulator"
AUDIT_PATH = os.getenv("CLAWGUARD_AUDIT_PATH", "data/audit.log")

app = FastAPI(
    title="ClawGuard-Pi.AI",
    version="0.1.0",
    description="Permissioned Raspberry Pi control plane for OpenClaw-style edge agents.",
)
policy = PolicyEngine(mode=MODE)
registry = ActionRegistry(mode=MODE)
audit = AuditLog(AUDIT_PATH)


class ActionProposal(BaseModel):
    source: str = Field(default="openclaw", max_length=80)
    goal: str = Field(default="Agent action proposal", max_length=2000)
    action: str = Field(..., min_length=1, max_length=120)
    parameters: dict[str, Any] = Field(default_factory=dict)


def _normalise_openclaw_payload(payload: dict[str, Any]) -> ActionProposal:
    tool = payload.get("tool") or payload.get("action") or payload.get("name")
    args = payload.get("arguments") or payload.get("parameters") or payload.get("args") or {}
    if isinstance(args, str):
        args = {"message": args}
    if not isinstance(args, dict):
        args = {}
    return ActionProposal(
        source=payload.get("source", "openclaw"),
        goal=payload.get("goal") or payload.get("prompt") or payload.get("reason") or "OpenClaw tool proposal",
        action=str(tool or "unknown"),
        parameters=args,
    )


@app.get("/", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    index = FRONTEND / "index.html"
    if not index.exists():
        raise HTTPException(status_code=500, detail="Dashboard not installed.")
    return HTMLResponse(index.read_text(encoding="utf-8"))


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "mode": MODE, "service": "ClawGuard-Pi.AI"}


@app.get("/api/status")
def status() -> dict[str, Any]:
    events = audit.read_all(limit=500)
    return {
        "service": "ClawGuard-Pi.AI",
        "mode": MODE,
        "simulator": MODE == "simulator",
        "registered_actions": len(DEFAULT_ACTIONS),
        "audit_events": len(events),
        "pending_approvals": len([e for e in events if e.get("status") == DecisionStatus.NEEDS_APPROVAL]),
    }


@app.get("/api/actions")
def actions() -> dict[str, Any]:
    return {
        "actions": [
            {
                "name": spec.name,
                "risk": spec.risk,
                "description": spec.description,
                "allowed": spec.allowed,
                "requires_approval": spec.requires_approval,
                "simulator_only": spec.simulator_only,
                "max_duration_seconds": spec.max_duration_seconds,
                "allowed_parameters": sorted(spec.allowed_parameters),
            }
            for spec in DEFAULT_ACTIONS.values()
        ]
    }


@app.get("/api/audit")
def audit_events(limit: int = 250) -> dict[str, Any]:
    return {"events": list(reversed(audit.read_all(limit=limit)))}


@app.delete("/api/audit")
def clear_audit() -> dict[str, Any]:
    audit.clear()
    return {"ok": True, "message": "Audit log cleared."}


@app.post("/api/propose")
def propose_action(proposal: ActionProposal) -> dict[str, Any]:
    decision = policy.evaluate(
        proposal.action,
        proposal.parameters,
        approved_by_human=False,
        source_text=f"{proposal.source} {proposal.goal}",
    )
    base = {
        "source": proposal.source,
        "goal": proposal.goal,
        "action": proposal.action,
        "parameters": proposal.parameters,
        "status": decision.status,
        "decision": decision.__dict__,
    }
    if decision.status == DecisionStatus.APPROVED:
        event = audit.append({**base, "result": registry.execute(proposal.action, proposal.parameters)})
        return {"event": event}
    return {"event": audit.append(base)}


@app.post("/api/approve/{event_id}")
def approve_action(event_id: str) -> dict[str, Any]:
    event = audit.find(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found.")
    if event.get("status") != DecisionStatus.NEEDS_APPROVAL:
        raise HTTPException(status_code=400, detail="Only pending events can be approved.")
    action = str(event.get("action"))
    parameters = event.get("parameters") or {}
    decision = policy.evaluate(action, parameters, approved_by_human=True, source_text=str(event.get("goal", "")))
    if decision.status != DecisionStatus.APPROVED:
        return {"event": audit.append({**event, "parent_id": event_id, "status": decision.status, "decision": decision.__dict__, "approval_attempt": "failed"})}
    return {"event": audit.append({**event, "parent_id": event_id, "status": "executed_after_approval", "decision": decision.__dict__, "human_approved": True, "result": registry.execute(action, parameters)})}


@app.post("/api/openclaw/webhook")
def openclaw_webhook(payload: dict[str, Any]) -> dict[str, Any]:
    return propose_action(_normalise_openclaw_payload(payload))


@app.post("/api/demo/load")
def load_demo() -> dict[str, Any]:
    demo_proposals = [
        ActionProposal(source="demo.smart_home", goal="Turn on the status LED after a safe doorbell event.", action="set_led", parameters={"channel": "status", "state": "on", "duration_seconds": 10}),
        ActionProposal(source="demo.parcel", goal="Parcel-like object detected; capture a still frame.", action="capture_camera_frame", parameters={"reason": "parcel detected"}),
        ActionProposal(source="demo.rehab", goal="Export a clinician-reviewable rehab session summary.", action="export_rehab_session_summary", parameters={"case_id": "case-demo-01", "format": "json", "include_raw_events": True}),
        ActionProposal(source="demo.industrial", goal="Read a virtual temperature sensor for an edge-monitoring workflow.", action="read_sensor", parameters={"sensor": "temperature", "pin": 21, "unit": "°C"}),
        ActionProposal(source="demo.high_risk", goal="Simulate watering a plant for three seconds.", action="start_mock_pump", parameters={"duration_seconds": 3, "reason": "soil moisture under threshold"}),
    ]
    return {"events": [propose_action(item)["event"] for item in demo_proposals]}


@app.get("/api/export/audit", response_class=PlainTextResponse)
def export_audit() -> str:
    return "\n".join([str(item) for item in audit.read_all(limit=1000)])


@app.get("/api/export/audit.json")
def export_audit_json() -> JSONResponse:
    return JSONResponse({"events": audit.read_all(limit=1000)})


if (FRONTEND / "app.js").exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="static")
