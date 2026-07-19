# Eden / Fable 5 — local cycle status

A recorded bounded-cycle status for the local Eden stack. **Local-only**:
external egress (Discord, remote writes) stays paused, and every service below is
on `127.0.0.1`.

## Latest bounded cycle

```
Bounded cycle 2/3 completed successfully:

- Jing tick completed
- Dataset and merge packet refreshed
- Fable5      :5619  HTTP 200
- EDEN        :8791  HTTP 200
- ComfyUI     :8188  HTTP 200, MPS
- SillyTavern :8000  HTTP 200
- Compact, bedrock, status, and Jing artifacts regenerated
- Exit code: 0
- Discord and remote writes remained paused
```

## Machine-readable status

The local media loop (`tools/fable5-media-loop.mjs`) writes its own real,
per-pass status to `eden-out/last-cycle.json` on every run — asset counts,
manifests written, and `externalRequests: 0`. That file is generated at runtime,
not committed.
