"""Portable provenance primitives used by the Goal 0 preflight."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


PRIVATE_PATH_PATTERNS = (
    re.compile(r"(?i)\b[A-Z]:[\\/]Users[\\/][^\\/\s]+"),
    re.compile(r"/(?:home|Users)/[^/\s]+/"),
)


class ProvenanceError(RuntimeError):
    """Raised when repository or provenance validation fails."""


def run_command(
    command: Sequence[str],
    *,
    cwd: Path,
    timeout: int = 30,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command without a shell and capture deterministic text output."""

    return subprocess.run(
        list(command),
        cwd=cwd,
        env=dict(env) if env is not None else None,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def run_git(root: Path, *args: str, timeout: int = 30) -> str:
    """Run Git at *root* and return stripped stdout or raise."""

    result = run_command(("git", *args), cwd=root, timeout=timeout)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise ProvenanceError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout.strip()


def repository_slug(remote: str) -> str:
    """Normalize an HTTPS/SSH Git remote to an owner/repository slug."""

    value = remote.strip().replace("\\", "/")
    if value.startswith("git@") and ":" in value:
        value = value.split(":", 1)[1]
    elif "://" in value:
        value = value.split("://", 1)[1]
        value = value.split("/", 1)[1] if "/" in value else value
    value = value.removesuffix(".git").strip("/")
    parts = value.split("/")
    return "/".join(parts[-2:]) if len(parts) >= 2 else value


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Hash one explicitly selected file; never recurse implicitly."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(payload: Any) -> str:
    """Hash a JSON-compatible value using canonical UTF-8 serialization."""

    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    """Write stable UTF-8 JSON with a terminal newline."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_csv(path: Path, rows: Iterable[Mapping[str, Any]], fields: Sequence[str]) -> None:
    """Write stable UTF-8 CSV with an explicit column contract."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(fields), lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def parse_status_paths(status: str) -> list[str]:
    """Extract repository-relative paths from porcelain-v1 status text."""

    paths: list[str] = []
    for line in status.splitlines():
        if len(line) < 4:
            continue
        value = line[3:].strip().replace("\\", "/")
        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        paths.append(value.strip('"'))
    return paths


def paths_outside_prefixes(paths: Iterable[str], prefixes: Iterable[str]) -> list[str]:
    """Return dirty paths outside an allowed, repository-relative scope."""

    normalized = [prefix.replace("\\", "/").rstrip("/") + "/" for prefix in prefixes]
    outside: list[str] = []
    for path in paths:
        candidate = path.replace("\\", "/")
        if not any(candidate.startswith(prefix) or candidate == prefix.rstrip("/") for prefix in normalized):
            outside.append(candidate)
    return outside


def private_path_hits(text: str) -> list[str]:
    """Return private absolute-path fragments found in serialized evidence."""

    hits: list[str] = []
    for pattern in PRIVATE_PATH_PATTERNS:
        hits.extend(match.group(0) for match in pattern.finditer(text))
    return sorted(set(hits))


def classify_read_only_check(return_code: int, source_unchanged: bool, failure_policy: str) -> str:
    """Classify a safe source check without hiding declared historical failures."""

    if return_code == 0 and source_unchanged:
        return "PASS"
    if return_code != 0 and source_unchanged and failure_policy == "condition":
        return "KNOWN_FAILURE"
    return "FAIL"


@dataclass(frozen=True)
class GitSnapshot:
    """Read-only snapshot of one Git checkout and its required ref."""

    repository: str
    root_locator: str
    remote: str
    current_branch: str
    current_head: str
    dirty: bool
    changed_paths: list[str]
    required_branch: str
    required_sha: str
    required_ref_accessible: bool
    branch_matches_required: bool
    ahead_of_remote: int | None
    behind_remote: int | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _resolve_required_sha(root: Path, branch: str) -> tuple[str, bool]:
    for ref in (f"refs/heads/{branch}", f"refs/remotes/origin/{branch}"):
        result = run_command(("git", "rev-parse", "--verify", ref), cwd=root)
        if result.returncode == 0:
            return result.stdout.strip(), True
    return "", False


def _ahead_behind(root: Path, branch: str) -> tuple[int | None, int | None]:
    local = run_command(("git", "show-ref", "--verify", f"refs/heads/{branch}"), cwd=root)
    remote = run_command(
        ("git", "show-ref", "--verify", f"refs/remotes/origin/{branch}"), cwd=root
    )
    if local.returncode != 0 or remote.returncode != 0:
        return None, None
    counts = run_git(
        root,
        "rev-list",
        "--left-right",
        "--count",
        f"refs/remotes/origin/{branch}...refs/heads/{branch}",
    ).split()
    behind, ahead = (int(value) for value in counts)
    return ahead, behind


def snapshot_repository(
    root: Path,
    *,
    expected_repository: str,
    required_branch: str,
    root_locator: str,
) -> GitSnapshot:
    """Inspect a Git source without checkout, fetch, pull or file writes."""

    root = root.resolve()
    inside = run_git(root, "rev-parse", "--is-inside-work-tree")
    if inside != "true":
        raise ProvenanceError(f"not a Git worktree: {root_locator}")
    remote = run_git(root, "remote", "get-url", "origin")
    actual_slug = repository_slug(remote)
    expected_slug = repository_slug(expected_repository)
    if actual_slug.casefold() != expected_slug.casefold():
        raise ProvenanceError(
            f"repository mismatch for {root_locator}: {actual_slug} != {expected_slug}"
        )
    branch = run_git(root, "branch", "--show-current") or "DETACHED"
    head = run_git(root, "rev-parse", "HEAD")
    status_result = run_command(
        ("git", "status", "--porcelain=v1", "--untracked-files=all"),
        cwd=root,
    )
    if status_result.returncode != 0:
        detail = status_result.stderr.strip() or status_result.stdout.strip()
        raise ProvenanceError(f"git status failed: {detail}")
    # Do not call strip(): the leading column is part of porcelain-v1 status.
    status = status_result.stdout.rstrip("\r\n")
    changed_paths = parse_status_paths(status)
    required_sha, accessible = _resolve_required_sha(root, required_branch)
    ahead, behind = _ahead_behind(root, required_branch)
    return GitSnapshot(
        repository=expected_slug,
        root_locator=root_locator,
        remote=remote,
        current_branch=branch,
        current_head=head,
        dirty=bool(changed_paths),
        changed_paths=changed_paths,
        required_branch=required_branch,
        required_sha=required_sha,
        required_ref_accessible=accessible,
        branch_matches_required=branch == required_branch,
        ahead_of_remote=ahead,
        behind_remote=behind,
    )
