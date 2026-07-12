#!/bin/zsh
set -u

WHA_ROOT="${WHA_ROOT:-/Users/fredwashere/wha-spell-simulator}"
EXT_REPO="https://github.com/webLiang/Pornhub-Video-Downloader-Plugin-v3.git"
EXT_WORKSPACE="${SG_EXTENSION_WORKSPACE:-/Users/fredwashere/browser-extension-workspaces/pornhub-video-downloader-plugin-v3}"
STATUS_FILE="${SG_EXTENSION_STATUS_FILE:-/tmp/shadow_garden_extension_workspace_status.json}"
REVIEW_PROMPT_FILE="${SG_EXTENSION_REVIEW_PROMPT_FILE:-/tmp/shadow_garden_extension_perplexity_review_prompt.md}"

print "[comet-extension] Shadow Garden Comet extension lane"
print "[comet-extension] repo: $EXT_REPO"
print "[comet-extension] workspace: $EXT_WORKSPACE"
print "[comet-extension] status: $STATUS_FILE"
print "[comet-extension] review prompt: $REVIEW_PROMPT_FILE"
print ""
print "[lawful-use] Set SG_LAWFUL_DOWNLOADS_CONFIRMED=1 only for user-confirmed lawful personal-use downloads."
print "[lawful-use] No DRM, paywall, auth bypass, or hidden scraping workflow is supported by this lane."
print ""

python3 "$WHA_ROOT/tools/extension_workspace_status.py" \
  --workspace "$EXT_WORKSPACE" \
  --status-file "$STATUS_FILE" \
  --review-prompt-file "$REVIEW_PROMPT_FILE"

print ""
print "[manual setup commands]"
print "mkdir -p \"$(dirname "$EXT_WORKSPACE")\""
if [[ -d "$EXT_WORKSPACE/.git" ]]; then
  print "git -C \"$EXT_WORKSPACE\" pull --ff-only"
else
  print "git clone $EXT_REPO \"$EXT_WORKSPACE\""
fi
print "git -C \"$EXT_WORKSPACE\" submodule update --init --recursive"
print "pnpm --dir \"$EXT_WORKSPACE\" install --frozen-lockfile"
print "pnpm --dir \"$EXT_WORKSPACE\" test"
print "pnpm --dir \"$EXT_WORKSPACE\" lint"
print "pnpm --dir \"$EXT_WORKSPACE\" build"
print ""
print "[artifact review]"
print "Build from source and manually quarantine/review any bundled .crx or .pem artifacts."
print "Do not load packaged artifacts merely because they are present."
print ""
print "[manual Comet / Chromium load]"
print "1. Open Comet or another Chromium browser extension settings page manually (chrome://extensions/)."
print "2. Enable developer mode manually."
print "3. Load unpacked extension directory: $EXT_WORKSPACE/dist"
print "4. Refresh the Shadow Garden mesh diagnostics after build/load."
