"""Typed contract for the keys we store in ``st.session_state``.

Streamlit's ``session_state`` is an open dict, which makes it easy to
add features but hard to audit: keys get sprinkled across pages, and
type information lives in your head. This module is the **canonical
list** of cross-page keys plus a :class:`~typing.TypedDict` describing
their value types so static checkers can sanity-check accesses.

Three categories of keys:

1. **Cross-page contract** -- set by the launcher (``app/app.py``) or
   the legacy folder browser (``novogene_explorer.py``); read by every
   page. These are the keys that, if renamed, would break the app.
   Use the ``KEY_*`` constants when reading or writing them.

2. **Component-local state** -- e.g. the gene basket. The owning
   component defines its own private constant.

3. **Widget keys** -- Streamlit auto-creates session_state entries for
   widgets keyed via ``key=``. Those are local to a single widget and
   don't belong here.

Helpers like :func:`get_results_path` / :func:`set_results_path` exist
so callers don't have to remember the literal string. Direct
``st.session_state[KEY_X]`` access is also fine and is type-checkable
against :class:`SessionState`.
"""

from __future__ import annotations

from typing import Any, Optional, TypedDict

import streamlit as st


# ---------------------------------------------------------------------------
# Cross-page contract keys
# ---------------------------------------------------------------------------

#: Path to the HDF5 results file the pages should load from. Set by the
#: launcher once the user picks a folder or supplies ``--config``.
KEY_RESULTS_PATH = "results_path"

#: Parsed pipeline config dict (organism, thresholds, project_name, etc.).
KEY_CONFIG = "config"

#: Path to ``config.yaml`` when the app was launched with ``--config``.
KEY_CONFIG_PATH = "config_path"

#: Selected raw Novogene delivery folder for the legacy single-file app.
KEY_DATA_DIR = "data_dir"

#: Folder-browser current path (legacy app) and its synced text input.
KEY_BROWSE_DIR = "browse_dir"
KEY_PATH_INPUT = "_path_input"

#: Welcome-screen data picker fields (multi-page launcher).
KEY_PICKER_PATH = "_picker_path"
KEY_PICKER_INPUT = "_picker_input"

#: In-app log capture: a list of formatted log lines, plus a one-time
#: flag so the handler is only installed once per session.
KEY_LOG = "_log"
KEY_LOG_HANDLER_INSTALLED = "_log_handler_installed"


class SessionState(TypedDict, total=False):
    """Documented schema for the cross-page session_state keys.

    ``total=False`` so individual entries are optional (each is set
    on-demand by the relevant page or launcher). Widget-local keys
    are intentionally not modelled.
    """

    results_path: str
    config: dict
    config_path: Optional[str]
    data_dir: str
    browse_dir: str
    _path_input: str
    _picker_path: str
    _picker_input: str
    _log: list[str]
    _log_handler_installed: bool


# ---------------------------------------------------------------------------
# Convenience accessors
# ---------------------------------------------------------------------------


def get_results_path(default: str = "") -> str:
    """Return the configured HDF5 results path, or *default* if unset."""
    return st.session_state.get(KEY_RESULTS_PATH, default)


def set_results_path(path: str) -> None:
    st.session_state[KEY_RESULTS_PATH] = path


def get_config() -> dict[str, Any]:
    """Return the pipeline config dict, or an empty dict if unset."""
    return st.session_state.get(KEY_CONFIG, {})


def set_config(config: dict[str, Any], path: Optional[str] = None) -> None:
    st.session_state[KEY_CONFIG] = config
    if path is not None:
        st.session_state[KEY_CONFIG_PATH] = path
