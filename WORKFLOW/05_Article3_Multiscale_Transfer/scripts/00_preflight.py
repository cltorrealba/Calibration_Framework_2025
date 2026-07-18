#!/usr/bin/env python3
"""Goal 0: portable preflight, provenance and Pilot 2026 run inventory."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping


PIPELINE_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PIPELINE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from article3_multiscale.environment import collect_environment
from article3_multiscale.gate import build_gate, validate_gate
from article3_multiscale.provenance import (
    GitSnapshot,
    ProvenanceError,
    classify_read_only_check,
    paths_outside_prefixes,
    private_path_hits,
    run_command,
    sha256_file,
    sha256_json,
    snapshot_repository,
    write_csv,
    write_json,
)
from article3_multiscale.run_layout import create_run_layout, make_run_id, output_inventory
from article3_multiscale.source_discovery import (
    MODEL_CANDIDATE_FIELDS,
    CandidateRecord,
    ResolvedSource,
    inventory_model_runs,
    inventory_smoke,
    resolve_source,
    select_candidate,
)


INPUT_HASH_FIELDS = ("scope", "locator", "kind", "bytes", "sha256")
CHECK_FIELDS = ("check_id", "scope", "status", "detail")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def portable_output(text: str, source: ResolvedSource) -> str:
    """Replace a resolved root with its environment-variable locator."""

    variants = {
        str(source.root),
        source.root.as_posix(),
        str(source.root).replace("\\", "/"),
    }
    value = text
    for variant in sorted(variants, key=len, reverse=True):
        value = value.replace(variant, source.root_locator)
    return value


def parse_junit(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"status": "NOT_PROVIDED"}
    tree = ET.parse(path)
    root = tree.getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0, "time_seconds": 0.0}
    for suite in suites:
        for key in ("tests", "failures", "errors", "skipped"):
            totals[key] += int(suite.attrib.get(key, 0))
        totals["time_seconds"] += float(suite.attrib.get("time", 0.0))
    totals["status"] = (
        "PASS" if totals["tests"] > 0 and totals["failures"] == 0 and totals["errors"] == 0 else "FAIL"
    )
    return totals


def add_hash(
    rows: list[dict[str, Any]],
    *,
    path: Path,
    scope: str,
    locator: str,
    kind: str,
) -> None:
    if path.is_file():
        rows.append(
            {
                "scope": scope,
                "locator": locator,
                "kind": kind,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )


def check_row(check_id: str, scope: str, status: str, detail: str) -> dict[str, str]:
    return {"check_id": check_id, "scope": scope, "status": status, "detail": detail}


def run_source_checks(
    sources: Iterable[ResolvedSource],
    *,
    timeout_seconds: int,
    skip: bool,
) -> tuple[dict[str, Any], list[str]]:
    results: dict[str, Any] = {}
    canonical_commands: list[str] = []
    if skip:
        return {"status": "SKIPPED_BY_CLI", "checks": {}}, canonical_commands
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
        }
    )
    overall = "PASS"
    for source in sources:
        for check in source.spec.get("safe_checks", []):
            canonical = [str(value) for value in check["command"]]
            actual = [sys.executable if value == "python" else value for value in canonical]
            canonical_commands.append(" ".join(canonical))
            before = snapshot_repository(
                source.root,
                expected_repository=str(source.spec["repository"]),
                required_branch=str(source.spec["required_branch"]),
                root_locator=source.root_locator,
            )
            started = time.perf_counter()
            result = run_command(
                actual,
                cwd=source.root,
                timeout=timeout_seconds,
                env=environment,
            )
            elapsed = time.perf_counter() - started
            after = snapshot_repository(
                source.root,
                expected_repository=str(source.spec["repository"]),
                required_branch=str(source.spec["required_branch"]),
                root_locator=source.root_locator,
            )
            unchanged = (
                before.current_head == after.current_head
                and before.current_branch == after.current_branch
                and before.changed_paths == after.changed_paths
            )
            stdout = portable_output(result.stdout, source)[-2000:]
            stderr = portable_output(result.stderr, source)[-2000:]
            failure_policy = str(check.get("failure_policy", "fail"))
            status = classify_read_only_check(result.returncode, unchanged, failure_policy)
            if status == "FAIL":
                overall = "FAIL"
            elif status == "KNOWN_FAILURE" and overall == "PASS":
                overall = "PASS_CONDITIONAL"
            results[f"{source.name}:{check['name']}"] = {
                "status": status,
                "return_code": result.returncode,
                "failure_policy": failure_policy,
                "known_context": str(check.get("known_context", "")),
                "runtime_seconds": round(elapsed, 6),
                "source_state_unchanged": unchanged,
                "stdout_tail": stdout,
                "stderr_tail": stderr,
            }
    return {"status": overall, "checks": results}, canonical_commands


def run_model_microbenchmark(
    source: ResolvedSource,
    candidate: CandidateRecord,
) -> tuple[dict[str, Any], str]:
    """Run the allowed read-only config/table/import smoke for one exact run."""

    before = snapshot_repository(
        source.root,
        expected_repository=str(source.spec["repository"]),
        required_branch=str(source.spec["required_branch"]),
        root_locator=source.root_locator,
    )
    timings: dict[str, float] = {}
    errors: list[str] = []

    config_path = source.root / "fermentation_model/pilot_2026/adaptive_design/model_dataset_config.json"
    started = time.perf_counter()
    try:
        config_payload = load_json(config_path)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        config_payload = {}
        errors.append(f"config_load:{type(exc).__name__}:{exc}")
    timings["config_load_seconds"] = time.perf_counter() - started

    table_path = source.root / candidate.small_table_relative_path
    started = time.perf_counter()
    row_count = 0
    try:
        with table_path.open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            row_count = sum(1 for _ in reader)
            if not reader.fieldnames or row_count == 0:
                raise ValueError("selected smoke table has no header or data rows")
    except (OSError, UnicodeError, csv.Error, ValueError) as exc:
        errors.append(f"small_table:{type(exc).__name__}:{exc}")
    timings["small_table_read_seconds"] = time.perf_counter() - started

    adapter_path = source.root / "fermentation_model/pilot_2026/adaptive_design/build_model_dataset.py"
    import_code = (
        "import importlib.util,sys; "
        "spec=importlib.util.spec_from_file_location('article3_source_adapter',sys.argv[1]); "
        "module=importlib.util.module_from_spec(spec); "
        "sys.modules[spec.name]=module; "
        "spec.loader.exec_module(module)"
    )
    environment = os.environ.copy()
    environment.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "OMP_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
        }
    )
    started = time.perf_counter()
    imported = run_command(
        (sys.executable, "-c", import_code, str(adapter_path)),
        cwd=source.root,
        timeout=60,
        env=environment,
    )
    timings["adapter_import_seconds"] = time.perf_counter() - started
    if imported.returncode != 0:
        errors.append(
            "adapter_import:"
            + portable_output(imported.stderr or imported.stdout, source)[-1000:]
        )

    after = snapshot_repository(
        source.root,
        expected_repository=str(source.spec["repository"]),
        required_branch=str(source.spec["required_branch"]),
        root_locator=source.root_locator,
    )
    unchanged = (
        before.current_head == after.current_head
        and before.current_branch == after.current_branch
        and before.changed_paths == after.changed_paths
    )
    if not unchanged:
        errors.append("source_state_changed")
    command = (
        "python -c <isolated-adapter-import> "
        f"{source.root_locator}/fermentation_model/pilot_2026/adaptive_design/build_model_dataset.py"
    )
    return (
        {
            "status": "PASS" if not errors else "FAIL",
            "selected_run_id": candidate.run_id,
            "campaign_id": config_payload.get("campaign_id"),
            "small_table_rows": row_count,
            "timings": {key: round(value, 6) for key, value in timings.items()},
            "adapter_imported": imported.returncode == 0,
            "fixture_simulation": "NOT_DECLARED",
            "simulation_executed": False,
            "calibration_executed": False,
            "source_state_unchanged": unchanged,
            "errors": errors,
        },
        command,
    )


def build_report(
    *,
    gate: Mapping[str, Any],
    source_snapshots: Iterable[tuple[str, GitSnapshot]],
    candidates: Iterable[CandidateRecord],
    tests: Mapping[str, Any],
    runtime_seconds: float,
) -> str:
    sources = list(source_snapshots)
    candidate_list = list(candidates)
    lines = [
        "# G0 preflight and provenance report",
        "",
        "## Question",
        "",
        "Can the Article 3 multiscale pipeline start from traceable repositories and an explicitly approved Pilot 2026 model-ready run without integrating data or advancing to G1?",
        "",
        "## Verdict",
        "",
        f"**{gate['status']}**. Goal 0 scaffolding and portable provenance were generated; no source data were copied and no scientific model was calibrated.",
        "",
        "## Visual evidence",
        "",
        "No figure was generated for G0. Source state and candidate evidence are tabulated in `tables/preflight_checks.csv` and `tables/model_run_candidates.csv`.",
        "",
        "## Decisions required",
        "",
    ]
    decisions = list(gate["decisions_required"])
    lines.extend([f"- {item}" for item in decisions] or ["- None."])
    lines.extend(
        [
            "",
            "## Source repositories",
            "",
            "| Source | Required ref | Required SHA | Checkout branch | Dirty | Ahead/behind |",
            "|---|---|---|---|---:|---|",
        ]
    )
    for name, snapshot in sources:
        ahead = "n/a" if snapshot.ahead_of_remote is None else str(snapshot.ahead_of_remote)
        behind = "n/a" if snapshot.behind_remote is None else str(snapshot.behind_remote)
        lines.append(
            f"| {name} | `{snapshot.required_branch}` | `{snapshot.required_sha[:12]}` | "
            f"`{snapshot.current_branch}` | {str(snapshot.dirty).lower()} | {ahead}/{behind} |"
        )
    lines.extend(
        [
            "",
            "## Pilot 2026 model-ready candidates",
            "",
            "| Run ID | Adapter schema | Status | Gate | QC | Complete | Eligible | Content group |",
            "|---|---:|---|---|---|---:|---:|---|",
        ]
    )
    for candidate in candidate_list:
        lines.append(
            f"| `{candidate.run_id}` | {candidate.adapter_schema_version} | {candidate.status} | "
            f"{candidate.gate_verdict} | {candidate.qc_verdict} | "
            f"{str(candidate.required_files_present).lower()} | {str(candidate.eligible).lower()} | "
            f"`{candidate.content_group}` |"
        )
    lines.extend(
        [
            "",
            "No candidate was selected by directory order or by a `latest` pointer.",
            "",
            "## Tests and smoke",
            "",
            f"- Pipeline pytest: `{tests['pipeline_pytest']['status']}`.",
            f"- Inventory smoke: `{tests['inventory_smoke']['status']}`; "
            f"{tests['inventory_smoke'].get('eligible_tables_checked', 0)} small tables checked.",
            f"- Read-only source checks: `{tests['source_structural_checks']['status']}`.",
            f"- Model microbenchmark: `{tests['model_microbenchmark']['status']}`.",
            "",
            "## Inputs and provenance",
            "",
            "Configuration, bundle documents, source indices and candidate manifests/QC files are hashed individually in `provenance/input_hashes.csv`. Large dataset payloads were not recursively hashed.",
            "",
            "## Runtime",
            "",
            f"Goal 0 preflight runtime: {runtime_seconds:.3f} seconds.",
            "",
            "## Limitations",
            "",
        ]
    )
    lines.extend([f"- {item}" for item in gate["conditions"]] or ["- None."])
    lines.extend(
        [
            "",
            "## Gate",
            "",
            f"G00 is `{gate['status']}`. Eligible next Goals: "
            + (", ".join(gate["eligible_next_goals"]) if gate["eligible_next_goals"] else "none"),
            "",
            "Stop after Goal 0. Do not integrate data or begin G1 without a new explicit Goal.",
            "",
        ]
    )
    return "\n".join(lines)


def validate_with_jsonschema(payload: Mapping[str, Any], schema_path: Path) -> None:
    import jsonschema  # type: ignore

    jsonschema.validate(instance=dict(payload), schema=load_json(schema_path))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="inspect without creating outputs")
    parser.add_argument("--run-id", help="explicit approved Pilot 2026 source run ID")
    parser.add_argument(
        "--config",
        type=Path,
        default=PIPELINE_ROOT / "config" / "sources.template.json",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=REPOSITORY_ROOT / "RESULT ANALYSIS" / "ARTICLE3_MULTISCALE_TRANSFER",
    )
    parser.add_argument("--output-run-id", help="explicit Goal 0 output run ID")
    parser.add_argument("--goal-start-sha", help="editable HEAD observed while clean at Goal start")
    parser.add_argument("--pytest-report", type=Path, help="JUnit XML from the pipeline pytest run")
    parser.add_argument("--skip-source-checks", action="store_true")
    parser.add_argument("--workspace-root", action="append", type=Path, default=[])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    started = time.perf_counter()
    created = utc_now()
    config_path = args.config.resolve()
    config = load_json(config_path)
    compute_path = PIPELINE_ROOT / "config" / "compute_budget.json"
    compute_budget = load_json(compute_path)
    configuration_hash = sha256_json({"sources": config, "compute_budget": compute_budget})

    checks: list[dict[str, str]] = []
    input_hashes: list[dict[str, Any]] = []
    conditions: list[str] = []
    blockers: list[str] = []
    decisions: list[str] = []
    failures: list[str] = []
    canonical_commands = [
        "python -m pytest WORKFLOW/05_Article3_Multiscale_Transfer/tests -q",
        "python WORKFLOW/05_Article3_Multiscale_Transfer/scripts/00_preflight.py --dry-run --goal-start-sha <goal-start-sha>",
        "python WORKFLOW/05_Article3_Multiscale_Transfer/scripts/00_preflight.py --goal-start-sha <goal-start-sha>",
    ]

    editable_spec = config["editable_repository"]
    editable = snapshot_repository(
        REPOSITORY_ROOT,
        expected_repository=str(editable_spec["repository"]),
        required_branch=str(editable_spec["required_branch"]),
        root_locator=".",
    )
    unexpected_dirty = paths_outside_prefixes(
        editable.changed_paths,
        editable_spec.get("allowed_goal_dirty_prefixes", []),
    )
    if editable.current_branch != editable.required_branch:
        failures.append("editable repository is on the wrong branch")
    if unexpected_dirty:
        failures.append("editable repository has changes outside Goal 0 scope")
    if args.goal_start_sha and editable.current_head != args.goal_start_sha:
        failures.append("editable HEAD differs from the declared Goal-start SHA")
    if not args.goal_start_sha:
        conditions.append("Goal-start SHA was not supplied to the preflight CLI.")
        blockers.append("goal_start_sha_required")
    editable_status = "FAIL" if failures else "PASS"
    checks.append(
        check_row(
            "editable_repository",
            "Calibration_Framework_2025",
            editable_status,
            f"branch={editable.current_branch}; head={editable.current_head}; "
            f"in_scope_changes={len(editable.changed_paths)}; unexpected={len(unexpected_dirty)}",
        )
    )

    add_hash(
        input_hashes,
        path=config_path,
        scope="editable",
        locator="WORKFLOW/05_Article3_Multiscale_Transfer/config/sources.template.json",
        kind="configuration",
    )
    add_hash(
        input_hashes,
        path=compute_path,
        scope="editable",
        locator="WORKFLOW/05_Article3_Multiscale_Transfer/config/compute_budget.json",
        kind="configuration",
    )

    missing_bundle: list[str] = []
    for relative in config.get("bundle_required_files", []):
        path = REPOSITORY_ROOT / str(relative)
        if not path.is_file():
            missing_bundle.append(str(relative))
            continue
        add_hash(
            input_hashes,
            path=path,
            scope="bundle",
            locator=str(relative),
            kind="governance_document",
        )
    if missing_bundle:
        failures.append("required governance bundle files are missing")
    checks.append(
        check_row(
            "bundle_files",
            "governance_bundle",
            "PASS" if not missing_bundle else "FAIL",
            f"present={len(config.get('bundle_required_files', [])) - len(missing_bundle)}; missing={';'.join(missing_bundle)}",
        )
    )

    resolved_sources: list[ResolvedSource] = []
    snapshots: list[tuple[str, GitSnapshot]] = []
    for spec in config.get("sources", []):
        name = str(spec["name"])
        try:
            source = resolve_source(spec, workspace_roots=args.workspace_root)
            snapshot = snapshot_repository(
                source.root,
                expected_repository=str(spec["repository"]),
                required_branch=str(spec["required_branch"]),
                root_locator=source.root_locator,
            )
        except (OSError, ProvenanceError) as exc:
            failures.append(f"source unavailable: {name}")
            checks.append(check_row("source_repository", name, "FAIL", str(exc)))
            continue
        resolved_sources.append(source)
        snapshots.append((name, snapshot))
        if not snapshot.required_ref_accessible:
            failures.append(f"required ref inaccessible: {name}@{snapshot.required_branch}")
        if snapshot.dirty:
            conditions.append(
                f"Source {name} is dirty: {', '.join(snapshot.changed_paths) or 'unreported changes'}."
            )
            blockers.append(f"source_dirty:{name}")
        if not snapshot.branch_matches_required:
            conditions.append(
                f"Source {name} checkout is `{snapshot.current_branch}`, while `{snapshot.required_branch}` is required and resolves without checkout."
            )
            blockers.append(f"source_branch_mismatch:{name}")
        checks.append(
            check_row(
                "source_repository",
                name,
                "PASS" if snapshot.required_ref_accessible else "FAIL",
                f"required_sha={snapshot.required_sha}; checkout={snapshot.current_branch}; "
                f"dirty={snapshot.dirty}; branch_match={snapshot.branch_matches_required}",
            )
        )
        if snapshot.branch_matches_required:
            for relative in spec.get("index_files", []):
                add_hash(
                    input_hashes,
                    path=source.root / str(relative),
                    scope=name,
                    locator=f"{source.root_locator}/{str(relative).replace(os.sep, '/')}",
                    kind="source_index_or_config",
                )

    candidates: list[CandidateRecord] = []
    candidate_source: ResolvedSource | None = None
    for source in resolved_sources:
        discovered = inventory_model_runs(source)
        if discovered:
            candidates.extend(discovered)
            candidate_source = source
            for candidate in discovered:
                manifest = source.root / candidate.relative_path / "run_manifest.json"
                add_hash(
                    input_hashes,
                    path=manifest,
                    scope=source.name,
                    locator=f"{source.root_locator}/{candidate.relative_path}/run_manifest.json",
                    kind="model_run_manifest",
                )
                qc = source.root / candidate.relative_path / "dataset_qc.json"
                add_hash(
                    input_hashes,
                    path=qc,
                    scope=source.name,
                    locator=f"{source.root_locator}/{candidate.relative_path}/dataset_qc.json",
                    kind="model_run_qc",
                )
    eligible = [candidate for candidate in candidates if candidate.eligible]
    if not candidates or not eligible:
        failures.append("no eligible Pilot 2026 model-ready candidate was found")
    selected: CandidateRecord | None = None
    if args.run_id:
        try:
            selected = select_candidate(candidates, args.run_id)
        except ValueError as exc:
            failures.append(str(exc))
    else:
        if len(eligible) > 1:
            conditions.append(
                f"{len(eligible)} eligible Pilot 2026 model-ready runs were found; none was selected."
            )
        elif len(eligible) == 1:
            conditions.append("One eligible Pilot 2026 run was found but still requires explicit approval.")
        decisions.append("Approve one exact Pilot 2026 model-dataset run ID; do not approve `latest`.")
        blockers.append("model_run_selection_required")
    checks.append(
        check_row(
            "model_run_inventory",
            "Pilot_2026",
            "PASS" if candidates and eligible else "FAIL",
            f"candidates={len(candidates)}; eligible={len(eligible)}; selected={selected.run_id if selected else 'none'}",
        )
    )

    if candidate_source is not None:
        inventory_smoke_result = inventory_smoke(candidate_source, candidates)
    else:
        inventory_smoke_result = {
            "status": "FAIL",
            "eligible_tables_checked": 0,
            "errors": ["candidate source unavailable"],
            "selection_performed": False,
        }
    if inventory_smoke_result["status"] != "PASS":
        failures.append("read-only inventory smoke failed")
    checks.append(
        check_row(
            "inventory_smoke",
            "Pilot_2026",
            str(inventory_smoke_result["status"]),
            f"eligible_tables_checked={inventory_smoke_result.get('eligible_tables_checked', 0)}; selection=false",
        )
    )

    pytest_result = parse_junit(args.pytest_report)
    if args.pytest_report and pytest_result["status"] != "PASS":
        failures.append("pipeline pytest failed")
    if not args.dry_run and not args.pytest_report:
        conditions.append("A JUnit pytest report was not supplied to the real preflight.")
        blockers.append("pipeline_pytest_evidence_missing")
    checks.append(
        check_row(
            "pipeline_pytest",
            "Goal_0_scaffolding",
            str(pytest_result["status"]),
            f"tests={pytest_result.get('tests', 'unknown')}; failures={pytest_result.get('failures', 'unknown')}",
        )
    )

    source_checks: dict[str, Any]
    source_check_commands: list[str]
    if args.dry_run:
        source_checks = {"status": "PLANNED", "checks": {}}
        source_check_commands = []
    else:
        source_checks, source_check_commands = run_source_checks(
            resolved_sources,
            timeout_seconds=int(compute_budget["goal0"]["source_check_timeout_seconds"]),
            skip=args.skip_source_checks,
        )
        if source_checks["status"] == "FAIL":
            failures.append("a read-only source structural check failed or changed source state")
        if source_checks["status"] == "PASS_CONDITIONAL":
            known = [
                name
                for name, result in source_checks["checks"].items()
                if result["status"] == "KNOWN_FAILURE"
            ]
            conditions.append(
                "Declared historical source-check failures remain unresolved: "
                + ", ".join(known)
                + "."
            )
            blockers.append("source_structural_check_known_failure")
        if source_checks["status"] == "SKIPPED_BY_CLI":
            conditions.append("Declared source structural checks were skipped by CLI.")
            blockers.append("source_structural_checks_skipped")
    canonical_commands.extend(source_check_commands)
    checks.append(
        check_row(
            "source_structural_checks",
            "read_only_sources",
            str(source_checks["status"]),
            f"declared_checks={sum(len(source.spec.get('safe_checks', [])) for source in resolved_sources)}",
        )
    )

    source_preconditions = all(
        not snapshot.dirty and snapshot.branch_matches_required for _, snapshot in snapshots
    ) and len(snapshots) == len(config.get("sources", []))
    microbenchmark_reasons: list[str] = []
    if selected is None:
        microbenchmark_reasons.append("no_explicit_approved_run_id")
    if not source_preconditions:
        microbenchmark_reasons.append("source_preflight_not_clean_and_branch_aligned")
    if microbenchmark_reasons:
        model_microbenchmark = {
            "status": "SKIPPED_BY_GATE",
            "reasons": microbenchmark_reasons,
            "simulation_executed": False,
            "calibration_executed": False,
        }
        conditions.append(
            "Model microbenchmark was not executed because its explicit-run and clean-source preconditions were not met."
        )
        blockers.append("model_microbenchmark_not_available")
    else:
        assert selected is not None and candidate_source is not None
        model_microbenchmark, model_command = run_model_microbenchmark(
            candidate_source,
            selected,
        )
        canonical_commands.append(model_command)
        if model_microbenchmark["status"] != "PASS":
            failures.append("the selected-run model microbenchmark failed")
    checks.append(
        check_row(
            "model_microbenchmark",
            "Pilot_2026",
            str(model_microbenchmark["status"]),
            ";".join(microbenchmark_reasons) or "portable config/table smoke only",
        )
    )

    tests: dict[str, Any] = {
        "pipeline_pytest": pytest_result,
        "inventory_smoke": inventory_smoke_result,
        "source_structural_checks": source_checks,
        "model_microbenchmark": model_microbenchmark,
        "schema_validation": {"status": "PASS"},
    }
    source_commits = {name: snapshot.required_sha for name, snapshot in snapshots}
    hash_index_digest = sha256_json(
        [
            {key: row[key] for key in INPUT_HASH_FIELDS}
            for row in sorted(input_hashes, key=lambda item: (item["scope"], item["locator"]))
        ]
    )
    gate_status = "FAIL" if failures else ("PASS_CONDITIONAL" if conditions else "PASS")
    gate = build_gate(
        status=gate_status,
        source_commits=source_commits,
        input_hashes={"input_hash_index": hash_index_digest, "configuration": configuration_hash},
        commands=canonical_commands,
        tests=tests,
        metrics={
            "sources_expected": len(config.get("sources", [])),
            "sources_resolved": len(resolved_sources),
            "model_run_candidates": len(candidates),
            "eligible_model_run_candidates": len(eligible),
            "selected_model_run": selected.run_id if selected else None,
            "large_dataset_payloads_hashed": 0,
        },
        conditions=sorted(set(conditions)),
        blockers=sorted(set(blockers + [f"failure:{value}" for value in failures])),
        decisions_required=sorted(set(decisions)),
    )
    validate_gate(gate)

    summary = {
        "dry_run": args.dry_run,
        "gate": gate["status"],
        "editable_branch": editable.current_branch,
        "editable_head": editable.current_head,
        "sources_resolved": len(resolved_sources),
        "candidate_count": len(candidates),
        "eligible_candidate_count": len(eligible),
        "selected_run_id": selected.run_id if selected else None,
        "conditions": gate["conditions"],
        "blockers": gate["blockers"],
    }
    if args.dry_run:
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        return 2 if gate["status"] == "FAIL" else 0

    run_id = args.output_run_id or make_run_id(
        f"{editable.current_head}:{configuration_hash}:{selected.run_id if selected else 'no-selection'}"
    )
    layout = create_run_layout(args.output_root.resolve(), run_id)
    runtime_seconds = time.perf_counter() - started

    effective_config = {
        "schema_version": 1,
        "goal": "G0",
        "configuration_hash": configuration_hash,
        "goal_start_sha": args.goal_start_sha,
        "source_run_id": selected.run_id if selected else None,
        "source_run_selection_policy": "exact_explicit_id_only_no_latest",
        "output_run_id": run_id,
        "source_contract": config,
        "compute_budget": compute_budget,
    }
    source_manifest = {
        "schema_version": 1,
        "created_utc": created,
        "editable_repository": {
            "repository": editable.repository,
            "root_locator": ".",
            "required_branch": editable.required_branch,
            "current_branch": editable.current_branch,
            "current_head": editable.current_head,
            "goal_start_sha": args.goal_start_sha,
            "in_scope_goal_changes": editable.changed_paths,
            "unexpected_dirty_paths": unexpected_dirty,
        },
        "sources": [
            {
                "name": name,
                **snapshot.to_dict(),
                "resolution_method": next(
                    source.resolution_method for source in resolved_sources if source.name == name
                ),
            }
            for name, snapshot in snapshots
        ],
    }
    environment = collect_environment(config.get("selected_packages", []))

    write_json(layout.path("config/effective_config.json"), effective_config)
    write_json(layout.path("provenance/source_manifest.json"), source_manifest)
    write_json(layout.path("provenance/environment.json"), environment)
    write_csv(
        layout.path("provenance/input_hashes.csv"),
        sorted(input_hashes, key=lambda item: (item["scope"], item["locator"])),
        INPUT_HASH_FIELDS,
    )
    write_csv(
        layout.path("tables/model_run_candidates.csv"),
        [candidate.to_csv_row() for candidate in candidates],
        MODEL_CANDIDATE_FIELDS,
    )
    write_csv(layout.path("tables/preflight_checks.csv"), checks, CHECK_FIELDS)
    layout.path("logs/commands.log").write_text(
        "\n".join(canonical_commands) + "\n", encoding="utf-8", newline="\n"
    )
    report = build_report(
        gate=gate,
        source_snapshots=snapshots,
        candidates=candidates,
        tests=tests,
        runtime_seconds=runtime_seconds,
    )
    layout.path("report.md").write_text(report, encoding="utf-8", newline="\n")
    write_json(layout.path("gate_status.json"), gate)

    validate_with_jsonschema(
        gate, PIPELINE_ROOT / "config" / "schemas" / "gate_status.schema.json"
    )
    validate_with_jsonschema(
        source_manifest,
        PIPELINE_ROOT / "config" / "schemas" / "source_manifest.schema.json",
    )
    manifest_status = {
        "PASS": "completed",
        "PASS_CONDITIONAL": "completed_conditionally",
        "FAIL": "failed",
    }[gate["status"]]
    run_manifest = {
        "schema_version": 1,
        "run_id": run_id,
        "goal": "G0",
        "created_utc": created,
        "status": manifest_status,
        "editable_repository": {
            "repository": editable.repository,
            "branch": editable.current_branch,
            "goal_start_sha": args.goal_start_sha,
            "head_at_generation": editable.current_head,
            "planned_commit_message": "chore(article3): establish multiscale preflight and provenance",
        },
        "source_commits": source_commits,
        "configuration_hash": configuration_hash,
        "random_seeds": [],
        "commands": canonical_commands,
        "tests": tests,
        "runtime_seconds": round(runtime_seconds, 6),
        "solver": {"used": False, "reason": "Goal 0 has no approved model run"},
        "selected_source_run": selected.run_id if selected else None,
        "outputs": output_inventory(layout.root, exclude=("run_manifest.json",)),
    }
    write_json(layout.path("run_manifest.json"), run_manifest)
    validate_with_jsonschema(
        run_manifest,
        PIPELINE_ROOT / "config" / "schemas" / "run_manifest.schema.json",
    )

    private_hits: list[str] = []
    for path in sorted(item for item in layout.root.rglob("*") if item.is_file()):
        try:
            private_hits.extend(private_path_hits(path.read_text(encoding="utf-8")))
        except UnicodeError:
            failures.append(f"non-UTF-8 Goal output: {path.name}")
    if private_hits:
        raise RuntimeError(f"private absolute paths detected in Goal outputs: {sorted(set(private_hits))}")

    summary.update(
        {
            "output_run_id": run_id,
            "output_locator": f"RESULT ANALYSIS/ARTICLE3_MULTISCALE_TRANSFER/runs/{run_id}",
            "runtime_seconds": round(runtime_seconds, 6),
        }
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 2 if gate["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
