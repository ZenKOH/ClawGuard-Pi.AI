# Architecture

ClawGuard-Pi.AI is built around one rule: an AI agent may propose an action, but it may not execute physical or privileged actions directly.

```text
Agent / OpenClaw / dashboard
        ↓
Action proposal JSON
        ↓
PolicyEngine
        ↓              ↘ blocked event
Approval gate             ↘ needs human approval
        ↓
ActionRegistry
        ↓
Simulator or deliberate Raspberry Pi hardware adapter
        ↓
AuditLog JSONL
```

## Components

- `backend/app.py`: local FastAPI control plane and dashboard server.
- `backend/policy_engine.py`: allowlist, risk tiers, approval rules, simulator-only constraints and hard-deny patterns.
- `backend/action_registry.py`: safe named actions only; no arbitrary shell or raw GPIO path.
- `backend/audit_log.py`: append-only JSONL audit trail.
- `simulator/virtual_gpio.py`: virtual sensor/output layer for safe first-run demos.
- `frontend/`: operator dashboard for proposals, approvals and audit export.

## Trust boundary

OpenClaw, browser content, messaging apps and local LLMs are treated as untrusted proposers. The trusted boundary is the policy engine, action registry, audit log and human approval decision.
