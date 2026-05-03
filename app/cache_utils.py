"""Helpers for keeping ``@st.cache_data`` results in sync with disk.

Streamlit's cache keys on the function arguments. If a loader takes only
the path string, edits to the file (regenerated ``.h5``, modified
``config.yaml``) won't bust the cache and the app keeps serving the
parsed result from before the edit until the user restarts.

The :func:`file_mtime_ns` helper exposes the file's modification time as
an extra cache-key argument so an in-place file change invalidates every
downstream cached value automatically.

Usage::

    @st.cache_data
    def _load(path: str, _mtime: int) -> ...:
        return load_results(path)

    _load(path, file_mtime_ns(path))
"""

from __future__ import annotations

import os


def file_mtime_ns(path: str | os.PathLike | None) -> int:
    """Return the file's modification time in nanoseconds.

    Returns 0 if *path* is empty/None or cannot be stat'd (missing,
    permission denied, on a disconnected external drive). 0 is a stable
    sentinel: all "unreadable" paths share the same cache key, but real
    files always have ``mtime_ns`` well above 0 so they don't collide.

    For directory paths, the returned mtime reflects when entries were
    last added or removed (not modifications inside) - good enough to
    invalidate caches when a Novogene delivery folder is regenerated
    wholesale, but not for content edits in nested files.
    """
    if not path:
        return 0
    try:
        return os.stat(os.fspath(path)).st_mtime_ns
    except OSError:
        return 0
