## ContentRegistry.gd  --  Godot 4 autoload
## Registers base scenes and DLC scenes SEPARATELY.
## Enforces the Steam-compliant separation pattern: adult content
## lives in its own depot; the base build must remain self-contained
## and complete. No hidden-toggle single-flag unlocks.
extends Node

const BASE_SCENES := [
	"sim_01_black_sun_apex",
	"sim_02_fields_of_doubt",
	"sim_03_glory_of_the_black_sun",
	"sim_04_winter_win",
	"sim_05_sunstop",
	"sim_06_solar_storm",
]

var _registered: Dictionary = {}   # scene_id -> {pack: String, path: String, rating: String}

func register(scene_id: String, pack: String, path: String, rating: String) -> void:
	assert(scene_id != "" and path.begins_with("res://"))
	_registered[scene_id] = {"pack": pack, "path": path, "rating": rating}

func list_available(installed_packs: Array) -> Array:
	var out := []
	for sid in _registered.keys():
		var rec: Dictionary = _registered[sid]
		if installed_packs.has(rec.pack):
			out.append(sid)
	return out

func resolve(scene_id: String) -> Dictionary:
	return _registered.get(scene_id, {})

func _ready() -> void:
	# Base pack: six shadow simulation scenes.
	register("sim_01_black_sun_apex",         "base", "res://q24/scenes/simulations/Simulation01.tscn", "everyone")
	register("sim_02_fields_of_doubt",        "base", "res://q24/scenes/simulations/Simulation02.tscn", "teen")
	register("sim_03_glory_of_the_black_sun", "base", "res://q24/scenes/simulations/Simulation03.tscn", "teen")
	register("sim_04_winter_win",             "base", "res://q24/scenes/simulations/Simulation04.tscn", "everyone")
	register("sim_05_sunstop",                "base", "res://q24/scenes/simulations/Simulation05.tscn", "teen")
	register("sim_06_solar_storm",            "base", "res://q24/scenes/simulations/Simulation06.tscn", "mature")
	# Adult DLC pack: separate depot, ownership-gated, no base overlap.
	# Actual .tscn paths ship only in the DLC build.
	# Left unregistered until the DLC is installed; do NOT hardcode paths
	# into the base build, per Steam adult-content policy.
