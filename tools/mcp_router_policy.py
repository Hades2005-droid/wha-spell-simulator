#!/usr/bin/env python3
"""Deterministic policy engine for the hierarchical MCP router.

The LLM planner proposes; this table decides. No network calls, no LLM
judgment, no side effects: pure functions over tools/mcp_router_registry.json.

Usage:
    python3 tools/mcp_router_policy.py validate
    python3 tools/mcp_router_policy.py route --domain source_control
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parent / "mcp_router_registry.json"

VALID_LANES = ("read_only", "draft_write", "confirmed_write")
WRITE_LANES = ("draft_write", "confirmed_write")
SECRET_VALUE_MARKERS = ("sk-", "xoxb-", "xoxp-", "ghp_", "github_pat_", "Bearer ", "AKIA")


def load_registry(path: Path | str = REGISTRY_PATH) -> dict:
    return json.loads(Path(path).read_text())


def validate_registry(registry: dict) -> list[str]:
    """Structural + policy validation. Returns a list of issues (empty = ok)."""
    issues: list[str] = []

    if registry.get("schema") != "shadow_garden.mcp_router_registry.v1":
        issues.append("schema: unexpected or missing schema id")
    if registry.get("secrets_policy") != "env_only":
        issues.append("secrets_policy: must be env_only")

    lanes = registry.get("policy", {}).get("lanes", {})
    for lane in VALID_LANES:
        if lane not in lanes:
            issues.append(f"policy.lanes: missing lane {lane}")
    for lane in WRITE_LANES:
        if lane in lanes and lanes[lane].get("requires_approval") is not True:
            issues.append(f"policy.lanes.{lane}: write lane must require approval")
    if lanes.get("read_only", {}).get("requires_approval") is not False:
        issues.append("policy.lanes.read_only: must not require approval")

    seen_ids = set()
    for server in registry.get("servers", []):
        sid = server.get("id", "<missing>")
        if sid in seen_ids:
            issues.append(f"servers.{sid}: duplicate id")
        seen_ids.add(sid)

        for field in ("domain", "transport", "env_vars", "allowed_lanes", "default_lane", "forbidden"):
            if field not in server:
                issues.append(f"servers.{sid}: missing field {field}")

        for lane in server.get("allowed_lanes", []):
            if lane not in VALID_LANES:
                issues.append(f"servers.{sid}: unknown lane {lane}")
        default_lane = server.get("default_lane")
        if default_lane not in server.get("allowed_lanes", []):
            issues.append(f"servers.{sid}: default_lane {default_lane} not in allowed_lanes")

        # env_only means variable NAMES only; reject anything shaped like a value.
        for env in server.get("env_vars", []):
            if any(marker in env for marker in SECRET_VALUE_MARKERS) or "=" in env:
                issues.append(f"servers.{sid}: env_vars must contain names only, found value-like entry")

    return issues


def find_servers(registry: dict, domain: str) -> list[dict]:
    return [s for s in registry.get("servers", []) if s.get("domain") == domain]


def select_route(registry: dict, domain: str, lane: str | None = None,
                 approval: dict | None = None) -> dict:
    """Pure routing decision. approval={'server','lane','scope'} when granted.

    Returns a decision dict suitable for the route ledger.
    """
    def decision(allowed: bool, reason: str, targets: list[str] | None = None,
                 requires_approval: bool = False, effective_lane: str | None = None) -> dict:
        return {
            "intent": f"{domain}:{effective_lane or lane or 'default'}",
            "domain": domain,
            "lane": effective_lane or lane,
            "targets": targets or [],
            "requires_approval": requires_approval,
            "approved": bool(approval),
            "allowed": allowed,
            "reason": reason,
        }

    candidates = find_servers(registry, domain)
    if not candidates:
        return decision(False, f"no server registered for domain {domain}")

    server = candidates[0]
    effective_lane = lane or server["default_lane"]
    if effective_lane not in VALID_LANES:
        return decision(False, f"unknown lane {effective_lane}", effective_lane=effective_lane)
    if effective_lane not in server["allowed_lanes"]:
        return decision(False, f"lane {effective_lane} not allowed for {server['id']}",
                        effective_lane=effective_lane)

    if effective_lane == "read_only":
        return decision(True, "read-only lane auto-approved", [server["id"]],
                        requires_approval=False, effective_lane=effective_lane)

    # Write lanes: approval must name this server and lane.
    if not approval or approval.get("server") != server["id"] or approval.get("lane") != effective_lane:
        return decision(False, "write lane blocked: explicit approval required",
                        [server["id"]], requires_approval=True, effective_lane=effective_lane)

    # Exact-scope servers (e.g. qdrant) additionally require a named scope.
    if server.get("write_approval_scope") == "exact_collection" and not approval.get("scope"):
        return decision(False, "write lane blocked: exact collection scope required",
                        [server["id"]], requires_approval=True, effective_lane=effective_lane)

    return decision(True, "write lane approved with explicit scope", [server["id"]],
                    requires_approval=True, effective_lane=effective_lane)


def ledger_entry(decision: dict) -> dict:
    """Decision + timestamp, shaped for the JSONL route ledger."""
    return {"timestamp": datetime.now(timezone.utc).isoformat(), **decision}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MCP router policy (deterministic, local-only)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate", help="validate the registry")
    route = sub.add_parser("route", help="print a route decision")
    route.add_argument("--domain", required=True)
    route.add_argument("--lane", default=None)
    args = parser.parse_args(argv)

    registry = load_registry()
    if args.cmd == "validate":
        issues = validate_registry(registry)
        print(json.dumps({"ok": not issues, "issues": issues}, indent=2))
        return 0 if not issues else 1

    print(json.dumps(ledger_entry(select_route(registry, args.domain, args.lane)), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
