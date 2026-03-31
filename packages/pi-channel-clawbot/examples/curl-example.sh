#!/usr/bin/env bash
set -euo pipefail

SERVER_URL="${SERVER_URL:-http://127.0.0.1:3000}"
TOKEN="${CLAWBOT_WEBHOOK_TOKEN:-}"

AUTH_ARGS=()
if [[ -n "${TOKEN}" ]]; then
  AUTH_ARGS=(-H "Authorization: Bearer ${TOKEN}")
fi

curl -sS \
  -X POST "${SERVER_URL}/api/channel/clawbot" \
  -H "Content-Type: application/json" \
  "${AUTH_ARGS[@]}" \
  --data @packages/pi-channel-clawbot/examples/minimal-payload.json
