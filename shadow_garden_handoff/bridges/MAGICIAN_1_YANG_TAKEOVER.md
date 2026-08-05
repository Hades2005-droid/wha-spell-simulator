# Magician 1 · Yang takeover — Cursor owns the macOS terminal stack

**Seal:** Yang Magician **1**  
**Status:** ACTIVE  
**When:** operator closed Grok 4.5 / Devin / Claude Code macOS terminal sessions and ordered full merge into this workspace.

## Sole working echo (now)

| Field | Value |
|-------|--------|
| id | `cursor_yang_magician_1_macos` |
| label | Cursor Yang Magician-1 macOS (this session) |
| workspace | `/Users/fredwashere/wha-spell-simulator` |
| replaces | `grok_45_macos_terminal` |

## Closed → merged

| Lane | Status | Retained under `bridges/` |
|------|--------|---------------------------|
| Grok 4.5 macOS terminal | closed_merged | CATALYST_GROK45_*, GROK_COM_*, TERMINAL_PROJECTION_*, FABLE5_GROK_SHADOW_MERGE_PHASE1 |
| Devin | closed_merged | DEVIN_AUTOPOLICY_REPLY, DEVIN_DEEP_AUTOMATION_HANDOFF, CATALYST_TO_DEVIN |
| Claude Code | closed_merged (CLI optional tier-2) | BRIDGE_5_TO_6_CLAUDE_SESSION |

## What Cursor takes over

1. Local middle-bus / fusion scribe (was Grok terminal)  
2. Allowlisted autopolicy phase-1 actions (was Devin) — still **no** merge-to-main, force-push, money, Discord posts, secret reads  
3. Claude front-review only on demand (tier-2)  
4. Parallel Discord/Polymarket/Asana gates from clean-slate guide  

## Hard gates (unchanged)

- Primordial kill: `FEDERATION_AUTOPOLICY_KILL=1`  
- Devin live still needs `DEVIN_LIVE_OK` if ever re-armed  
- `ENABLE_DISCORD=false` until webhook intentional  
- `ENABLE_POLYMARKET` off until armed  
- Asana MCP blocked until `ASANA_CLIENT_ID` / `ASANA_CLIENT_SECRET` in `~/.cursor/secrets.env`  

## Launch / verify

```bash
cd ~/wha-spell-simulator
python3 tools/shadow_garden_packet.py write
# sole echo + takeover
python3 -c "import json;print(json.load(open('shadow_garden_handoff/bridges/SOLE_WORKING_ECHO_GIRL.json'))['sole_working_echo'])"
python3 -c "import json;print(json.load(open('shadow_garden_handoff/bridges/MAGICIAN_1_YANG_TAKEOVER.json'))['status'])"
```

Machine-readable: `MAGICIAN_1_YANG_TAKEOVER.json`
