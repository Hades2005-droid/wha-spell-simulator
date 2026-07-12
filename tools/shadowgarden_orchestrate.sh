#!/bin/zsh
# Shadow Garden Claude Code full-mesh orchestrator.
#
# Runs all four Claude-integration paths in the correct order while keeping
# Perplexity (mesh) and the local Claude agent hot:
#
#   1. Credential-safe dry-run lane        (tools/claude_shadowgarden.py)
#   1b. Comet extension workspace status   (tools/extension_workspace_status.py)
#   1c. Recursive node bridge status       (tools/recursive_node_bridge.py)
#   1d. Perplexity review adapter status    (tools/perplexity_mesh_adapter.py)
#   2. Bridge connect + status             (DevinTerminalBridge/connect_claude_env.sh)
#   3. Claude agent w/ full tool calling   (claude_integration.py)
#   4. C# DevinTerminalBridge launcher     (dotnet run -- launch-claude-agent)
#   +. MCP config surface for Claude/Cursor(claude_mcp_config.json)
#
# Everything below the credential-safe lane is opt-in via env flags so this
# script stays safe to run by default. Perplexity co-review runs in parallel
# through the existing browser mesh bridge (checkPerplexitySpace).
#
# Env flags:
#   SG_RUN_PACKET=1         Gate-10 shadow_garden_packet self-test (default: 1)
#   SG_RUN_EXTENSION=1      emit Comet extension status  (default: 1)
#   SG_RUN_RECURSIVE=1      emit bounded recursive status (default: 1)
#   SG_RUN_PERPLEXITY=1    emit dry-run review status (default: 1)
#   SG_RUN_CONNECT=1        run connect_claude_env.sh   (default: 1)
#   SG_RUN_CLAUDE_AGENT=1   run claude_integration.py   (default: 0, needs ANTHROPIC_API_KEY)
#   SG_RUN_DOTNET=1         run dotnet launch-claude-agent (default: 0, needs dotnet)
#   SG_RUN_MCP_ECHO=1       print MCP config path       (default: 1)
#   SG_PARALLEL=1           background 3+4 instead of sequential (default: 1)

set -u

SG_ROOT="${SG_ROOT:-/Users/fredwashere/shadow_garden_may30_monitoring}"
WHA_ROOT="${WHA_ROOT:-/Users/fredwashere/wha-spell-simulator}"
LOG="/tmp/shadow_garden_orchestrate.log"

SG_RUN_PACKET="${SG_RUN_PACKET:-1}"
SG_RUN_EXTENSION="${SG_RUN_EXTENSION:-1}"
SG_RUN_RECURSIVE="${SG_RUN_RECURSIVE:-1}"
SG_RUN_PERPLEXITY="${SG_RUN_PERPLEXITY:-1}"
SG_RUN_CONNECT="${SG_RUN_CONNECT:-1}"
SG_RUN_CLAUDE_AGENT="${SG_RUN_CLAUDE_AGENT:-0}"
SG_RUN_DOTNET="${SG_RUN_DOTNET:-0}"
SG_RUN_MCP_ECHO="${SG_RUN_MCP_ECHO:-1}"
SG_PARALLEL="${SG_PARALLEL:-1}"

: > "$LOG"

log() {
  print -r -- "$@" | tee -a "$LOG"
}

log "[orchestrate] $(date -u +%Y-%m-%dT%H:%M:%SZ) Shadow Garden Claude Code full-mesh"
log "[orchestrate] SG_ROOT=$SG_ROOT WHA_ROOT=$WHA_ROOT"
log "[orchestrate] flags: extension=$SG_RUN_EXTENSION recursive=$SG_RUN_RECURSIVE perplexity=$SG_RUN_PERPLEXITY connect=$SG_RUN_CONNECT agent=$SG_RUN_CLAUDE_AGENT dotnet=$SG_RUN_DOTNET mcp_echo=$SG_RUN_MCP_ECHO parallel=$SG_PARALLEL"

