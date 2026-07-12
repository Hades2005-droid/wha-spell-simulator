# Bounded Mesh Review Loop

The mesh review loop combines local nine-node recursive telemetry with the existing Perplexity docs-only review adapter. It cannot connect to the Cascade chat session, execute model output, control browser profiles, or broadcast prompts to other agents.

See also: `docs/chronology-recursive-bridge.md` (full multi-agent map + Jing Power + Fable5/ComfyUI bridge) and `tools/complete_agent_bridge.sh`.

## PDF-safe document handoff

The text-review model path does not accept native PDF parts. Normalize local
documents before a dry run or provider request; PDFs are parsed locally and
sent onward only as bounded, redacted UTF-8 text:

```sh
python3 -m pip install -r requirements-tools.txt
python3 tools/perplexity_mesh_adapter.py \
  --request "Review the Q24 recommendation for ingestion risks." \
  --document "/path/to/recommendation.pdf"
```

The adapter remains dry-run by default. It records `native_pdf_input: false`
and never stores the original PDF bytes in the request payload. If a PDF has
no extractable text, export it to `.txt`/`.md` or use a separately reviewed
image/OCR workflow instead of retrying the native PDF upload.

## Local dry-run

Run six bounded local cycles without an API key or network request:

```sh
python3 tools/mesh_review_loop.py \
  --cycles 6 \
  --interval 1 \
  --max-seconds 120
```

The macOS double-clickable helper runs the same safe mode:

```sh
tools/launch_mesh_review_loop.command
```

Artifacts:

```txt
/tmp/shadow_garden_mesh_review_loop_status.json
/tmp/shadow_garden_mesh_review_loop_results.json
/tmp/shadow_garden_recursive_node_status.json
/tmp/shadow_garden_mesh_review_loop.log
```

## Explicit Perplexity review

Revoke any credential previously shared in chat and export a rotated replacement locally. External review requires all of the following:

- `PERPLEXITY_API_KEY` in the process environment,
- `--send-perplexity`,
- `--confirm-send PERPLEXITY_LOOP_OK`,
- no more than three cycles,
- at least 30 seconds between cycles,
- a maximum duration of 15 minutes.

Example for one docs-only review:

```sh
python3 tools/mesh_review_loop.py \
  --cycles 1 \
  --interval 30 \
  --max-seconds 60 \
  --send-perplexity \
  --confirm-send PERPLEXITY_LOOP_OK
```

Provider responses are written as data only. They are never interpreted as terminal commands.

## Hard limits

- Local mode: 12 cycles maximum.
- External mode: 3 requests maximum.
- Duration: 900 seconds maximum.
- Local interval: 0.1 seconds minimum.
- External interval: 30 seconds minimum.
- Requests containing credential-like values are rejected.
- Ctrl-C stops foreground execution; the loop never launches an unattended daemon.

## Validation

```sh
python3 -m unittest tests.test_mesh_review_loop
python3 -m py_compile tools/mesh_review_loop.py
zsh -n tools/launch_mesh_review_loop.command
```
