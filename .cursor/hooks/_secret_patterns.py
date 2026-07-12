"""Shared raw-secret detectors for Cursor hooks (deterministic, no network)."""

from __future__ import annotations

import re
from typing import Iterable

# Apparent raw credential values — not bare env-var *names*.
_RAW_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("pplx_key", re.compile(r"(?i)\bpplx-[A-Za-z0-9_\-]{8,}\b")),
    ("xai_key", re.compile(r"(?i)\bxai-[A-Za-z0-9_\-]{8,}\b")),
    ("openai_sk", re.compile(r"(?i)\bsk-[A-Za-z0-9_\-]{20,}\b")),
    ("sk_underscore", re.compile(r"(?i)\bsk_[A-Za-z0-9_\-]{16,}\b")),
    ("github_pat", re.compile(r"(?i)\b(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}\b")),
    ("slack_token", re.compile(r"(?i)\bxox[baprs]-[A-Za-z0-9\-]{10,}\b")),
    ("bearer_token", re.compile(r"(?i)\bBearer\s+[A-Za-z0-9\-_\.=]{20,}\b")),
    (
        "assignment",
        re.compile(
            r"(?i)\b(?:API_KEY|SECRET_KEY|ACCESS_TOKEN|ACCESS_SECRET|BOT_TOKEN|"
            r"XAI_API_KEY|LINEAR_API_KEY|GITHUB_TOKEN|GH_TOKEN|ATLASSIAN_API_TOKEN)"
            r"\s*[:=]\s*['\"]?[^\s'\"]{8,}"
        ),
    ),
]

# Commands that dump credential stores / print raw secret material.
_SHELL_DUMP_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "dump_auth_json",
        re.compile(
            r"(?i)(?:\bcat\b|\btype\b|\bprint\b|\bhead\b|\btail\b|\bless\b|\bmore\b|"
            r"\bjq\b|\bpython3?\b.*\bopen\b).*(?:auth\.json|\.env(?:\.local)?|"
            r"credentials\.json|secrets?\.(?:json|yml|yaml|env)|id_rsa|"
            r"\.npmrc|\.netrc)"
        ),
    ),
    (
        "printenv_secrets",
        re.compile(
            r"(?i)\b(?:printenv|env)\b.*\|\s*(?:grep|rg|egrep).*"
            r"(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD|BEARER|CREDENTIAL)"
        ),
    ),
    (
        "echo_raw_key",
        re.compile(r"(?i)\becho\b[^|;]*\b(?:pplx-|xai-|sk-|sk_|ghp_|xox[baprs]-|Bearer\s+)"),
    ),
]

# Placeholders and fixture tokens — allowed in prompts/docs; not real credentials.
_PLACEHOLDER_RE = re.compile(
    r"(?i)("
    r"\[REDACTED\]|"
    r"\$\{?[A-Z][A-Z0-9_]*\}?|"
    r"<\s*(?:your|api|secret|token)[^>]*>|"
    r"YOUR_[A-Z0-9_]+|"
    r"xxx+|"
    r"PLACEHOLDER|"
    r"TODO_SET|"
    r"env_only|"
    # Common redaction / example fixtures (never treat as live secrets)
    r"\bpplx-(?:REDACTED(?:_FAKE)?(?:_[A-Z0-9_]+)?|example|fake|test|dummy)[A-Za-z0-9_\-]*\b|"
    r"\bxai-(?:REDACTED(?:_FAKE)?(?:_[A-Z0-9_]+)?|example|fake|test|dummy)[A-Za-z0-9_\-]*\b|"
    r"\bsk-(?:REDACTED|example|fake|test|dummy)[A-Za-z0-9_\-]*\b|"
    r"\*\*\*+|"
    r"<REDACTED>"
    r")"
)


def _masked(text: str) -> str:
    """Strip obvious placeholders / env refs so they do not trigger false positives."""
    return _PLACEHOLDER_RE.sub(" ", text)


def find_raw_secrets(text: str) -> list[str]:
    if not text:
        return []
    hay = _masked(text)
    hits: list[str] = []
    for name, pattern in _RAW_PATTERNS:
        if pattern.search(hay):
            hits.append(name)
    return hits


def find_shell_secret_risks(command: str) -> list[str]:
    hits = find_raw_secrets(command)
    if not command:
        return hits
    hay = _masked(command)
    for name, pattern in _SHELL_DUMP_PATTERNS:
        if pattern.search(hay):
            hits.append(name)
    return hits


def unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out
