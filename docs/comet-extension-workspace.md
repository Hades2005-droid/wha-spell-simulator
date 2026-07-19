# Comet Extension Workspace

Shadow Garden tracks `webLiang/Pornhub-Video-Downloader-Plugin-v3` as a dedicated local browser-extension workspace for Comet/Chromium review and manual use.

## Boundary

This lane is for user-confirmed lawful personal-use only. It does not add downloader code to this app, automate downloads, bypass DRM, bypass paywalls, bypass authentication, or automate a browser profile.

## Workspace

Default workspace:

```txt
/Users/fredwashere/browser-extension-workspaces/pornhub-video-downloader-plugin-v3
```

Repository:

```txt
https://github.com/webLiang/Pornhub-Video-Downloader-Plugin-v3.git
```

The workspace intentionally lives outside this project so the WHA simulator does not import or vendor the extension source.

## Status Lane

Emit local status JSON and a Perplexity review prompt:

```sh
python3 tools/extension_workspace_status.py
```

Outputs:

```txt
/tmp/shadow_garden_extension_workspace_status.json
/tmp/shadow_garden_extension_perplexity_review_prompt.md
```

Set this only when the intended use is lawful personal-use:

```sh
export SG_LAWFUL_DOWNLOADS_CONFIRMED=1
```

Without that flag, the lane reports `blocked_lawful_confirmation_required`.

Status progression:

```txt
blocked_lawful_confirmation_required
not_ready_workspace_missing
not_ready_package_json_missing
not_ready_build_missing
not_ready_manifest_v3_required
ready
```

`ready` means only that the lawful-use gate is set and a local Manifest V3 build is present. It does not mean the extension has been security-reviewed or verified in Comet.

Run the double-clickable status helper to print the current state and exact manual commands without executing clone, install, build, browser-load, or download actions:

```sh
tools/launch_comet_extension_workspace.command
```

## Manual Setup

These commands mutate the filesystem and run third-party code, so run them manually after review:

```sh
mkdir -p /Users/fredwashere/browser-extension-workspaces
git clone https://github.com/webLiang/Pornhub-Video-Downloader-Plugin-v3.git /Users/fredwashere/browser-extension-workspaces/pornhub-video-downloader-plugin-v3
git -C /Users/fredwashere/browser-extension-workspaces/pornhub-video-downloader-plugin-v3 submodule update --init --recursive
```

Build and validate from source with workspace-scoped commands:

```sh
pnpm --dir /Users/fredwashere/browser-extension-workspaces/pornhub-video-downloader-plugin-v3 install --frozen-lockfile
pnpm --dir /Users/fredwashere/browser-extension-workspaces/pornhub-video-downloader-plugin-v3 test
pnpm --dir /Users/fredwashere/browser-extension-workspaces/pornhub-video-downloader-plugin-v3 lint
pnpm --dir /Users/fredwashere/browser-extension-workspaces/pornhub-video-downloader-plugin-v3 build
```

If `.crx` or `.pem` files are present, keep them quarantined and inspect them manually. Load only the unpacked source build unless a packaged artifact has been independently reviewed.

## Manual Comet / Chromium Load

1. Open Comet or another Chromium browser extension settings page manually.
2. Enable developer mode manually.
3. Load this unpacked directory manually:

```txt
/Users/fredwashere/browser-extension-workspaces/pornhub-video-downloader-plugin-v3/dist
```

4. Verify popup, content-script, downloads API, host-permission, and offscreen behavior manually.
5. Record manual verification, then regenerate status:

```sh
export SG_COMET_EXTENSION_VERIFIED=1
python3 tools/extension_workspace_status.py
```

6. Refresh Shadow Garden mesh diagnostics.

## Perplexity Review

Use the generated prompt at:

```txt
/tmp/shadow_garden_extension_perplexity_review_prompt.md
```

Ask Perplexity for docs-only architecture notes, Manifest V3 compatibility notes, permission-risk review, build/test troubleshooting, and task backlog. Do not ask for downloader implementation logic or bypass instructions.

## Mesh Diagnostics

The browser mesh probes `cometExtension` via the local Shadow Garden Control extension endpoint. The diagnostics panel surfaces:

- workspace and unpacked `dist` paths,
- lane and lawful-use-gate status,
- Manifest V3 and manual Comet verification state,
- permission and quarantined-artifact risk flags,
- Perplexity review prompt path.

## Validation

Run the local workspace-state tests and bridge normalization tests without cloning or running the third-party extension:

```sh
python3 -m unittest tests.test_extension_workspace_status
node --test tests/bridge.test.js
```

Manual extension validation remains separate and requires explicit operator action.

## Related mesh docs

- `docs/chronology-recursive-bridge.md` — multi-agent bridge + alchemy catalyst
- `docs/mesh-review-loop.md` — bounded review loop
- `tools/complete_agent_bridge.sh` — one-shot dry-run agent chain
