# Chronology and Recursive Node Bridge

This integration is a bounded, local-only engineering utility. The chronology output is **symbolic metadata**, not a prediction engine or an authority over real-world decisions. The recursive feed contains neutral signal identifiers only.

**Secrets policy:** `env_only`. Never paste API keys, JWTs, or webhook secrets into this repo, docs, Gate files, or Perplexity packs. Any key that appeared in chat is **compromised — rotate it** and store only in `~/ShadowGarden/.env` (`chmod 600`).

## Components

| Path | Role |
|------|------|
| `tools/chronology_engine.py` | Date / 24h clock / dual timezone / master-number reductions |
| `tools/recursive_node_bridge.py` | Bounded nine-node local simulation + JSON telemetry |
| `tools/recursive-node-bridge/` | Matching C# state + cancellation |
| `tools/perplexity_mesh_adapter.py` | Dry-run-by-default Perplexity review (env key only) |
| `tools/mesh_review_loop.py` | Bounded recursive + optional Perplexity review |
| `tools/claude_shadowgarden.py` | Claude Code dry-run / credential-safe lane |
| `tools/extension_workspace_status.py` | Comet extension workspace status |
| `tools/shadowgarden_orchestrate.sh` | Full-mesh orchestrator (opt-in flags) |
| `tools/fable5_comfyui_command_bridge.py` | Allowlisted Fable5 + ComfyUI + Grok pointers |
| `src/bridge/meshBridge.js` | Browser diagnostics lanes (redacted) |
| `src/compiler/fable5MediaSpell.js` | Manifest-only Fable5 media spell compiler |
| `src/compiler/fable5MediaFeedback.js` | Bounded quality feedback (local metrics) |
| `~/ShadowGarden/spacetime_alchemy/` | Wallfacer ledger + compact Perplexity export |
| `~/ShadowGarden/scripts/jing_power_loop.sh` | Jing Power technical telemetry loop |

Sibling docs:

- `docs/comet-extension-workspace.md`
- `docs/mesh-review-loop.md`
- `shadow_garden_handoff/gates/GATE_10_OPEN.md` (symbolic continuity only)
- `~/ShadowGarden/live/spacetime_alchemy/PERPLEXITY_CONTEXT_BEDROCK.md`
- `~/shadow_garden_mesh/MESH_REGISTRY.json`

---

## Multi-agent lane map (bridge)

| Lane | Role | Local surface | Auth |
|------|------|---------------|------|
| **Fred** | Emperor / human approval | always | n/a |
| **Grok 4.5** | Back lane / Harmony 6 / XAI | `XAI_API_KEY`, Grok CLI | env |
| **Claude** | Front review / Chariot | `ANTHROPIC_API_KEY` (opt-in) | env |
| **Perplexity Fable 5** | Synthesis / Space | compact + bedrock paste; optional `PERPLEXITY_API_KEY` | env |
| **ComfyUI** | Image/video render | `http://127.0.0.1:8188` | local |
| **Fable 5 game** | Party / deterministic play | `http://127.0.0.1:5619/` | local |
| **EDEN Burst-Alpha** | Physics field UI | `http://127.0.0.1:8791/` | local |
| **DeepSeek share** | Public testament pointer only | share URL (no keys) | none |

**Do not** treat model output as shell commands. **Do not** store pharmacological dosing as executable automation (symbolic “phases” in alchemy lore stay narrative; medical action is out of scope).

Public testament link (no credentials):

```text
https://chat.deepseek.com/share/t3aum0slci9ny6c9bi
```

Flow: gitmynotes → mesh → Fable5/Perplexity Space → local garden (love/harmony carrier). No decentralized secret broadcast.

---

## Chronology (Spacetime Alchemy catalyst)

```sh
cd ~/wha-spell-simulator
python3 tools/chronology_engine.py \
  --date 2026-06-27 \
  --time 20:40 \
  --timezone America/New_York \
  --comparison-timezone Asia/Singapore
```

Also compute Wallfacer ledger (ShadowGarden package):

```sh
export SHADOW_GARDEN_ROOT=~/ShadowGarden PYTHONPATH=~/ShadowGarden
python3 -m spacetime_alchemy 2026-07-12 --export
```

