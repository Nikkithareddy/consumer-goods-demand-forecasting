"""Generate 3 years of synthetic daily sales data for 5 consumer-goods categories."""
import numpy as np
import pandas as pd

np.random.seed(42)
categories = {
    "Beverages":     {"base": 220, "season_amp": 60, "peak_month": 6, "promo_lift": 1.35},
    "Snacks":        {"base": 180, "season_amp": 35, "peak_month": 11, "promo_lift": 1.30},
    "Personal Care": {"base": 140, "season_amp": 15, "peak_month": 12, "promo_lift": 1.20},
    "Home Cleaning": {"base": 110, "season_amp": 20, "peak_month": 3, "promo_lift": 1.15},
    "Frozen Foods":  {"base": 160, "season_amp": 45, "peak_month": 1, "promo_lift": 1.25},
}
dates = pd.date_range("2023-01-01", "2025-12-31", freq="D")
promo_idx = set(np.random.choice(len(dates), size=int(len(dates) * 0.08), replace=False))

rows = []
for cat, p in categories.items():
    for i, d in enumerate(dates):
        month_angle = 2 * np.pi * (d.month - p["peak_month"]) / 12
        season = p["season_amp"] * np.cos(month_angle)
        weekday_effect = 1.15 if d.weekday() >= 5 else 1.0
        promo = p["promo_lift"] if i in promo_idx else 1.0
        noise = np.random.normal(0, p["base"] * 0.08)
        units = max(0, (p["base"] + season) * weekday_effect * promo + noise)
        rows.append((d, cat, round(units), i in promo_idx))

df = pd.DataFrame(rows, columns=["date", "category", "units_sold", "on_promo"])
df.to_csv("data/daily_sales.csv", index=False)
print("Rows:", len(df), "| Categories:", list(df['category'].unique()))
