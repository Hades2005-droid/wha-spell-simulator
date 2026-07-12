#!/usr/bin/env python3
"""Bounded, metadata-only ingestion for the Shadow Garden Eden lane.

The Eden lane accepts explicitly supplied local files or directories and emits
only classification, size, depth, and SHA-256 metadata. It never sends
content to a provider, follows symlinks, or treats an incoming document as an
instruction.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


SCHEMA = "shadow_garden.eden_metadata_catalog.v1"
DEFAULT_MAX_DEPTH = 2
DEFAULT_MAX_ENTRIES = 5_000
DEFAULT_MAX_BYTES = 64 * 1024 * 1024
DEFAULT_MAX_RECORD_BYTES = 16 * 1024 * 1024
REMOTE_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")
SECRET_COMPONENTS = {
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".env.test",
    "credentials",
    "credentials.json",
    "id_rsa",
    "id_ed25519",
    "private_key",
    "secrets",
    "secrets.json",
}
SECRET_MARKERS = ("api_key", "apikey", "password", "secret", "token")


class EdenIngestError(ValueError):
    """Raised for unsafe or invalid local ingestion input."""


@dataclass(frozen=True)
class EdenPolicy:
    """Limits applied before any local metadata is recorded."""

    max_depth: int = DEFAULT_MAX_DEPTH
    max_entries: int = DEFAULT_MAX_ENTRIES
    max_bytes: int = DEFAULT_MAX_BYTES
    max_record_bytes: int = DEFAULT_MAX_RECORD_BYTES
    allowed_roots: tuple[Path, ...] = ()

    def __post_init__(self) -> None:
        if self.max_depth < 0:
            raise EdenIngestError("max_depth must be non-negative")
        if self.max_entries < 1:
            raise EdenIngestError("max_entries must be greater than zero")
        if self.max_bytes < 1 or self.max_record_bytes < 1:
            raise EdenIngestError("byte limits must be greater than zero")
        if self.max_record_bytes > self.max_bytes:
            raise EdenIngestError("max_record_bytes cannot exceed max_bytes")
        object.__setattr__(
            self,
            "allowed_roots",
            tuple(Path(root).expanduser().resolve() for root in self.allowed_roots),
        )


@dataclass(frozen=True)
class EdenRecord:
    """Metadata for one accepted local record; no payload is retained."""

    kind: str
    name: str
    path: str
    bytes: int
    depth: int
    sha256: str


@dataclass
class EdenMetadataCatalog:
    """Accumulate bounded local metadata with explicit rejection reasons."""

    policy: EdenPolicy = field(default_factory=EdenPolicy)
    records: list[EdenRecord] = field(default_factory=list)
    rejected: list[dict[str, Any]] = field(default_factory=list)
    _seen_paths: set[Path] = field(default_factory=set, init=False, repr=False)
    _seen_digests: set[str] = field(default_factory=set, init=False, repr=False)
    _total_bytes: int = field(default=0, init=False, repr=False)
    _scanned_entries: int = field(default=0, init=False, repr=False)

    @property
    def total_bytes(self) -> int:
        return self._total_bytes

    def absorb(self, values: Iterable[str | Path]) -> "EdenMetadataCatalog":
        """Absorb explicit local files/directories without retaining content."""

        for value in values:
            if self._scanned_entries >= self._scan_limit:
                self._reject(str(value), "entry_scan_limit_exceeded")
                break
            self._absorb_target(value)
        return self

    def snapshot(self) -> dict[str, Any]:
        """Return a stable, JSON-serializable metadata-only snapshot."""

        counts = {kind: 0 for kind in ("land", "astro_node", "data")}
        for record in self.records:
            counts[record.kind] += 1
        return {
            "schema": SCHEMA,
            "controls": {
                "local_only": True,
                "explicit_paths_only": True,
                "payloads_stored": False,
                "payloads_emitted": False,
                "remote_fetch": False,
                "credentials_allowed": False,
                "symlinks_followed": False,
                "secret_named_paths_allowed": False,
            },
            "policy": {
                "max_depth": self.policy.max_depth,
                "max_entries": self.policy.max_entries,
                "max_bytes": self.policy.max_bytes,
                "max_record_bytes": self.policy.max_record_bytes,
                "allowed_roots": [str(root) for root in self.policy.allowed_roots],
            },
            "accepted": len(self.records),
            "rejected": len(self.rejected),
            "bytes": self.total_bytes,
            "counts": counts,
            "lunar": {
                "mode": "symbolic_metadata_only",
                "moon_18": {
                    "target": 18,
                    "sealed": True,
                    "secret_material_present": False,
                },
            },
            "records": [asdict(record) for record in self.records],
            "rejections": list(self.rejected),
        }

    def _absorb_target(self, value: str | Path) -> None:
        raw = str(value)
        if REMOTE_SCHEME.match(raw.strip()):
            self._reject(raw, "remote_source_rejected")
            return
        if _has_secret_component(raw):
            self._reject(raw, "secret_named_path_rejected")
            return

        try:
            target = Path(value).expanduser()
            if not target.exists():
                raise EdenIngestError("path does not exist")
            if target.is_symlink():
                raise EdenIngestError("symlink_rejected")
            target = target.resolve()
        except (OSError, RuntimeError, EdenIngestError) as exc:
            self._reject(raw, str(exc))
            return

        if not _within_allowed_roots(target, self.policy.allowed_roots):
            self._reject(str(target), "outside_allowlisted_root")
            return

        if target.is_file():
            self._absorb_file(target, depth=0)
            return
        if target.is_dir():
            self._absorb_directory(target)
            return
        self._reject(str(target), "unsupported_path_type")

    def _absorb_directory(self, target: Path) -> None:
        for root_string, directories, filenames in os.walk(
            target, topdown=True, followlinks=False
        ):
            root = Path(root_string)
            relative_root = root.relative_to(target)
            root_depth = len(relative_root.parts)
            next_directories: list[str] = []
            for directory in sorted(directories):
                directory_path = root / directory
                if not self._consume_scan(directory_path):
                    directories[:] = []
                    return
                if directory_path.is_symlink():
                    self._reject(str(directory_path), "symlink_rejected")
                elif _has_secret_component(directory):
                    self._reject(str(directory_path), "secret_named_path_rejected")
                elif root_depth >= self.policy.max_depth:
                    self._reject(str(directory_path), "depth_limit_exceeded")
                else:
                    next_directories.append(directory)
            directories[:] = next_directories
            for filename in sorted(filenames):
                candidate = root / filename
                depth = root_depth
                if not self._consume_scan(candidate):
                    return
                if _has_secret_component(filename):
                    self._reject(str(candidate), "secret_named_path_rejected")
                elif depth > self.policy.max_depth:
                    self._reject(str(candidate), "depth_limit_exceeded")
                else:
                    self._absorb_file(candidate, depth=depth, scanned=True)

    def _absorb_file(self, path: Path, *, depth: int, scanned: bool = False) -> None:
        if not scanned and not self._consume_scan(path):
            return
        if len(self.records) >= self.policy.max_entries:
            self._reject(str(path), "entry_limit_exceeded")
            return
        if path in self._seen_paths:
            self._reject(str(path), "duplicate_path")
            return
        self._seen_paths.add(path)

        if path.is_symlink():
            self._reject(str(path), "symlink_rejected")
            return
        try:
            size = path.stat().st_size
        except OSError as exc:
            self._reject(str(path), f"stat_failed:{type(exc).__name__}")
            return
        if size > self.policy.max_record_bytes:
            self._reject(str(path), "record_byte_limit_exceeded")
            return
        if self.total_bytes + size > self.policy.max_bytes:
            self._reject(str(path), "total_byte_limit_exceeded")
            return

        try:
            digest = _sha256(path)
        except OSError as exc:
            self._reject(str(path), f"read_failed:{type(exc).__name__}")
            return
        if digest in self._seen_digests:
            self._reject(str(path), "duplicate_content")
            return

        self._seen_digests.add(digest)
        self._total_bytes += size
        self.records.append(
            EdenRecord(
                kind=classify_path(path),
                name=path.name,
                path=str(path),
                bytes=size,
                depth=depth,
                sha256=digest,
            )
        )

    @property
    def _scan_limit(self) -> int:
        return self.policy.max_entries * 2 + self.policy.max_depth + 1

    def _consume_scan(self, path: Path) -> bool:
        if self._scanned_entries >= self._scan_limit:
            self._reject(str(path), "entry_scan_limit_exceeded")
            return False
        self._scanned_entries += 1
        return True

    def _reject(self, value: str, reason: str) -> None:
        self.rejected.append(
            {
                "source": _safe_source(value),
                "reason": reason,
            }
        )


def _safe_source(value: str) -> str:
    if REMOTE_SCHEME.match(value.strip()):
        return "[REMOTE_SOURCE_REDACTED]"
    if _has_secret_component(value):
        return "[SECRET_NAMED_PATH_REDACTED]"
    return value


def _has_secret_component(value: str | Path) -> bool:
    components = str(value).replace("\\", "/").split("/")
    for component in components:
        lowered = component.lower()
        if lowered in SECRET_COMPONENTS:
            return True
        if any(marker in lowered for marker in SECRET_MARKERS):
            return True
    return False


def _within_allowed_roots(path: Path, roots: tuple[Path, ...]) -> bool:
    if not roots:
        return True
    return any(path == root or root in path.parents for root in roots)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tokens(path: Path) -> set[str]:
    return {
        token
        for part in path.parts
        for token in re.split(r"[^a-z0-9]+", part.lower())
        if token
    }


def classify_path(path: str | Path) -> str:
    """Classify a path into the three bounded Eden lanes."""

    tokens = _tokens(Path(path))
    if tokens.intersection({"astro", "astronomy", "node", "moon", "lunar", "celestial"}):
        return "astro_node"
    if tokens.intersection({"land", "terrain", "region", "world"}):
        return "land"
    return "data"


def catalog_from_paths(
    values: Iterable[str | Path],
    *,
    policy: EdenPolicy | None = None,
) -> dict[str, Any]:
    """Build one bounded catalog from caller-supplied paths."""

    return EdenMetadataCatalog(policy=policy or EdenPolicy()).absorb(values).snapshot()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a bounded, metadata-only Eden catalog from local paths"
    )
    parser.add_argument(
        "--path",
        action="append",
        default=[],
        help="explicit local file or directory; repeat for multiple paths",
    )
    parser.add_argument(
        "--allow-root",
        action="append",
        default=[],
        help="optional root that every path must remain within",
    )
    parser.add_argument("--max-depth", type=int, default=DEFAULT_MAX_DEPTH)
    parser.add_argument("--max-entries", type=int, default=DEFAULT_MAX_ENTRIES)
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    parser.add_argument(
        "--max-record-bytes", type=int, default=DEFAULT_MAX_RECORD_BYTES
    )
    parser.add_argument("--output", help="optional JSON output path")
    args = parser.parse_args(argv)

    try:
        roots = tuple(Path(value).expanduser().resolve() for value in args.allow_root)
        payload = catalog_from_paths(
            args.path,
            policy=EdenPolicy(
                max_depth=args.max_depth,
                max_entries=args.max_entries,
                max_bytes=args.max_bytes,
                max_record_bytes=args.max_record_bytes,
                allowed_roots=roots,
            ),
        )
    except (EdenIngestError, OSError, RuntimeError) as exc:
        print(json.dumps({"schema": SCHEMA, "status": "error", "error": str(exc)}))
        return 2

    rendered = json.dumps(payload, indent=2)
    if args.output:
        output = Path(args.output).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
