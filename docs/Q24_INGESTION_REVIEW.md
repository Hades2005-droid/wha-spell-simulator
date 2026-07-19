# Q24 Recommendation — Ingestion Risk Review

**Verdict:** safe to ingest as scaffolding, with 4 items to scrub or gate first.

## Risk Table

| # | Risk | Severity | Action |
|---|------|----------|--------|
| 1 | **Embedded infra identifiers** — the source doc hard-codes cloud IDs, team UUIDs, and credential handles. Not secrets, but they leak infra topology if this packet is passed to other agents. | **Med** | Redact to placeholders before any cross-agent ingestion. They are metadata, not needed for the design. |
| 2 | **Content-architecture dominates code risk.** The adult-DLC-in-separate-depot pattern is correct, but ingestion must guarantee **no adult scene paths in the base pack manifest** — a single-flag unlock is a Steam policy violation, not just a smell. | **High** | `ContentRegistry` must register adult scenes at runtime only. Verify the adapter enforces it; do not trust prose alone. |
| 3 | **External repo reference** (third-party patch, Appendix A). Currently `action: none_taken`, symbolic-only. Correct. The risk is a future step silently cloning or vendoring it. | **Low** | Keep it a reference string. Never ingest its code — third-party patch for a commercial title. |
| 4 | **Consent-gate as prose vs. enforcement.** Design says consent transitions live in the state machine, not the UI layer alone. Good design — but a doc stating it is not the adapter doing it. | **Med** | Confirm `Q24StateAdapter` actually has consent gate-states in `TRANSITION_TABLE`, else it is an unbacked claim. |

## Clean Strengths (low ingestion risk)

- `symbolic_only: true` contract holds throughout.
- Determinism preserved via Python engine wrap (byte-identical replay — verified 6/6).
- No rendered adult assets in the bundle.

## Gate Procedure

1. Run the adapter with `--send` **off** first.
2. Confirm output flags items 1 and 4 above.
3. Rotate keys.
4. Then go live with `--send`.

If the adapter does not surface items 1 and 4, its risk pass is too shallow — do not proceed.

## Standing Boundary Rules

These apply to all agents ingesting this packet:

- Never paste raw API tokens (`pplx-*`, `xai-*`, `sk-*`).
- Never inline adult HTML or rendered scene content.
- Never include jailbreak-polarity text.
- Keys live in `.env` only, never in committed source.
