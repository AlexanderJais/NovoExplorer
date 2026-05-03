"""Download buttons for CSV and figure exports in NovoExplorer.

Provides ``download_csv_button`` for DataFrame exports and
``download_figure_buttons`` for PNG/SVG figure exports (supports
both Plotly and Matplotlib).
"""

import csv
from io import BytesIO

import streamlit as st


# Plotly's static image export (``fig.to_image``) goes through kaleido.
# Probe once at module load so we can render disabled buttons with a
# clear tooltip instead of letting users click a button that takes a
# few seconds and then errors. We pin kaleido<1.0 in requirements.txt;
# the 1.x rewrite has a different API.
try:  # pragma: no cover - environment-dependent
    import kaleido  # noqa: F401

    _HAS_KALEIDO = True
except ImportError:
    _HAS_KALEIDO = False

_KALEIDO_HELP = (
    "Image export needs the kaleido package. Install it with:\n\n"
    "    pip install 'kaleido<1.0'\n\n"
    "Then restart the app."
)


def download_csv_button(df, filename, label="Download CSV", key=None):
    """Render a download button for a DataFrame as CSV.

    Parameters
    ----------
    df : pandas.DataFrame
        The dataframe to export.
    filename : str
        Name of the downloaded file (should end in .csv).
    label : str
        Button label text.
    key : str, optional
        Unique widget key.  Defaults to ``"dl_csv_{filename}"``.
    """
    if key is None:
        key = f"dl_csv_{filename}"
    csv_data = df.to_csv(index=True, quoting=csv.QUOTE_NONNUMERIC).encode("utf-8")
    st.download_button(
        label=label,
        data=csv_data,
        file_name=filename,
        mime="text/csv",
        key=key,
    )


def _is_plotly_figure(fig):
    """Check whether a figure is a Plotly figure."""
    try:
        import plotly.graph_objects as go

        return isinstance(fig, go.Figure)
    except ImportError:
        return False


def _is_matplotlib_figure(fig):
    """Check whether a figure is a Matplotlib figure."""
    try:
        import matplotlib.figure

        return isinstance(fig, matplotlib.figure.Figure)
    except ImportError:
        return False


def download_figure_buttons(fig, filename_base):
    """Render PNG and SVG download buttons for a figure.

    Handles both Plotly and Matplotlib figure objects.

    Parameters
    ----------
    fig : plotly.graph_objects.Figure or matplotlib.figure.Figure
        The figure to export.
    filename_base : str
        Base filename without extension (e.g. "volcano_plot").
    """
    col_png, col_svg = st.columns(2)

    if _is_plotly_figure(fig):
        if not _HAS_KALEIDO:
            with col_png:
                st.button(
                    "Download PNG", disabled=True,
                    help=_KALEIDO_HELP,
                    key=f"dl_png_{filename_base}_disabled",
                )
            with col_svg:
                st.button(
                    "Download SVG", disabled=True,
                    help=_KALEIDO_HELP,
                    key=f"dl_svg_{filename_base}_disabled",
                )
            return
        try:
            with col_png:
                png_bytes = fig.to_image(format="png", scale=2, width=1200, height=800)
                st.download_button(
                    label="Download PNG",
                    data=png_bytes,
                    file_name=f"{filename_base}.png",
                    mime="image/png",
                    key=f"dl_png_{filename_base}",
                )

            with col_svg:
                svg_bytes = fig.to_image(format="svg")
                st.download_button(
                    label="Download SVG",
                    data=svg_bytes,
                    file_name=f"{filename_base}.svg",
                    mime="image/svg+xml",
                    key=f"dl_svg_{filename_base}",
                )
        except (ValueError, ImportError):
            # kaleido is installed but the export still failed (e.g.
            # browser-binary issues). Surface that distinctly from the
            # not-installed case handled above.
            st.warning(
                "Image export failed. The **kaleido** package is installed "
                "but couldn't render this figure. See the terminal for details."
            )

    elif _is_matplotlib_figure(fig):
        with col_png:
            buf = BytesIO()
            fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
            buf.seek(0)
            st.download_button(
                label="Download PNG",
                data=buf.getvalue(),
                file_name=f"{filename_base}.png",
                mime="image/png",
                key=f"dl_png_{filename_base}",
            )

        with col_svg:
            buf = BytesIO()
            fig.savefig(buf, format="svg", bbox_inches="tight")
            buf.seek(0)
            st.download_button(
                label="Download SVG",
                data=buf.getvalue(),
                file_name=f"{filename_base}.svg",
                mime="image/svg+xml",
                key=f"dl_svg_{filename_base}",
            )

    else:
        st.error("Unsupported figure type. Provide a Plotly or Matplotlib figure.")
