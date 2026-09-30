"""Build a self-contained interactive HTML dashboard (Power BI-style views)."""
import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

df = pd.read_csv("data/daily_sales.csv", parse_dates=["date"])
seasonal = pd.read_csv("data/seasonal_avg_units.csv", index_col=0)
policy = pd.read_csv("data/inventory_policy.csv")
sim = pd.read_csv("data/stockout_simulation.csv")
with open("data/summary_metrics.json") as f:
    summary = json.load(f)

fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "Seasonal Demand Pattern by Category (avg units/day)",
        "Reorder Point: Optimized vs. Prior Rule-of-Thumb",
        "Simulated Stockout Rate by Policy",
        "Promotional Demand Lift by Category (%)",
    ),
    specs=[[{"type": "scatter"}, {"type": "bar"}],
           [{"type": "bar"}, {"type": "bar"}]],
    vertical_spacing=0.14, horizontal_spacing=0.10,
)

for cat in seasonal.columns:
    fig.add_trace(go.Scatter(x=seasonal.index, y=seasonal[cat], mode="lines+markers", name=cat),
                  row=1, col=1)

fig.add_trace(go.Bar(x=policy["category"], y=policy["naive_reorder_point"], name="Prior policy",
                      marker_color="#c96a6a"), row=1, col=2)
fig.add_trace(go.Bar(x=policy["category"], y=policy["reorder_point"], name="Optimized policy",
                      marker_color="#2f6db5"), row=1, col=2)

pivot = sim.pivot(index="category", columns="policy", values="stockout_rate_pct")
fig.add_trace(go.Bar(x=pivot.index, y=pivot["naive_fixed_lt"], name="Prior policy stockout %",
                      marker_color="#c96a6a", showlegend=False), row=2, col=1)
fig.add_trace(go.Bar(x=pivot.index, y=pivot["optimized_stochastic_lt"], name="Optimized stockout %",
                      marker_color="#2f6db5", showlegend=False), row=2, col=1)

promo = summary["promo_lift_pct_by_category"]
fig.add_trace(go.Bar(x=list(promo.keys()), y=list(promo.values()), marker_color="#4caf7d",
                      showlegend=False), row=2, col=2)

fig.update_layout(
    title=dict(text="Consumer Goods Demand Forecasting & Safety Stock Optimization",
               x=0.5, font=dict(size=20)),
    height=820, width=1180, barmode="group",
    template="plotly_white", legend=dict(orientation="h", y=-0.08),
    margin=dict(t=90),
)
fig.update_xaxes(title_text="Month", row=1, col=1)
fig.update_yaxes(title_text="Avg units/day", row=1, col=1)
fig.update_yaxes(title_text="Units", row=1, col=2)
fig.update_yaxes(title_text="Stockout rate (%)", row=2, col=1)
fig.update_yaxes(title_text="Lift vs. non-promo (%)", row=2, col=2)

kpi_html = f"""
<div style="display:flex;gap:24px;justify-content:center;font-family:Arial;margin:18px 0 6px;">
  <div style="background:#eef4fb;border-radius:10px;padding:14px 22px;text-align:center;">
    <div style="font-size:26px;font-weight:700;color:#2f6db5;">{summary['avg_stockout_rate_optimized_stochastic_lt_pct']}%</div>
    <div style="font-size:12px;color:#555;">Optimized stockout rate</div>
  </div>
  <div style="background:#fbeeee;border-radius:10px;padding:14px 22px;text-align:center;">
    <div style="font-size:26px;font-weight:700;color:#c96a6a;">{summary['avg_stockout_rate_naive_pct']}%</div>
    <div style="font-size:12px;color:#555;">Prior policy stockout rate</div>
  </div>
  <div style="background:#eef8f0;border-radius:10px;padding:14px 22px;text-align:center;">
    <div style="font-size:26px;font-weight:700;color:#4caf7d;">-{summary['avg_stockout_reduction_pct_points']} pts</div>
    <div style="font-size:12px;color:#555;">Stockout reduction</div>
  </div>
  <div style="background:#f5f0fb;border-radius:10px;padding:14px 22px;text-align:center;">
    <div style="font-size:26px;font-weight:700;color:#7a52a3;">{int(summary['target_service_level']*100)}%</div>
    <div style="font-size:12px;color:#555;">Target service level</div>
  </div>
</div>
"""

fig_html = fig.to_html(include_plotlyjs="cdn", full_html=False)
html = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Consumer Goods Demand Forecasting & Safety Stock Optimization</title></head>
<body style="margin:0;background:#fafafa;">
{kpi_html}
{fig_html}
</body></html>"""

with open("dashboard/dashboard.html", "w") as f:
    f.write(html)
print("Dashboard written to dashboard/dashboard.html")
