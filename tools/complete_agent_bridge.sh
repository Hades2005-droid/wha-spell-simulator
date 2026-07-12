#!/bin/zsh
# Complete agent bridge — chronology + recursive + Fable5/ComfyUI + spacetime + jing
# Dry-run / local-first. Never prints secret values.
set -u

WHA="${WHA_SPELL_ROOT:-$HOME/wha-spell-simulator}"
export SHADOW_GARDEN_ROOT="${SHADOW_GARDEN_ROOT:-$HOME/ShadowGarden}"
export PYTHONPATH="$SHADOW_GARDEN_ROOT${PYTHONPATH:+:$PYTHONPATH}"
export PATH="$HOME/.grok/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

cd "$WHA" || exit 1
LOG="/tmp/shadow_garden_complete_agent_bridge.log"
: >"$LOG"
echo "=== complete agent bridge $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee -a "$LOG"

run() {
  echo "" | tee -a "$LOG"
  echo ">> $*" | tee -a "$LOG"
  # shellcheck disable=SC2068
  $@ 2>&1 | tee -a "$LOG" || echo "(non-fatal) exit $?" | tee -a "$LOG"
}

# Soft-load env file without echoing values
if [[ -f "$SHADOW_GARDEN_ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$SHADOW_GARDEN_ROOT/.env" 2>/dev/null || true
  set +a
  echo "env: loaded $SHADOW_GARDEN_ROOT/.env (values not logged)" | tee -a "$LOG"
fi

SG_RUN_CHRONOLOGY="${SG_RUN_CHRONOLOGY:-1}"
SG_RUN_RECURSIVE="${SG_RUN_RECURSIVE:-1}"
SG_RUN_MESH="${SG_RUN_MESH:-1}"
SG_RUN_FABLE5_BRIDGE="${SG_RUN_FABLE5_BRIDGE:-1}"
SG_RUN_EXPORT="${SG_RUN_EXPORT:-1}"
SG_RUN_JING="${SG_RUN_JING:-1}"
SG_RUN_PERMISSION_WIRE="${SG_RUN_PERMISSION_WIRE:-1}"
SG_RUN_PACKET="${SG_RUN_PACKET:-1}"
SG_RUN_CLAUDE_PACKET="${SG_RUN_CLAUDE_PACKET:-1}"
SG_RUN_ORCHESTRATE="${SG_RUN_ORCHESTRATE:-0}"

if [[ "$SG_RUN_PACKET" == "1" ]]; then
  run python3 tools/shadow_garden_packet.py write
fi

if [[ "$SG_RUN_CLAUDE_PACKET" == "1" ]]; then
  run python3 tools/claude_shadowgarden.py --run-packet
fi

if [[ "$SG_RUN_CHRONOLOGY" == "1" ]]; then
  run python3 tools/chronology_engine.py --date "$(date -u +%Y-%m-%d)" --time "$(date -u +%H:%M)"
fi

if [[ "$SG_RUN_RECURSIVE" == "1" ]]; then
  run python3 tools/recursive_node_bridge.py --cycles 1 --gain 1
fi

if [[ "$SG_RUN_MESH" == "1" ]]; then
  run python3 tools/mesh_review_loop.py --cycles 2 --interval 1 --max-seconds 30
fi

if [[ "$SG_RUN_FABLE5_BRIDGE" == "1" ]]; then
  run python3 tools/fable5_comfyui_command_bridge.py write
fi

if [[ "$SG_RUN_EXPORT" == "1" ]]; then
  run python3 -m spacetime_alchemy "$(date -u +%Y-%m-%d)" --export
fi

if [[ "$SG_RUN_JING" == "1" ]]; then
  run python3 -m spacetime_alchemy.jing_power_monitor --once
fi

if [[ "$SG_RUN_ORCHESTRATE" == "1" ]]; then
  run zsh tools/shadowgarden_orchestrate.sh
fi

echo "" | tee -a "$LOG"
echo "=== complete agent bridge finished ===" | tee -a "$LOG"
echo "log: $LOG"
echo "status: /tmp/shadow_garden_fable5_comfyui_bridge_status.json"
echo "jing: $SHADOW_GARDEN_ROOT/live/spacetime_alchemy/jing_power_latest.json"
echo "compact: $SHADOW_GARDEN_ROOT/live/spacetime_alchemy/fable5-compact.json"
exit 0
