"""Tests for ``app.file_utils`` -- shared filesystem helpers used by both
the direct-browse single-file app and the pipeline-backed launcher.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.file_utils import (
    external_disk_roots,
    list_subdirs,
    looks_like_novogene_delivery,
    looks_like_novogene_shallow,
    safe_is_dir,
    safe_iterdir,
)


# ---------------------------------------------------------------------------
# safe_is_dir / safe_iterdir
# ---------------------------------------------------------------------------


def test_safe_is_dir_true_for_existing_dir(tmp_path):
    assert safe_is_dir(tmp_path) is True


def test_safe_is_dir_false_for_missing_path(tmp_path):
    assert safe_is_dir(tmp_path / "nope") is False


def test_safe_is_dir_false_for_file(tmp_path):
    f = tmp_path / "f.txt"
    f.write_text("x")
    assert safe_is_dir(f) is False


def test_safe_iterdir_returns_children(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "c.txt").write_text("x")
    children = {p.name for p in safe_iterdir(tmp_path)}
    assert children == {"a", "b", "c.txt"}


def test_safe_iterdir_empty_for_missing(tmp_path):
    assert safe_iterdir(tmp_path / "nope") == []


# ---------------------------------------------------------------------------
# list_subdirs
# ---------------------------------------------------------------------------


def test_list_subdirs_filters_files_and_hidden(tmp_path):
    (tmp_path / "visible").mkdir()
    (tmp_path / ".hidden").mkdir()
    (tmp_path / "file.txt").write_text("x")
    assert list_subdirs(tmp_path) == ["visible"]


def test_list_subdirs_sorted(tmp_path):
    for name in ["zeta", "alpha", "mike"]:
        (tmp_path / name).mkdir()
    assert list_subdirs(tmp_path) == ["alpha", "mike", "zeta"]


def test_list_subdirs_empty_on_missing(tmp_path):
    assert list_subdirs(tmp_path / "nope") == []


# ---------------------------------------------------------------------------
# external_disk_roots
# ---------------------------------------------------------------------------


def test_external_disk_roots_returns_only_existing_paths():
    # Don't assert which roots exist (depends on host) - only that whatever
    # comes back is a subset of the documented candidates and exists.
    roots = external_disk_roots()
    candidates = {Path("/Volumes"), Path("/mnt"), Path("/media"), Path("/run/media")}
    assert set(roots).issubset(candidates)
    for r in roots:
        assert r.is_dir()


# ---------------------------------------------------------------------------
# looks_like_novogene_shallow
# ---------------------------------------------------------------------------


def test_shallow_match_on_differential(tmp_path):
    (tmp_path / "Differential").mkdir()
    assert looks_like_novogene_shallow(tmp_path) is True


def test_shallow_match_lowercase(tmp_path):
    (tmp_path / "enrichment").mkdir()
    assert looks_like_novogene_shallow(tmp_path) is True


def test_shallow_no_match(tmp_path):
    (tmp_path / "random").mkdir()
    assert looks_like_novogene_shallow(tmp_path) is False


# ---------------------------------------------------------------------------
# looks_like_novogene_delivery (deeper check)
# ---------------------------------------------------------------------------


def test_delivery_top_level_marker(tmp_path):
    (tmp_path / "Differential").mkdir()
    assert looks_like_novogene_delivery(tmp_path) is True


def test_delivery_pattern_match(tmp_path):
    # Folder names that *start with* a known pattern should match.
    (tmp_path / "diff_expr").mkdir()
    assert looks_like_novogene_delivery(tmp_path) is True


def test_delivery_one_level_nesting(tmp_path):
    # Real Novogene deliveries sometimes wrap the marker dirs under a
    # project folder. The deeper check looks one level down.
    project = tmp_path / "project_name"
    project.mkdir()
    (project / "Quantification").mkdir()
    assert looks_like_novogene_delivery(tmp_path) is True


def test_delivery_no_match(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "foo").mkdir()
    assert looks_like_novogene_delivery(tmp_path) is False


def test_delivery_handles_missing_directory(tmp_path):
    # Non-existent path must return False, not raise.
    assert looks_like_novogene_delivery(tmp_path / "nope") is False
