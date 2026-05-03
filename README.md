# NovoExplorer

**A point-and-click app for exploring Novogene RNA-Seq results -- no coding required.**

Got a Novogene delivery folder back from the sequencing service and want to see
your differentially expressed genes, pathways, and quality-control plots
without writing any code? That's what this is for.

Open the app, point it at the folder Novogene gave you, and you'll get:

- volcano plots of every comparison
- searchable gene tables and per-gene fold-change charts
- enrichment dot plots for GO, KEGG, Reactome, DisGeNET, and DO
- protein-protein interaction networks
- UpSet / Venn overlaps between comparisons
- one-click Excel and CSV exports

You don't need to understand the file formats or run any scripts on the data.
Everything happens inside the app once you've installed it.

---

## Getting started

You'll need to do this once to install the app, then you can open it any time.

### 1. Install (one time)

Open a terminal in the folder where you've downloaded NovoExplorer and run:

```bash
bash setup.sh
```

This sets up an isolated Python environment and downloads everything the app
needs. It can take a few minutes the first time. You only do this once.

> **Don't have Python yet?** Install Python 3.10 or newer from
> [python.org](https://www.python.org/downloads/) (any version 3.10, 3.11, or
> 3.12 works), then run the line above.

### 2. Open the app

Every time you want to use NovoExplorer, run these two lines in a terminal
opened in the NovoExplorer folder:

```bash
source .venv/bin/activate
streamlit run novogene_explorer.py
```

Your browser will open automatically. If it doesn't, copy the
`http://localhost:...` link the terminal prints into your browser.

### 3. Pick your data folder

In the sidebar on the left, use the folder browser to navigate to the Novogene
delivery folder (the top-level folder you got from the sequencing service)
and click **Use this folder**. That's it -- the tabs across the top will fill
with plots and tables.

> **External hard drive?** Quick-jump shortcuts for `/Volumes` (macOS),
> `/mnt`, `/media`, and `/run/media` (Linux) sit right above the file
> browser, so external drives are one click away. The app handles
> permission errors and disconnected disks gracefully.

> **Prefer to skip the picker?** You can pass the folder directly:
>
> ```bash
> streamlit run novogene_explorer.py -- /path/to/your/novogene/results
> ```

### 4. Stop the app

When you're done, switch back to the terminal and press `Ctrl+C` (or just close
the terminal window). Your data is never modified -- the app only reads from
the delivery folder.

---

## What you can do in the app

NovoExplorer organises everything into 11 tabs. Pick the one that matches your
question:

| Tab | What it answers |
|-----|-----------------|
| **Overview** | "How many up- and down-regulated genes are there per comparison?" |
| **Gene Explorer** | "What does this specific gene do across all my comparisons?" |
| **Comparison Browser** | "Show me a volcano plot and let me filter the DEG table." |
| **Enrichment** | "Which biological pathways are enriched? GO, KEGG, Reactome, etc." |
| **MA Plot** | "Are my fold changes biased by expression level?" |
| **Venn / UpSet** | "Which DEGs are shared between two or more comparisons?" |
| **Ranked Genes** | "Show every gene ranked by fold change or significance." |
| **DEG Summary** | "I want one wide table: log2FC + padj for every gene, every comparison." |
| **Pathway Viewer** | "Show me the genes in this pathway, coloured by their fold change." |
| **PPI Network** | "Which genes are network hubs? What's the neighborhood of my gene of interest?" |
| **Export** | "Give me a single Excel workbook (or ZIP of CSVs) for sharing." |

All plots are interactive: hover for tooltips, drag to zoom, double-click to
reset, and click the camera icon to download a PNG.

---

## What kind of folder works?

The standard Novogene RNA-Seq delivery, untouched. The app looks for the
folders Novogene already creates (`Differential/`, `Enrichment/`,
`Quantification/`) and figures out the layout automatically -- both the
"by database" layout (`Enrichment/GO/CompA_vs_CompB/...`) and the "by
comparison" layout (`Enrichment/CompA_vs_CompB/GO/...`) are handled.

If your delivery doesn't load, the most common culprits are:

- The folder you pointed at is one level too high or too low. Try the
  parent or a child folder.
- The DEG files are named in a non-standard way. The app accepts most common
  variants but you can compare against the layout below.

<details>
<summary>Click to see the expected folder layout</summary>

