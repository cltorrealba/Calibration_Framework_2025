from datetime import datetime, timezone
from pathlib import Path

import pytest

from article3_multiscale.run_layout import RUN_SUBDIRECTORIES, create_run_layout, make_run_id


def test_run_id_is_deterministic_for_seed_and_time() -> None:
    now = datetime(2026, 7, 18, 12, 0, tzinfo=timezone.utc)
    assert make_run_id("seed", now) == make_run_id("seed", now)
    assert make_run_id("seed", now).startswith("G0_20260718T120000Z_")


def test_layout_is_immutable_by_collision(tmp_path: Path) -> None:
    layout = create_run_layout(tmp_path, "G0_fixture")
    assert layout.root == tmp_path / "runs" / "G0_fixture"
    assert all((layout.root / name).is_dir() for name in RUN_SUBDIRECTORIES)
    with pytest.raises(FileExistsError):
        create_run_layout(tmp_path, "G0_fixture")
