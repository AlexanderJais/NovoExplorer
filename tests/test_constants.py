"""Tests for ``pipeline.constants``.

These tests pin the canonical default values so that:

  * accidental edits to ``pipeline/constants.py`` don't silently shift
    significance thresholds across the whole pipeline,
  * ``config.yaml`` and ``_DEFAULT_CONFIG`` continue to agree with the
    constants.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml

from pipeline import constants
from pipeline.utils import _DEFAULT_CONFIG


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_pinned_values():
    assert constants.DEFAULT_PADJ_THRESHOLD == 0.05
    assert constants.DEFAULT_LOG2FC_THRESHOLD == 1.0
    assert constants.DEFAULT_ORGANISM == "human"
    assert constants.DEFAULT_TOP_VAR_GENES == 5000
    assert constants.DEFAULT_MIN_COMPARISONS == 2
    assert constants.PVALUE_FLOOR == 1e-300


def test_default_config_uses_constants():
    assert _DEFAULT_CONFIG["padj_threshold"] == constants.DEFAULT_PADJ_THRESHOLD
    assert _DEFAULT_CONFIG["log2fc_threshold"] == constants.DEFAULT_LOG2FC_THRESHOLD
    assert _DEFAULT_CONFIG["organism"] == constants.DEFAULT_ORGANISM


def test_yaml_template_matches_constants():
    """The shipped ``config.yaml`` must agree with the Python constants.

    If this test fails, either update ``pipeline/constants.py`` or the
    YAML to match - never let them drift apart silently.
    """
    cfg = yaml.safe_load((PROJECT_ROOT / "config.yaml").read_text())
    assert cfg.get("padj_threshold") == constants.DEFAULT_PADJ_THRESHOLD
    assert cfg.get("log2fc_threshold") == constants.DEFAULT_LOG2FC_THRESHOLD
