#!/usr/bin/env python3
"""
bva_variance_ai_commentary.py
------------------------------
Retail FP&A automation: ingests raw monthly Budget and Actual GL exports,
calculates Budget-vs-Actual (BvA) variances, flags material variances, and
generates an AI-written executive commentary summarizing the drivers.

This is the "Automate Ingestion & AI Commentary" deliverable (Phase 4) of the
Apple Retail FP&A portfolio project. In a live environment this script (or an
equivalent Power Query pipeline) would run monthly against a real GL export;
here it runs against CSV mockups in data/ so the pipeline is fully reproducible.

USAGE
-----
    python bva_variance_ai_commentary.py \
        --budget data/budget_oct2025.csv \
        --actual data/actual_oct2025.csv \
        --out-dir output/

    # Without an API key, the script still runs end-to-end using a
    # deterministic rule-based commentary generator (see generate_commentary_fallback).
    # With one set, it calls the Anthropic API for natural-language commentary:
    export ANTHROPIC_API_KEY=sk-ant-...
    python bva_variance_ai_commentary.py --use-ai

REQUIREMENTS
------------
    pip install pandas
    pip install anthropic   # only required if --use-ai is passed
"""

import argparse
import os
import sys
from datetime import datetime

import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# A variance is "material" (flagged for commentary) if it exceeds EITHER threshold.
MATERIALITY_PCT_THRESHOLD = 0.10       # 10%
MATERIALITY_ABS_THRESHOLD = 50_000     # $50K

# Rule-based "likely driver" tags, keyed by GL account. Used both by the
# fallback commentary generator and as structured context fed to the AI model
# so its commentary is grounded in something more specific than the raw numbers.
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


# ---------------------------------------------------------------------------
# Step 1: Ingestion (stand-in for a Power Query / GL export pull)
# ---------------------------------------------------------------------------

def load_gl_data(budget_path: str, actual_path: str) -> pd.DataFrame:
    """Load and merge raw Budget and Actual GL extracts into one variance-ready table."""
    budget = pd.read_csv(budget_path)
    actual = pd.read_csv(actual_path)

    key_cols = ["month", "department", "gl_account", "gl_account_name"]
    for df, name in [(budget, "budget"), (actual, "actual")]:
        missing = set(key_cols) - set(df.columns)
        if missing:
            raise ValueError(f"{name} file is missing required columns: {missing}")

    merged = pd.merge(budget, actual, on=key_cols, how="outer")
    merged["budget_amount"] = merged["budget_amount"].fillna(0)
    merged["actual_amount"] = merged["actual_amount"].fillna(0)
    return merged


# ---------------------------------------------------------------------------
# Step 2: Variance calculation
# ---------------------------------------------------------------------------

def calculate_variances(df: pd.DataFrame) -> pd.DataFrame:
    """Add variance $, variance %, and a materiality flag to each GL line."""
    df = df.copy()
    df["variance_amount"] = df["actual_amount"] - df["budget_amount"]
    df["variance_pct"] = df.apply(
        lambda row: (row["variance_amount"] / row["budget_amount"])
        if row["budget_amount"] != 0 else float("inf"),
        axis=1,
    )
    df["is_material"] = (
        df["variance_pct"].abs().ge(MATERIALITY_PCT_THRESHOLD)
        | df["variance_amount"].abs().ge(MATERIALITY_ABS_THRESHOLD)
    )
    df["likely_driver"] = df["gl_account"].map(LIKELY_DRIVER_TAGS).fillna("driver not tagged")
    return df.sort_values("variance_amount", key=lambda s: s.abs(), ascending=False)


# ---------------------------------------------------------------------------
# Step 3a: Commentary — rule-based fallback (no API key required)
# ---------------------------------------------------------------------------

def generate_commentary_fallback(variances: pd.DataFrame) -> str:
    """Deterministic, template-based executive summary. Runs with zero external
    dependencies so the pipeline always produces an answer, even without API access."""
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


# ---------------------------------------------------------------------------
# Step 3b: Commentary — Anthropic API (optional, richer natural-language output)
# ---------------------------------------------------------------------------

def generate_commentary_ai(variances: pd.DataFrame, model: str = "claude-sonnet-4-6") -> str:
    """Calls the Anthropic API to write a 2-sentence executive BvA commentary.

    Requires `pip install anthropic` and the ANTHROPIC_API_KEY environment
    variable to be set. Falls back to the rule-based generator automatically
    if the package or key is unavailable, so this function is always safe to call.
    """
    try:
        import anthropic
    except ImportError:
        print("[warn] `anthropic` package not installed — falling back to rule-based commentary. "
              "Run `pip install anthropic` to enable AI commentary.", file=sys.stderr)
        return generate_commentary_fallback(variances)

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[warn] ANTHROPIC_API_KEY not set — falling back to rule-based commentary.", file=sys.stderr)
        return generate_commentary_fallback(variances)

    material = variances[variances["is_material"]].copy()
    if material.empty:
        return "No GL lines exceeded the materiality threshold this period; spend tracked closely to budget."

    # Build a compact, structured context block — this is what actually grounds
    # the model's output in real numbers instead of letting it invent figures.
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

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in response.content if block.type == "text").strip()
    return text or generate_commentary_fallback(variances)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run(budget_path: str, actual_path: str, out_dir: str, use_ai: bool) -> None:
    os.makedirs(out_dir, exist_ok=True)

    print(f"[1/4] Loading GL data from {budget_path} and {actual_path} ...")
    merged = load_gl_data(budget_path, actual_path)

    print("[2/4] Calculating variances ...")
    variances = calculate_variances(merged)
    n_material = int(variances["is_material"].sum())
    print(f"      {len(variances)} GL lines processed, {n_material} flagged as material "
          f"(>{MATERIALITY_PCT_THRESHOLD:.0%} or >${MATERIALITY_ABS_THRESHOLD:,.0f}).")

    report_path = os.path.join(out_dir, "variance_report.csv")
    variances.to_csv(report_path, index=False)
    print(f"      Variance report written to {report_path}")

    print(f"[3/4] Generating executive commentary ({'AI' if use_ai else 'rule-based'}) ...")
    commentary = generate_commentary_ai(variances) if use_ai else generate_commentary_fallback(variances)

    print("[4/4] Writing commentary output ...")
    commentary_path = os.path.join(out_dir, "executive_commentary.md")
    period = variances["month"].iloc[0] if not variances.empty else "period"
    with open(commentary_path, "w") as f:
        f.write(f"# Budget vs. Actual — Executive Commentary ({period})\n\n")
        f.write(f"_Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} "
                f"by bva_variance_ai_commentary.py{' (AI-generated)' if use_ai else ' (rule-based)'}_\n\n")
        f.write(commentary + "\n")
    print(f"      Commentary written to {commentary_path}\n")

    print("=" * 70)
    print("EXECUTIVE COMMENTARY")
    print("=" * 70)
    print(commentary)
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Retail FP&A Budget-vs-Actual automation with AI commentary.")
    parser.add_argument("--budget", default="data/budget_oct2025.csv", help="Path to budget GL CSV.")
    parser.add_argument("--actual", default="data/actual_oct2025.csv", help="Path to actual GL CSV.")
    parser.add_argument("--out-dir", default="output", help="Directory to write outputs to.")
    parser.add_argument("--use-ai", action="store_true",
                         help="Use the Anthropic API for commentary (requires ANTHROPIC_API_KEY). "
                              "Without this flag, uses the deterministic rule-based generator.")
    args = parser.parse_args()
    run(args.budget, args.actual, args.out_dir, args.use_ai)


if __name__ == "__main__":
    main()
