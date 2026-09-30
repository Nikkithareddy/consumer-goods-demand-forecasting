# Consumer Goods Demand Forecasting & Safety Stock Optimization

**Tech Stack:** Python, SQL, Power BI-style dashboard (Plotly), MS Excel-compatible CSV outputs

A simulated retail analytics project that analyzes demand patterns across 5 consumer-goods
categories, builds a short-horizon demand forecast, and optimizes safety-stock / reorder-point
policy to hit a target service level while minimizing stockouts.

> **Note on data:** this project uses a synthetically generated 3-year daily sales dataset
> (`src/generate_data.py`) built with realistic seasonality, weekday effects, promo lifts, and
> noise, so the full pipeline — and every number below — can be reproduced end-to-end without
> needing a real company's data.

## What it does

1. **Seasonal demand analysis** — aggregates 3 years of daily sales across 5 product categories
   to surface seasonal peaks, weekday/weekend effects, and promotional lift.
2. **Demand forecasting** — a 28-day-ahead forecast combining exponential smoothing (for the
   demand level) with a day-of-week seasonal index.
3. **Safety stock & reorder-point optimization** — computes safety stock under a **stochastic
   lead-time model** (lead time ~ N(7, 1.5) days) using the combined-variance formula, so the
   buffer accounts for *both* demand variability and supplier lead-time variability — not just
   demand alone.
4. **Monte Carlo validation** — 2,000-trial simulation per category comparing the optimized
   policy against a prior rule-of-thumb policy (calibrated to an ~85% service level, accounting
   for demand variance only) to quantify the real-world impact of the switch.

## Key results (from this run)

| Metric | Prior policy | Optimized policy |
|---|---|---|
| Target service level | ~85% (implicit) | **95%** |
| Avg. simulated stockout rate | 14.7% | **5.0%** |
| Stockout rate reduction | — | **~10 percentage points** |

Promotional lift ranged from **+17% (Home Cleaning)** to **+34% (Beverages)**, informing which
categories need the largest short-term reorder-point adjustments around promo weeks.

## Project structure

```
data/                    generated & derived CSVs (sales, seasonality, policy, simulation)
src/generate_data.py     synthetic 3-year daily sales generator
src/analysis.py          seasonality, forecasting, safety-stock optimization, Monte Carlo sim
src/load_to_sqlite.py    loads CSV into SQLite and runs sql/queries.sql
sql/queries.sql          seasonality, promo lift, rolling averages, volatility (SQL views)
src/build_dashboard.py   builds the interactive HTML/Plotly dashboard
dashboard/dashboard.html self-contained interactive dashboard (open directly in a browser)
```

## How to run

```bash
pip install -r requirements.txt
python src/generate_data.py      # 1. generate synthetic sales data
python src/analysis.py           # 2. run seasonality / forecast / safety-stock analysis
python src/load_to_sqlite.py     # 3. (optional) run the SQL views
python src/build_dashboard.py    # 4. build dashboard/dashboard.html
```

Then open `dashboard/dashboard.html` in any browser — it's fully self-contained.

## Why a Plotly dashboard instead of a `.pbix` file?

The dashboard reproduces the same 4 core views a Power BI report would have (seasonal trend,
reorder-point comparison, stockout-rate comparison, promo lift), but as a portable, self-contained
HTML file so it's viewable directly on GitHub/browser without Power BI Desktop installed. The
underlying `data/*.csv` files are Power BI/Excel-ready if you want to load them into an actual
`.pbix` report.

## Methodology notes

- Safety stock formula (stochastic lead time):
  `SS = Z * sqrt(LT_mean * σ_demand² + μ_demand² * LT_std²)`
- Reorder point: `ROP = μ_demand * LT_mean + SS`
- Service level → Z-score via the inverse normal CDF (`scipy.stats.norm.ppf`)
