#!/bin/zsh
# Shadow Garden Claude Code lane launcher (Mac double-clickable .command).
#
# Runs the Python Claude Code lane in dry-run. Live mode requires the explicit
# --execute-claude / --confirm-token flags documented in claude_shadowgarden.py.
#
# Combined output is teed to a log under /tmp.

set -u

PROJECT_ROOT="/Users/fredwashere/wha-spell-simulator"
LOG="/tmp/shadow_garden_claude_launch.log"
PLAN="/tmp/shadow_garden_claude_commands.json"

: > "$LOG"

log() {
  print -r -- "$@" | tee -a "$LOG"
}

log "[launch] $(date -u +%Y-%m-%dT%H:%M:%SZ) Shadow Garden Claude Code lane (dry-run)"

if [[ -d "$PROJECT_ROOT" ]]; then
  cd "$PROJECT_ROOT" || { log "[launch] ERROR: cannot cd to $PROJECT_ROOT"; exit 1; }
  log "[launch] cwd: $PROJECT_ROOT"
else
  log "[launch] WARN: $PROJECT_ROOT not found; staying in $(pwd)"
fi

PY_SCRIPT=""
for candidate in \
  "$PROJECT_ROOT/tools/claude_shadowgarden.py" \
  "./tools/claude_shadowgarden.py" \
  "./claude_shadowgarden.py"; do
  if [[ -f "$candidate" ]]; then
    PY_SCRIPT="$candidate"
    break
  fi
done

if [[ -n "$PY_SCRIPT" ]]; then
  log "[launch] python lane: $PY_SCRIPT (dry-run)"
  python3 "$PY_SCRIPT" \
    --mode auto \
    --prompt "Extend Shadow Garden mesh with Claude Code cloud environment." \
    --command-out "$PLAN" 2>&1 | tee -a "$LOG"
else
  log "[launch] ERROR: claude_shadowgarden.py not found; skipping python lane."
fi

log "[launch] done. Combined log: $LOG"
