#!/bin/zsh
set -euo pipefail
ROOT="/Users/fredwashere/wha-spell-simulator/shadow_garden_handoff/terminal_auto"
echo "=== Shadow Garden Terminal Auto Status ==="
echo "Root: $ROOT"
find "$ROOT" -maxdepth 2 -type f | sort
echo "\nLast log lines:"
[ -f "$ROOT/logs/terminal_auto.log" ] && tail -20 "$ROOT/logs/terminal_auto.log" || echo "No log yet."
echo "\nValidate Claude JSON from clipboard:"
echo "pbpaste | python3 /validate_claude_json.py"
