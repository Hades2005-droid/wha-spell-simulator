---
description: Full-mesh Claude Code activation across Shadow Garden while Perplexity + mesh bridge stay hot.
auto_execution_mode: 2
---

# /shadowgarden

Activates all four Claude-integration paths plus the Comet browser-extension workspace, chronology engine, and bounded recursive bridge lanes while the browser
mesh keeps Perplexity, Grok, Gemini, Linear, ComfyUI, SillyTavern, and the
local Shadow Garden Control endpoint polled in parallel (see
`src/bridge/meshBridge.js` → `refreshMesh`).

Paths orchestrated:

1. **Credential-safe dry-run lane** — `tools/claude_shadowgarden.py`
2. **Comet extension workspace status** — `tools/extension_workspace_status.py`
3. **Chronology analysis** — `tools/chronology_engine.py` (symbolic metadata only)
4. **Bounded recursive node bridge** — `tools/recursive_node_bridge.py` / `tools/recursive-node-bridge/`
5. **Bridge connect + sovereign tag** — `DevinTerminalBridge/connect_claude_env.sh`
6. **Claude agent (full tool calling)** — `claude_integration.py` (Shadow Garden automation, Devin CLI, Jira, Terminal, Elmedia, MCP)
7. **C# DevinTerminalBridge launcher** — `dotnet run -- launch-claude-agent`
8. **MCP surface** — `claude_mcp_config.json` for Claude Desktop / Cursor

## Steps

1. Ensure scripts are executable.
// turbo
```
chmod +x tools/claude_shadowgarden.py tools/extension_workspace_status.py tools/chronology_engine.py tools/recursive_node_bridge.py tools/perplexity_mesh_adapter.py tools/mesh_review_loop.py tools/launch_claude_shadowgarden.command tools/launch_comet_extension_workspace.command tools/launch_mesh_review_loop.command tools/shadowgarden_orchestrate.sh
```

2. Run the dry-run planning lane so the mesh diagnostics have a fresh status file. If `ANTHROPIC_OAUTH_TOKEN` and `ANTHROPIC_API_KEY_ID` are exported, also verify the API key via the Anthropic Admin API (`GET /v1/organizations/api_keys/$API_KEY_ID`).
// turbo
```
python3 tools/claude_shadowgarden.py --mode auto --prompt "Full-mesh Claude Code activation across Shadow Garden + Perplexity." ${ANTHROPIC_OAUTH_TOKEN:+--verify-admin-key}
```

2b. Manual admin-key probe (curl equivalent, for out-of-band verification):
```
curl -sS https://api.anthropic.com/v1/organizations/api_keys/$ANTHROPIC_API_KEY_ID \
  -H 'anthropic-version: 2023-06-01' \
  -H "Authorization: Bearer $ANTHROPIC_OAUTH_TOKEN"
```

2c. Emit Comet extension workspace status + Perplexity docs-only review prompt. This does not clone, install, build, load, or run the extension.
// turbo
```
python3 tools/extension_workspace_status.py --workspace "${SG_EXTENSION_WORKSPACE:-/Users/fredwashere/browser-extension-workspaces/pornhub-video-downloader-plugin-v3}"
```

2d. Print the generated Perplexity review prompt.
// turbo
```
cat /tmp/shadow_garden_extension_perplexity_review_prompt.md
```

2e. Run the deterministic chronology engine. Its output is symbolic metadata only.
// turbo
```
python3 tools/chronology_engine.py --date 2026-06-27 --time 20:40 --timezone America/New_York --comparison-timezone Asia/Singapore
```

2f. Run one bounded recursive bridge cycle. Gain 8 is permitted but hard-capped; continuous mode requires an explicit duration.
// turbo
```
python3 tools/recursive_node_bridge.py --cycles 1 --gain 8
```

2g. Generate a local Perplexity review status. This is dry-run only and makes no API request.
// turbo
```
python3 tools/perplexity_mesh_adapter.py --request "Review local Shadow Garden mesh and Comet status for integration risks."
```

2g.1. If a source document is a PDF, normalize it locally before passing it to
the review lane. The model path accepts the resulting text representation, not
the native PDF part.
// turbo
```
python3 -m pip install -r requirements-tools.txt
python3 tools/perplexity_mesh_adapter.py \
  --request "Review the attached technical recommendation for integration risks." \
  --document "/absolute/path/to/recommendation.pdf"
```

2h. Run six bounded local mesh review cycles. This is dry-run only, makes no Perplexity API request, and cannot connect to the Cascade chat session.
// turbo
```
python3 tools/mesh_review_loop.py --cycles 6 --interval 1 --max-seconds 120
```

2i. After rotating the exposed credential and exporting a replacement as `PERPLEXITY_API_KEY`, an operator may explicitly send one docs-only review. This does not control Comet, execute model output, or broadcast to agents.
```
python3 tools/mesh_review_loop.py --cycles 1 --interval 30 --max-seconds 60 --send-perplexity --confirm-send PERPLEXITY_LOOP_OK
```

3. Print bridge connect status + sovereign tag (path 5).
// turbo
```
SG_RUN_CONNECT=1 SG_RUN_CLAUDE_AGENT=0 SG_RUN_DOTNET=0 tools/shadowgarden_orchestrate.sh
```

