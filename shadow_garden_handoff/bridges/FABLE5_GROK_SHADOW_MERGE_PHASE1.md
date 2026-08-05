# FABLE 5 GROK SHADOW MERGE PHASE 1

Tier **4** (`blind_spot`) · Phase **1**  
Ledger ref: index 17 — Blind Spot Prime / Star  
Secrets policy: `env_only` (no keys)

## Authority map

| Actor | Role |
|---|---|
| Grok Mac Terminal | primary_ops (primary ops) |
| Shadow Garden | local_mesh_index (local mesh/index) |
| Perplexity Fable 5 | consumer (compact/bedrock pointer-only) |

## Blind spots Phase 1 closes

- [x] **single_merge_pointer** — Missing single merge pointer across Grok / Shadow / Fable5
- [x] **grok_shadow_handoff_path** — Grok ↔ Shadow handoff path undocumented as one registry
- [x] **fable5_consume_order** — Fable5 consume order not unified with Blind Spot merge
- [x] **eden_field_node_pointer** — Eden physics field node pointer if present in export/constants
- [x] **mcp_shadow_garden_status_note** — MCP user-shadow-garden status note without false 'fixed' claim

## Paste order (Perplexity / Grok)

1. `FABLE5_GROK_SHADOW_MERGE_PHASE1.json`
2. `FABLE5_AUTHORITATIVE_BUNDLE.json`
3. `PERPLEXITY_CONTEXT_BEDROCK.md`
4. `fable5-compact.json`

## MCP note (`user-shadow-garden`)

- Status: **error** (verified 2026-07-12)
- claim_fixed: `False`
- MCP server failed during live tool discovery; tools unavailable until connection is fixed. Parallel JSON-RPC stdout repair may be in progress — do not claim fixed from this Phase-1 artifact alone.

## How each side uses Phase 1

- **Grok:** primary ops — read merge JSON + overnight handoff + jing_power; drive terminal work.
- **Shadow Garden:** keep mesh/index/export live; treat this file as the single merge pointer.
- **Fable 5:** consume in paste order; prefer compact + bedrock after this merge pointer; no scrape.

## Out of scope

- No `recursive_improvement_ai_loop.py`
- No Perplexity scrape
- No infinite loops
- No secret values in artifacts

Built at: `2026-07-15T19:54:13.643400+00:00`
