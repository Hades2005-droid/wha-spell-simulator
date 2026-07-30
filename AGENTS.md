# AGENTS.md — wha-spell-simulator

Generated: 2026-07-29T18:32:45Z

## Purpose

Fable5 spell sim + shadow_garden_handoff bridges. Evolve tools/, tests/, bridges; keep content-neutral.


## Multi-agent stack

| Tool | Role |
|------|------|
| **Kimi3** (Moonshot `kimi-k2.6` / `kimi-k2.7-code`) | Primary evolve / code agent after balance recharge |
| **Devin** | Long-horizon engineering sessions in this directory |
| **Perplexity** | Research + synthesis; no secret paste |
| **Codex** | Local CLI agent: `codex` |
| **Grok / Shadow Garden** | Lattice + :8790 control plane |

### Secrets

```bash
source ~/.config/kimi/env
```

- Never commit `.env`, `.env.local`, or `~/.config/kimi/env`
- Never write API keys into JSON/MD artifacts
- Registry: `~/production/kimi3_evolution/PROJECT_REGISTRY.json`
- Handoff: `~/ShadowGarden/live/spacetime_alchemy/KIMI3_DEVIN_PERPLEXITY_HANDOFF.md`

### Evolution defaults

1. Read this file + repo README first
2. Prefer small reversible commits / patches
3. Run existing tests if present
4. Keep Discord/webhooks paused unless operator-armed
5. Content-neutral for persona/lattice work

