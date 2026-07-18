"""Gate construction and schema-level validation."""

from __future__ import annotations

from typing import Any, Mapping


GATE_STATUSES = {"PASS", "PASS_CONDITIONAL", "FAIL"}
REQUIRED_GATE_FIELDS = {
    "gate_id",
    "goal",
    "status",
    "source_commits",
    "input_hashes",
    "commands",
    "tests",
    "metrics",
    "figures",
    "conditions",
    "blockers",
    "decisions_required",
    "eligible_next_goals",
}


def validate_gate(payload: Mapping[str, Any]) -> None:
    """Fail on missing fields, invalid status or unsafe next-goal promotion."""

    missing = REQUIRED_GATE_FIELDS.difference(payload)
    if missing:
        raise ValueError(f"gate missing required fields: {sorted(missing)}")
    if payload["status"] not in GATE_STATUSES:
        raise ValueError(f"invalid gate status: {payload['status']}")
    for field in ("commands", "figures", "conditions", "blockers", "decisions_required", "eligible_next_goals"):
        if not isinstance(payload[field], list):
            raise TypeError(f"gate field must be a list: {field}")
    if payload["status"] != "PASS" and payload["eligible_next_goals"]:
        raise ValueError("conditional or failed gates cannot authorize a next Goal")


def build_gate(
    *,
    status: str,
    source_commits: Mapping[str, str],
    input_hashes: Mapping[str, str],
    commands: list[str],
    tests: Mapping[str, Any],
    metrics: Mapping[str, Any],
    conditions: list[str],
    blockers: list[str],
    decisions_required: list[str],
) -> dict[str, Any]:
    """Build and validate the canonical G00 payload."""

    payload: dict[str, Any] = {
        "gate_id": "G00",
        "goal": "Preflight and provenance",
        "status": status,
        "source_commits": dict(source_commits),
        "input_hashes": dict(input_hashes),
        "commands": commands,
        "tests": dict(tests),
        "metrics": dict(metrics),
        "figures": [],
        "conditions": conditions,
        "blockers": blockers,
        "decisions_required": decisions_required,
        "eligible_next_goals": ["G1"] if status == "PASS" else [],
    }
    validate_gate(payload)
    return payload
