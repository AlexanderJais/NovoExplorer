"""Tests for ``app.cache_utils.file_mtime_ns``."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.cache_utils import file_mtime_ns


def test_returns_zero_for_none():
    assert file_mtime_ns(None) == 0


def test_returns_zero_for_empty_string():
    assert file_mtime_ns("") == 0


def test_returns_zero_for_missing_file(tmp_path):
    assert file_mtime_ns(tmp_path / "does-not-exist.txt") == 0


def test_returns_mtime_for_existing_file(tmp_path):
    p = tmp_path / "data.txt"
    p.write_text("hello")
    mtime = file_mtime_ns(p)
    assert mtime > 0
    assert mtime == os.stat(p).st_mtime_ns


def test_changes_on_modification(tmp_path):
    # The point of this helper is to bust @st.cache_data when a file is
    # edited in place; verify the returned key actually moves.
    p = tmp_path / "data.txt"
    p.write_text("v1")
    first = file_mtime_ns(p)
    # Sleep enough for mtime resolution on any reasonable filesystem.
    time.sleep(0.01)
    p.write_text("v2")
    second = file_mtime_ns(p)
    assert second != first


def test_accepts_path_object(tmp_path):
    p = tmp_path / "data.txt"
    p.write_text("x")
    assert file_mtime_ns(p) == file_mtime_ns(str(p))
