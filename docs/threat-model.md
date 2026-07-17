# Threat model

## Assets

- Raspberry Pi host integrity
- GPIO and peripheral safety
- local audit log
- action approvals
- user secrets and credentials
- clinical-style demo data
- messaging and notification channels

## Adversaries

- malicious webpage content read by an agent
- hostile prompt injection in email, Slack, Telegram or browser text
- malicious OpenClaw skill or plugin
- compromised local network caller
- confused or over-trusting human operator
- hallucinated package names or fake documentation

## Main risks

### Raw tool execution

If an agent can run shell commands, it can damage files, change configuration or leak data. ClawGuard does not expose raw shell actions.

### Prompt injection

External content may tell the agent to ignore rules or bypass safety controls. ClawGuard scans source text and parameters for common bypass markers and still requires action-level policy checks.

### Privilege drift

A sequence of small allowed actions may produce unintended authority. ClawGuard logs every proposal and keeps medium/high actions behind approval gates.

### Unsafe hardware actuation

High-risk physical examples are simulator-only in v0.1. Developers must write explicit hardware adapters and policies before real relays, pumps, motors or servos are connected.

## Mitigations in v0.1

- action allowlist
- parameter allowlist
- duration limits
- simulator-only high-risk examples
- blocked critical actions
- approval gate
- prompt-injection markers
- audit logging
- dashboard visibility

## Out of scope

- public internet deployment
- multi-tenant authorization
- production medical-device use
- production industrial use
- autonomous security response
