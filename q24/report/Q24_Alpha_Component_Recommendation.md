# Q24 Alpha Component Recommendation — Shadow Garden Project

**Deliverable:** Part 3/3, unified asset bundle.
**Version:** 1.0.0
**Canonical identifier:** `q24_eternal_dao_temperance_14_harmony_paradox_ignite_19_10_1`
**Symbolic-only:** true
**Fable5 bedrock coupling:** `0.4.0-engine-bedrock-10`
**Bridge signature:** `f2e596cd043d6819`

---

## 0. What this bundle is

One unified deliverable that closes the Magician-1 (Sovereign Prime) → High-Priestess-2 (Q24) arc for the Shadow Garden alpha. It contains four layers, in one archive:

1. **Canon layer** — the Q24 canonical identifier as YAML, marked `symbolic_only: true`, preserving Temperance 14 unreduced and the 19 → 10 → 1 ignition path.
2. **Godot bedrock** — a Godot 4 `.tres` resource plus the autoload contracts (`GameSession`, `SaveManager`, `ContentRegistry`, `Q24StateAdapter`, `Q24CanonicalAnchor`) that turn the existing deterministic Python state machine into a playable vertical slice.
3. **Ren'Py wrapper (optional)** — a minimal `q24_canon.rpy` that mounts the same Python engine inside Ren'Py for the visual-novel path.
4. **Fable5 engine bedrock 10 reference** — the live Three.js voxel preview (v0.4.0-engine-bedrock-10) with Temperance-14 toggle, quantum-gap ring, primordial 5, catalyst circle — used as the playable proof-of-concept while the Godot alpha is built.

The bundle is content-neutral scaffolding. No rendered adult assets are included, and none are recommended for the base build.

---

## 1. Executive recommendation

**Adopt a two-track engine plan, not a single-engine choice.**

| Track | Engine | Role | Why |
|------|--------|------|-----|
| **A** | **Godot 4** | Primary alpha for a navigable 3D, six-scene, Steam-shipped title | The updated scope (Minecraft-like world, Hades player controller, six spatial simulations, Steam DLC separation) has moved past what Ren'Py alone can support. Godot 4 provides the 3D scene graph, physics, and DLC-separation surface. |
| **B** | **Ren'Py** | Narrative fallback / visual-novel path if the alpha pivots back to text-first | Wraps the existing `shadowgarden_unified_game.py` deterministic state machine with almost zero rewrite because Ren'Py runs Python. Kept as an intentional fallback, not a discard. |

Both tracks share:

- the **same canonical anchor** (`Q24_EternalDao_Temperance14_HarmonyParadox_19to10to1.tres` / `q24_canon.rpy`),
- the **same Python state machine** (`shadowgarden_unified_game.py`, `MAX_TURNS = 24`),
- the **same Steam-compliant DLC separation pattern** (base pack + adult pack in a separate depot).

This preserves the deterministic engine already validated by the 18-seed tournament tests, and it keeps the alpha's asset budget in one place regardless of which front-end is chosen.

---

## 2. Canonical identifier (symbolic only)

```yaml
id: q24_eternal_dao_temperance_14_harmony_paradox_ignite_19_10_1
symbolic_only: true
sequence: [19, 10, 1]
anchor: 14
reduce_anchor: false
carrier: love_and_harmony_6
display:
  en: "Eternal Dao: Temperance 14, Perfect Harmony Paradox"
  zh: "永恒之道：十四节制与完美和谐悖论"
  ja: "永遠の道：節制14と完全調和のパラドックス"
  ko: "영원의 도: 절제 14와 완벽한 조화의 역설"
```