```
your_results/
  Differential/
    1.deglist/
      GroupA_vs_GroupB/
        GroupA_vs_GroupB_deg.xls
    2.cluster/ ...
  Enrichment/
    GO/
      GroupA_vs_GroupB/ALL/*.xls
    KEGG/
      GroupA_vs_GroupB/ALL/*.xls
    DisGeNET/
      GroupA_vs_GroupB/ALL/*.xls
    DO/
      GroupA_vs_GroupB/ALL/*.xls
    Reactome/
      GroupA_vs_GroupB/ALL/*.xls
    PPI/
      GroupA_vs_GroupB/ALL/*.xls
```

Files in any encoding (UTF-8, GB18030, or Latin-1) are handled.

</details>

---

## Troubleshooting

### The terminal says `setup.sh` failed

Re-running `bash setup.sh` is safe. It picks up where it left off. If a
specific dependency keeps failing on macOS Intel, the [Platform Notes](#platform-notes-for-developers)
section below has manual steps.

### "No module named 'pipeline'" when launching the app

You're not in the NovoExplorer folder. In your terminal, run:

```bash
cd /path/to/NovoExplorer
source .venv/bin/activate
streamlit run novogene_explorer.py
```

### The app says my folder isn't recognised

Try the parent folder, or open the delivery in a file manager and look for a
folder called `Differential` or `Enrichment` -- point NovoExplorer one level
above that.

### A page is showing the wrong / stale data after I edited my files

The app caches loaded data per-folder. Reload the browser tab (or restart
with `Ctrl+C` and `streamlit run ...` again).

---

## For analysts and developers

Everything below is optional. The point-and-click app above is enough for most
visual exploration.

### Advanced: Analysis Pipeline + Multi-Page App

For deeper analysis (normalization, QC, gene-similarity, GSEA, signature
overlap), NovoExplorer ships a computational pipeline and a separate
multi-page Streamlit app that builds on the pipeline's results.

```bash
# Option A: launch the multi-page app and run the pipeline from the browser
streamlit run app/app.py

# Option B: run the pipeline from the command line, then open the app
python run_pipeline.py --config config.yaml
streamlit run app/app.py -- --config config.yaml
```

The multi-page app at `app/app.py` can detect a raw Novogene delivery folder,
let you set parameters in the browser, and run the pipeline without touching
the command line.

#### Pipeline stages

| Stage | Module | What it does |
|-------|--------|-------------|
| **1. Ingest** | `pipeline/ingest.py` | Walks the delivery folder, discovers quantification matrices, DEG tables, and enrichment results. |
| **2. Normalize** | `pipeline/normalize.py` | Filters low-count genes, computes TPM, produces a log2(TPM+1) matrix. |
| **3. QC** | `pipeline/qc.py` | Library sizes, detection rates, mitochondrial fractions, sample correlation, PCA, UMAP. |
| **4. Differential expression** | `pipeline/diffexp.py` | Cleans Novogene DEG results. Optionally re-runs DE via pyDESeq2. |
| **5. Similarity** | `pipeline/similarity.py` | Gene-gene cosine similarity, hierarchical clustering, signature vectors. |
| **6. Signatures** | `pipeline/signatures.py` | GSEA, ORA via gseapy, Jaccard overlap, core/unique pathway signatures. |
| **7. Save** | `pipeline/persistence.py` | Atomically writes every output to `results/novoexplorer_results.h5`. |

#### Extra pages (pipeline-backed app only)

| Page | What it adds |
|------|--------------|
| **Overview** | PCA scatter, UMAP, sample correlation heatmap, library size / detection rate QC |
| **Differential Expression** | Per-gene expression bar charts, gene basket for collecting genes across pages |
| **Gene Search** | Similar-gene discovery via cosine similarity across expression profiles |
| **Signatures & Pathways** | GSEA dot plots, Jaccard overlap heatmap, core / unique signature identification |
| **Multi-Condition** | Fold-change concordance scatter between comparison pairs |

### Configuration (`config.yaml`)

Only used by the pipeline -- not by the main explorer. All keys are optional;
defaults are applied for anything omitted.

| Key | Default | Description |
|-----|---------|-------------|
| `project_name` | `""` | Display name shown in the app sidebar. |
| `data_dir` | `"."` | Path to the Novogene delivery folder. |
| `output_dir` | `"results"` | Where the HDF5 results file is written. Relative paths resolve against `data_dir`. |
| `organism` | `"human"` | `"human"` or `"mouse"`. Controls gene-name mappings and gene-set organisms. |
| `padj_threshold` | `0.05` | Inclusive adjusted-p-value cutoff for "significant". |
| `log2fc_threshold` | `1.0` | Inclusive absolute log2 fold-change cutoff. |
| `rerun_de` | `false` | If `true`, re-run DE from raw counts via pyDESeq2 even when Novogene DEG results are present. |
| `comparisons` | `"auto"` | `"auto"` discovers them from folder names; or pass a list (e.g. `[["Treatment", "Control"]]`). |
| `similarity_variable_genes` | `5000` | Top-variable genes used for the gene-gene cosine similarity matrix. |
| `signature_min_comparisons` | `2` | Minimum number of comparisons a pathway must appear in to be a "core" signature. |
| `gene_set_databases` | `["MSigDB_Hallmark_2020", ...]` | Gene-set libraries for enrichment analysis (see [Enrichr libraries](https://maayanlab.cloud/Enrichr/#libraries)). |
| `log_level` | `"INFO"` | Python logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

The defaults are defined in `pipeline/constants.py` so editing them in one place
updates the entire pipeline.

### Requirements

- **Python 3.10+** (tested on 3.10, 3.11, 3.12)
- See `requirements.txt` for the full pinned dependency list.

Key dependencies: Streamlit, pandas, NumPy, Plotly, Matplotlib, pyDESeq2,
gseapy, scikit-learn, UMAP, h5py, networkx.

#### Platform notes (for developers)

`setup.sh` handles the following automatically:

- **macOS (Intel x86_64):** gseapy has no prebuilt wheel for this platform.
  The setup script installs a minimal Rust toolchain via
  [rustup](https://rustup.rs) so pip can build gseapy from source.
  numba/llvmlite are pinned to versions that still ship Intel Mac wheels.
- **macOS (Apple Silicon):** all dependencies install from prebuilt wheels.
- **Linux:** all dependencies install from prebuilt wheels.

Manual install:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install --prefer-binary -r requirements.txt
```

### Project layout

```
NovoExplorer/
  novogene_explorer.py    # Main app (11 tabs, direct Novogene folder browsing)
  run_pipeline.py         # CLI entry point for the analysis pipeline
  config.yaml             # Pipeline configuration (not needed for the main app)
  setup.sh                # One-step setup script (venv + deps + gene sets)
  requirements.txt        # Python dependencies, pinned at major versions
  app/                    # Multi-page app (pipeline-backed analyses)
    app.py                #   Welcome screen, data picker, in-app pipeline runner
    pages/                #   Individual pages
    components/           #   Shared UI widgets (filters, gene basket, downloads)
    cache_utils.py        #   File-mtime cache invalidation helper
    file_utils.py         #   Safe filesystem traversal helpers
    session.py            #   Typed session_state contract
  pipeline/               # Analysis pipeline modules
    constants.py          #   Single source of truth for default thresholds
    ingest.py             #   Folder discovery, file parsing (UTF-8 / GB18030 / Latin-1)
    normalize.py          #   Count filtering, TPM, log2 transform
    qc.py                 #   PCA, UMAP, correlation, outlier detection
    diffexp.py            #   DEG cleaning, pyDESeq2 re-analysis
    similarity.py         #   Cosine similarity, hierarchical clustering
    signatures.py         #   GSEA, ORA, Jaccard overlap
    persistence.py        #   Atomic HDF5 save/load
    utils.py              #   Column standardisation, encoding-flexible reader, config
  plotting/               # Figure builders (Plotly + Matplotlib)
  tests/                  # Pytest suite (244 tests covering pipeline, app pages, plots)
```

### Running the test suite

```bash
source .venv/bin/activate
pytest tests/
```

To run a specific module:

```bash
pytest tests/test_diffexp.py -v
```

### Troubleshooting (developer environments)

**`setup.sh` fails with "can't find Rust compiler"** -- gseapy needs Rust when
building from source. The setup script installs Rust automatically on macOS;
if it doesn't, run:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"
bash setup.sh
```

**`setup.sh` fails with "No such file or directory: 'cmake'"** -- this happens
when llvmlite has to build from source. The pinned versions in
`requirements.txt` should ship prebuilt wheels; if you hit this anyway:

```bash
# macOS
brew install cmake
# Ubuntu / Debian
sudo apt-get install cmake

bash setup.sh
```
