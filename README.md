# Olist E-Commerce: Sales & Operations Analysis

End-to-end analysis of 96,478 delivered orders from the [Olist Brazilian E-Commerce public dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (Sep 2016 - Aug 2018): from raw CSVs to an executive dashboard and three quantified business opportunities.

**Headline:** R$ 13.2M revenue analyzed. Late deliveries (8.1% of orders) earn 1-star reviews 46% of the time vs 7% on-time. Only 3.0% of customers ever reorder. Three opportunities modeled at **R$ 555,651/year combined** (5.5% of annual revenue) - a scenario illustration across distinct bases (revenue opportunities + conditional freight savings), with explicit assumptions and no double-counting; not a guaranteed annual benefit.

## Deliverables

| Item | Where |
|---|---|
| Interactive dashboard (self-contained HTML) | `dashboard/index.html` |
| Findings & recommendations report (PDF) | `Olist-Findings-Report.pdf` |
| Business questions in SQL (8 queries, SQLite) | `sql/analysis.sql` |
| Data cleaning pipeline | `python/clean_data.py` |
| KPI & opportunity models | `analysis/run_analysis.py`, `analysis/opportunities.py` |
| Validation checks (grain, denominators, reconciliation) | `analysis/validate.py` |

## Findings

1. **Growth then plateau.** Monthly revenue grew 8x during 2017 (Black Friday peak, R$ 988k), then held near R$ 1M/month. Growth came from order volume; AOV stayed near R$ 137.
2. **Category concentration.** Top 10 categories drive 62% of revenue; Health & Beauty leads at 9.3%.
3. **Late deliveries track with low ratings.** Late orders average a 2.57 review vs 4.29 on-time (observational association, not proof of causation).
4. **Retention gap.** Only 3.0% of customers placed a second observed order within the dataset window (Sep 2016 - Aug 2018); late cohorts had little time to reorder, so the true lifetime rate cannot be established from this window.
5. **Cost pressure.** Freight charges average 31% of item value per order (mean per-order ratio; R$ 2.2M total, about 17% of item revenue).

## Method

- **Cleaning:** timestamps parsed; delivered orders only; latest review per order; categories translated to English; master table at one row per order (grain verified).
- **Definitions:** revenue = item prices of delivered orders, excluding freight. Payments reconcile within R$ 1 on 99.75% of orders. Late = delivered after the estimate shown at purchase.
- **Opportunity models:** computed on the last 12 complete months (Sep 2017 - Aug 2018). Delivery and retention scenarios overlap; the delivery-recovered cohort is deducted from the retention scenario so the total is additive.

## Getting the data

The raw CSVs are not included in the zip (about 160 MB). Two options:

1. Run `python download_data.py` - fetches the 8 CSVs from a public GitHub mirror (verified 24 Nov 2026) into `data/raw/`.
2. Or download the canonical dataset from [Kaggle](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) and place the same 8 CSVs in `data/raw/`.

## Reproduce

```bash
pip install -r requirements.txt
python download_data.py            # raw CSVs -> data/raw/ (one-time)
python python/clean_data.py        # raw CSVs -> data/clean/
python analysis/run_analysis.py    # KPIs -> analysis/stats.json
python analysis/opportunities.py   # modeled impact -> analysis/opportunities.json
python analysis/validate.py        # consistency checks
python dashboard/charts.py         # static charts (matplotlib)
python dashboard/generate_dashboard.py  # interactive dashboard (plotly)
```

Stack: Python (Pandas), SQL (SQLite), Plotly, Matplotlib.
