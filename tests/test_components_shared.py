"""Tests for ``app.components.shared`` rendering helpers.

Focus on the parts that interpolate user-controllable strings into
``unsafe_allow_html`` markdown - the dynamic substitutions must be HTML
escaped so callers don't have to remember to sanitise. We exercise the
helpers through ``streamlit.testing.v1.AppTest`` rather than mocking
``st.markdown`` so the assertions reflect what the real Streamlit
runtime actually emits.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

streamlit = pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402


def _markdown_bodies(at: AppTest) -> str:
    """Concatenate every st.markdown body emitted during the run."""
    return "\n".join(md.body for md in at.markdown)


def _run_inline(script_text: str) -> AppTest:
    at = AppTest.from_string(script_text, default_timeout=30)
    at.run()
    return at


# ---------------------------------------------------------------------------
# render_empty_state
# ---------------------------------------------------------------------------


def test_render_empty_state_escapes_message():
    script = """
import sys
sys.path.insert(0, %r)
from app.components.shared import render_empty_state
render_empty_state("<script>alert(1)</script>", "<img src=x onerror=alert(2)>")
""" % str(Path(__file__).resolve().parent.parent)
    at = _run_inline(script)
    body = _markdown_bodies(at)
    # The literal tags must not appear; only their escaped form.
    assert "<script>alert(1)</script>" not in body
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in body
    assert "<img src=x onerror=alert(2)>" not in body
    assert "&lt;img src=x onerror=alert(2)&gt;" in body


def test_render_empty_state_keeps_known_icon():
    script = """
import sys
sys.path.insert(0, %r)
from app.components.shared import render_empty_state
render_empty_state("hello", icon="warning")
""" % str(Path(__file__).resolve().parent.parent)
    at = _run_inline(script)
    body = _markdown_bodies(at)
    # The warning emoji should pass through; whitelist members aren't
    # escaped twice.
    assert "⚠" in body  # ⚠ U+26A0


def test_render_empty_state_unknown_icon_is_escaped():
    script = """
import sys
sys.path.insert(0, %r)
from app.components.shared import render_empty_state
render_empty_state("hello", icon="<b>oops</b>")
""" % str(Path(__file__).resolve().parent.parent)
    at = _run_inline(script)
    body = _markdown_bodies(at)
    assert "<b>oops</b>" not in body
    assert "&lt;b&gt;oops&lt;/b&gt;" in body


# ---------------------------------------------------------------------------
# render_stat_badge
# ---------------------------------------------------------------------------


def test_render_stat_badge_escapes_label_and_value():
    script = """
import sys
sys.path.insert(0, %r)
from app.components.shared import render_stat_badge
render_stat_badge("<x>", "<y>")
""" % str(Path(__file__).resolve().parent.parent)
    at = _run_inline(script)
    body = _markdown_bodies(at)
    assert "<x>" not in body
    assert "&lt;x&gt;" in body
    assert "&lt;y&gt;" in body


def test_render_stat_badge_rejects_non_hex_color():
    # An attacker-supplied color value with a closing quote could break
    # out of the style attribute. The whitelist falls back to the
    # default colour for anything that isn't a hex literal.
    script = """
import sys
sys.path.insert(0, %r)
from app.components.shared import render_stat_badge
render_stat_badge("ok", "1", color='" onmouseover="alert(1)')
""" % str(Path(__file__).resolve().parent.parent)
    at = _run_inline(script)
    body = _markdown_bodies(at)
    assert "onmouseover" not in body
    # The default color (#0072B2) should be substituted.
    assert "#0072B2" in body
