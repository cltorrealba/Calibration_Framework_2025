"""Read-only source resolution and Pilot 2026 model-run inventory."""

from __future__ import annotations

import csv
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from .provenance import ProvenanceError, repository_slug, run_command, sha256_file


@dataclass(frozen=True)
class ResolvedSource:
    name: str
    root: Path
    root_locator: str
    resolution_method: str
    spec: Mapping[str, Any]


@dataclass(frozen=True)
class CandidateRecord:
    source: str
    run_id: str
    relative_path: str
    created_utc: str
    stage: str
    status: str
    gate_verdict: str
    qc_verdict: str
    schema_version: str
    adapter_schema_version: str
    source_branch: str
    source_commit: str
    source_dirty: bool
    required_files_present: bool
    required_files_missing: tuple[str, ...]
    declared_outputs_present: bool
    declared_output_size_match: bool
    eligible: bool
    manifest_sha256: str
    qc_sha256: str
    content_group: str
    small_table_relative_path: str

    def to_csv_row(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "run_id": self.run_id,
            "relative_path": self.relative_path,
            "created_utc": self.created_utc,
            "stage": self.stage,
            "status": self.status,
            "gate_verdict": self.gate_verdict,
            "qc_verdict": self.qc_verdict,
            "schema_version": self.schema_version,
            "adapter_schema_version": self.adapter_schema_version,
            "source_branch": self.source_branch,
            "source_commit": self.source_commit,
            "source_dirty_at_creation": str(self.source_dirty).lower(),
            "required_files_present": str(self.required_files_present).lower(),
            "required_files_missing": ";".join(self.required_files_missing),
            "declared_outputs_present": str(self.declared_outputs_present).lower(),
            "declared_output_size_match": str(self.declared_output_size_match).lower(),
            "eligible": str(self.eligible).lower(),
            "manifest_sha256": self.manifest_sha256,
            "qc_sha256": self.qc_sha256,
            "content_group": self.content_group,
        }


MODEL_CANDIDATE_FIELDS = (
    "source",
    "run_id",
    "relative_path",
    "created_utc",
    "stage",
    "status",
    "gate_verdict",
    "qc_verdict",
    "schema_version",
    "adapter_schema_version",
    "source_branch",
    "source_commit",
    "source_dirty_at_creation",
    "required_files_present",
    "required_files_missing",
    "declared_outputs_present",
    "declared_output_size_match",
    "eligible",
    "manifest_sha256",
    "qc_sha256",
    "content_group",
)


def _matches_repository(root: Path, expected_repository: str) -> bool:
    result = run_command(("git", "remote", "get-url", "origin"), cwd=root)
    return (
        result.returncode == 0
        and repository_slug(result.stdout).casefold()
        == repository_slug(expected_repository).casefold()
    )


def resolve_source(
    spec: Mapping[str, Any],
    *,
    workspace_roots: Iterable[Path] = (),
) -> ResolvedSource:
    """Resolve a source from its environment variable or configured workspaces."""

    env_var = str(spec["env_var"])
    repository = str(spec["repository"])
    configured = os.environ.get(env_var)
    if configured:
        root = Path(configured).expanduser().resolve()
        if not root.is_dir():
            raise ProvenanceError(f"{env_var} does not name a directory")
        if not _matches_repository(root, repository):
            raise ProvenanceError(f"{env_var} does not resolve {repository}")
        return ResolvedSource(
            name=str(spec["name"]),
            root=root,
            root_locator=f"${{{env_var}}}",
            resolution_method=f"environment:{env_var}",
            spec=spec,
        )

    matches: list[Path] = []
    for workspace in workspace_roots:
        base = workspace.expanduser().resolve()
        if not base.is_dir():
            continue
        for config in base.rglob(".git/config"):
            root = config.parent.parent
            if _matches_repository(root, repository):
                matches.append(root)
    unique = sorted(set(matches))
    if len(unique) != 1:
        raise ProvenanceError(
            f"could not resolve {repository}: set {env_var}; workspace matches={len(unique)}"
        )
    return ResolvedSource(
        name=str(spec["name"]),
        root=unique[0],
        root_locator=f"${{{env_var}}}",
        resolution_method="workspace_remote_match",
        spec=spec,
    )


