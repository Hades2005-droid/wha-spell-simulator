#!/usr/bin/env python3
"""Perplexity mesh adapter — review one named local document with Sonar.

Scoped and deliberate by design: it sends exactly the document you point it at,
to Perplexity only, and only when you pass --send. Default is a dry run that
assembles the request and prints a preview without touching the network. It does
not scan Downloads/Drive or any folder — you name the file.

    python3 tools/perplexity_mesh_adapter.py \\
      --request "Review the Q24 recommendation for ingestion risks." \\
      --document "/path/to/Q24_Alpha_Component_Recommendation.pdf"
    #   ^ dry run: shows the assembled prompt, sends nothing
    # add --send to make the live Sonar call.

The API key is read only from the environment (PERPLEXITY_API_KEY) — never from
a flag and never printed. Keep it in ~/ShadowGarden/.env or your shell env.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

PERPLEXITY_BASE = os.getenv("PERPLEXITY_BASE_URL", "https://api.perplexity.ai")
PERPLEXITY_ENDPOINT = os.getenv("PERPLEXITY_ENDPOINT", "/v1/sonar")
DEFAULT_MODEL = os.getenv("PERPLEXITY_MODEL", "sonar-reasoning-pro")
DOC_CHAR_CAP = 48000  # bound the request; large docs are truncated with a note.

TEXTUAL = {".txt", ".md", ".json", ".csv", ".log", ".yaml", ".yml", ".xml", ""}


def die(msg: str) -> "None":
    raise SystemExit(f"[mesh] {msg}")


def extract_pdf(path: Path) -> str:
    for mod_name in ("pypdf", "PyPDF2"):
        try:
            mod = importlib.import_module(mod_name)
        except ImportError:
            continue
        try:
            reader = mod.PdfReader(str(path))
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception as exc:  # pragma: no cover - malformed pdf
            die(f"{mod_name} could not read the PDF: {exc}")
    if shutil.which("pdftotext"):
        try:
            out = subprocess.run(
                ["pdftotext", str(path), "-"], capture_output=True, text=True, timeout=60,
            )
        except subprocess.TimeoutExpired:
            die(f"pdftotext timed out after 60s on {path.name} — the PDF may be malformed.")
        if out.returncode == 0:
            return out.stdout
        die(f"pdftotext failed (exit {out.returncode}): {out.stderr.strip()[:200] or 'no stderr output'}")
    die("PDF extraction needs 'pypdf' (pip install pypdf) or the 'pdftotext' CLI.")
    return ""  # unreachable


def read_document(path_str: str) -> str:
    path = Path(path_str).expanduser()
    if not path.exists():
        die(f"document not found: {path}")
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        text = extract_pdf(path)
    elif suffix in TEXTUAL:
        text = path.read_text(errors="replace")
    else:
        try:
            text = path.read_text(errors="replace")
        except Exception:
            die(f"cannot read '{suffix}' as text — convert it to .txt or .pdf first.")
            text = ""
    text = text.strip()
    if len(text) > DOC_CHAR_CAP:
        text = text[:DOC_CHAR_CAP] + f"\n\n[...truncated at {DOC_CHAR_CAP} chars...]"
    return text


def build_messages(request: str, doc_text: str, doc_name: str) -> list:
    system = (
        "You are the Perplexity Sonar reviewer for the Shadow Garden mesh. Ground your "
        "review in the attached document, and use the web only to check facts. Be "
        "concrete: surface risks, gaps, and one clear recommendation."
    )
    user = request
    if doc_text:
        user += f"\n\n--- DOCUMENT: {doc_name} ---\n{doc_text}"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def call_sonar(messages: list, model: str, max_tokens: int, timeout: int = 120) -> str:
    key = os.environ.get("PERPLEXITY_API_KEY")
    if not key:
        die("PERPLEXITY_API_KEY is not set (keep it in ~/ShadowGarden/.env or your shell env).")
    body = {"model": model, "messages": messages, "max_tokens": max_tokens}
    req = urllib.request.Request(
        PERPLEXITY_BASE + PERPLEXITY_ENDPOINT,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        die(f"Perplexity HTTP {exc.code}: {exc.read().decode('utf-8', 'replace')[:200]}")
    except urllib.error.URLError as exc:
        die(f"Perplexity connection error: {exc.reason}")
    return payload["choices"][0]["message"]["content"]


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Review one local document with Perplexity Sonar.")
    parser.add_argument("--request", required=True, help="What to ask Sonar about the document.")
    parser.add_argument("--document", help="Path to a local document (.pdf/.txt/.md/...).")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Sonar model (default {DEFAULT_MODEL}).")
    parser.add_argument("--max-tokens", type=int, default=1200)
    parser.add_argument("--send", action="store_true", help="Make the live Sonar call (default: dry run).")
    args = parser.parse_args(argv)

    doc_name = Path(args.document).name if args.document else "(none)"
    doc_text = read_document(args.document) if args.document else ""
    messages = build_messages(args.request, doc_text, doc_name)
    key_present = bool(os.environ.get("PERPLEXITY_API_KEY"))

    print("[mesh] Perplexity mesh adapter")
    print(f"  endpoint : {PERPLEXITY_BASE}{PERPLEXITY_ENDPOINT}")
    print(f"  model    : {args.model}")
    print(f"  request  : {args.request}")
    print(f"  document : {doc_name} ({len(doc_text)} chars)")
    print(f"  api key  : {'present (env)' if key_present else 'NOT set'}")

    if not args.send:
        preview = messages[1]["content"]
        print("\n[mesh] DRY RUN — nothing sent. Add --send for the live Sonar call.")
        print("  prompt preview:")
        print("  " + preview[:500].replace("\n", "\n  ") + ("..." if len(preview) > 500 else ""))
        return

    print("\n[mesh] sending to Perplexity Sonar...")
    answer = call_sonar(messages, args.model, args.max_tokens)
    print("\n" + answer.strip())


if __name__ == "__main__":
    main()
