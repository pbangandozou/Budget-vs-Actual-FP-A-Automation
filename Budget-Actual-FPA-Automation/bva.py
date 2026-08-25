import io
import os
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

# Optional Anthropic support
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="BvA Variance Analysis | FP&A",
    page_icon="▣",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# STYLING (same green system)
# ============================================================

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Inter:wght@400;500;600;700&display=swap');

.stApp { background:#f7f8f6; color:#17221d; }
.block-container { max-width:1180px; padding-top:2.8rem; padding-bottom:4rem; }
header { background:transparent !important; }
#MainMenu, footer { visibility:hidden; }

.brand-bar {
  display:flex; justify-content:space-between; align-items:center;
  padding-bottom:18px; margin-bottom:28px; border-bottom:1px solid #dfe5e1;
}
.brand-name { font-size:15px; font-weight:700; letter-spacing:1px; color:#17221d; }
.brand-name span { color:#2f8053; }
.brand-meta, .section-meta, .sidebar-caption {
  font-family:'DM Mono',monospace; font-size:9px; letter-spacing:1px;
  color:#7c8982; text-transform:uppercase;
}
.eyebrow {
  font-family:'DM Mono',monospace; font-size:9px; letter-spacing:1.5px;
  color:#2f8053; text-transform:uppercase; margin-bottom:10px;
}
.page-title {
  font-size:38px; line-height:1.1; letter-spacing:-1.7px;
  font-weight:700; margin:0; color:#17221d;
}
.page-subtitle {
  font-size:13px; line-height:1.7; color:#68756e;
  max-width:820px; margin-top:12px; margin-bottom:8px;
}
.section-header {
  display:flex; justify-content:space-between; align-items:end;
  margin-top:36px; margin-bottom:16px;
  border-bottom:1px solid #dfe5e1; padding-bottom:12px;
}
.section-title { font-size:17px; font-weight:600; letter-spacing:-.3px; color:#17221d; }

.kpi-card, .analysis-card {
  background:#fff; border:1px solid #d5ded8; padding:18px 20px;
}
.kpi-card { min-height:112px; }
.kpi-label, .analysis-number {
  font-family:'DM Mono',monospace; font-size:9px; letter-spacing:1px;
  color:#7c8982; text-transform:uppercase;
}
.kpi-value {
  font-family:'DM Mono',monospace; font-size:23px; font-weight:500;
  color:#17221d; margin-top:12px;
}
.kpi-note {
  font-family:'DM Mono',monospace; font-size:9px; color:#2f8053; margin-top:5px;
}
.analysis-title { font-size:15px; font-weight:600; margin-top:14px; color:#17221d; }
.analysis-text { font-size:11px; line-height:1.7; color:#68756e; margin-top:7px; }

.risk-low { color:#2f8053; font-weight:700; }
.risk-moderate { color:#8a6d1d; font-weight:700; }
.risk-elevated { color:#9a5a20; font-weight:700; }
.risk-high { color:#9a3434; font-weight:700; }

section[data-testid="stSidebar"] {
  background:#edf2ee; border-right:1px solid #dfe5e1;
}
.sidebar-brand {
  font-size:15px; font-weight:700; letter-spacing:1px;
  color:#17221d; margin-bottom:3px;
}
.sidebar-brand span { color:#2f8053; }
.sidebar-section {
  font-family:'DM Mono',monospace; font-size:9px; letter-spacing:1.2px;
  color:#2f8053; text-transform:uppercase; margin-top:20px; margin-bottom:4px;
}

.stNumberInput label, .stTextInput label, .stSelectbox label,
.stSlider label, .stFileUploader label {
  font-size:11px !important; color:#536159 !important;
}
.stNumberInput input {
  font-family:'DM Mono',monospace !important; font-size:11px !important;
}

.stButton > button {
  width:100%; border-radius:4px; border:1px solid #17221d;
  background:#17221d; color:#fff; font-size:11px; font-weight:600;
}
.stButton > button:hover { border-color:#2f8053; background:#2f8053; }
.stDownloadButton > button {
  width:100%; border-radius:4px; border:1px solid #2f8053;
  background:transparent; color:#2f8053; font-size:10px; font-weight:600;
}
.stDownloadButton > button:hover { background:#2f8053; color:#fff; }

.stTabs [data-baseweb="tab-list"] { gap:0; border-bottom:1px solid #d5ded8; }
.stTabs [data-baseweb="tab"] { font-size:10px; color:#6e7b74; padding:12px 18px; }
.stTabs [aria-selected="true"] { color:#2f8053 !important; }
.stTabs [data-baseweb="tab-highlight"] { background-color:#2f8053 !important; }

[data-testid="stDataFrame"] { border:1px solid #d5ded8; }

.app-footer {
  margin-top:55px; padding-top:18px; border-top:1px solid #dfe5e1;
  display:flex; justify-content:space-between;
  font-family:'DM Mono',monospace; font-size:8px; color:#849089;
  text-transform:uppercase; letter-spacing:.7px;
}

@media (prefers-color-scheme: dark) {
  .stApp { background:#111613; color:#e8eee9; }
  .brand-bar, .section-header, .app-footer { border-color:#29332d; }
  .brand-name, .page-title, .section-title, .kpi-value, .analysis-title, .sidebar-brand { color:#e8eee9; }
  .brand-meta, .page-subtitle, .section-meta, .kpi-label, .analysis-text { color:#9aa89f; }
  .kpi-card, .analysis-card { background:#171d19; border-color:#303b34; }
  section[data-testid="stSidebar"] { background:#171d19; border-color:#29332d; }
  .stTabs [data-baseweb="tab-list"], [data-testid="stDataFrame"] { border-color:#303b34; }
  .stTabs [data-baseweb="tab"] { color:#9aa89f; }
}
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# REFERENCE DATA & CORE LOGIC
# ============================================================

LIKELY_DRIVER_TAGS = {
    6010: "seasonal store headcount timing ahead of the holiday ramp",
    6015: "unplanned overtime to cover peak in-store traffic",
    6100: "lower store supply consumption than planned",
    6200: "higher utility rates / seasonal HVAC usage",
    6300: "corporate FTE hiring pacing behind plan",
    6310: "contractor usage extended to cover a delayed project timeline",
    6320: "reduced corporate travel activity",
    6400: "software licensing in line with plan",
    6410: "incremental support-contract scope added mid-quarter",
    6420: "unplanned POS hardware repairs at several locations",
    6500: "an unplanned in-store merchandising campaign",
    6510: "an event de-scoped or postponed",
    6600: "remodel work phased later than planned",
    6610: "unplanned facility repairs at multiple stores",
    6620: "new-store opening timeline pulled forward",
}

def make_sample_data():
    """Generate realistic sample budget + actual CSVs so the app works out of the box."""
    rows = [
        ("2025-10", "Retail Stores", 6010, "Store Labor", 1_250_000, 1_385_000),
        ("2025-10", "Retail Stores", 6015, "Store Overtime", 85_000, 142_000),
        ("2025-10", "Retail Stores", 6100, "Store Supplies", 95_000, 78_000),
        ("2025-10", "Retail Stores", 6200, "Utilities", 210_000, 248_000),
        ("2025-10", "Corporate", 6300, "Corporate Salaries", 420_000, 395_000),
        ("2025-10", "Corporate", 6310, "Contractors", 65_000, 98_000),
        ("2025-10", "Corporate", 6320, "Travel", 45_000, 28_000),
        ("2025-10", "IT", 6400, "Software Licenses", 180_000, 182_000),
        ("2025-10", "IT", 6410, "Support Contracts", 55_000, 72_000),
        ("2025-10", "IT", 6420, "Hardware Repairs", 22_000, 41_000),
        ("2025-10", "Marketing", 6500, "In-Store Campaigns", 120_000, 165_000),
        ("2025-10", "Marketing", 6510, "Events", 40_000, 18_000),
        ("2025-10", "Facilities", 6600, "Remodel Capex", 300_000, 210_000),
        ("2025-10", "Facilities", 6610, "Facility Repairs", 55_000, 89_000),
        ("2025-10", "Facilities", 6620, "New Store Openings", 150_000, 195_000),
    ]
    budget = pd.DataFrame([
        {"month": m, "department": d, "gl_account": g, "gl_account_name": n, "budget_amount": b}
        for m, d, g, n, b, a in rows
    ])
    actual = pd.DataFrame([
        {"month": m, "department": d, "gl_account": g, "gl_account_name": n, "actual_amount": a}
        for m, d, g, n, b, a in rows
    ])
    return budget, actual


def load_gl_data(budget_df: pd.DataFrame, actual_df: pd.DataFrame) -> pd.DataFrame:
    key_cols = ["month", "department", "gl_account", "gl_account_name"]
    for df, name in [(budget_df, "budget"), (actual_df, "actual")]:
        missing = set(key_cols) - set(df.columns)
        if missing:
            raise ValueError(f"{name} file is missing required columns: {missing}")
    merged = pd.merge(budget_df, actual_df, on=key_cols, how="outer")
    merged["budget_amount"] = merged["budget_amount"].fillna(0)
    merged["actual_amount"] = merged["actual_amount"].fillna(0)
    return merged


def calculate_variances(df: pd.DataFrame, pct_threshold: float, abs_threshold: float) -> pd.DataFrame:
    df = df.copy()
    df["variance_amount"] = df["actual_amount"] - df["budget_amount"]
    df["variance_pct"] = df.apply(
        lambda row: (row["variance_amount"] / row["budget_amount"])
        if row["budget_amount"] != 0 else float("inf"),
        axis=1,
    )
    df["is_material"] = (
        df["variance_pct"].abs().ge(pct_threshold)
        | df["variance_amount"].abs().ge(abs_threshold)
    )
    df["likely_driver"] = df["gl_account"].map(LIKELY_DRIVER_TAGS).fillna("driver not tagged")
    return df.sort_values("variance_amount", key=lambda s: s.abs(), ascending=False)


def generate_commentary_fallback(variances: pd.DataFrame) -> str:
    material = variances[variances["is_material"]].copy()
    if material.empty:
        return "No GL lines exceeded the materiality threshold this period; spend tracked closely to budget."

    total_budget = variances["budget_amount"].sum()
    total_actual = variances["actual_amount"].sum()
    total_var = total_actual - total_budget
    direction = "over" if total_var > 0 else "under"

    biggest = material.iloc[0]
    biggest_dir = "over" if biggest["variance_amount"] > 0 else "under"

    sentence_1 = (
        f"Total retail opex ran ${abs(total_var):,.0f} {direction} budget "
        f"({total_var / total_budget:+.1%}), driven primarily by "
        f"{biggest['department']} {biggest['gl_account_name']} "
        f"(${abs(biggest['variance_amount']):,.0f} {biggest_dir}, "
        f"{biggest['variance_pct']:+.1%}) attributed to {biggest['likely_driver']}."
    )

    if len(material) > 1:
        second = material.iloc[1]
        second_dir = "over" if second["variance_amount"] > 0 else "under"
        sentence_2 = (
            f"{second['department']} {second['gl_account_name']} was the next-largest driver at "
            f"${abs(second['variance_amount']):,.0f} {second_dir} budget "
            f"({second['variance_pct']:+.1%}), linked to {second['likely_driver']}; "
            f"{len(material) - 2 if len(material) > 2 else 0} other line(s) also crossed the "
            f"materiality threshold and are itemized in the attached variance report."
        )
    else:
        sentence_2 = "No other GL lines crossed the materiality threshold this period."

    return sentence_1 + " " + sentence_2


def generate_commentary_ai(variances: pd.DataFrame, model: str = "claude-sonnet-4-20250514") -> str:
    if not ANTHROPIC_AVAILABLE:
        st.warning("`anthropic` package not installed — using rule-based commentary.")
        return generate_commentary_fallback(variances)
    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.warning("ANTHROPIC_API_KEY not set — using rule-based commentary.")
        return generate_commentary_fallback(variances)

    material = variances[variances["is_material"]].copy()
    if material.empty:
        return "No GL lines exceeded the materiality threshold this period; spend tracked closely to budget."

    lines = []
    for _, row in material.iterrows():
        lines.append(
            f"- {row['department']} | {row['gl_account_name']} (GL {row['gl_account']}): "
            f"budget ${row['budget_amount']:,.0f}, actual ${row['actual_amount']:,.0f}, "
            f"variance ${row['variance_amount']:,.0f} ({row['variance_pct']:+.1%}), "
            f"likely driver: {row['likely_driver']}"
        )
    context = "\n".join(lines)

    total_budget = variances["budget_amount"].sum()
    total_actual = variances["actual_amount"].sum()
    total_var = total_actual - total_budget

    prompt = f"""You are an FP&A analyst writing a Budget-vs-Actual executive summary for retail
leadership. Total retail opex: budget ${total_budget:,.0f}, actual ${total_actual:,.0f},
variance ${total_var:,.0f} ({total_var / total_budget:+.1%}).

Material GL variances this period:
{context}

Write EXACTLY two sentences summarizing the variance drivers for a retail VP audience.
Be specific with dollar figures and drivers. No preamble, no bullet points, no headers —
just the two sentences."""

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=model,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(block.text for block in response.content if block.type == "text").strip()
        return text or generate_commentary_fallback(variances)
    except Exception as e:
        st.warning(f"AI call failed ({e}) — using rule-based commentary.")
        return generate_commentary_fallback(variances)


def kpi_card(label, value, note):
    return f"""
    <div class="kpi-card">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      <div class="kpi-note">{note}</div>
    </div>
    """


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
<div class="brand-bar">
  <div class="brand-name">Prustide Bangandozou<span>.</span></div>
  <div class="brand-meta">Finance · Analytics · Technology</div>
</div>
<div class="eyebrow">RETAIL FP&amp;A · BUDGET VS ACTUAL · AI COMMENTARY</div>
<div class="page-title">BvA Variance Analysis</div>
<div class="page-subtitle">
  Ingest monthly Budget and Actual GL exports, calculate material variances,
  flag key drivers, and generate executive commentary for retail leadership.
</div>
""",
    unsafe_allow_html=True,
)

# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.markdown(
    """
<div class="sidebar-brand">BVA<span>.</span></div>
<div class="sidebar-caption">Budget vs Actual Platform</div>
""",
    unsafe_allow_html=True,
)

st.sidebar.markdown('<div class="sidebar-section">Data Source</div>', unsafe_allow_html=True)
use_sample = st.sidebar.checkbox("Use sample retail data", value=True)

budget_file = None
actual_file = None
if not use_sample:
    budget_file = st.sidebar.file_uploader("Budget CSV", type=["csv"])
    actual_file = st.sidebar.file_uploader("Actual CSV", type=["csv"])

st.sidebar.markdown('<div class="sidebar-section">Materiality Thresholds</div>', unsafe_allow_html=True)
pct_threshold = st.sidebar.slider("Variance % Threshold", 0.05, 0.30, 0.10, 0.01)
abs_threshold = st.sidebar.number_input(
    "Absolute $ Threshold",
    min_value=10_000,
    max_value=500_000,
    value=50_000,
    step=5_000,
)

st.sidebar.markdown('<div class="sidebar-section">Commentary</div>', unsafe_allow_html=True)
use_ai = st.sidebar.checkbox(
    "Use AI commentary (Anthropic)",
    value=False,
    help="Requires ANTHROPIC_API_KEY environment variable and the anthropic package.",
)

# ============================================================
# LOAD DATA
# ============================================================

try:
    if use_sample:
        budget_df, actual_df = make_sample_data()
        period_label = "October 2025 (Sample)"
    else:
        if budget_file is None or actual_file is None:
            st.info("Upload both Budget and Actual CSV files, or enable sample data.")
            st.stop()
        budget_df = pd.read_csv(budget_file)
        actual_df = pd.read_csv(actual_file)
        period_label = "Uploaded Period"

    merged = load_gl_data(budget_df, actual_df)
    variances = calculate_variances(merged, pct_threshold, abs_threshold)

except Exception as e:
    st.error(f"Failed to process data: {e}")
    st.stop()

# ============================================================
# KPI SNAPSHOT
# ============================================================

total_budget = variances["budget_amount"].sum()
total_actual = variances["actual_amount"].sum()
total_var = total_actual - total_budget
n_material = int(variances["is_material"].sum())
n_lines = len(variances)

st.markdown(
    """
<div class="section-header">
  <div class="section-title">Period Snapshot</div>
  <div class="section-meta">Current underwriting assumptions</div>
</div>
""",
    unsafe_allow_html=True,
)

c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(kpi_card("Total Budget", f"${total_budget:,.0f}", period_label), unsafe_allow_html=True)
with c2:
    st.markdown(kpi_card("Total Actual", f"${total_actual:,.0f}", "GL actuals"), unsafe_allow_html=True)
with c3:
    direction = "Over" if total_var > 0 else "Under"
    st.markdown(
        kpi_card("Variance $", f"${total_var:+,.0f}", f"{direction} budget"),
        unsafe_allow_html=True,
    )
with c4:
    var_pct = total_var / total_budget if total_budget else 0
    st.markdown(kpi_card("Variance %", f"{var_pct:+.1%}", "vs budget"), unsafe_allow_html=True)
with c5:
    st.markdown(
        kpi_card("Material Lines", f"{n_material}", f"of {n_lines} GL lines"),
        unsafe_allow_html=True,
    )

st.caption(
    f"Materiality: ≥ {pct_threshold:.0%} variance or ≥ ${abs_threshold:,.0f} absolute. "
    "Educational FP&A model — not a formal audit determination."
)

# ============================================================
# TABS
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs([
    "Dashboard",
    "Variance Detail",
    "Executive Commentary",
    "Export",
])

# ── Tab 1: Dashboard ───────────────────────────────────────
with tab1:
    st.markdown(
        """
<div class="section-header">
  <div class="section-title">Variance Dashboard</div>
  <div class="section-meta">Executive view</div>
</div>
""",
        unsafe_allow_html=True,
    )

    left, right = st.columns([1, 1.5])

    with left:
        material = variances[variances["is_material"]]
        if not material.empty:
            top = material.iloc[0]
            st.markdown(
                f"""
                <div class="analysis-card">
                  <div class="analysis-number">LARGEST DRIVER</div>
                  <div class="kpi-value">${abs(top['variance_amount']):,.0f}</div>
                  <div class="analysis-title">{top['department']} · {top['gl_account_name']}</div>
                  <div class="analysis-text">
                    {top['variance_pct']:+.1%} vs budget<br>
                    Driver: {top['likely_driver']}
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                """
                <div class="analysis-card">
                  <div class="analysis-number">STATUS</div>
                  <div class="analysis-title">On Track</div>
                  <div class="analysis-text">No material variances this period.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        over = variances[variances["variance_amount"] > 0]["variance_amount"].sum()
        under = variances[variances["variance_amount"] < 0]["variance_amount"].sum()
        st.markdown(
            f"""
            <div class="analysis-card">
              <div class="analysis-number">NET POSITION</div>
              <div class="kpi-value">${total_var:+,.0f}</div>
              <div class="analysis-title">{"Overspend" if total_var > 0 else "Underspend"}</div>
              <div class="analysis-text">
                Favorable lines: ${abs(under):,.0f}<br>
                Unfavorable lines: ${over:,.0f}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        # Top 8 absolute variances chart
        top_n = variances.head(8).copy()
        top_n["label"] = top_n["department"].str[:8] + " · " + top_n["gl_account_name"].str[:18]
        fig, ax = plt.subplots(figsize=(8, 4.2))
        colors = ["#9a3434" if v > 0 else "#2f8053" for v in top_n["variance_amount"]]
        ax.barh(top_n["label"], top_n["variance_amount"], color=colors)
        ax.axvline(0, color="#17221d", linewidth=0.8)
        ax.set_xlabel("Variance $")
        ax.set_title("Largest Absolute Variances")
        ax.grid(axis="x", alpha=0.2)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)

    # Department rollup
    st.markdown(
        """
<div class="section-header">
  <div class="section-title">Department Rollup</div>
  <div class="section-meta">Aggregated view</div>
</div>
""",
        unsafe_allow_html=True,
    )
    dept = (
        variances.groupby("department", as_index=False)
        .agg(
            budget=("budget_amount", "sum"),
            actual=("actual_amount", "sum"),
            variance=("variance_amount", "sum"),
        )
    )
    dept["variance_pct"] = dept.apply(
        lambda r: r["variance"] / r["budget"] if r["budget"] else 0, axis=1
    )
    st.dataframe(
        dept.style.format({
            "budget": "${:,.0f}",
            "actual": "${:,.0f}",
            "variance": "${:+,.0f}",
            "variance_pct": "{:+.1%}",
        }),
        use_container_width=True,
        hide_index=True,
    )

# ── Tab 2: Variance Detail ─────────────────────────────────
with tab2:
    st.markdown(
        """
<div class="section-header">
  <div class="section-title">GL Line Detail</div>
  <div class="section-meta">Full variance table</div>
</div>
""",
        unsafe_allow_html=True,
    )

    show_only_material = st.checkbox("Show material lines only", value=False)
    view = variances[variances["is_material"]] if show_only_material else variances

    display = view[[
        "department", "gl_account", "gl_account_name",
        "budget_amount", "actual_amount", "variance_amount",
        "variance_pct", "is_material", "likely_driver"
    ]].copy()
    display.columns = [
        "Department", "GL Account", "Account Name",
        "Budget", "Actual", "Variance $",
        "Variance %", "Material", "Likely Driver"
    ]

    st.dataframe(
        display.style.format({
            "Budget": "${:,.0f}",
            "Actual": "${:,.0f}",
            "Variance $": "${:+,.0f}",
            "Variance %": "{:+.1%}",
        }),
        use_container_width=True,
        hide_index=True,
    )

# ── Tab 3: Executive Commentary ────────────────────────────
with tab3:
    st.markdown(
        """
<div class="section-header">
  <div class="section-title">Executive Commentary</div>
  <div class="section-meta">AI / rule-based summary</div>
</div>
""",
        unsafe_allow_html=True,
    )

    if st.button("Generate Commentary"):
        with st.spinner("Generating commentary..."):
            if use_ai:
                commentary = generate_commentary_ai(variances)
                source = "AI-generated (Anthropic)"
            else:
                commentary = generate_commentary_fallback(variances)
                source = "Rule-based"

        st.session_state["commentary"] = commentary
        st.session_state["commentary_source"] = source

    if "commentary" in st.session_state:
        st.markdown(
            f"""
            <div class="analysis-card">
              <div class="analysis-number">{st.session_state.get("commentary_source", "Commentary")}</div>
              <div class="analysis-text" style="font-size:13px; line-height:1.8; color:white; margin-top:12px;">
                {st.session_state["commentary"]}
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("Click **Generate Commentary** to produce the executive summary.")

# ── Tab 4: Export ──────────────────────────────────────────
with tab4:
    st.markdown(
        """
<div class="section-header">
  <div class="section-title">Export</div>
  <div class="section-meta">Download outputs</div>
</div>
""",
        unsafe_allow_html=True,
    )

    # Variance report CSV
    csv_buf = io.StringIO()
    variances.to_csv(csv_buf, index=False)
    st.download_button(
        "Download Variance Report (CSV)",
        data=csv_buf.getvalue(),
        file_name=f"variance_report_{datetime.now():%Y%m%d_%H%M%S}.csv",
        mime="text/csv",
    )

    # Commentary markdown
    if "commentary" in st.session_state:
        period = variances["month"].iloc[0] if not variances.empty else "period"
        md = (
            f"# Budget vs. Actual — Executive Commentary ({period})\n\n"
            f"_Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} "
            f"({st.session_state.get('commentary_source', 'rule-based')})_\n\n"
            f"{st.session_state['commentary']}\n"
        )
        st.download_button(
            "Download Executive Commentary (Markdown)",
            data=md,
            file_name=f"executive_commentary_{datetime.now():%Y%m%d_%H%M%S}.md",
            mime="text/markdown",
        )
    else:
        st.caption("Generate commentary first to enable the Markdown download.")

# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
<div class="app-footer">
  <span>Prustide Bangandozou · FINANCE &amp; ANALYTICS</span>
  <span>BvA · PYTHON · STREAMLIT · FP&amp;A AUTOMATION</span>
</div>
""",
    unsafe_allow_html=True,
)