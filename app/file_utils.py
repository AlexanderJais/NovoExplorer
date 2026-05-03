"""Shared filesystem helpers for the Streamlit UIs.

Both ``novogene_explorer.py`` (the direct-browse single-file app) and
``app/app.py`` (the pipeline-backed multi-page launcher) need to walk
arbitrary user-selected folders that may live on external drives,
network mounts, or encrypted volumes. Those filesystems can raise
``PermissionError`` or ``OSError`` mid-iteration, and the UIs should
degrade gracefully rather than crashing.

This module centralises the safe-traversal primitives so the two apps
(and any future entry point) stay in sync. The functions here are
side-effect free; logging belongs in callers.
"""

from __future__ import annotations

from pathlib import Path


def safe_is_dir(p: Path) -> bool:
    """Return True iff *p* is a directory, swallowing ``OSError``.

    External drives that have been ejected, broken symlinks, and stale
    NFS handles all surface as ``OSError`` from ``Path.is_dir()``;
    returning False is the correct UX response for a folder browser.
    """
    try:
        return p.is_dir()
    except OSError:
        return False


def safe_iterdir(p: Path) -> list[Path]:
    """List children of *p*, returning ``[]`` on permission / I/O errors.

    Returns a fully materialised list rather than a generator so the
    caller can iterate it twice without re-triggering the underlying
    syscall.
    """
    try:
        return list(p.iterdir())
    except (PermissionError, OSError):
        return []


def list_subdirs(parent: Path) -> list[str]:
    """Return sorted, dot-prefix-filtered subdirectory names under *parent*.

    Used by the folder browser sidebar; hidden directories are skipped.
    """
    names: list[str] = []
    for child in safe_iterdir(parent):
        if child.name.startswith("."):
            continue
        if safe_is_dir(child):
            names.append(child.name)
    return sorted(names)


def external_disk_roots() -> list[Path]:
    """Return existing mount-point roots commonly used for external disks.

    Covers macOS (``/Volumes``) and the major Linux conventions
    (``/mnt``, ``/media``, ``/run/media``). Non-existent roots are
    skipped so the returned list contains only paths the user can
    actually navigate to.
    """
    roots: list[Path] = []
    for candidate in ("/Volumes", "/mnt", "/media", "/run/media"):
        p = Path(candidate)
        if safe_is_dir(p):
            roots.append(p)
    return roots


def looks_like_novogene_shallow(p: Path) -> bool:
    """Quick check: does *p* directly contain ``Differential`` or ``Enrichment``?

    Cheap test used by the sidebar to decorate folders with a "looks
    like a Novogene delivery" badge during browsing. Use
    :func:`looks_like_novogene_delivery` for the deeper, slower check
    that decides whether to launch the pipeline.
    """
    for child in ("Differential", "differential", "Enrichment", "enrichment"):
        try:
            if (p / child).is_dir():
                return True
        except OSError:
            continue
    return False


def looks_like_novogene_delivery(folder: Path) -> bool:
    """Deeper check: does *folder* contain Novogene-shaped subdirectories?

    Walks one level deeper than :func:`looks_like_novogene_shallow` and
    matches against the standard Novogene folder-name patterns
    (``diff*``, ``deg*``, ``enrich*``, ``quant*``, ``readcount*``,
    ``fpkm*``) plus the canonical marker names. Used by the pipeline
    launcher to decide whether the selected folder is a raw delivery.
    """
    if not safe_is_dir(folder):
        return False
    names = {c.name.lower() for c in safe_iterdir(folder) if safe_is_dir(c)}
    # Novogene sometimes nests the actual delivery under a project dir;
    # peek one level deeper so we still recognise it.
    for child in safe_iterdir(folder):
        if safe_is_dir(child):
            names |= {gc.name.lower() for gc in safe_iterdir(child) if safe_is_dir(gc)}
    markers = {"differential", "enrichment", "quantification"}
    for n in names:
        for pat in ("diff", "deg", "enrich", "quant", "readcount", "fpkm"):
            if n.startswith(pat):
                return True
    return bool(markers & names)
