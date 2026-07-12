# Eden hook — WHA spell simulator

This folder wires the WHA spell simulator into the **Eden constellation** so the
Shadow Garden launcher can ignite it with a single command, and so the simulator
can talk to **Claude Fable 5** natively.

```
eden/
  fable5.mjs      →  native communication layer to Claude Fable 5 (JS)
  eden_spell.mjs  →  headless spell/physics burst, narrated by Fable 5
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

## Honest scope

- The burst here is a **headless numeric sim** so the launcher always gets data
  back; the full interactive simulator still lives in `../src` and `index.html`.
- Fable 5 narration requires **your own API key**. Nothing calls out otherwise.
