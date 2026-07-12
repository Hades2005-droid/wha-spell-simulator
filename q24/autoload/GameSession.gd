## GameSession.gd  --  Godot 4 autoload
## Vertical-slice orchestration for Q24 Shadow Garden alpha.
## Owns runtime state. Delegates canonical labeling to Q24CanonicalAnchor
## and deterministic transitions to Q24StateAdapter (which wraps the
## existing Python shadowgarden_unified_game.py state machine via a
## GDExtension bridge or a subprocess adapter, depending on target).
##
## Scope of this file: state ownership, save-load, scene dispatch,
## content-pack registration, DLC ownership check surface. It does NOT
## implement rendering, physics, or dialogue. Those live in scene files.
extends Node

const CANON_PATH := "res://q24/canon/Q24_EternalDao_Temperance14_HarmonyParadox_19to10to1.tres"
const SAVE_VERSION := 1

signal state_changed(old_state: String, new_state: String)
signal simulation_changed(scene_id: String)
signal resonance_changed(value: int)
signal q24_turn_advanced(turn: int)

var canon: Q24CanonicalAnchor = null

# Owned runtime state (documented in Grok share #2)
var player_state: Dictionary = {}
var world_seed: int = 42
var current_simulation: String = ""       # "sim_01" .. "sim_06"
var q24_turn: int = 0                     # 0..MAX_TURNS (MAX_TURNS = 24)
var resonance: int = 0                    # 0..42, deterministic-noise bounded
var inventory: Array = []
var scene_flags: Dictionary = {}
var consent_flags: Dictionary = {
	"nuance_layer_acknowledged": false,
	"adult_dlc_owned": false,
	"age_verified": false,
}
var installed_content_packs: Array = ["base"]
var save_version: int = SAVE_VERSION

const MAX_TURNS: int = 24  # Q24: hard turn cap enforced by underlying engine

func _ready() -> void:
	canon = load(CANON_PATH) as Q24CanonicalAnchor
	assert(canon != null, "Q24 canonical anchor failed to load")
	assert(canon.symbolic_only, "canon must remain symbolic_only=true")

func start_new_run(seed: int) -> void:
	world_seed = seed
	q24_turn = 0
	resonance = 0
	current_simulation = ""
	scene_flags.clear()
	inventory.clear()
	emit_signal("state_changed", "", "launch")

func advance_turn() -> bool:
	if q24_turn >= MAX_TURNS:
		return false
	q24_turn += 1
	emit_signal("q24_turn_advanced", q24_turn)
	return true

func enter_simulation(sim_id: String) -> void:
	# sim_id must be one of the six base scenes; adult_dlc scenes are gated.
	var old := current_simulation
	current_simulation = sim_id
	emit_signal("simulation_changed", sim_id)
	emit_signal("state_changed", old, sim_id)

func adjust_resonance(delta: int) -> void:
	resonance = clampi(resonance + delta, 0, 42)
	emit_signal("resonance_changed", resonance)

func has_dlc(pack: String) -> bool:
	return installed_content_packs.has(pack)

func to_save_dict() -> Dictionary:
	return {
		"save_version": save_version,
		"canonical_id": canon.canonical_id,
		"world_seed": world_seed,
		"q24_turn": q24_turn,
		"resonance": resonance,
		"current_simulation": current_simulation,
		"scene_flags": scene_flags,
		"inventory": inventory,
		"consent_flags": consent_flags,
		"installed_content_packs": installed_content_packs,
		"player_state": player_state,
	}

func load_from_dict(d: Dictionary) -> bool:
	if int(d.get("save_version", -1)) != SAVE_VERSION:
		return false
	if String(d.get("canonical_id", "")) != canon.canonical_id:
		return false
	world_seed = int(d.get("world_seed", 42))
	q24_turn = int(d.get("q24_turn", 0))
	resonance = int(d.get("resonance", 0))
	current_simulation = String(d.get("current_simulation", ""))
	scene_flags = d.get("scene_flags", {})
	inventory = d.get("inventory", [])
	consent_flags = d.get("consent_flags", consent_flags)
	installed_content_packs = d.get("installed_content_packs", ["base"])
	player_state = d.get("player_state", {})
	return true
