# ClawGuard-Pi.AI

A permissioned Raspberry Pi control plane for OpenClaw-style edge agents.

ClawGuard-Pi.AI lets AI agents observe, propose and assist while a local policy engine decides what actions are allowed. It is designed for Raspberry Pi edge-AI workflows involving sensors, cameras, GPIO, messaging, rehabilitation prototypes, home automation and industrial monitoring.

The agent never receives unrestricted hardware access. Every action passes through an allowlist, a risk policy, optional human approval and a JSONL audit log.

> This project is for education, prototyping and research. It is not a medical device, safety-critical controller, autonomous industrial controller, or substitute for licensed clinical judgement.

## Why this exists

OpenClaw-style agents can read, reason, call tools and operate software or hardware. On Raspberry Pi, that becomes powerful because the agent can interact with cameras, sensors, GPIO pins, relays and edge devices. It also becomes dangerous if the agent receives raw shell access or direct hardware authority.

ClawGuard-Pi.AI treats the Raspberry Pi as a contained edge appliance and inserts a safety layer between agent intention and physical execution:

```text
OpenClaw / LLM agent → proposal → policy engine → approval gate → safe action registry → simulator or Pi hardware adapter → audit log
```

## v0.1 “Bounded Agent” features

- FastAPI backend with local REST API and dashboard.
- Policy engine with allowlists, risk tiers, approval rules, simulator-only constraints and hard-deny patterns.
- Safe action registry for camera, sensor, LED, notification, rehab export and simulator-only relay/pump examples.
- OpenClaw webhook endpoint for proposed tool calls.
- JSONL audit log with pending, approved, blocked and executed states.
- Browser dashboard for action review, pending approvals, simulated demos and audit export.
- Virtual GPIO simulator so the first release is safe without real hardware.
- Rehab/assistive prototype demo mode with clinician-reviewed export.
- Security tests for prompt injection, malicious tool requests and expected blocks.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn backend.app:app --host 0.0.0.0 --port 8080 --reload
```

Open `http://localhost:8080`.

## Safe by default

The default mode is `simulator`. High-risk actions such as relays and pumps are simulator-only unless a developer explicitly changes configuration and writes a hardware adapter.

Hard-denied by default:

- raw shell commands
- arbitrary file deletion
- credential access
- unapproved email sending
- uncontrolled relay or pump execution
- unregistered actions
- action parameters containing secret-like fields such as `password`, `token`, `secret`, `api_key` or `command`

## Example proposal

```bash
curl -X POST http://localhost:8080/api/propose \
  -H 'Content-Type: application/json' \
  -d '{"source":"openclaw","goal":"Parcel-like object detected.","action":"capture_camera_frame","parameters":{"reason":"parcel-detection-demo"}}'
```

## Example high-risk proposal

```bash
curl -X POST http://localhost:8080/api/propose \
  -H 'Content-Type: application/json' \
  -d '{"source":"openclaw","goal":"Water a plant for three seconds.","action":"start_mock_pump","parameters":{"duration_seconds":3,"reason":"soil low"}}'
```

The first response will be `needs_approval`.

## Repository map

```text
backend/       FastAPI app, policy engine, action registry and audit logger
frontend/      Local browser dashboard
simulator/     Virtual GPIO and demo data
docs/          Architecture and threat model
tests/         Policy, registry and security tests
scripts/       Local run helpers
```

## Integration stance

ClawGuard-Pi.AI is designed to sit beside OpenClaw, not replace it. OpenClaw can propose tool calls through the webhook; ClawGuard decides whether those tool calls are allowed, blocked, simulated or escalated for human approval.

## Licence

MIT.