- **14 stays 14.** The anchor is not reduced to `1+4=5`. This is enforced by `reduce_anchor: false` and mirrored in every consumer (Godot resource, Ren'Py dict, catalyst circle JSON).
- **19 → 10 → 1** is the explicit ignition path. It maps to the same Sun-19 + Moon-18 = 37 → gap-10 → loop-19 hinge already encoded in `shadow_garden_mirror/vector_evolution/quantum_gap/scaffold.json` (sig `8116ed3788a22448`).
- **`symbolic_only: true`** is contractual. The identifier is metadata for the state machine and scene registry. It is not physics, not executable authority, and not a safety override.

Godot asset name (preserved verbatim):

```
Q24_EternalDao_Temperance14_HarmonyParadox_19to10to1.tres
```

---

## 3. Godot 4 bedrock — file layout

```
q24/
├── autoload/
│   ├── GameSession.gd          # runtime state ownership + save-load contract
│   ├── SaveManager.gd          # user:// save slots, canonical_id gated
│   └── ContentRegistry.gd      # base pack + DLC pack separation
├── adapters/
│   └── Q24StateAdapter.gd      # wraps shadowgarden_unified_game.py, byte-identical replay
├── canon/
│   ├── Q24_EternalDao_Temperance14_HarmonyParadox_19to10to1.tres
│   └── Q24CanonicalAnchor.gd
├── scenes/
│   ├── world/ShadowWorld.tscn                (voxel world, Hades controller)
│   ├── simulations/Simulation01..06.tscn     (six shadow simulation scenes)
│   └── ui/MainMenu.tscn
├── content/
│   ├── base/                                  (ships in every build)
│   └── adult_dlc/                             (separate Steam depot, DLC ID gated)
└── python_engine/
    └── shadowgarden_unified_game.py           (imported by Q24StateAdapter, MAX_TURNS = 24)
```

Key contracts (excerpts, full source in the archive):

- `GameSession` owns `player_state`, `world_seed`, `current_simulation`, `q24_turn`, `resonance`, `inventory`, `scene_flags`, `consent_flags`, `installed_content_packs`, `save_version` — exactly the ten fields specified in Grok share #2 message 3.
- `ContentRegistry` refuses to hardcode adult-DLC scene paths in the base build. Adult scenes are registered at runtime only when the DLC pack is installed (Steam `BIsDlcInstalled` on the C# side, or an equivalent ownership check).
- `Q24StateAdapter` never guesses transitions locally. It always delegates to the Python engine, so the 18-seed determinism tests continue to pass on the Godot side.

---

## 4. Fable5 engine bedrock 10 — playable proof

The current live preview is not a placeholder — it is the **Sovereign Prime (Magician 1)** playable ground truth that the Godot alpha will inherit:

- 4 warpable 3D shadow scenes (Fields of Doubt, Glory of the Black Sun, Winter Win, Sunstop) — the seed of the six-scene alpha.
- Black sun orb + halo at world center.
- 91=10 quantum-gap torus ring at radius 10, y=10.
- 9-point lattice: hades sovereign (dark purple emissive) + 8 octad.
- Primordial 5 larger teal-emissive markers: angela / lainie / sophie / addie / sabina.
- **Temperance 14 dual-mode toggle** (hotkey `T`): `MODE_SOLAR` (PBR-leaning, warm, yang, Yelm 19) ↔ `MODE_LUNAR` (stylized flat, cool, yin, Blue Moon 18). Programmatic hook: `window.justiceToggle14()`.
- Loop-19 collapse: ticks wrap at 19, logs `loop19_ignited_black_sun`.
- Catalyst 3 alchemical circle closure: `catalyst_light + catalyst_gen + catalyst_review` bound to the 91=10 scaffold, sig `85d7b489eb360a65`.

Version: `0.4.0-engine-bedrock-10`. Bridge signature `f2e596cd043d6819`. Federation manifest sources: 14 at v0.5.0 (bumped to 0.5.1 by this deliverable to register the Q24 unified asset).

---

## 5. Decision framework (unchanged, with updated answers)

| Question | Answer |
|----------|--------|
| Preserve existing deterministic engine, or rewrite? | **Preserve.** Wrap `shadowgarden_unified_game.py` via `Q24StateAdapter` (Godot) or `init python:` (Ren'Py). Byte-identical replay stays. |
| Text/narrative-forward, or spatial/graphical? | **Spatial + narrative.** The updated scope (3D world, block interactions, Hades controller, six simulations) makes Godot 4 the primary track. Ren'Py becomes the fallback narrative-only path, not the primary. |
| Adult-only (18+) Steam requirements? | **Yes.** DLC pack in a separate depot. No hidden-toggle unlocks in the base build. Consent-gate transitions are added to the state machine, not to the UI layer alone. |
| Six scenes + nuance layer as content modules, not code branches? | **Yes.** `ContentRegistry` enforces this. Adult scenes never appear in the base pack manifest. |

---

## 6. Integration risks (recap, still binding)

1. **Content-architecture risk dominates code risk.** Steam's payment-processor rules cover all uploaded files, including inaccessible ones. Single-flag unlocks are a policy violation, not just bad practice.
2. **Itch.io is not a safe fallback.** ~20,000 NSFW works deindexed in 2025 under payment-processor pressure. Self-hosted payment is the only channel with lower processor exposure.
3. **Skill-catalog gap.** `catalyst-light-shadow-extension` and `mac-multilingual-translator` are inspectable now — they contain no rendering code that would force a heavier engine choice than Godot 4. Confirmed.
4. **Atlassian design-doc blind spot.** Confluence app-install is still pending. KAN-13 remains the only visible Atlassian anchor.
5. **Consent-aware state design.** Implemented as explicit gate states in `Q24StateAdapter` on top of the existing `TRANSITION_TABLE`, not as UI toggles.
6. **Compliance overhead is ongoing.** Granular content metadata, age-verification API integration, audit trails — budget 7–10% build time.
7. **xAI credit top-up.** The `custom-cred:api.x.ai` handle is wired but the team is currently `permission-denied: team out of credits`. Grok 4.5 in-world dialogue is blocked until top-up.

---

## 7. Next moves (pick any, in order)

1. Zip this bundle and ship it (this deliverable does that).
2. Rename any of the primordial 5 (`angela / lainie / sophie / addie / sabina`) — I'll rewrite the ring and the .tres in one pass.
3. Top up xAI team `afe1e08b-e409-434a-9297-0a2105ffcbb9` so the Grok 4.5 in-world dialogue panel becomes live.
4. Publish Fable5 to a permanent `*.pplx.app` link when you explicitly say publish.
5. Get the Atlassian app installed on `6b617e25-0e28-4b49-a35a-28a7361a73d5` so Confluence six-scene design docs become readable.

---

## 8. Cross-refs (single source of truth)

- Fable5 live preview: [/computer/a/fable5-black-sun-shadow-garden-m9X4GKmaQFuDleHkgrYFnw](https://www.perplexity.ai/computer/a/fable5-black-sun-shadow-garden-m9X4GKmaQFuDleHkgrYFnw)
- Q24 recommendation source app: [/computer/a/9d099171-69ed-479e-aa42-c1f6698a7360](https://www.perplexity.ai/computer/a/9d099171-69ed-479e-aa42-c1f6698a7360)
- Q24 task thread: [ai-generated-video-game-example](https://www.perplexity.ai/computer/tasks/ai-generated-video-game-exampl-QrTieGJzShyyrfBucFBTqw?view=thread)
- Grok share #2: [c2hhcmQtNA_9737c6af](https://grok.com/share/c2hhcmQtNA_9737c6af-3175-41d1-8017-375627c00eaf)
- GitHub repo: `Hades2005-droid/shadow-garden-launcher` (`shaoshi_bridge/south_star/shadowgarden_unified_game.py`)
- Atlassian anchor: KAN-13 on cloud `6b617e25-0e28-4b49-a35a-28a7361a73d5`

---

*symbolic_only: true — this document, the .tres, the YAML, and the Ren'Py dict are metadata labels for the deterministic state machine. They are not physics, not executable authority, and not a safety override.*

---

## Appendix A. Final patch subatomic merge — session close

**Trigger:** user directive `merge this final 14 patch subatomic ly then my work ? and thjink are finished for now`, board-approved auto-agi decision-making, ignite until final engine deliverable assets.

**Registered symbolic reference (not cloned, not executed, not vendored):**

```yaml
related_references:
  - id: kk_hf_patch_public_reference
    kind: external_public_patch
    url: https://github.com/ManlyMarco/KK-HF_Patch.git
    scope: symbolic_only
    role: mod-scene precedent for content-neutral base + separate adult-pack pattern
    action: none_taken
    reason: public third-party patch for a commercial title; used only as an external precedent for the base-pack + adult-DLC separation already recommended in section 4. No code, binaries, or assets from the referenced repository are ingested, copied, redistributed, or executed inside the Shadow Garden bundle.
    symbolic_only: true
```

**Front-lane close, as declared by the user:**

| Lane                | Path                                                                             | State           |
| ------------------- | -------------------------------------------------------------------------------- | --------------- |
| Claude front review | `shaoshi_bridge/outbox/claude_feedback/sonnet46_final_three_catalysts_gift.json` | gifted (manual) |
| Paste return        | `shaoshi_bridge/inbox/claude_feedback/sonnet46_final_catalysts_return.json`      | awaited         |
| Playable sim (local)| `shaoshi_bridge/tools/launch_shadowgarden_unified_game.sh`                       | local-only      |
| Back supervisor     | 45/45 gate + ingest watch                                                        | running (Fred)  |

**What this appendix does NOT do:**

- Does not clone, mirror, or redistribute [KK-HF_Patch](https://github.com/ManlyMarco/KK-HF_Patch.git).
- Does not bind Shadow Garden to any real person or licensed character.
- Does not modify the safety gate. The gate stays as declared: permissive for legal consenting-adult content, refuses minors+sexual, coercion, incest, hidden-cam, trafficking, non-consent, exploitation.
- Does not treat any symbolic identifier as physics, executable authority, or safety override.

**Close state:** Part 3/3 sealed. Federation bumped again to record the merge note.
