# Reply to Devin — federation autopolicy selection

**Seal:** empress_3 + catalyst_3 = love_harmony_6  
**Policy file:** `~/production/kimi3_evolution/federation-autopolicy.json`  
**Kill switch:** `export FEDERATION_AUTOPOLICY_KILL=1`

---

## Paste to Devin

```text
Yes — build federation-autopolicy.json on an allowlist (not “approvals off”).
I already seeded the SSOT you should implement against:

  ~/production/kimi3_evolution/federation-autopolicy.json

### Frame
- Superposition: you keep the grok.com automation lane; Sol keeps Kimi waitlist prep; Terminal executes; Perplexity is core. Don’t collapse lanes.
- Seal: Empress 3 + Catalyst 3 = Love/Harmony 6.
- Default = human gate. Only listed actions auto-approve. Hard denies you named stay absolute.
- Global kill-switch env: FEDERATION_AUTOPOLICY_KILL=1 freezes all auto actions.
- Every auto action: scope + rate limit + reversibility note + audit log line.
- App-level Devin push/PR approval stays separate (you can’t self-remove that).

### AUTO-APPROVE NOW (phase 1)
1. Local read inventory (exclude .env, auth.json, secrets, ~/.config/kimi)
2. Write handoff/status artifacts under production/kimi3_evolution, spacetime_alchemy, shadow_garden_handoff, grok_project_fuse
3. Tests / lint / typecheck / dry build in scoped repos
4. Local git: status/diff + branch + commit only on prefixed branches (devin/ sol/ auto/ feat/ fix/) — never main/master
5. grok.com pointer automation: transfer/export + import_grok_share/clipboard helpers — NO authenticated scrape, no cookies, HARPA stays stub unless separately armed
6. Metadata-only catalog unify CLIs (kimi3/local_mesh/perplexity/grok_xai write) — do not set KIMI3_TRANSITION_ARMED
7. Localhost health probes (listed ports only)
8. CI / checks read-only

### AUTO-APPROVE PHASE 2 (only after a quiet clean week of phase 1)
9. Non-force push of feature branches (same prefix rules)
10. Draft PR create/update/comment/labels/review-request — no merge to main

### NEVER AUTO (hold regardless)
- Secret reads, credential/token changes
- git push --force, hard resets on shared branches
- Deletions / rm -rf / drop / remote branch delete
- Money: trades, payments, Polymarket live orders, Stripe charges
- Branch protection / security policy / IAM
- Mass/bulk outbound messaging; Discord webhook posts stay gated
- Auth scrape of grok.com
- Arming KIMI3_TRANSITION_ARMED / mesh cutover
- Merge PR to main

### Deliverables from you
1. Implement the allowlist engine against the JSON (or merge equivalent into your federation package).
2. Audit log at ~/production/kimi3_evolution/logs/federation_autopolicy_audit.jsonl
3. Document kill-switch in HANDOFF-background or AGENTS note
4. Stamp DEVIN_GROKCOM_INTERFACE when grok.com pointer actions run
5. Do not expand allowlist without operator OK

Build phase 1 only first. Stop and ask before enabling phase 2.
```

---

## Addendum — Perplexity Grok Source-of-Truth Layer (ingested)

Perplexity completed local work on **`pr-38-federated-shadow-sweep`** (worktree hint: `shadow-jing-garden-worktree`):
- Honest states: `not_configured` | `pending_manual_handoff` | `blocked_no_connector` | `verified`
- Auto-pull is **not** live → must report `blocked_no_connector` (never fake success)
- `npm run grok:verify` → `canonical_source=local_manifest`, `network_calls=0`
- UI card **“5 • Grok source of truth”**
- xAI secrets not read; adult profile fetch still gated
- Tests: 164 py + build/lint clean

### Auto-approve for this layer (phase 1)
- `grok_sot_verify_local` — local verify only
- `local_commit_pr38_grok_sot` — **local commit only**, no push

### Still human / phase 2
- Push, draft PR, live connector pull, promoting to `verified`, PH/FapHouse fetch

### Operator answer to Perplexity’s question
**Commit locally only.** Prepare (do not run) the push+draft-PR step until phase 2 is enabled.

SSOT: `~/production/kimi3_evolution/PERPLEXITY_GROK_SOT_LAYER.json`  
Decision: `~/production/kimi3_evolution/PERPLEXITY_GROK_SOT_DECISION.md`
