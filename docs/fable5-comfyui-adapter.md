# Fable 5 → ComfyUI local adapter

`eden/comfyuiAdapter.mjs` compiles a WHA spell descriptor (or a full `SpellIR`
from `src/compiler`) into a **deterministic, ComfyUI-shaped manifest** for
image / video / audio generation, and — only when explicitly approved — hands
that manifest to a **local** ComfyUI instance.

It is the local unification point between the Fable 5 native comms layer
(`eden/fable5.mjs`) and a ComfyUI render backend. It is intentionally small,
dependency-free, and does no network I/O unless you opt in.

## Canonical wiring

| Field | Value |
| --- | --- |
| Target task | `37bce2fb-1ba6-471f-854f-3871d9c19947` |
| Lead task | `2366bfee-b78c-4ddc-9f86-304c30c67c4d` |
| Policy | `no_scrape_pointer_only` |
| Branch | `fable5-comfyui-unification` |
| Roles | `unification_target`, `fable5_comfyui_open_merge_target` |

Local endpoints (loopback only): **Fable 5** `:5619`, **ComfyUI** `:8188`
(`/system_stats` health), **EDEN** `:8791`.

## Safety contract

These are enforced in code (`DEFAULT_POLICY` + `normalizePolicy`) and cannot be
loosened by a caller — overrides may only make the policy *stricter*:

- **`manifest_only` by default.** `compileManifest()` never touches the network.
- **`approve:true` required before any queue.** Queuing also requires
  `mode:"queue"` and `allowLocalRequests:true`.
- **`externalRequests = 0`.** Only loopback hosts are ever contacted; any
  non-local endpoint is refused with a `PolicyViolationError`.
- **`trainingAllowed = false`** and **weights are never auto-downloaded.** All
  checkpoint / model references are local pointers (`source:"local_pointer"`),
  never URLs. This is the `no_scrape_pointer_only` policy.
- **Video / audio ≤ 30s.**
- **At most five abstract roles.** Roles are always normalized to
  `kind:"abstract"`.
- **Content guard.** Prohibited categories are rejected outright: minors,
  non-consent, incest, trafficking, hidden-cam, exploitation. There is **no
  real-person likeness engine** — explicit real-person likeness requests are
  refused.
- **No broadcast / external connector.** The adapter has no X / social writes,
  stores no credentials, and opens no outbound connector.

## API

```js
import {
  compileManifest,
  queueManifest,
  checkComfyUiHealth,
  screenContent,
} from '../eden/comfyuiAdapter.mjs';
```

### `compileManifest(spec, options)` → manifest

Pure and deterministic — the same `spec` always yields the same manifest
(stable `manifestId`, no wall-clock, no RNG).

```js
const manifest = compileManifest(
  {
    media: 'image', // 'image' | 'video' | 'audio'
    intent: 'a glowing witch-hat sigil radiating warm firelight',
    negativeIntent: 'blurry, text',
    roles: [{ id: 'caster', descriptor: 'abstract robed figure' }], // ≤ 5
    tags: ['fire', 'atelier'],
    spell: someSpellIR, // optional: element/quality/stability drive params
    durationSeconds: 8, // video/audio only, ≤ 30
    checkpoint: 'my_local_model.safetensors', // pointer name, not a URL
  },
  { role: 'unification_target' }, // or 'fable5_comfyui_open_merge_target'
);
```

The manifest carries a ComfyUI `prompt` node graph under `manifest.prompt`,
the resolved `policy`, `provenance`, normalized `roles`, derived `parameters`
(`seed`, `steps`, `cfg`), and a deterministic `manifestId`.

### `queueManifest(manifest, options)` → `{ queued, reason?, promptId? }`

Gated. Returns `{ queued:false, reason:'manifest_only' }` by default. To
actually POST to `http://127.0.0.1:8188/prompt` you must pass a manifest
compiled with `policy:{ mode:'queue', allowLocalRequests:true }` **and**
`options.approve === true`. A non-local endpoint is always refused. Inject
`options.fetchImpl` for tests.

### `checkComfyUiHealth(options)` → `{ ok, ... }`

Read-only probe of ComfyUI `/system_stats`. No-op unless
`policy.allowLocalRequests` is true; refuses non-local endpoints.

### `screenContent(spec)` → `{ allowed, violations }`

The deterministic content guard used inside `compileManifest`. Call it directly
to pre-check a spec.

## Determinism & tests

`tests/comfyuiAdapter.test.js` runs fully offline (a fake `fetch` is injected
wherever gating is exercised) and asserts byte-stable compilation, the media
caps, role limits, every content-guard category, endpoint locality, and the
queue-approval gate.

```sh
node --test tests/comfyuiAdapter.test.js
```