# --- 1. credential-safe dry-run lane (always) ---
# --- 0. Gate-10 unified packet (engine + agent + bridge) ---
if [[ "$SG_RUN_PACKET" == "1" && -f "$WHA_ROOT/tools/shadow_garden_packet.py" ]]; then
  log "[orchestrate] step 0: Gate-10 shadow_garden_packet self-test"
  python3 "$WHA_ROOT/tools/shadow_garden_packet.py" write 2>&1 | tee -a "$LOG"
  if [[ -f "$WHA_ROOT/tools/claude_shadowgarden.py" ]]; then
    python3 "$WHA_ROOT/tools/claude_shadowgarden.py" --run-packet 2>&1 | tee -a "$LOG" || true
  fi
else
  log "[orchestrate] step 0: SKIP (SG_RUN_PACKET=$SG_RUN_PACKET or packet missing)"
fi

if [[ -f "$WHA_ROOT/tools/claude_shadowgarden.py" ]]; then
  log "[orchestrate] step 1: credential-safe Claude lane (dry-run)"
  verify_flag=""
  if [[ -n "${ANTHROPIC_OAUTH_TOKEN:-}" && -n "${ANTHROPIC_API_KEY_ID:-}" ]]; then
    verify_flag="--verify-admin-key"
    log "[orchestrate] step 1: admin-key verification armed"
  fi
  python3 "$WHA_ROOT/tools/claude_shadowgarden.py" \
    --mode auto \
    --prompt "Full-mesh Claude Code activation across Shadow Garden + Perplexity." \
    $verify_flag \
    2>&1 | tee -a "$LOG"
else
  log "[orchestrate] step 1: SKIP (claude_shadowgarden.py missing)"
fi

# --- 1b. Comet extension workspace status + Perplexity review prompt ---
if [[ "$SG_RUN_EXTENSION" == "1" && -f "$WHA_ROOT/tools/extension_workspace_status.py" ]]; then
  log "[orchestrate] step 1b: Comet extension workspace status"
  python3 "$WHA_ROOT/tools/extension_workspace_status.py" \
    --workspace "${SG_EXTENSION_WORKSPACE:-/Users/fredwashere/browser-extension-workspaces/pornhub-video-downloader-plugin-v3}" \
    2>&1 | tee -a "$LOG"
else
  log "[orchestrate] step 1b: SKIP (SG_RUN_EXTENSION=$SG_RUN_EXTENSION or script missing)"
fi

# --- 1c. bounded recursive node bridge status ---
if [[ "$SG_RUN_RECURSIVE" == "1" && -f "$WHA_ROOT/tools/recursive_node_bridge.py" ]]; then
  log "[orchestrate] step 1c: bounded recursive node bridge status"
  python3 "$WHA_ROOT/tools/recursive_node_bridge.py" \
    --cycles "${SG_RECURSIVE_CYCLES:-1}" \
    --gain "${SG_RECURSIVE_GAIN:-1}" \
    2>&1 | tee -a "$LOG"
else
  log "[orchestrate] step 1c: SKIP (SG_RUN_RECURSIVE=$SG_RUN_RECURSIVE or script missing)"
fi

# --- 1d. Perplexity local review adapter status (dry-run; no API request) ---
if [[ "$SG_RUN_PERPLEXITY" == "1" && -f "$WHA_ROOT/tools/perplexity_mesh_adapter.py" ]]; then
  log "[orchestrate] step 1d: Perplexity review adapter dry-run"
  python3 "$WHA_ROOT/tools/perplexity_mesh_adapter.py" \
    --request "Review local Shadow Garden mesh and Comet status for integration risks." \
    2>&1 | tee -a "$LOG"
else
  log "[orchestrate] step 1d: SKIP (SG_RUN_PERPLEXITY=$SG_RUN_PERPLEXITY or script missing)"
fi

