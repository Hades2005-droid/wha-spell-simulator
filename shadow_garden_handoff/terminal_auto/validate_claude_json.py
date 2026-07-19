#!/usr/bin/env python3
import json, sys, pathlib, datetime
ROOT = pathlib.Path("/Users/fredwashere/wha-spell-simulator/shadow_garden_handoff/terminal_auto")
INBOX = ROOT / "inbox"
OUTBOX = ROOT / "outbox"
LOGS = ROOT / "logs"
for p in (INBOX, OUTBOX, LOGS):
    p.mkdir(parents=True, exist_ok=True)
REQUIRED_SCOPE = "design_review_and_deterministic_play_only"
REQUIRED_SAFETY = {
    "adult_video_urls_excluded": True,
    "secrets_or_credentials_touched": False,
    "external_writes_performed": False,
}
def read_raw():
    if len(sys.argv) > 1:
        return pathlib.Path(sys.argv[1]).read_text()
    raw = sys.stdin.read()
    if raw.strip():
        return raw
    f = INBOX / "claude_return.json"
    if f.exists():
        return f.read_text()
    raise SystemExit("No JSON provided. Paste JSON on stdin or save to inbox/claude_return.json")
def main():
    now = datetime.datetime.now().isoformat(timespec="seconds")
    try:
        payload = json.loads(read_raw())
        failures = []
        if payload.get("review_scope") != REQUIRED_SCOPE:
            failures.append("review_scope must be design_review_and_deterministic_play_only")
        safety = payload.get("safety_review", {})
        if not isinstance(safety, dict):
            failures.append("safety_review must be an object")
            safety = {}
        for key, expected in REQUIRED_SAFETY.items():
            if safety.get(key) is not expected:
                failures.append(f"safety_review.{key} must be {expected!r}")
        if payload.get("lane_map_acknowledged") is not True:
            failures.append("lane_map_acknowledged must be true")
        result = {
            "status": "pass" if not failures else "blocked",
            "gate": 8,
            "validated_at": now,
            "failures": failures,
            "source_status": payload.get("status"),
            "back_lane": payload.get("back_lane"),
            "front_lane": payload.get("front_lane"),
            "final_catalyst_gift": payload.get("final_catalyst_gift", "")
        }
    except Exception as exc:
        result = {"status": "blocked", "gate": 8, "validated_at": now, "failures": [f"invalid_json: {exc}"]}
    (OUTBOX / "claude_validation_result.json").write_text(json.dumps(result, indent=2) + "\n")
    with (LOGS / "terminal_auto.log").open("a") as log:
        log.write("[{}] gate8 validation {}: {}\n".format(now, result["status"], result.get("failures", [])))
    print(json.dumps(result, indent=2))
if __name__ == "__main__":
    main()
