#!/usr/bin/env python3
"""Alias → tools/github_asuna_point0_unify.py (Perplexity Asuna point-0 catalog)."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

TARGET = Path(__file__).resolve().parent / "github_asuna_point0_unify.py"

if __name__ == "__main__":
    sys.argv[0] = str(TARGET)
    runpy.run_path(str(TARGET), run_name="__main__")
