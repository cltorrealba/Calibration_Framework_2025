from pathlib import Path

from article3_multiscale.provenance import (
    classify_read_only_check,
    parse_status_paths,
    paths_outside_prefixes,
    private_path_hits,
    repository_slug,
    sha256_file,
)


def test_sha256_file_is_deterministic(tmp_path: Path) -> None:
    fixture = tmp_path / "fixture.txt"
    fixture.write_bytes(b"article3\n")
    assert sha256_file(fixture) == "da1c88eb7d932f80061f5280ac1a71deb6f605fb73825a57b978f157b6fa8cb9"


def test_repository_slug_normalizes_https_and_ssh() -> None:
    assert repository_slug("https://github.com/cltorrealba/pyomo-doe.git") == "cltorrealba/pyomo-doe"
    assert repository_slug("git@github.com:cltorrealba/Tesis.git") == "cltorrealba/Tesis"


def test_dirty_scope_is_fail_closed() -> None:
    paths = [
        "WORKFLOW/05_Article3_Multiscale_Transfer/src/module.py",
        "RESULT ANALYSIS/ARTICLE3_MULTISCALE_TRANSFER/README.md",
        "WORKFLOW/model/legacy.m",
    ]
    outside = paths_outside_prefixes(
        paths,
        [
            "WORKFLOW/05_Article3_Multiscale_Transfer/",
            "RESULT ANALYSIS/ARTICLE3_MULTISCALE_TRANSFER/",
        ],
    )
    assert outside == ["WORKFLOW/model/legacy.m"]


def test_porcelain_status_preserves_first_path_character() -> None:
    assert parse_status_paths(" M references/library.bib\n?? new/file.txt\n") == [
        "references/library.bib",
        "new/file.txt",
    ]


def test_private_path_detection() -> None:
    assert private_path_hits(r"C:\Users\person\secret\file.csv")
    assert private_path_hits("/home/person/data/file.csv")
    assert private_path_hits("${PYOMO_DOE_ROOT}/relative/file.csv") == []


def test_read_only_check_known_failure_is_not_hidden_or_fatal() -> None:
    assert classify_read_only_check(1, True, "condition") == "KNOWN_FAILURE"
    assert classify_read_only_check(1, True, "fail") == "FAIL"
    assert classify_read_only_check(0, False, "condition") == "FAIL"
