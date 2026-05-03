"""Smoke tests for the Streamlit app pages.

These run each page through :class:`streamlit.testing.v1.AppTest` (a
headless Streamlit harness; no display server needed) against a
minimal fixture results file. The contract tested is intentionally
broad: each page must run end-to-end without raising an exception
both when the session is uninitialised (welcome / empty-state path)
and when a valid ``results.h5`` is present (data-loading path).

Detailed assertions about page contents belong in higher-level UI
tests; the goal here is to catch import / cache-key / column-access
regressions before they ship.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless backend, must be set before pyplot import

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.persistence import save_results

# Streamlit's AppTest harness ships with the streamlit package.
streamlit = pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402


PROJECT_ROOT = Path(__file__).resolve().parent.parent

# All Streamlit pages we want to keep healthy. Paths are relative to the
# project root so AppTest.from_file resolves them consistently across
# environments.
PAGES = [
    PROJECT_ROOT / "app" / "pages" / "01_overview.py",
    PROJECT_ROOT / "app" / "pages" / "02_diffexp.py",
    PROJECT_ROOT / "app" / "pages" / "03_gene_search.py",
    PROJECT_ROOT / "app" / "pages" / "04_signatures.py",
    PROJECT_ROOT / "app" / "pages" / "05_multi_condition.py",
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_minimal_results() -> dict:
    """Build a tiny but schema-complete results dict.

    Columns and key names mirror :func:`tests.test_persistence._make_results`;
    we duplicate inline so this module doesn't depend on private test
    helpers from another file.
    """
    rng = np.random.default_rng(0)
    n_genes, n_samples = 30, 6
    genes = [f"GENE{i}" for i in range(1, n_genes + 1)]
    samples = [f"S{i}" for i in range(1, n_samples + 1)]

    counts = pd.DataFrame(
        rng.integers(0, 5000, (n_genes, n_samples)),
        index=genes, columns=samples,
    )
    tpm = counts.div(counts.sum(axis=0).replace(0, 1), axis=1) * 1e6

    deg = pd.DataFrame({
        "gene_name": genes[:15],
        "log2fc": rng.normal(0, 2, 15),
        "padj": np.clip(rng.exponential(0.1, 15), 1e-6, 1),
        "basemean": rng.uniform(10, 1000, 15),
    })

    enrichment = pd.DataFrame({
        "term_id": [f"GO:{i:07d}" for i in range(5)],
        "term_name": [f"pathway {i}" for i in range(5)],
        "padj": [1e-5, 1e-3, 0.01, 0.05, 0.1],
        "gene_count": [40, 20, 10, 5, 2],
        "gene_ratio": [0.4, 0.2, 0.1, 0.05, 0.02],
    })

    pca_coords = pd.DataFrame(
        rng.random((n_samples, 2)),
        index=samples, columns=["PC1", "PC2"],
    )

    return {
        "expression": {"counts": counts, "tpm": tpm, "fpkm": None},
        "deg": {"A_vs_B": deg, "C_vs_D": deg.copy()},
        "enrichment": {"A_vs_B": {"GO": enrichment}, "C_vs_D": {"GO": enrichment}},
        "similarity": {
            "cosine_matrix": pd.DataFrame(
                np.eye(5), index=genes[:5], columns=genes[:5]
            ),
            "gene_clusters": pd.Series(
                [0, 0, 1, 1, 2], index=genes[:5], name="cluster"
            ),
            "signature_vectors": None,
        },
        "embeddings": {
            "pca_coordinates": pca_coords,
            "pca_variance": np.array([0.5, 0.3]),
            "umap": None,
        },
        "qc": {
            "library_sizes": pd.Series(
                counts.sum(axis=0).values, index=samples, name="library_size"
            ),
            "detection_rates": None,
            "mito_fractions": None,
            "correlation": pd.DataFrame(
                np.corrcoef(tpm.T), index=samples, columns=samples
            ),
        },
        "signatures": {"overlap_matrix": None, "core": None, "unique": None},
        "metadata": {
            "samples": pd.DataFrame({
                "sample_id": samples,
                "group": ["A"] * 3 + ["B"] * 3,
            }),
            "genes": pd.DataFrame({"gene_id": genes}),
            "comparisons": pd.DataFrame({"comparison": ["A_vs_B", "C_vs_D"]}),
            "project": {"project_name": "Test", "organism": "human"},
        },
    }


@pytest.fixture(scope="module")
def fixture_h5(tmp_path_factory):
    """Write a minimal results.h5 once per test module."""
    out = tmp_path_factory.mktemp("results") / "novoexplorer_results.h5"
    save_results(_make_minimal_results(), out)
    return out


def _assert_no_exceptions(at: AppTest, page_path: Path) -> None:
    """Fail with a useful message if the page raised inside Streamlit."""
    if at.exception:
        excs = "\n".join(str(e.value) for e in at.exception)
        pytest.fail(f"{page_path.name} raised:\n{excs}")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_page_runs_with_valid_results(page, fixture_h5):
    """Each page must run end-to-end against a minimal results.h5."""
    at = AppTest.from_file(str(page), default_timeout=30)
    at.session_state["results_path"] = str(fixture_h5)
    at.session_state["config"] = {"project_name": "Test", "organism": "human"}
    at.run()
    _assert_no_exceptions(at, page)


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_page_runs_without_session_state(page):
    """Each page must handle the no-data-loaded case without crashing.

    The pages display a friendly empty / welcome state via
    ``check_data_path`` when no results file is set; the test verifies
    that path doesn't itself raise.
    """
    at = AppTest.from_file(str(page), default_timeout=30)
    at.run()
    _assert_no_exceptions(at, page)
