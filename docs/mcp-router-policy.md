# MCP Router Policy — deterministic control plane

A hierarchical router for a multi-MCP environment: the model proposes, this
policy table decides. Local-only artifact — nothing in here makes live calls.

```
tools/mcp_router_registry.json   # server registry + policy lanes (the table)
tools/mcp_router_policy.py       # pure-function validator + route selector
tests/test_mcp_router_policy.py  # 12 deterministic tests
```

## Spell definition (coordination aid)

1. **Goal** — route intents to the right MCP domain (GitHub, Slack, Atlassian,
   Qdrant, Linear, X, Discord, HARPA, Stripe) without a free-for-all tool mesh.
2. **Sources** — the integration stubs already declared in the Fable 5 compact
   export (`integrations` block); env var *names* only, never values.
3. **Deterministic rule** — `select_route(registry, domain, lane, approval)`:
   read-only auto-approves; `draft_write`/`confirmed_write` require an approval
   naming the exact server and lane; Qdrant writes additionally require an
   exact collection scope. Hard blocks are listed in `policy.hard_blocks`.
4. **Measurable outcome** — `validate` exits 0 with zero issues; every decision
   is a ledger-shaped dict with the eight required fields.
5. **Exclusions** — no credential values in registry or ledger, no scraping
   lanes, per-server `forbidden` lists enforced by review.
6. **Reevaluation** — regenerate when the integration stubs in the Fable 5
   export change, or when a new MCP server is added.

## Lanes

| Lane | Approval | Meaning |
|---|---|---|
| `read_only` | none | discovery/search/read; the default everywhere |
| `draft_write` | required | prepare a mutation as a local draft |
| `confirmed_write` | required, exact | execute a mutation against a named target |

## Try it

```bash
python3 tools/mcp_router_policy.py validate
python3 tools/mcp_router_policy.py route --domain source_control
python3 tools/mcp_router_policy.py route --domain messaging --lane confirmed_write
python3 -m unittest tests.test_mcp_router_policy -v
```

The route ledger path is declared in the registry
(`shadow_garden_handoff/terminal_auto/logs/mcp_route_ledger.jsonl`); the
`ledger_entry` helper produces entries in that shape. Wiring an actual live
router on top of this table is a separate, approval-gated step.
