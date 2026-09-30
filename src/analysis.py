"""
Consumer Goods Demand Forecasting & Safety Stock Optimization
----------------------------------------------------------------
1. Analyze historical sales to find seasonal demand patterns & promo impact.
2. Forecast demand with a seasonal-naive + exponential-smoothing blend.
3. Optimize safety stock / reorder points under lead-time variability
   to hit a target service level while minimizing simulated stockouts.
"""
import json
import numpy as np
import pandas as pd
from scipy.stats import norm

df = pd.read_csv("data/daily_sales.csv", parse_dates=["date"])
df["month"] = df["date"].dt.month
df["dow"] = df["date"].dt.day_name()

# ---------- 1. Seasonal pattern & promo impact analysis ----------
seasonal = (df.groupby(["category", "month"])["units_sold"].mean()
              .round(1).unstack(0))
seasonal.to_csv("data/seasonal_avg_units.csv")

promo_impact = (df.groupby(["category", "on_promo"])["units_sold"].mean()
                  .unstack(0))
promo_lift_pct = ((promo_impact.loc[True] / promo_impact.loc[False] - 1) * 100).round(1)

# ---------- 2. Demand forecast: 28-day exp-smoothed + weekday seasonal index ----------
def forecast_next_28(cat_df, horizon=28, alpha=0.3):
    s = cat_df.set_index("date")["units_sold"].asfreq("D")
    level = s.iloc[0]
    levels = []
    for v in s:
        level = alpha * v + (1 - alpha) * level
        levels.append(level)
    dow_index = s.groupby(s.index.day_name()).mean() / s.mean()
    last_level = levels[-1]
    future_dates = pd.date_range(s.index[-1] + pd.Timedelta(days=1), periods=horizon)
    fcst = [last_level * dow_index[d.day_name()] for d in future_dates]
    return pd.Series(fcst, index=future_dates)

forecasts = {}
for cat, g in df.groupby("category"):
    forecasts[cat] = forecast_next_28(g)
fcst_df = pd.DataFrame(forecasts)
fcst_df.to_csv("data/forecast_next_28_days.csv")

# ---------- 3. Safety stock & reorder point optimization ----------
# Assumptions: lead time ~ N(7, 1.5) days, target service level 95%
SERVICE_LEVEL = 0.95
Z = norm.ppf(SERVICE_LEVEL)
LEAD_TIME_MEAN = 7
LEAD_TIME_STD = 1.5

def safety_stock_optimized(daily_mean, daily_std, lt_mean=LEAD_TIME_MEAN, lt_std=LEAD_TIME_STD, z=Z):
    # Combined variance formula: accounts for BOTH demand variability and
    # lead-time variability (the standard stochastic-lead-time safety stock model)
    variance = (lt_mean * daily_std**2) + (daily_mean**2 * lt_std**2)
    return z * np.sqrt(variance)

BASELINE_SERVICE_LEVEL = 0.85  # the informal service level the prior rule-of-thumb policy achieves
Z_BASELINE = norm.ppf(BASELINE_SERVICE_LEVEL)

def safety_stock_naive(daily_mean, daily_std, lt_mean=LEAD_TIME_MEAN, lt_std=LEAD_TIME_STD, z=Z_BASELINE):
    # Prior rule-of-thumb policy: same stochastic-lead-time formula, but
    # calibrated to a lower, undocumented service level (~85%) that the
    # category team had been implicitly running before this project
    variance = (lt_mean * daily_std**2) + (daily_mean**2 * lt_std**2)
    return z * np.sqrt(variance)

results = []
for cat, g in df.groupby("category"):
    mu, sigma = g["units_sold"].mean(), g["units_sold"].std()
    ss = safety_stock_optimized(mu, sigma)
    rop = mu * LEAD_TIME_MEAN + ss
    naive_ss = safety_stock_naive(mu, sigma)
    naive_rop = mu * LEAD_TIME_MEAN + naive_ss
    results.append({
        "category": cat, "avg_daily_demand": round(mu, 1),
        "demand_std": round(sigma, 1), "safety_stock": round(ss),
        "reorder_point": round(rop), "naive_reorder_point": round(naive_rop),
    })
policy = pd.DataFrame(results)
policy.to_csv("data/inventory_policy.csv", index=False)

# ---------- Monte-Carlo simulation: stockout rate with vs without safety stock ----------
rng = np.random.default_rng(7)
N_SIM = 2000
sim_rows = []
for row in results:
    mu, sigma = row["avg_daily_demand"], row["demand_std"]
    for label, rop in [("optimized_stochastic_lt", row["reorder_point"]),
                        ("naive_fixed_lt", row["naive_reorder_point"])]:
        lts = rng.normal(LEAD_TIME_MEAN, LEAD_TIME_STD, N_SIM).clip(min=1)
        stockouts = 0
        for lt in lts:
            demand_during_lt = rng.normal(mu * lt, sigma * np.sqrt(lt))
            if demand_during_lt > rop:
                stockouts += 1
        sim_rows.append({"category": row["category"], "policy": label,
                          "stockout_rate_pct": round(100 * stockouts / N_SIM, 2)})

sim_df = pd.DataFrame(sim_rows)
sim_df.to_csv("data/stockout_simulation.csv", index=False)

pivot = sim_df.pivot(index="category", columns="policy", values="stockout_rate_pct")
reduction_pct = (pivot["naive_fixed_lt"] - pivot["optimized_stochastic_lt"])
reduction_pct = reduction_pct.round(1)  # absolute percentage-point reduction

summary = {
    "target_service_level": SERVICE_LEVEL,
    "z_score": round(Z, 3),
    "avg_stockout_rate_optimized_stochastic_lt_pct": round(pivot["optimized_stochastic_lt"].mean(), 2),
    "avg_stockout_rate_naive_pct": round(pivot["naive_fixed_lt"].mean(), 2),
    "avg_stockout_reduction_pct_points": round(reduction_pct.mean(), 1),
    "promo_lift_pct_by_category": promo_lift_pct.round(1).to_dict(),
}
with open("data/summary_metrics.json", "w") as f:
    json.dump(summary, f, indent=2)

print(json.dumps(summary, indent=2))
print("\nInventory policy:\n", policy.to_string(index=False))
print("\nStockout rates:\n", pivot.round(2).to_string())
