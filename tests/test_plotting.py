"""Smoke tests for the ``plotting/`` package.

These are *contract* tests, not pixel-perfect snapshots: each test verifies
that a plotting function returns the documented type, accepts the documented
columns, and degrades gracefully on empty / single-row / column-missing
inputs. The goal is to catch regressions like an accidental ``KeyError``,
silent shape mismatch, or a change to the strict-vs-inclusive significance
boundary - not to lock in any particular layout or style.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless backend; must be set before importing pyplot

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from plotting.enrichment import create_enrichment_barplot, create_enrichment_dotplot
from plotting.heatmap import create_heatmap_plotly
from plotting.ma_plot import create_ma_plot_matplotlib, create_ma_plot_plotly
from plotting.pca import create_pca_scatter, create_umap_scatter
from plotting.ppi_network import build_ego_network, build_ppi_network
from plotting.similarity_viz import create_gene_network, create_similarity_table
from plotting.theme import classify_genes
from plotting.upset import create_upset_data, create_upset_plot
from plotting.volcano import create_volcano_matplotlib, create_volcano_plotly


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def deg_df():
    """A small DEG table with a mix of up/down/non-significant genes."""
    rng = np.random.default_rng(42)
    n = 60
    return pd.DataFrame({
        "gene_name": [f"GENE{i}" for i in range(n)],
        "log2fc": rng.normal(0, 1.5, n),
        "padj": rng.uniform(0, 1, n).clip(1e-6, 1),
        "basemean": rng.uniform(1, 1000, n),
    })


@pytest.fixture
def expression_df():
    rng = np.random.default_rng(0)
    return pd.DataFrame(
        rng.uniform(0, 100, (40, 8)),
        index=[f"GENE{i}" for i in range(40)],
        columns=[f"S{i}" for i in range(8)],
    )


@pytest.fixture
def enrichment_df():
    return pd.DataFrame({
        "term_id": [f"GO:{i:07d}" for i in range(8)],
        "term_name": [f"pathway {i}" for i in range(8)],
        "padj": [1e-5, 1e-4, 1e-3, 0.01, 0.02, 0.05, 0.1, 0.5],
        "gene_count": [50, 40, 30, 20, 15, 10, 5, 2],
        "gene_ratio": [0.5, 0.4, 0.3, 0.2, 0.15, 0.1, 0.05, 0.02],
    })


@pytest.fixture
def sample_groups():
    return pd.Series(
        {f"S{i}": ("ctrl" if i < 4 else "treat") for i in range(8)},
    )


# ---------------------------------------------------------------------------
# theme.classify_genes -- canonical significance classifier
# ---------------------------------------------------------------------------


class TestClassifyGenes:
    def test_basic_classification(self):
        df = pd.DataFrame({
            "padj": [0.001, 0.001, 0.5, 0.001],
            "log2fc": [2.0, -2.0, 2.0, 0.5],
        })
        cats = classify_genes(df, padj_threshold=0.05, log2fc_threshold=1.0)
        assert list(cats) == ["up", "down", "ns", "ns"]

    def test_threshold_boundaries_inclusive(self):
        # padj == threshold and |log2fc| == threshold must count as
        # significant -- guards the consistency fix shipped in commit ae1ce0d.
        df = pd.DataFrame({
            "padj": [0.05, 0.05, 0.06, 0.05],
            "log2fc": [1.0, -1.0, 1.0, 0.99],
        })
        cats = classify_genes(df, padj_threshold=0.05, log2fc_threshold=1.0)
        assert cats.iloc[0] == "up"
        assert cats.iloc[1] == "down"
        assert cats.iloc[2] == "ns"  # padj fails
        assert cats.iloc[3] == "ns"  # |log2fc| fails


# ---------------------------------------------------------------------------
# Volcano
# ---------------------------------------------------------------------------


class TestVolcano:
    def test_plotly_returns_figure(self, deg_df):
        fig = create_volcano_plotly(deg_df, title="Test")
        assert isinstance(fig, go.Figure)
        # At least one Scattergl trace expected for the gene categories
        assert len(fig.data) >= 1

    def test_plotly_missing_columns_raises(self):
        bad = pd.DataFrame({"gene_name": ["A", "B"]})
        with pytest.raises(ValueError, match="missing required columns"):
            create_volcano_plotly(bad)

    def test_plotly_empty_after_dropna(self):
        df = pd.DataFrame({
            "gene_name": ["A", "B"],
            "log2fc": [np.nan, np.nan],
            "padj": [np.nan, np.nan],
        })
        fig = create_volcano_plotly(df)
        assert isinstance(fig, go.Figure)
        # Placeholder annotation is added
        assert any(
            "No genes" in (a.text or "") for a in fig.layout.annotations or []
        )

    def test_plotly_handles_padj_zero(self, deg_df):
        deg_df.loc[0, "padj"] = 0.0
        fig = create_volcano_plotly(deg_df)
        assert isinstance(fig, go.Figure)
        # No infinite y-values should leak into traces
        for trace in fig.data:
            ys = np.asarray(trace.y) if trace.y is not None else np.array([])
            assert np.all(np.isfinite(ys))

    def test_matplotlib_returns_figure(self, deg_df):
        result = create_volcano_matplotlib(deg_df, title="MPL")
        fig = result[0] if isinstance(result, tuple) else result
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


# ---------------------------------------------------------------------------
# MA plot
# ---------------------------------------------------------------------------


class TestMAPlot:
    def test_plotly_returns_figure(self, deg_df):
        fig = create_ma_plot_plotly(deg_df)
        assert isinstance(fig, go.Figure)

    def test_plotly_missing_columns_raises(self, deg_df):
        with pytest.raises(ValueError, match="missing required columns"):
            create_ma_plot_plotly(deg_df.drop(columns=["basemean"]))

    def test_matplotlib_returns_figure(self, deg_df):
        result = create_ma_plot_matplotlib(deg_df)
        fig = result[0] if isinstance(result, tuple) else result
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


# ---------------------------------------------------------------------------
# Heatmap
# ---------------------------------------------------------------------------


class TestHeatmap:
    def test_plotly_returns_figure(self, expression_df, sample_groups):
        fig = create_heatmap_plotly(expression_df, sample_groups=sample_groups)
        assert isinstance(fig, go.Figure)

    def test_plotly_explicit_genes(self, expression_df):
        genes = expression_df.index[:5].tolist()
        fig = create_heatmap_plotly(expression_df, genes=genes)
        assert isinstance(fig, go.Figure)

    def test_plotly_handles_constant_row(self, expression_df):
        # A row with zero variance previously produced a divide-by-zero
        # in the z-score; verify we still render.
        expression_df.iloc[0] = 5.0
        fig = create_heatmap_plotly(expression_df, n_top_genes=10)
        assert isinstance(fig, go.Figure)


# ---------------------------------------------------------------------------
# Enrichment
# ---------------------------------------------------------------------------


class TestEnrichment:
    def test_dotplot_returns_figure(self, enrichment_df):
        fig = create_enrichment_dotplot(enrichment_df)
        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 1

    def test_dotplot_handles_empty(self):
        empty = pd.DataFrame({"term_name": [], "padj": []})
        fig = create_enrichment_dotplot(empty)
        assert isinstance(fig, go.Figure)
        assert any(
            "No significant" in (a.text or "")
            for a in fig.layout.annotations or []
        )

    def test_dotplot_caps_at_max_terms(self, enrichment_df):
        fig = create_enrichment_dotplot(enrichment_df, max_terms=3)
        assert isinstance(fig, go.Figure)
        # The y-axis is one term per displayed row.
        scatter = fig.data[0]
        assert len(scatter.y) <= 3

    def test_barplot_returns_figure(self, enrichment_df):
        fig = create_enrichment_barplot(enrichment_df)
        assert isinstance(fig, go.Figure)

    def test_works_without_optional_columns(self):
        # Only term_name + padj should be enough.
        df = pd.DataFrame({
            "term_name": ["a", "b", "c"],
            "padj": [0.01, 0.02, 0.03],
        })
        fig = create_enrichment_dotplot(df)
        assert isinstance(fig, go.Figure)


# ---------------------------------------------------------------------------
# PCA / UMAP scatter
# ---------------------------------------------------------------------------


class TestPCA:
    def test_pca_returns_figure(self, sample_groups):
        rng = np.random.default_rng(1)
        coords = pd.DataFrame(
            rng.normal(0, 1, (8, 2)),
            index=sample_groups.index,
            columns=["PC1", "PC2"],
        )
        fig = create_pca_scatter(coords, [0.4, 0.3], sample_groups)
        assert isinstance(fig, go.Figure)
        # One Scatter per group, plus optional ellipse traces
        assert len(fig.data) >= 2

    def test_pca_no_groups(self):
        coords = np.random.default_rng(0).normal(0, 1, (5, 2))
        fig = create_pca_scatter(coords, [0.5, 0.4])
        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1

    def test_pca_pads_short_variance_explained(self, caplog):
        # Only one PC's variance provided -- function should warn and pad,
        # not crash.
        coords = np.random.default_rng(0).normal(0, 1, (5, 2))
        fig = create_pca_scatter(coords, [0.6])
        assert isinstance(fig, go.Figure)

    def test_umap_returns_figure(self, sample_groups):
        coords = pd.DataFrame(
            np.random.default_rng(2).normal(0, 1, (8, 2)),
            index=sample_groups.index,
            columns=["UMAP1", "UMAP2"],
        )
        fig = create_umap_scatter(coords, sample_groups)
        assert isinstance(fig, go.Figure)


# ---------------------------------------------------------------------------
# UpSet
# ---------------------------------------------------------------------------


class TestUpSet:
    def test_create_data_binary_matrix(self):
        deg_results = {
            "A_vs_B": pd.DataFrame({
                "gene_name": ["G1", "G2", "G3", "G4"],
                "padj": [0.01, 0.5, 0.02, 0.6],
                "log2fc": [2, 0.5, -2, 0.1],
            }),
            "C_vs_D": pd.DataFrame({
                "gene_name": ["G1", "G2", "G3", "G4"],
                "padj": [0.5, 0.02, 0.01, 0.5],
                "log2fc": [0.1, 2.0, -1.5, 0.1],
            }),
        }
        binary = create_upset_data(deg_results)
        assert set(binary.columns) == {"A_vs_B", "C_vs_D"}
        # G1 is significant only in A_vs_B; G3 is significant in both.
        assert binary.loc["G1", "A_vs_B"] == 1
        assert binary.loc["G1", "C_vs_D"] == 0
        assert binary.loc["G3", "A_vs_B"] == 1
        assert binary.loc["G3", "C_vs_D"] == 1

    def test_threshold_inclusive_in_upset(self):
        # Mirrors the consistency convention used in classify_genes:
        # padj == threshold counts as significant.
        deg = {
            "X": pd.DataFrame({
                "gene_name": ["A", "B"],
                "padj": [0.05, 0.06],
                "log2fc": [1.0, 1.0],
            })
        }
        binary = create_upset_data(deg, padj_threshold=0.05, log2fc_threshold=1.0)
        assert binary.loc["A", "X"] == 1
        assert "B" not in binary.index  # filtered out

    def test_create_plot_returns_figure(self):
        binary = pd.DataFrame({
            "A": [1, 1, 0, 1],
            "B": [1, 0, 1, 1],
            "C": [0, 1, 1, 1],
        }, index=["G1", "G2", "G3", "G4"])
        result = create_upset_plot(binary)
        # Function returns (fig, axes) or just fig depending on version
        fig = result[0] if isinstance(result, tuple) else result
        assert isinstance(fig, plt.Figure)
        plt.close(fig)


# ---------------------------------------------------------------------------
# Similarity visualisations
# ---------------------------------------------------------------------------


class TestSimilarity:
    def test_similarity_table_round_trip(self, expression_df):
        neighbors = pd.DataFrame({
            "gene": ["GENE0", "GENE0", "GENE1"],
            "neighbor": ["GENE5", "GENE7", "GENE3"],
            "similarity": [0.9123456, 0.8456789, 0.7234567],
        })
        out = create_similarity_table(neighbors, expression_df)
        assert "expression_profile" in out.columns
        # Similarity is rounded to 4 decimals
        assert out["similarity"].iloc[0] == 0.9123

    def test_gene_network_returns_figure(self):
        rng = np.random.default_rng(3)
        n = 12
        m = rng.uniform(0, 1, (n, n))
        m = (m + m.T) / 2  # symmetric
        np.fill_diagonal(m, 1.0)
        sim = pd.DataFrame(
            m, index=[f"G{i}" for i in range(n)], columns=[f"G{i}" for i in range(n)]
        )
        fig = create_gene_network(sim, top_n=8)
        assert isinstance(fig, go.Figure)


# ---------------------------------------------------------------------------
# PPI network
# ---------------------------------------------------------------------------


class TestPPI:
    def test_returns_figure(self):
        ppi = pd.DataFrame({
            "source_name": ["A", "B", "C", "A"],
            "target_name": ["B", "C", "D", "C"],
            "score": [0.9, 0.8, 0.7, 0.95],
        })
        fig = build_ppi_network(ppi)
        assert isinstance(fig, go.Figure)

    def test_empty_input_returns_placeholder(self):
        fig = build_ppi_network(
            pd.DataFrame(columns=["source_name", "target_name", "score"])
        )
        assert isinstance(fig, go.Figure)

    def test_ego_network_returns_figure(self):
        ppi = pd.DataFrame({
            "source_name": ["TP53", "TP53", "MDM2", "BRCA1"],
            "target_name": ["MDM2", "BRCA1", "BRCA1", "ATM"],
            "score": [0.9, 0.8, 0.85, 0.7],
        })
        fig = build_ego_network(ppi, gene="TP53")
        assert isinstance(fig, go.Figure)