4. Show the MCP config path so Claude Desktop / Cursor can point at it (path 5).
// turbo
```
ls -l /Users/fredwashere/shadow_garden_may30_monitoring/claude_mcp_config.json && cat /Users/fredwashere/shadow_garden_may30_monitoring/claude_mcp_config.json
```

5. Print the mesh status files (the browser mesh bridge is what keeps Perplexity co-review live).
// turbo
```
cat /tmp/shadow_garden_claude_status.json && cat /tmp/shadow_garden_extension_workspace_status.json && cat /tmp/shadow_garden_recursive_node_status.json && cat /tmp/shadow_garden_perplexity_status.json && cat /tmp/shadow_garden_mesh_review_loop_status.json
```

6. **Manual Comet extension setup (requires explicit user action; mutates filesystem and runs third-party code).**
```
mkdir -p /Users/fredwashere/browser-extension-workspaces
git clone https://github.com/webLiang/Pornhub-Video-Downloader-Plugin-v3.git /Users/fredwashere/browser-extension-workspaces/pornhub-video-downloader-plugin-v3
git -C /Users/fredwashere/browser-extension-workspaces/pornhub-video-downloader-plugin-v3 submodule update --init --recursive
pnpm --dir /Users/fredwashere/browser-extension-workspaces/pornhub-video-downloader-plugin-v3 install --frozen-lockfile
pnpm --dir /Users/fredwashere/browser-extension-workspaces/pornhub-video-downloader-plugin-v3 test
pnpm --dir /Users/fredwashere/browser-extension-workspaces/pornhub-video-downloader-plugin-v3 lint
pnpm --dir /Users/fredwashere/browser-extension-workspaces/pornhub-video-downloader-plugin-v3 build
```

7. **Manual Comet / Chromium load.** Quarantine and inspect any `.crx`/`.pem` artifacts, open extension settings manually, enable developer mode manually, then load the unpacked source build:
```
/Users/fredwashere/browser-extension-workspaces/pornhub-video-downloader-plugin-v3/dist
```

After manually verifying Manifest V3, popup/content scripts, downloads API, host permissions, and offscreen behavior, record that verification and regenerate status:
```
export SG_COMET_EXTENSION_VERIFIED=1
python3 tools/extension_workspace_status.py
```

8. **Lawful-use gate.** Only set this for user-confirmed lawful personal-use downloads:
```
export SG_LAWFUL_DOWNLOADS_CONFIRMED=1
```

9. **Live activation (requires explicit consent + secrets).** Launches path 3 (Claude agent) and path 4 (C# bridge) in parallel; Perplexity co-review continues via the mesh.
```
ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY SG_RUN_CLAUDE_AGENT=1 SG_RUN_DOTNET=1 tools/shadowgarden_orchestrate.sh
```

10. **Quick bridge command (from any terminal, mirrors the user's shortcut).**
```
zsh /Users/fredwashere/shadow_garden_may30_monitoring/DevinTerminalBridge/connect_claude_env.sh
```

## Notes

- Steps 1–5 are safe (dry-run + status inspection). Steps 6–8 are manual browser-extension setup/load/legal-gate actions. A `ready` lane means only that the gate and local Manifest V3 build are present; `SG_COMET_EXTENSION_VERIFIED=1` records a separate manual compatibility check. Step 9 is live and only runs when `SG_RUN_CLAUDE_AGENT=1` / `SG_RUN_DOTNET=1` are set and `ANTHROPIC_API_KEY` is exported.
- The chronology output is symbolic metadata only; it is not a prediction, diagnosis, or decision authority.
- The recursive bridge is local-only, bounded, metadata-only, and does not call DeepSeek or any external provider. Continuous mode requires an explicit duration.
- Perplexity is not launched here; it is polled continuously by the mesh bridge (`checkPerplexitySpace` in `src/bridge/meshBridge.js:226`).
- `tools/extension_workspace_status.py` writes `/tmp/shadow_garden_extension_workspace_status.json` and `/tmp/shadow_garden_extension_perplexity_review_prompt.md` for docs-only review.
- `tools/recursive_node_bridge.py` writes `/tmp/shadow_garden_recursive_node_status.json` for the mesh diagnostics lane.
- `tools/perplexity_mesh_adapter.py` writes `/tmp/shadow_garden_perplexity_status.json`; API responses are written separately to `/tmp/shadow_garden_perplexity_review.json` only after explicit `--send`.
- `tools/document_ingest.py` converts local PDFs to bounded, redacted text; native PDF parts are never sent to the model path.
- `tools/mesh_review_loop.py` is bounded to 12 local cycles or 3 explicitly confirmed external reviews, never runs as an unattended daemon, and never executes provider output.
- Perplexity credentials are read only from `PERPLEXITY_API_KEY`, never printed, stored in source, exposed to the browser, or sent to Comet/other agents.
- `tools/shadowgarden_orchestrate.sh` respects `SG_PARALLEL=1` (default) so paths 3 and 4 run concurrently, keeping Perplexity + Claude both live.
