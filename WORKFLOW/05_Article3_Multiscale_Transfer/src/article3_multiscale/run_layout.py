"""Immutable run-directory creation and portable output inventory."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .provenance import sha256_file


RUN_SUBDIRECTORIES = ("config", "provenance", "tables", "figures", "logs")


@dataclass(frozen=True)
class RunLayout:
    run_id: str
    root: Path

    def path(self, relative: str) -> Path:
        return self.root / relative


def make_run_id(seed: str, now: datetime | None = None) -> str:
    """Create a readable Goal 0 run ID without relying on a `latest` alias."""

    current = now or datetime.now(timezone.utc)
    stamp = current.strftime("%Y%m%dT%H%M%SZ")
    suffix = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8]
    return f"G0_{stamp}_{suffix}"


def create_run_layout(output_root: Path, run_id: str) -> RunLayout:
    """Create a new run directory and fail closed on collisions."""

    root = output_root / "runs" / run_id
    if root.exists():
        raise FileExistsError(f"run already exists: {run_id}")
    root.mkdir(parents=True)
    for name in RUN_SUBDIRECTORIES:
        (root / name).mkdir()
    return RunLayout(run_id=run_id, root=root)


def output_inventory(run_root: Path, exclude: Iterable[str] = ()) -> list[dict[str, object]]:
    """Hash only files inside one small Goal output directory."""

    excluded = {value.replace("\\", "/") for value in exclude}
    rows: list[dict[str, object]] = []
    for path in sorted(item for item in run_root.rglob("*") if item.is_file()):
        relative = path.relative_to(run_root).as_posix()
        if relative in excluded:
            continue
        rows.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return rows
