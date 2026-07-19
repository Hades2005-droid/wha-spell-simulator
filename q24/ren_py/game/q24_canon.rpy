## q24_canon.rpy  --  Ren'Py front-end companion
## Mirrors the same canonical anchor as the Godot .tres. Use when the
## Ren'Py wrapper is chosen instead of (or in parallel with) Godot.
## Same identifier. Same symbolic_only guarantee.

init python:
    Q24_CANON = {
        "id": "q24_eternal_dao_temperance_14_harmony_paradox_ignite_19_10_1",
        "symbolic_only": True,
        "sequence": [19, 10, 1],
        "anchor": 14,
        "reduce_anchor": False,
        "carrier": "love_and_harmony_6",
        "display": {
            "en": "Eternal Dao: Temperance 14, Perfect Harmony Paradox",
            "zh": "永恒之道：十四节制与完美和谐悖论",
            "ja": "永遠の道：節制14と完全調和のパラドックス",
            "ko": "영원의 도: 절제 14와 완벽한 조화의 역설",
        },
        "ignition_path": "19 -> 10 -> 1",
        "bindings": {
            "fable5_bedrock_version": "0.4.0-engine-bedrock-10",
            "quantum_gap_sig": "8116ed3788a22448",
            "catalyst_circle_sig": "85d7b489eb360a65",
            "bridge_signature": "f2e596cd043d6819",
            "primordial_five": ["angela", "lainie", "sophie", "addie", "sabina"],
            "sovereign_zero": "hades",
        },
    }

    # Wrap the existing deterministic engine directly.
    # Ren'Py runs Python, so shadowgarden_unified_game.py imports natively.
    import importlib, sys, os
    _shaoshi_path = os.path.join(config.gamedir, "python_engine")
    if _shaoshi_path not in sys.path:
        sys.path.insert(0, _shaoshi_path)
    try:
        from shadowgarden_unified_game import ShadowGardenUnifiedGame, GameConfig, MAX_TURNS
        Q24_ENGINE_LOADED = True
    except Exception as e:
        Q24_ENGINE_LOADED = False
        Q24_ENGINE_ERROR = repr(e)

label q24_bootstrap:
    "Eternal Dao: Temperance 14, Perfect Harmony Paradox"
    if not Q24_ENGINE_LOADED:
        "engine bridge missing: [Q24_ENGINE_ERROR]"
        return
    "ignition path: [Q24_CANON['ignition_path']]"
    "max turns: [MAX_TURNS]"
    return
