"""Single source of truth for pipeline default thresholds.

These values were previously duplicated across ``pipeline/utils.py``
(``_DEFAULT_CONFIG``), individual function signatures in
``pipeline/diffexp.py`` and ``pipeline/signatures.py``, and the YAML
``config.yaml``. Centralising them here lets ``_DEFAULT_CONFIG`` and
function default arguments reference the same constants, so updating a
default in one place is enough.

These constants intentionally mirror the YAML defaults; do not change
them without also updating ``config.yaml``.
"""

from __future__ import annotations

#: Adjusted p-value cutoff for "significant" gene / pathway calls.
#: Inclusive boundary (``padj <= DEFAULT_PADJ_THRESHOLD``) - see commit
#: ae1ce0d for the consistency convention.
DEFAULT_PADJ_THRESHOLD: float = 0.05

#: Absolute log2 fold-change cutoff. Inclusive
#: (``|log2fc| >= DEFAULT_LOG2FC_THRESHOLD``).
DEFAULT_LOG2FC_THRESHOLD: float = 1.0

#: Default organism for ingest / signature lookups.
DEFAULT_ORGANISM: str = "human"

#: Number of top-variance genes used for similarity / clustering.
DEFAULT_TOP_VAR_GENES: int = 5000

#: Minimum comparisons a pathway must appear in to count as a "core"
#: signature.
DEFAULT_MIN_COMPARISONS: int = 2

#: Lower clip applied to p-values before ``-log10``. Anything smaller
#: would round to zero in float64 and produce ``+inf``.
PVALUE_FLOOR: float = 1e-300
