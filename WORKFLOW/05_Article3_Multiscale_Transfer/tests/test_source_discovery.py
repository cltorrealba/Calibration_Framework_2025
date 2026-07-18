import json
from pathlib import Path

import pytest

from article3_multiscale.source_discovery import (
    ResolvedSource,
    inventory_model_runs,
    inventory_smoke,
    select_candidate,
)


def _candidate_source(tmp_path: Path) -> ResolvedSource:
    run_dir = tmp_path / "runs" / "run-001"
    run_dir.mkdir(parents=True)
    required = ["run_manifest.json", "dataset_qc.json", "run_metadata.csv"]
    (run_dir / "dataset_qc.json").write_text('{"verdict":"PASS"}\n', encoding="utf-8")
    (run_dir / "run_metadata.csv").write_text("run,value\nA,1\n", encoding="utf-8")
    manifest = {
        "run_id": "run-001",
        "created_utc": "2026-07-18T00:00:00Z",
        "stage": "model_dataset",
        "status": "completed",
        "schema_version": 1,
        "configuration": {
            "sha256": "a" * 64,
            "payload": {"adapter_schema_version": 2},
        },
        "gate": {"verdict": "PASS"},
        "git": {"branch": "ctorrealba_fermentation", "commit": "b" * 40, "dirty": False},
        "outputs": {
            "runs/run-001/dataset_qc.json": {
                "bytes": (run_dir / "dataset_qc.json").stat().st_size,
                "sha256": "c" * 64,
            },
            "runs/run-001/run_metadata.csv": {
                "bytes": (run_dir / "run_metadata.csv").stat().st_size,
                "sha256": "d" * 64,
            },
        },
    }
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    spec = {
        "name": "pyomo-doe",
        "model_run_manifest_glob": "runs/*/run_manifest.json",
        "required_model_run_files": required,
        "small_table_smoke_file": "run_metadata.csv",
    }
    return ResolvedSource(
        name="pyomo-doe",
        root=tmp_path,
        root_locator="${PYOMO_DOE_ROOT}",
        resolution_method="fixture",
        spec=spec,
    )


def test_inventory_and_smoke_do_not_select(tmp_path: Path) -> None:
    source = _candidate_source(tmp_path)
    candidates = inventory_model_runs(source)
    assert len(candidates) == 1
    assert candidates[0].eligible is True
    smoke = inventory_smoke(source, candidates)
    assert smoke["status"] == "PASS"
    assert smoke["eligible_tables_checked"] == 1
    assert smoke["selection_performed"] is False


def test_selection_rejects_latest_and_requires_exact_id(tmp_path: Path) -> None:
    source = _candidate_source(tmp_path)
    candidates = inventory_model_runs(source)
    with pytest.raises(ValueError, match="latest"):
        select_candidate(candidates, "latest")
    with pytest.raises(ValueError, match="exactly one"):
        select_candidate(candidates, "run")
    assert select_candidate(candidates, "run-001").run_id == "run-001"