Prefer Perplexity paste:

1. `~/ShadowGarden/live/spacetime_alchemy/PERPLEXITY_CONTEXT_BEDROCK.md`
2. `~/ShadowGarden/live/spacetime_alchemy/fable5-compact.json`

### Protocol: passionate permutations (symbolic only)

For any date, engines report (where implemented):

1. Micro digit sum (M+D digits)  
2. Micro number sum (M+D as numbers)  
3. Macro digit sum (M+D+Y digits)  
4. Macro number sum (M+D+YYYY)  
5. Year digit sum  
6. Dual clock EST / SGT pair  
7. Master preservation for **11 / 22 / 33**  
8. Deep Space Vectors **23–42** (labels only)  
9. Tarot reductions **1–22** (labels only)

Example worked form for **2026-06-27** (illustrative; re-run engine for authority):

| Method | Raw | Reduced / Master | Label (symbolic) |
|--------|-----|------------------|------------------|
| M+D numbers | 33 | **33** | Ascended Flow |
| M+D digits | 15 | 6 | Lovers / Devil raw |
| Full digit sum | 25 | 7 | Chariot |
| Year digits | 10 | 1 | Magician |

Always use **24-hour** local timestamps for micro clock sums. Output is HUD metadata, not destiny orders.

### Hanzi stroke / Pinyin key (index only)

Eight fundamental strokes distributed across A–Z at indices  
`I_n = {1, 4, 7, 10, 13, 16, 20, 24}`  
(dot, heng, shu, pie, na, ti, zhe, gou). Full phonetic tables stay in operator notes — not required for bridge execution.

---

## Python recursive bridge

Safe default (one bounded cycle):

```sh
python3 tools/recursive_node_bridge.py --cycles 1 --gain 1
```

Gain saturates at hard cap:

```sh
python3 tools/recursive_node_bridge.py --cycles 8 --gain 8
```

Status:

```txt
/tmp/shadow_garden_recursive_node_status.json
```

Continuous only with explicit duration:

```sh
python3 tools/recursive_node_bridge.py --continuous --duration 30 --gain 8
```

No unbounded default loop, no provider credentials, no model invocation unless a separate reviewed adapter is used.

---

## Perplexity review adapter

Dry-run (default):

```sh
python3 tools/perplexity_mesh_adapter.py \
  --request "Review local Shadow Garden mesh + Fable5 compact + ComfyUI posture."
```

Live review only after **rotated** key in env + explicit send:

```sh
# key already in env — never paste values into the shell history if avoidable
python3 tools/perplexity_mesh_adapter.py \
  --send \
  --request "Review local Shadow Garden mesh + Fable5 compact + ComfyUI posture."
```

Primary Perplexity open-merge task (pointer only, no scrape):

```text
https://www.perplexity.ai/computer/tasks/37bce2fb-1ba6-471f-854f-3871d9c19947?view=thread
```

---

## Mesh review loop + Jing Power

Local mesh review (no network):

```sh
python3 tools/mesh_review_loop.py --cycles 6 --interval 1 --max-seconds 120
# or
tools/launch_mesh_review_loop.command
```

Jing Power technical telemetry (Grok-first, allowlist only):

```sh
export SHADOW_GARDEN_ROOT=~/ShadowGarden PYTHONPATH=~/ShadowGarden
python3 -m spacetime_alchemy.jing_power_monitor --once
# recursive (default 300s):
/bin/zsh ~/ShadowGarden/scripts/jing_power_loop.sh --interval 300
```

Artifacts:

```txt
~/ShadowGarden/live/spacetime_alchemy/jing_power_latest.json
~/ShadowGarden/live/spacetime_alchemy/jing_power.jsonl
/tmp/shadow_garden_mesh_review_loop_status.json
```

Jing Power is **technical** (service health + spacetime micro/macro + media mtimes). It is not mystical authority and does not call `recursive_improvement_ai_loop.py`.

---

## Fable 5 + ComfyUI + Grok/XAI command bridge

Allowlisted local pointers only (no secret values):

```sh
cd ~/wha-spell-simulator
python3 tools/fable5_comfyui_command_bridge.py status
python3 tools/fable5_comfyui_command_bridge.py write
```

