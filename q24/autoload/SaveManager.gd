## SaveManager.gd  --  Godot 4 autoload
## Deterministic-seed save/load. Uses user:// on Steam, respects
## GameSession.SAVE_VERSION. Refuses to load saves whose canonical_id
## does not match the current Q24 anchor.
extends Node

const SAVE_DIR := "user://saves"
const SAVE_EXT := ".q24save"

func _ready() -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(SAVE_DIR))

func save(slot: String) -> bool:
	var path := "%s/%s%s" % [SAVE_DIR, slot, SAVE_EXT]
	var f := FileAccess.open(path, FileAccess.WRITE)
	if f == null:
		return false
	f.store_string(JSON.stringify(GameSession.to_save_dict(), "\t"))
	f.close()
	return true

func load(slot: String) -> bool:
	var path := "%s/%s%s" % [SAVE_DIR, slot, SAVE_EXT]
	if not FileAccess.file_exists(path):
		return false
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return false
	var txt := f.get_as_text()
	f.close()
	var d = JSON.parse_string(txt)
	if typeof(d) != TYPE_DICTIONARY:
		return false
	return GameSession.load_from_dict(d)
