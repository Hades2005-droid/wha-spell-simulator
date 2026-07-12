# Eden hook — WHA spell simulator

This folder wires the WHA spell simulator into the **Eden constellation** so the
Shadow Garden launcher can ignite it with a single command, and so the simulator
can talk to **Claude Fable 5** natively.

```
eden/
  fable5.mjs          →  native communication layer to Claude Fable 5 (JS)
  eden_spell.mjs      →  headless spell/physics burst, narrated by Fable 5
  comfyuiAdapter.mjs  →  Fable 5 spell → ComfyUI local image/video/audio manifest
```

## Run it

Standalone:

```bash
node eden/eden_spell.mjs "frostfang"
```

Or let the Shadow Garden launcher call it for you — from `../shadow-garden-launcher`:

```bash
python eden/launch.py "frostfang"
```

The hook runs a small deterministic spell burst (particles, kinetic energy,
momentum) seeded from your input, prints the telemetry, and — if an API key is
set — asks Fable 5 to narrate it in one line.

## Fable 5 native comms

`fable5.mjs` is the JS twin of `eden/fable5.py` in the sibling repos. It defaults
to `claude-fable-5` and opts into a **server-side refusal fallback** to
`claude-opus-4-8`, so behaviour matches across the whole constellation.

```bash
npm install @anthropic-ai/sdk
export ANTHROPIC_API_KEY=sk-ant-...   # or: ant auth login
node eden/eden_spell.mjs "emberveil"
```

## Fable 5 → ComfyUI adapter

`comfyuiAdapter.mjs` compiles a spell descriptor into a deterministic,
ComfyUI-shaped manifest for image / video / audio, and — only when explicitly
approved — queues it to a **local** ComfyUI (`:8188`, `/system_stats` health).
It is `manifest_only` by default, makes **zero external requests**, never
auto-downloads weights (pointer-only), caps video/audio at 30s and roles at
five abstract roles, and refuses prohibited content. See
[`../docs/fable5-comfyui-adapter.md`](../docs/fable5-comfyui-adapter.md).

```js
import { compileManifest } from './comfyuiAdapter.mjs';
const manifest = compileManifest({ media: 'image', intent: 'a glowing sigil' });
// manifest_only: nothing is queued until you opt in AND approve.
```

## Honest scope

- The burst here is a **headless numeric sim** so the launcher always gets data
  back; the full interactive simulator still lives in `../src` and `index.html`.
- Fable 5 narration requires **your own API key**. Nothing calls out otherwise.
- The ComfyUI adapter only ever contacts **loopback** endpoints, and only when
  you pass `allowLocalRequests:true` with an approved, queue-mode manifest.