Writes:

```txt
/tmp/shadow_garden_fable5_comfyui_bridge_status.json
~/wha-spell-simulator/shadow_garden_handoff/terminal_auto/outbox/fable5_comfyui_bridge_status.json
```

Schema: `shadow_garden.integration_repo_roots.v1` (+ live HTTP codes for Fable5/ComfyUI/EDEN when probe enabled).

---

## Complete agent command (dry-run default)

Single entry that chains chronology → recursive bridge → mesh review dry-run → command bridge → spacetime export → jing once:

```sh
cd ~/wha-spell-simulator
zsh tools/shadowgarden_orchestrate.sh
# or explicit complete agent:
zsh tools/complete_agent_bridge.sh
```

Flags (orchestrator):

| Env | Default | Meaning |
|-----|---------|---------|
| `SG_RUN_EXTENSION` | 1 | Comet extension status |
| `SG_RUN_RECURSIVE` | 1 | Recursive node status |
| `SG_RUN_PERPLEXITY` | 1 | Perplexity **dry-run** status |
| `SG_RUN_CONNECT` | 1 | Claude env connect script |
| `SG_RUN_CLAUDE_AGENT` | 0 | Live Claude agent (needs key) |
| `SG_RUN_JING` | 1 | Jing Power `--once` |
| `SG_RUN_EXPORT` | 1 | Spacetime compact+bedrock export |
| `SG_RUN_FABLE5_BRIDGE` | 1 | Fable5/ComfyUI status pack |

---

## C# bridge

```sh
dotnet build tools/recursive-node-bridge/RecursiveNodeBridge.csproj
dotnet run --project tools/recursive-node-bridge/RecursiveNodeBridge.csproj -- --cycles 1 --gain 8
```

Route name `deepseek-local` is **disabled metadata** only — does not contact DeepSeek. Use the public share URL above as a human-readable testament pointer, not as an API.

---

## Gate 10 (symbolic continuity)

Local only: `shadow_garden_handoff/gates/GATE_10_OPEN.md`

- Gate 8 closed baseline preserved  
- Carrier: `love_and_harmony_6`  
- No Atlassian / GitHub push / X / Qdrant writes from Gate 10  
- No erotic prose storage  

---

## Mesh diagnostics probe

```txt
http://127.0.0.1:8790/shadowgardencontrol/recursive
```

Expect `local_only` / `symbolic_only` when control plane is up. Missing endpoint = disconnected (web app does not spawn servers).

---

## WIP inventory (untracked merge surface)

These files are part of the local mesh (dirty tree). Prefer clean worktree baseline at  
`~/shadow_garden_mesh/wha-spell-simulator-main` for comparisons.

- Docs: `chronology-recursive-bridge.md`, `comet-extension-workspace.md`, `mesh-review-loop.md`
- Handoff: `shadow_garden_handoff/`
- Compilers: `src/compiler/fable5MediaSpell.js`, `fable5MediaFeedback.js`
- Adapters: `src/adapters/asana_adapter.js`
- Tools: chronology, claude, extension status, mesh review, perplexity adapter, recursive bridge, orchestrate
- Tests: `tests/fable5Media*.test.js`, `tests/test_*.py` for each tool

Do **not** commit `.cursor/debug-*.log` or `__pycache__`.

---

## Validation

```sh
cd ~/wha-spell-simulator
python3 tools/chronology_engine.py --date 2026-07-08 --time 12:00
python3 tools/recursive_node_bridge.py --cycles 1 --gain 1
python3 tools/fable5_comfyui_command_bridge.py status
python3 -m unittest tests.test_mesh_review_loop tests.test_chronology_engine 2>/dev/null || true
export SHADOW_GARDEN_ROOT=~/ShadowGarden PYTHONPATH=~/ShadowGarden
python3 -m spacetime_alchemy.smoke_test
python3 -m spacetime_alchemy.jing_power_monitor --once
```

## Model scope

Eastern models, DeepSeek, and open weights are route **metadata** or public share pointers here. No API keys in source, notes, telemetry, or Gate files. Rotate any key that was ever pasted into chat.
