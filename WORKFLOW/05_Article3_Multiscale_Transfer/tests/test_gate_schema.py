import json
from pathlib import Path

import jsonschema
import pytest

from article3_multiscale.gate import build_gate, validate_gate


SCHEMA = Path(__file__).resolve().parents[1] / "config" / "schemas" / "gate_status.schema.json"


def test_conditional_gate_cannot_promote_next_goal() -> None:
    gate = build_gate(
        status="PASS_CONDITIONAL",
        source_commits={"source": "a" * 40},
        input_hashes={"index": "b" * 64},
        commands=[],
        tests={},
        metrics={},
        conditions=["approval required"],
        blockers=["run selection"],
        decisions_required=["select run"],
    )
    assert gate["eligible_next_goals"] == []
    validate_gate(gate)
    jsonschema.validate(gate, json.loads(SCHEMA.read_text(encoding="utf-8")))


def test_invalid_gate_status_fails() -> None:
    with pytest.raises(ValueError, match="invalid gate status"):
        build_gate(
            status="CONDITIONAL",
            source_commits={},
            input_hashes={},
            commands=[],
            tests={},
            metrics={},
            conditions=[],
            blockers=[],
            decisions_required=[],
        )
