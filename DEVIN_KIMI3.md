# Devin + Kimi3 — wha-spell-simulator

Generated: 2026-07-29T18:32:45Z

## Project

- **Path:** `/Users/fredwashere/wha-spell-simulator`
- **Blurb:** Fable5 spell sim + shadow_garden_handoff bridges. Evolve tools/, tests/, bridges; keep content-neutral.

## Start session

```bash
source ~/.config/kimi/env
cd /Users/fredwashere/wha-spell-simulator
# Devin:
devin
# Codex:
codex
```

## Models

- Planning / general: `KIMI_MODEL=kimi-k2.6`
- Code-heavy: `KIMI_CODE_MODEL=kimi-k2.7-code`
- Base URL: `https://api.moonshot.ai/v1` (OpenAI-compatible)
- **Note:** account must have balance; last probe returned HTTP 429 insufficient balance

## Context files

- `~/production/kimi3_evolution/PROJECT_REGISTRY.json`
- `~/ShadowGarden/live/spacetime_alchemy/KIMI3_DEVIN_PERPLEXITY_HANDOFF.md`
- This directory's `AGENTS.md` / `README.md` if present

## Do not

- Commit secrets
- Paste keys into Perplexity / Discord / public chats
- Arm `KIMI3_TRANSITION_ARMED` without operator intent
- Generate prohibited content

## First evolve tasks (suggested)

1. Inventory scripts/tests and note broken entrypoints
2. Add/refresh README section for multi-agent open path
3. Fix lint/type issues if tooling exists
4. Wire OpenAI-compatible client to env names only (no hardcoding keys)
5. Leave a short CHANGELOG or handoff note for the next agent
