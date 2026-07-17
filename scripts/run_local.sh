#!/usr/bin/env bash
set -euo pipefail

export CLAWGUARD_MODE="${CLAWGUARD_MODE:-simulator}"
export CLAWGUARD_AUDIT_PATH="${CLAWGUARD_AUDIT_PATH:-data/audit.log}"
uvicorn backend.app:app --host 0.0.0.0 --port "${PORT:-8080}"
