# NWW Asana Connector

Optional, non-blocking integration that reports spell-simulator glyph telemetry
to [Asana](https://asana.com). It posts **sanitized, aggregate metrics** as task
comments or milestone tasks — never raw stroke data, canvas coordinates, or user
identifiers.

## What it reports

The connector reduces compiled spell results into four aggregate metrics:

| Metric | Meaning | Derived from |
| --- | --- | --- |
| Glyph recognition accuracy | How confidently symbols were recognized | primary sigil + sign confidence |
| Compilation success rate | Share of attempts that compiled to a valid SpellIR | `spellIR.valid` |
| Copy technique effectiveness | Neatness/stability of the drawn glyph | `neatness`, `stability` |
| Soul alignment / resonance | Coherence of intent | `quality`, `directionCoherence`, `stability` |

Only numeric/boolean aggregates and short sanitized labels leave the process.

## Security model

- **No secrets in code.** All credentials come from environment variables.
- **Token never touches the browser.** The config module refuses to return a
  token in a DOM-like context, and reporting auto-disables there. Do not import
  `src/reporting/*` into the client bundle with a real token; use the CLI or a
  server process. `VITE_`-prefixed variables must never hold a PAT.
- **Opt-in.** Nothing is sent unless `ASANA_REPORTING_ENABLED=1` **and** a token
  **and** a destination (task or project) are all present.
- **Non-blocking.** Config/network failures resolve to a skipped/error result
  object; they never throw into simulator code.
- **Redaction.** Bearer tokens are stripped from any error message.
- **Sanitization.** Labels/milestones are stripped of control characters and
  markup before being sent.

## Environment variables

See [`.env.example`](../.env.example). `.env` is git-ignored.

| Variable | Required | Purpose |
| --- | --- | --- |
| `ASANA_ACCESS_TOKEN` | yes | Asana Personal Access Token (secret) |
| `ASANA_PROJECT_SPELLSIM` | one of | Project GID; a new task is created per report |
| `ASANA_TASK_ID` | one of | Existing task GID; reports are posted as comments (takes precedence) |
| `ASANA_WORKSPACE_ID` | optional | Workspace GID for scoping |
| `ASANA_REPORTING_ENABLED` | yes | Set to `1`/`true` to actually contact Asana |
| `RUN_LIVE_ASANA_TESTS` | test-only | Set to `1` to run the opt-in live test suite |

## CLI usage

The CLI is the recommended way to report, since tokens stay server-side.

```bash
# Preview without contacting Asana (no token needed):
node tools/asanaReport.js --dry-run --input samples.json --milestone "Sprint 3"

# Verify credentials only:
ASANA_ACCESS_TOKEN=... ASANA_PROJECT_SPELLSIM=... ASANA_REPORTING_ENABLED=1 \
  node tools/asanaReport.js --verify

# Report aggregate metrics:
ASANA_ACCESS_TOKEN=... ASANA_PROJECT_SPELLSIM=... ASANA_REPORTING_ENABLED=1 \
  node tools/asanaReport.js --input samples.json --milestone "Sprint 3"
```

`samples.json` is a JSON array of `{ "spellIR": {...}, "glyphAST": {...} }`
objects (the outputs of `compileSpell`). Samples may also be piped via stdin.

The token is **never** accepted as a command-line argument (argv is visible in
process listings) — only via the environment.

## Programmatic usage

```js
import { createAsanaReporter } from '../src/reporting/asanaReporter.js';

const reporter = createAsanaReporter(); // reads env, disabled unless configured

// Fully safe to call even when disabled — returns a skipped result.
await reporter.reportMetrics(results, { milestone: 'Sprint 3' });
await reporter.reportMilestone('Beta cut', 'all effect renderers green');
```

## Testing

Default tests fully mock Asana HTTP calls:

```bash
npm test                 # mocked, no network
RUN_LIVE_ASANA_TESTS=1 npm test   # opt-in: also hits real Asana (needs a token)
```
