# BvA Variance Analysis — Retail FP&A Automation

Automated Budget-vs-Actual (BvA) variance analysis for retail operations, with AI-generated executive commentary. Available as both a command-line pipeline (`bva_variance_ai_commentary.py`) and an interactive Streamlit dashboard (`bva.py`).

---

## What it does

1. **Ingests** raw monthly Budget and Actual GL exports (CSV).
2. **Merges** them on `month`, `department`, `gl_account`, and `gl_account_name`.
3. **Calculates** variance $ and variance % for every GL line.
4. **Flags material variances** — any line exceeding a % threshold (default 10%) or a $ threshold (default $50,000).
5. **Tags likely drivers** for known GL accounts (e.g., overtime, remodel timing, contractor usage).
6. **Generates executive commentary** — either a deterministic rule-based summary (no dependencies) or a natural-language summary written by Claude via the Anthropic API.
7. **Exports** a full variance report (CSV) and an executive commentary (Markdown).

---

## Project structure

```
.
├── bva_variance_ai_commentary.py   # CLI pipeline — run monthly, output to files
├── bva.py                          # Streamlit dashboard — interactive, upload-your-own-data
├── data/
│   ├── budget_oct2025.csv          # sample budget GL export
│   └── actual_oct2025.csv          # sample actual GL export
└── output/
    ├── variance_report.csv         # generated
    └── executive_commentary.md     # generated
```

### Required CSV columns
Both `budget` and `actual` files need:
`month, department, gl_account, gl_account_name, budget_amount` (budget file) or `actual_amount` (actual file).

---

## Installation

```bash
pip install pandas
pip install anthropic   # optional — only needed for AI commentary
pip install streamlit matplotlib numpy   # only needed for the dashboard (bva.py)
```

---

## Usage

### Option A: Command-line pipeline

```bash
python bva_variance_ai_commentary.py \
    --budget data/budget_oct2025.csv \
    --actual data/actual_oct2025.csv \
    --out-dir output/
```

Runs end-to-end with a deterministic rule-based commentary generator — no API key required.

**To use AI-generated commentary instead:**

```bash
export ANTHROPIC_API_KEY=sk-ant-...
python bva_variance_ai_commentary.py --use-ai
```

If the `anthropic` package or API key isn't available, the script automatically falls back to the rule-based generator, so the pipeline never fails.

**Outputs:**
- `output/variance_report.csv` — every GL line with variance $, variance %, materiality flag, and likely driver
- `output/executive_commentary.md` — a short written summary for leadership

### Option B: Interactive dashboard

```bash
streamlit run bva.py
```

From the sidebar you can:
- Use built-in sample retail data, or upload your own Budget/Actual CSVs
- Adjust the materiality % and $ thresholds live with sliders
- Toggle AI commentary on/off (requires `ANTHROPIC_API_KEY`)

The dashboard has four tabs: **Dashboard** (KPIs, top variances chart, department rollup), **Variance Detail** (full sortable/filterable table), **Executive Commentary** (generate and view the summary), and **Export** (download the CSV report and Markdown commentary).

---

## Configuration

| Setting | Default | Where |
|---|---|---|
| Variance % materiality threshold | 10% | CLI: constant in script / Dashboard: sidebar slider |
| Variance $ materiality threshold | $50,000 | CLI: constant in script / Dashboard: sidebar number input |
| AI model | `claude-sonnet-4-6` | `generate_commentary_ai()` |

A variance is flagged as **material** if it exceeds *either* threshold.

---

## Notes

- This is an educational/portfolio FP&A model, not a formal audit or accounting determination.
- The "likely driver" tags are illustrative mappings by GL account number — update `LIKELY_DRIVER_TAGS` for your own chart of accounts.
- The CLI script and dashboard share the same core logic (ingestion, variance calc, commentary generation) so behavior stays consistent between the automated pipeline and the interactive tool.
