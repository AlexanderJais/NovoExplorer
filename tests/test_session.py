"""Tests for ``app.session`` -- the typed session_state contract."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

streamlit = pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402


# Use AppTest so st.session_state has a real Streamlit context. We
# embed each assertion in the rendered script body rather than running
# helper code in the test process - that's the only way session_state
# is properly initialised.

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _run(script_body: str) -> AppTest:
    boilerplate = f"""
import sys
sys.path.insert(0, {str(_PROJECT_ROOT)!r})
import streamlit as st
from app import session
"""
    at = AppTest.from_string(boilerplate + "\n" + script_body, default_timeout=15)
    at.run()
    if at.exception:
        excs = "\n".join(str(e.value) for e in at.exception)
        pytest.fail(f"AppTest raised:\n{excs}")
    return at


def test_get_results_path_default_when_unset():
    at = _run("st.write(repr(session.get_results_path('NOPE')))")
    bodies = "\n".join(md.body for md in at.markdown)
    assert "'NOPE'" in bodies


def test_set_results_path_round_trip():
    at = _run(
        "session.set_results_path('/tmp/x.h5')\n"
        "st.write(repr(session.get_results_path()))"
    )
    bodies = "\n".join(md.body for md in at.markdown)
    assert "'/tmp/x.h5'" in bodies


def test_set_config_with_path_writes_both_keys():
    at = _run(
        "session.set_config({'organism': 'mouse'}, path='/x/config.yaml')\n"
        "st.write(repr(session.get_config()))\n"
        "st.write(repr(st.session_state.get(session.KEY_CONFIG_PATH)))"
    )
    bodies = "\n".join(md.body for md in at.markdown)
    assert "'mouse'" in bodies
    assert "'/x/config.yaml'" in bodies


def test_typed_dict_documents_known_keys():
    # Smoke test: every documented key constant should appear in the
    # SessionState TypedDict. This guards against the constant being
    # added without a matching schema entry.
    from app.session import (
        KEY_BROWSE_DIR,
        KEY_CONFIG,
        KEY_CONFIG_PATH,
        KEY_DATA_DIR,
        KEY_LOG,
        KEY_LOG_HANDLER_INSTALLED,
        KEY_PATH_INPUT,
        KEY_PICKER_INPUT,
        KEY_PICKER_PATH,
        KEY_RESULTS_PATH,
        SessionState,
    )

    keys = {
        KEY_RESULTS_PATH,
        KEY_CONFIG,
        KEY_CONFIG_PATH,
        KEY_DATA_DIR,
        KEY_BROWSE_DIR,
        KEY_PATH_INPUT,
        KEY_PICKER_PATH,
        KEY_PICKER_INPUT,
        KEY_LOG,
        KEY_LOG_HANDLER_INSTALLED,
    }
    schema_keys = set(SessionState.__optional_keys__) | set(SessionState.__required_keys__)
    missing = keys - schema_keys
    assert not missing, f"Constants without schema entries: {missing}"