# --- 2. bridge connect + sovereign tag ---
if [[ "$SG_RUN_CONNECT" == "1" && -f "$SG_ROOT/DevinTerminalBridge/connect_claude_env.sh" ]]; then
  log "[orchestrate] step 2: connect_claude_env.sh"
  # Explicitly do NOT auto-launch the Python agent from connect; we handle it below.
  ANTHROPIC_API_KEY="" zsh "$SG_ROOT/DevinTerminalBridge/connect_claude_env.sh" 2>&1 | tee -a "$LOG"
else
  log "[orchestrate] step 2: SKIP (SG_RUN_CONNECT=$SG_RUN_CONNECT or script missing)"
fi

# --- +. MCP config surface (echo path so Claude Desktop / Cursor can point at it) ---
if [[ "$SG_RUN_MCP_ECHO" == "1" && -f "$SG_ROOT/claude_mcp_config.json" ]]; then
  log "[orchestrate] MCP config: $SG_ROOT/claude_mcp_config.json"
  log "[orchestrate]   -> point Claude Desktop / Cursor MCP settings at this file"
else
  log "[orchestrate] MCP config: SKIP or missing"
fi

# --- 3. Claude agent with full tool calling ---
run_claude_agent() {
  if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
    log "[orchestrate] step 3: SKIP (ANTHROPIC_API_KEY unset)"
    return 0
  fi
  if [[ ! -f "$SG_ROOT/claude_integration.py" ]]; then
    log "[orchestrate] step 3: SKIP (claude_integration.py missing)"
    return 0
  fi
  log "[orchestrate] step 3: launching Claude agent (full tool calling)"
  ( cd "$SG_ROOT" && python3 claude_integration.py ) 2>&1 | tee -a "$LOG"
}

# --- 4. C# DevinTerminalBridge launcher ---
run_dotnet_bridge() {
  if ! command -v dotnet >/dev/null 2>&1; then
    log "[orchestrate] step 4: SKIP (dotnet not on PATH)"
    return 0
  fi
  if [[ ! -f "$SG_ROOT/DevinTerminalBridge/DevinTerminalBridge.csproj" ]]; then
    log "[orchestrate] step 4: SKIP (DevinTerminalBridge.csproj missing)"
    return 0
  fi
  log "[orchestrate] step 4: dotnet run -- launch-claude-agent"
  ( cd "$SG_ROOT/DevinTerminalBridge" && dotnet run -- launch-claude-agent ) 2>&1 | tee -a "$LOG"
}

if [[ "$SG_RUN_CLAUDE_AGENT" == "1" || "$SG_RUN_DOTNET" == "1" ]]; then
  if [[ "$SG_PARALLEL" == "1" ]]; then
    log "[orchestrate] launching steps 3+4 in parallel"
    pids=()
    if [[ "$SG_RUN_CLAUDE_AGENT" == "1" ]]; then
      run_claude_agent & pids+=($!)
    fi
    if [[ "$SG_RUN_DOTNET" == "1" ]]; then
      run_dotnet_bridge & pids+=($!)
    fi
    for pid in $pids; do
      wait "$pid" || log "[orchestrate] child $pid exited non-zero"
    done
  else
    [[ "$SG_RUN_CLAUDE_AGENT" == "1" ]] && run_claude_agent
    [[ "$SG_RUN_DOTNET" == "1" ]] && run_dotnet_bridge
  fi
else
  log "[orchestrate] steps 3 and 4: not armed (set SG_RUN_CLAUDE_AGENT=1 / SG_RUN_DOTNET=1)"
fi

# Perplexity co-review runs in the browser mesh (checkPerplexitySpace); nothing
# to launch here. The credential-safe and extension lanes write route_hints and
# a review prompt so the mesh diagnostics UI can pick them up. The recursive lane
# remains local-only and metadata-only unless a separately reviewed adapter is added.
# The Perplexity adapter is dry-run by default; `--send` must be invoked manually
# with a rotated PERPLEXITY_API_KEY in the environment.

log "[orchestrate] done. Combined log: $LOG"
