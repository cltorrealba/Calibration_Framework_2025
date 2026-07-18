"""Environment capture that omits usernames, hostnames and absolute paths."""

from __future__ import annotations

import importlib.metadata
import os
import platform
import shutil
import subprocess
import sys
from typing import Any, Iterable


def _package_version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def _total_memory_bytes() -> int | None:
    try:
        import psutil  # type: ignore

        return int(psutil.virtual_memory().total)
    except (ImportError, OSError):
        return None


def _git_version() -> str | None:
    try:
        result = subprocess.run(
            ["git", "--version"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def collect_environment(packages: Iterable[str]) -> dict[str, Any]:
    """Collect a portable environment record suitable for version control."""

    thread_vars = {
        name: os.environ.get(name)
        for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")
    }
    return {
        "python": {
            "version": platform.python_version(),
            "implementation": platform.python_implementation(),
            "executable_name": os.path.basename(sys.executable),
        },
        "operating_system": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
        },
        "hardware": {
            "logical_cpu_count": os.cpu_count(),
            "processor": platform.processor() or None,
            "total_memory_bytes": _total_memory_bytes(),
        },
        "packages": {name: _package_version(name) for name in packages},
        "executables": {
            "git": _git_version(),
            "ipopt_available": shutil.which("ipopt") is not None,
        },
        "thread_limits": thread_vars,
    }
