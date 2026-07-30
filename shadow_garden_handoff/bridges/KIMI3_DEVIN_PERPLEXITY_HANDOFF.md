# Kimi3 × Devin × Perplexity — Project Evolution Prep

Generated: `2026-07-29T18:32:23Z`

## Status

| Item | State |
|------|--------|
| API key stored | `~/.config/kimi/env` (mode 600) + gitignored project envs |
| Auth (`api.moonshot.ai`) | **OK** (models list HTTP 200) |
| Chat completions | **Blocked** — insufficient balance (HTTP 429) → recharge |
| Available models | `kimi-k2.6`, `kimi-k2.7-code` |
| Default model | `kimi-k2.6` |
| Code model | `kimi-k2.7-code` |
| CN endpoint | Invalid for this key (use `.ai` not `.cn`) |

## Load secrets (never paste into Perplexity/Discord)

```bash
source ~/.config/kimi/env
# or
eval "$(kimi-env)"
```

## Open projects

### Primary
- **`/Users/fredwashere/ShadowGarden`** — VOID-IGNITION / lattice / ST staging (dir)
  - Codex: `cd /Users/fredwashere/ShadowGarden && codex`
- **`/Users/fredwashere/shadow-jing-garden`** — Vite app + federation + AGENTS (git, npm, AGENTS)
  - Codex: `cd /Users/fredwashere/shadow-jing-garden && codex`
- **`/Users/fredwashere/wha-spell-simulator`** — Fable5 / handoff bridges / tools (git, npm)
  - Codex: `cd /Users/fredwashere/wha-spell-simulator && codex`
- **`/Users/fredwashere/xai-sdk-python`** — xAI official Python SDK clone (git, py)
  - Codex: `cd /Users/fredwashere/xai-sdk-python && codex`
- **`/Users/fredwashere/SillyTavern`** — SillyTavern main install (git, npm)
  - Codex: `cd /Users/fredwashere/SillyTavern && codex`
- **`/Users/fredwashere/ComfyUI`** — Open-weight image pipeline (git, py, AGENTS)
  - Codex: `cd /Users/fredwashere/ComfyUI && codex`
- **`/Users/fredwashere/Movies/Grok-Videos`** — Grok video / ST merge scripts (git)
  - Codex: `cd /Users/fredwashere/Movies/Grok-Videos && codex`
- **`/Users/fredwashere/shadow-garden-launcher`** — Launcher (git)
  - Codex: `cd /Users/fredwashere/shadow-garden-launcher && codex`
- **`/Users/fredwashere/flux_klein_local`** — Flux Klein local (git)
  - Codex: `cd /Users/fredwashere/flux_klein_local && codex`
- **`/Users/fredwashere/gitmynotes`** — Notes repo (git)
  - Codex: `cd /Users/fredwashere/gitmynotes && codex`
- **`/Users/fredwashere/shadow_garden_mesh`** — Mesh mirrors + packages (dir)
  - Codex: `cd /Users/fredwashere/shadow_garden_mesh && codex`
- **`/Users/fredwashere/shadow_garden_mcp`** — MCP packages (dir)
  - Codex: `cd /Users/fredwashere/shadow_garden_mcp && codex`
- **`/Users/fredwashere/shadow_garden_may30_monitoring`** — Monitoring + home black sun (npm)
  - Codex: `cd /Users/fredwashere/shadow_garden_may30_monitoring && codex`
- **`/Users/fredwashere/xai-voice-pack`** — Voice pack (dir)
  - Codex: `cd /Users/fredwashere/xai-voice-pack && codex`
- **`/Users/fredwashere/echo-agent-bundle`** — Echo agent bundle (dir)
  - Codex: `cd /Users/fredwashere/echo-agent-bundle && codex`
- **`/Users/fredwashere/production`** — Production lattice tools (dir)
  - Codex: `cd /Users/fredwashere/production && codex`
- **`/Users/fredwashere/shadow-garden-launcher`** — Launcher (git)
  - Codex: `cd /Users/fredwashere/shadow-garden-launcher && codex`

### Secondary (worktrees / copies)
- `/Users/fredwashere/CascadeProjects/shadow-jing-garden-agent-merge`
- `/Users/fredwashere/CascadeProjects/shadow-jing-garden-pr15`
- `/Users/fredwashere/CascadeProjects/shadow-jing-garden-pr33`
- `/Users/fredwashere/CascadeProjects/sjg-1783725409-remove-unused-imports`
- `/Users/fredwashere/CascadeProjects/sjg-1783726150-fstring-noplaceholder`
- `/Users/fredwashere/Desktop/shadow-jing-garden`
- `/Users/fredwashere/Desktop/light-jing-garden 2 + 3 = 5 bridge copy`
- `/Users/fredwashere/Desktop/Eden/wha-spell-simulator`
- `/Users/fredwashere/Desktop/Eden/Eden-x-Shadow-Gaden`
- `/Users/fredwashere/ShadowGarden/SillyTavern`
- `/Users/fredwashere/shadow_garden_mesh/gitmynotes`
- `/Users/fredwashere/shadow_garden_mesh/flux_klein_local`
- `/Users/fredwashere/shadow_garden_mesh/wha-spell-simulator-ytnrvdf`
- `/Users/fredwashere/shadow_garden_may30_monitoring/sillytavern`

## Recommended evolution order

1. ShadowGarden (control plane, lattice, ST)
2. wha-spell-simulator (bridges, Fable5 tools)
3. shadow-jing-garden (app + federation)
4. xai-sdk-python (SDK)
5. SillyTavern
6. ComfyUI
7. Movies/Grok-Videos
8. mesh / monitoring / flux

## Devin playbook

```bash
source ~/.config/kimi/env
cd ~/ShadowGarden   # or other primary
devin
# Prefer KIMI_MODEL=kimi-k2.6 for planning, kimi-k2.7-code for code edits
```

- Attach this file + `PROJECT_REGISTRY.json` as context.
- Do **not** commit `.env`, `.env.local`, or `~/.config/kimi/env`.
- Keep Discord paused unless explicitly armed.

## Perplexity playbook

- Research / synthesis only; use existing `PERPLEXITY_API_KEY` in ShadowGarden `.env`.
- Point at public docs + local handoff JSON paths — **never** paste API keys.
- Existing bridge: `wha-spell-simulator/tools/perplexity_asuna_central_control.py`

## Codex playbook

```bash
codex --version   # expect 0.146.0+
cd ~/xai-sdk-python && codex
```

## Refresh lattice catalogs

```bash
source ~/.config/kimi/env
python3 ~/wha-spell-simulator/tools/kimi3_asuna_point0_unify.py write
python3 ~/wha-spell-simulator/tools/local_open_weights_mesh_prep.py write
python3 ~/wha-spell-simulator/tools/perplexity_asuna_central_control.py write 2>/dev/null || true
```

## Security

- API key was pasted in chat — **rotate after recharge** if this session is shared.
- Artifacts under this prep **never** embed secret values (env names only).
- `KIMI3_TRANSITION_ARMED` stays unset until you intentionally cut over to local mesh.
