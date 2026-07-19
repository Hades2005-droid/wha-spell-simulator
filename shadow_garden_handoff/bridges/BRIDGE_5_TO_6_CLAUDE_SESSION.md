# Bridge 5 to 6 — Claude Code Session Pointer

Status: staged local-only.

Claude Code session:
`https://claude.ai/code/session_01G6jmjJriJW51biCRWsnVPL`

## Symbolic routing

- Bridge 5: Perplexity / Fable / front synthesis.
- Bridge 6: Grok 4.5 / Harmony / back-lane validation.
- Claude session is the handoff bridge from 5 to 6.
- Symbolic labels only. No permission escalation.

## Read-only extraction rules

When opened in Claude:
- Extract project facts, branch, files, test results, commands, and JSON return only.
- Do not inspect secrets, tokens, credentials, cookies, private messages, or protected files.
- Do not use adult video URLs or explicit content.
- Do not commit, push, edit, run commands, post, create Jira, or mutate Qdrant/X/GitHub.

## Connector posture

- Atlassian: no write unless explicitly approved.
- GitHub: no commit/push/PR unless explicitly approved.
- X: no social interactions.
- Qdrant: no mutation; connector previously degraded.

## Waiting for extraction

Paste or ingest Claude JSON/project return here when available, then route to Gate 6 / Grok Harmony validation.
