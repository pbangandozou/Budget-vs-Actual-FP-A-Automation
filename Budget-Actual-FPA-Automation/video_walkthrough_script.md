# Loom Walkthrough Script (~2 minutes)

Record this as a screen share: Excel workbook open to the Dashboard tab, with the automation script's
terminal output ready in a second window/tab to cut to. Read at a natural pace — this script runs
close to 2 minutes spoken aloud; trim a sentence or two per section if you land long.

---

**[0:00–0:15] — Open on the Dashboard tab**

> "This is a Retail FP&A portfolio project I built on Apple's actual public financials — a full
> 3-statement model, retail-specific planning schedules, and a Python automation pipeline. I'm on the
> executive dashboard now, which pulls live from the rest of the workbook — nothing here is hardcoded."

*(Point at the KPI tiles and the two charts.)*

**[0:15–0:40] — Income Statement**

*(Switch to the Income_Statement tab.)*

> "The model is built off Apple's FY2024 and FY2025 actuals, straight from the 10-K. The interesting
> part is the revenue build: Apple only discloses a 40/60 Direct-vs-Indirect channel split for FY2025 —
> it doesn't break out Stores vs. E-Commerce. So I modeled that split explicitly as an estimate, and
> every one of those cells has a comment explaining exactly what's real and what's assumed."

*(Hover over a blue input cell to show the comment tooltip.)*

**[0:40–1:05] — Balance Sheet & the balance check**

*(Switch to Balance_Sheet, scroll to the bottom.)*

> "Balance Sheet and Cash Flow are fully linked — working capital ties to the Income Statement on a
> days-outstanding basis, PP&E rolls forward with CapEx and depreciation, and equity rolls forward with
> net income, dividends, and buybacks. This bottom row is a balance check — Assets minus Liabilities and
> Equity — and it holds at zero in every single year, historical and projected."

**[1:05–1:30] — Retail CapEx and GRS Headcount schedules**

*(Switch to Retail_CapEx, then GRS_Headcount.)*

> "These two tabs are the retail-specialization piece. CapEx is built bottom-up from new store counts
> and remodel counts, with a simplified depreciation schedule that feeds straight back into the core
> model. And headcount has a scenario toggle right here — I can convert contractors to full-time
> employees and immediately see the run-rate impact, which is the kind of lever a real GRS finance
> partner would want to flex."

**[1:30–1:50] — Automation pipeline**

*(Cut to terminal / automation script output.)*

> "Last piece: a Python script that ingests raw budget and actual GL exports, calculates variances,
> flags anything material, and writes an executive commentary automatically — here it's flagging GRS
> Contractor Fees running 19% over budget and explaining why, without me writing a single sentence by
> hand. It'll use the Anthropic API if a key's available, or fall back to a rule-based version if not,
> so it always runs."

**[1:50–2:00] — Close**

> "That's the project end to end — model, schedules, and automation, all in the GitHub repo linked
> below, along with the 1-page executive summary. Thanks for watching."

---

### Recording checklist
- [ ] Zoom Excel to ~120% so cell comments and formulas are legible on screen
- [ ] Have the terminal pre-run once so output appears instantly on cut (avoid dead air waiting on `pip`/API calls)
- [ ] Trim total recording to under 2:15 — Loom viewers drop off fast past 2 minutes
- [ ] Add the GitHub repo link and this project's README in the Loom description
