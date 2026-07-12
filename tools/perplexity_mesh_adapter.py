#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .document_ingest import (
        DEFAULT_MAX_CHARS,
        DocumentIngestError,
        NormalizedDocument,
        document_prompt_block,
        load_documents,
    )
except ImportError:
    from document_ingest import (
        DEFAULT_MAX_CHARS,
        DocumentIngestError,
        NormalizedDocument,
        document_prompt_block,
        load_documents,
    )

DEFAULT_API_URL = "https://api.perplexity.ai/chat/completions"
DEFAULT_MODEL = "sonar"
DEFAULT_STATUS_FILE = "/tmp/shadow_garden_perplexity_status.json"
DEFAULT_OUTPUT_FILE = "/tmp/shadow_garden_perplexity_review.json"
LOCAL_CONTEXT_FILES = (
    "/tmp/shadow_garden_recursive_node_status.json",
    "/tmp/shadow_garden_extension_workspace_status.json",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: str) -> dict[str, Any] | None:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def local_context() -> dict[str, Any]:
    context: dict[str, Any] = {}
    for path in LOCAL_CONTEXT_FILES:
        payload = read_json(path)
        if payload is not None:
            context[Path(path).stem] = payload
    return context


def build_prompt(
    request: str,
    context: dict[str, Any],
    documents: list[NormalizedDocument] | None = None,
) -> str:
    normalized = " ".join((request or "").split())
    if not normalized:
        normalized = "Review the current local Shadow Garden mesh status."
    lines = [
        "Shadow Garden local mesh review.",
        "Boundary: docs-only technical analysis; do not control browser profiles, automate Comet, scrape third-party pages, extract credentials, or broadcast prompts to other agents.",
        "Treat chronology/vector output as symbolic metadata only, not as factual authority or a decision system.",
        "Review the following request and local status metadata for reliability, integration risks, and a short actionable checklist.",
        "Native PDF parts are not supported by this model path. Any PDF below has already been converted to bounded, redacted UTF-8 text.",
        f"Request: {normalized}",
        f"Local status metadata: {json.dumps(context, ensure_ascii=False, sort_keys=True)}",
    ]
    if documents:
        lines.extend(document_prompt_block(document) for document in documents)
    return "\n".join(lines)


def build_payload(model: str, prompt: str, max_tokens: int) -> dict[str, Any]:
    return {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a technical reviewer for a local-only development mesh. Stay grounded and follow the stated boundary.",
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }


def write_json(path: str, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(f"{target.suffix}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)


def request_perplexity(
    api_url: str,
    api_key: str,
    payload: dict[str, Any],
    timeout: float,
) -> dict[str, Any]:
    request = urllib.request.Request(
        api_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Perplexity API returned HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Perplexity API request failed: {exc}") from exc
    try:
        parsed = json.loads(body)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Perplexity API returned non-JSON data") from exc
    return parsed if isinstance(parsed, dict) else {"response": parsed}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local Perplexity mesh review adapter")
    parser.add_argument("--request", action="append", default=[])
    parser.add_argument("--model", default=os.environ.get("PERPLEXITY_MODEL", DEFAULT_MODEL))
    parser.add_argument("--api-url", default=os.environ.get("PERPLEXITY_API_URL", DEFAULT_API_URL))
    parser.add_argument("--status-file", default=DEFAULT_STATUS_FILE)
    parser.add_argument("--output-file", default=DEFAULT_OUTPUT_FILE)
    parser.add_argument("--max-tokens", type=int, default=800)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument(
        "--document",
        action="append",
        default=[],
        help="local text/PDF document to normalize before review; may be repeated",
    )
    parser.add_argument("--max-document-chars", type=int, default=DEFAULT_MAX_CHARS)
    parser.add_argument("--send", action="store_true", help="Explicitly allow one API request")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.max_tokens < 1 or args.timeout <= 0:
        print(json.dumps({"error": "max-tokens must be positive and timeout must be greater than zero"}))
        return 2

    request_text = " ".join(args.request).strip()
    try:
        documents = load_documents(args.document, max_chars=args.max_document_chars)
    except DocumentIngestError as exc:
        status = {
            "kind": "shadow_garden_perplexity_status",
            "generated_at": utc_now(),
            "status": "document_ingest_error",
            "local_only_handoff": True,
            "native_pdf_input": False,
            "error": str(exc),
        }
        write_json(args.status_file, status)
        print(json.dumps(status, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2

    context = local_context()
    prompt = build_prompt(request_text, context, documents)
    api_key = os.environ.get("PERPLEXITY_API_KEY", "")
    status: dict[str, Any] = {
        "kind": "shadow_garden_perplexity_status",
        "generated_at": utc_now(),
        "status": "ready" if api_key else "blocked_api_key_missing",
        "local_only_handoff": True,
        "native_pdf_input": False,
        "browser_automation": False,
        "broadcast_to_agents": False,
        "api_key_present": bool(api_key),
        "api_url": args.api_url,
        "model": args.model,
        "context_files": list(context),
        "document_names": [document.name for document in documents],
        "document_count": len(documents),
        "document_representations": [document.source_type for document in documents],
        "guardrails": [
            "env_only_secret",
            "dry_run_by_default",
            "pdfs_normalized_to_text",
            "explicit_send_required",
            "no_browser_profile_control",
            "no_third_party_scraping",
            "no_credential_logging",
            "docs_only_review",
        ],
    }

    if not args.send:
        status["status"] = "dry_run_ready" if api_key else "dry_run_api_key_missing"
        status["prompt_preview"] = prompt
        write_json(args.status_file, status)
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return 0

    if not api_key:
        status["status"] = "blocked_api_key_missing"
        write_json(args.status_file, status)
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return 2

    try:
        response = request_perplexity(
            args.api_url,
            api_key,
            build_payload(args.model, prompt, args.max_tokens),
            args.timeout,
        )
    except RuntimeError as exc:
        status["status"] = "api_error"
        status["error"] = str(exc)
        write_json(args.status_file, status)
        print(json.dumps(status, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    status["status"] = "review_complete"
    status["response_saved_to"] = args.output_file
    write_json(args.output_file, {"generated_at": utc_now(), "request": request_text, "response": response})
    write_json(args.status_file, status)
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
