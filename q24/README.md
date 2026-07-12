# Q24 Unified Deliverable — Shadow Garden Project

Part 3/3. One archive. Four layers.

```
q24_unified/
├── canon/
│   └── q24_canonical.yaml                                        # symbolic-only anchor
├── godot/
│   ├── Q24_EternalDao_Temperance14_HarmonyParadox_19to10to1.tres # the .tres asset
│   ├── Q24CanonicalAnchor.gd                                     # resource class
│   ├── GameSession.gd                                            # autoload, state owner
│   ├── SaveManager.gd                                            # autoload, user:// saves
│   ├── ContentRegistry.gd                                        # base + adult DLC separation
│   └── Q24StateAdapter.gd                                        # wraps Python engine
├── ren_py/
│   └── game/q24_canon.rpy                                        # optional VN fallback
└── report/
    └── Q24_Alpha_Component_Recommendation.md                     # full recommendation
```

Canonical id: `q24_eternal_dao_temperance_14_harmony_paradox_ignite_19_10_1`
Symbolic only. Not physics. Not executable authority.
Fable5 bedrock coupling: `0.4.0-engine-bedrock-10`.
Bridge signature: `f2e596cd043d6819`.

Read `report/Q24_Alpha_Component_Recommendation.md` first.
