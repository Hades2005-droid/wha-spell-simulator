## Q24StateAdapter.gd  --  Godot 4
## Thin adapter to the existing deterministic Python state machine
## (shadowgarden_unified_game.py). Preserves byte-identical replay
## by delegating transitions to the Python engine and mirroring the
## result into GameSession.
##
## Two implementation options (pick one at project setup):
##   A) GDExtension: embed CPython or call via a small C++ shim.
##   B) Subprocess: spawn `python3 shadowgarden_unified_game.py` and
##      pipe JSON in/out. Higher latency but zero binding surface.
##
## This file describes the CONTRACT. The actual implementation is
## selected by the alpha team based on Steam build constraints.
class_name Q24StateAdapter
extends Node

signal transition_applied(from: String, to: String, meta: Dictionary)

var backend_mode: String = "subprocess"   # "subprocess" | "gdextension"
var last_state: String = ""

func apply_action(state: String, action: String, seed: int, mastery: int) -> Dictionary:
	# Contract: returns { "ok": bool, "next_state": String, "resonance": int,
	#                     "turn": int, "aborted": bool, "reason": String }
	# The Python engine enforces MAX_TURNS = 24 and rejects illegal
	# transitions. This adapter MUST NOT locally guess transitions;
	# it MUST call the underlying engine so determinism is preserved.
	push_warning("Q24StateAdapter.apply_action: implement via %s" % backend_mode)
	return {
		"ok": false,
		"next_state": state,
		"resonance": 0,
		"turn": 0,
		"aborted": true,
		"reason": "adapter_not_wired",
	}
