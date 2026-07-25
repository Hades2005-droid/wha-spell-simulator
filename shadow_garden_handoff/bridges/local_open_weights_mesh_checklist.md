# Local open-weights mesh — readiness checklist

Generated: `2026-07-25T23:53:09Z`
Mesh: `local_open_weights_mesh` · Carrier: `love_and_harmony_6`
Prep ready: **True** · Cutover ready: **False**

## Checklist

- [x] `bind_loopback` (blocking) — All prep routes use 127.0.0.1
- [x] `ollama_up` (blocking) — Ollama tags reachable (4 models)
- [ ] `deepseek_local_tag` (soft) — Pull a local deepseek model when ready (optional for prep)
- [ ] `kimi_local_tag` (soft) — Pull a local kimi/moonshot model before full cutover (optional for prep)
- [ ] `comfy_8189` (soft) — ComfyUI daemon down — prefer COMFYUI_URL=http://127.0.0.1:8189 (alt 8188) when up
- [x] `catalogs_refreshed` (blocking) — 6/6 catalogs ok
- [x] `packet_refreshed` (blocking) — packet artifact present=True (refresh skipped)
- [ ] `remote_keys_unset_preferred` (soft) — Remote provider key names present — leave unset for pure local
- [x] `discord_paused` (blocking) — Discord status_notify remains paused by default
- [x] `stripe_dry_run` (blocking) — Stripe stays dry-run unless STRIPE_LIVE_OK=1
- [x] `transition_arm_gate` (soft) — Final cutover still requires KIMI3_TRANSITION_ARMED=1 after approval
- [x] `sg_connect_off` (blocking) — SG_RUN_CONNECT should stay 0 unless explicitly reviewed

## Local ports

- `fable5` :5619 — UP
- `comfyui` :8189 — down
- `comfyui_alt` :8188 — down
- `eden` :8791 — down
- `void_ignition` :8790 — down
- `portal` :8760 — down
- `ollama` :11434 — UP
- `stripe_local` :4242 — down
- `vite_dev` :5173 — down
- `sillytavern` :8000 — down

## Operator cutover (after prep)

1. Optionally pull local models: `ollama pull deepseek-r1` / kimi-class tag.
2. Leave remote API keys unset in the shell.
3. `export LOCAL_MESH_PREP=1`
4. After approval: `export KIMI3_TRANSITION_ARMED=1`
5. `python3 tools/kimi3_asuna_point0_unify.py write`
6. `python3 tools/local_open_weights_mesh_prep.py write`
7. `python3 tools/perplexity_asuna_central_control.py write`
8. `python3 tools/shadow_garden_packet.py write`
9. Keep Discord paused; Stripe dry-run; `SG_RUN_CONNECT=0`.

