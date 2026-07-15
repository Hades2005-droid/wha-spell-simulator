#!/usr/bin/env python3
"""ASCII normalization for authority-package text (Copilot prompt safety)."""

from __future__ import annotations

from pathlib import Path

ASCII_REPLACEMENTS = {
    "\u2014": "-",  # em dash
    "\u2013": "-",  # en dash
    "\u2192": "->",
    "\u2190": "<-",
    "\u2194": "<->",
    "\u00d7": "x",
    "\u00b7": ".",
    "\u2026": "...",
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u00a0": " ",
}


def normalize_ascii(text: str, *, strip_emoji: bool = True) -> str:
    for src, dst in ASCII_REPLACEMENTS.items():
        text = text.replace(src, dst)
    if strip_emoji:
        text = "".join(ch for ch in text if ord(ch) <= 127 or ch.isascii())
    return text


def has_non_ascii(text: str) -> bool:
    return any(ord(ch) > 127 for ch in text)