def _content_group(manifest: Mapping[str, Any]) -> str:
    configuration = manifest.get("configuration", {})
    output_values = manifest.get("outputs", {})
    hashes = sorted(
        str(value.get("sha256", ""))
        for value in output_values.values()
        if isinstance(value, Mapping)
    )
    seed = json.dumps(
        {
            "configuration": configuration.get("sha256", ""),
            "outputs": hashes,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(seed).hexdigest()[:12]


def inventory_model_runs(source: ResolvedSource) -> list[CandidateRecord]:
    """Inventory every explicit model-run manifest without using `latest`."""

    pattern = source.spec.get("model_run_manifest_glob")
    if not pattern:
        return []
    required_files = tuple(str(value) for value in source.spec.get("required_model_run_files", []))
    smoke_name = str(source.spec.get("small_table_smoke_file", ""))
    records: list[CandidateRecord] = []
    for manifest_path in sorted(source.root.glob(str(pattern))):
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        run_dir = manifest_path.parent
        missing = tuple(name for name in required_files if not (run_dir / name).is_file())
        outputs = payload.get("outputs", {})
        present = True
        size_match = True
        for relative, metadata in outputs.items():
            output_path = source.root / str(relative)
            if not output_path.is_file():
                present = False
                size_match = False
                continue
            expected_bytes = metadata.get("bytes") if isinstance(metadata, Mapping) else None
            if expected_bytes is not None and output_path.stat().st_size != int(expected_bytes):
                size_match = False
        qc_path = run_dir / "dataset_qc.json"
        qc_payload: Mapping[str, Any] = {}
        qc_sha = ""
        if qc_path.is_file():
            qc_payload = json.loads(qc_path.read_text(encoding="utf-8"))
            qc_sha = sha256_file(qc_path)
        gate = payload.get("gate", {})
        git = payload.get("git", {})
        configuration = payload.get("configuration", {}).get("payload", {})
        status = str(payload.get("status", "unknown"))
        gate_verdict = str(gate.get("verdict", "unknown"))
        qc_verdict = str(qc_payload.get("verdict", "missing"))
        required_present = not missing
        eligible = (
            status.casefold() == "completed"
            and gate_verdict == "PASS"
            and qc_verdict == "PASS"
            and required_present
            and present
        )
        records.append(
            CandidateRecord(
                source=source.name,
                run_id=str(payload.get("run_id", run_dir.name)),
                relative_path=run_dir.relative_to(source.root).as_posix(),
                created_utc=str(payload.get("created_utc", "")),
                stage=str(payload.get("stage", "")),
                status=status,
                gate_verdict=gate_verdict,
                qc_verdict=qc_verdict,
                schema_version=str(payload.get("schema_version", "")),
                adapter_schema_version=str(configuration.get("adapter_schema_version", "")),
                source_branch=str(git.get("branch", "")),
                source_commit=str(git.get("commit", "")),
                source_dirty=bool(git.get("dirty", False)),
                required_files_present=required_present,
                required_files_missing=missing,
                declared_outputs_present=present,
                declared_output_size_match=size_match,
                eligible=eligible,
                manifest_sha256=sha256_file(manifest_path),
                qc_sha256=qc_sha,
                content_group=_content_group(payload),
                small_table_relative_path=(run_dir / smoke_name).relative_to(source.root).as_posix()
                if smoke_name and (run_dir / smoke_name).is_file()
                else "",
            )
        )
    return records


def inventory_smoke(
    source: ResolvedSource,
    candidates: Iterable[CandidateRecord],
) -> dict[str, Any]:
    """Read one header and one row from every eligible small table."""

    checked = 0
    errors: list[str] = []
    columns: dict[str, int] = {}
    for candidate in candidates:
        if not candidate.eligible or not candidate.small_table_relative_path:
            continue
        path = source.root / candidate.small_table_relative_path
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                first = next(reader, None)
                if not reader.fieldnames or first is None:
                    raise ValueError("table has no header or data row")
                columns[candidate.run_id] = len(reader.fieldnames)
                checked += 1
        except (OSError, UnicodeError, csv.Error, ValueError) as exc:
            errors.append(f"{candidate.run_id}: {type(exc).__name__}: {exc}")
    return {
        "status": "PASS" if checked > 0 and not errors else "FAIL",
        "eligible_tables_checked": checked,
        "column_counts": columns,
        "errors": errors,
        "selection_performed": False,
    }


def select_candidate(candidates: Iterable[CandidateRecord], run_id: str) -> CandidateRecord:
    """Resolve one exact approved run ID; prefixes and `latest` are rejected."""

    if run_id.casefold() == "latest" or "latest" in run_id.casefold():
        raise ValueError("`latest` is not an admissible run ID")
    matches = [candidate for candidate in candidates if candidate.run_id == run_id]
    if len(matches) != 1:
        raise ValueError(f"run ID must match exactly one candidate: {run_id}")
    if not matches[0].eligible:
        raise ValueError(f"selected run is not eligible: {run_id}")
    return matches[0]
