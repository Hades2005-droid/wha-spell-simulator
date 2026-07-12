#!/bin/zsh
set -u

WHA_ROOT="${WHA_ROOT:-/Users/fredwashere/wha-spell-simulator}"
LOG="${SG_MESH_REVIEW_LOG:-/tmp/shadow_garden_mesh_review_loop.log}"
CYCLES="${SG_MESH_REVIEW_CYCLES:-6}"
INTERVAL="${SG_MESH_REVIEW_INTERVAL:-1}"
MAX_SECONDS="${SG_MESH_REVIEW_MAX_SECONDS:-120}"

: > "$LOG"

print "[mesh-review] bounded local dry-run" | tee -a "$LOG"
print "[mesh-review] cycles=$CYCLES interval=$INTERVAL max_seconds=$MAX_SECONDS" | tee -a "$LOG"
print "[mesh-review] Perplexity send disabled; Cascade chat is not an API peer." | tee -a "$LOG"

python3 "$WHA_ROOT/tools/mesh_review_loop.py" \
  --cycles "$CYCLES" \
  --interval "$INTERVAL" \
  --max-seconds "$MAX_SECONDS" \
  --request "Review local recursive and Comet extension status for reliability and integration risks." \
  2>&1 | tee -a "$LOG"

result=${pipestatus[1]}
print "[mesh-review] exit=$result log=$LOG" | tee -a "$LOG"
exit "$result"
