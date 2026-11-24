"""
Olist E-Commerce - Interactive Dashboard (self-contained HTML)
=============================================================
Builds dashboard/index.html: KPI cards + 5 interactive Plotly charts.
No server needed; opens in any browser. plotly.js is inlined.
"""
import pandas as pd
import json
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

BASE = Path(__file__).resolve().parents[1]
m = pd.read_csv(BASE / "data" / "clean" / "orders_master.csv",
                parse_dates=["order_purchase_timestamp"])
items = pd.read_csv(BASE / "data" / "clean" / "order_items_full.csv")
opp = json.loads((BASE / "analysis" / "opportunities.json").read_text())

NAVY, ACCENT, TEAL, GRAY = "#1b2a4a", "#e8590c", "#0ca678", "#868e96"

# KPIs
rev_total = m["total_price"].sum()
aov = rev_total / len(m)
m2 = m.dropna(subset=["delivery_days"])
late_rate = m2["is_late"].mean() * 100
mr = m2.dropna(subset=["review_score"])
cust_orders = m.groupby("customer_unique_id")["order_id"].count()
repeat_rate = (cust_orders > 1).mean() * 100

kpis = [
    ("Total revenue", f"R$ {rev_total/1e6:.1f}M", "delivered orders, 2016-2018"),
    ("Orders", f"{len(m):,}", "97.0% of all orders delivered"),
    ("Avg order value", f"R$ {aov:.0f}", "product value, excl. freight"),
    ("Late deliveries", f"{late_rate:.1f}%", "arrived after promised date"),
    ("Avg review", f"{mr['review_score'].mean():.2f} / 5", "4.29 on-time vs 2.57 late"),
    ("Repeat customers", f"{repeat_rate:.0f}%", "observed 2nd order in window"),
]

CAT_LABELS = {"health_beauty": "Health & Beauty", "watches_gifts": "Watches & Gifts",
              "bed_bath_table": "Bed, Bath & Table", "sports_leisure": "Sports & Leisure",
              "computers_accessories": "Computers & Accessories", "furniture_decor": "Furniture & Decor",
              "housewares": "Housewares", "cool_stuff": "Cool Stuff", "auto": "Auto", "toys": "Toys"}

# chart 1: monthly revenue
monthly = m.groupby("purchase_month")["total_price"].sum().reset_index()
monthly = monthly[(monthly["purchase_month"] >= "2017-01") & (monthly["purchase_month"] <= "2018-08")]
f1 = go.Figure(go.Scatter(x=monthly["purchase_month"], y=monthly["total_price"],
                          mode="lines+markers", line=dict(color=NAVY, width=3),
                          hovertemplate="%{x}<br>R$ %{y:,.0f}<extra></extra>"))
peak = monthly.loc[monthly["total_price"].idxmax()]
f1.add_annotation(x=peak["purchase_month"], y=peak["total_price"], text="Black Friday",
                  showarrow=True, arrowcolor=ACCENT, font=dict(color=ACCENT), ay=-40)
f1.update_layout(title="Monthly revenue (R$)", height=340, margin=dict(t=60, b=40),
                 hovermode="x unified", yaxis=dict(tickprefix="R$ "))

# chart 2: categories
cat = items.groupby("category_en")["price"].sum().sort_values(ascending=False).head(10)
f2 = go.Figure(go.Bar(y=[CAT_LABELS.get(c, c) for c in cat.index][::-1],
                      x=cat.values[::-1], orientation="h", marker_color=NAVY,
                      hovertemplate="%{y}<br>R$ %{x:,.0f}<extra></extra>"))
f2.update_layout(title="Top 10 categories by revenue (62% of total)", height=380,
                 margin=dict(t=60, b=40, l=180), xaxis=dict(tickprefix="R$ "))

# chart 3: late vs on-time reviews
late = mr[mr["is_late"]]["review_score"]
ontime = mr[~mr["is_late"]]["review_score"]
on_d = [(ontime == s).mean() * 100 for s in range(1, 6)]
late_d = [(late == s).mean() * 100 for s in range(1, 6)]
f3 = go.Figure([
    go.Bar(x=["1", "2", "3", "4", "5"], y=on_d, name=f"On time (avg {ontime.mean():.2f})",
           marker_color=TEAL, hovertemplate="%{y:.1f}%<extra>On time</extra>"),
    go.Bar(x=["1", "2", "3", "4", "5"], y=late_d, name=f"Late (avg {late.mean():.2f})",
           marker_color=ACCENT, hovertemplate="%{y:.1f}%<extra>Late</extra>")])
f3.update_layout(title="Review score: on-time vs late deliveries", barmode="group",
                 height=340, margin=dict(t=60, b=40), yaxis=dict(title="% of orders"),
                 xaxis=dict(title="Review stars"))

# chart 4: delivery histogram
f4 = go.Figure(go.Histogram(x=m2["delivery_days"].clip(0, 40), nbinsx=40, marker_color=NAVY,
                            hovertemplate="%{x:.0f} days: %{y} orders<extra></extra>"))
f4.add_vline(x=m2["delivery_days"].mean(), line_dash="dash", line_color=ACCENT,
             annotation_text=f"avg {m2['delivery_days'].mean():.1f} days",
             annotation_font_color=ACCENT)
f4.update_layout(title="Delivery time distribution (days)", height=340, margin=dict(t=60, b=40))

# chart 5: payment mix
paymix = m.groupby("main_payment_type")["order_id"].count().sort_values(ascending=False)
nice = {"credit_card": "Credit card", "boleto": "Boleto", "voucher": "Voucher", "debit_card": "Debit card"}
f5 = go.Figure(go.Pie(labels=[nice.get(p, p) for p in paymix.index], values=paymix.values,
                      hole=0.45, marker_colors=[NAVY, ACCENT, TEAL, GRAY],
                      hovertemplate="%{label}: %{percent}<extra></extra>"))
f5.update_layout(title="Payment methods (share of orders)", height=340, margin=dict(t=60, b=40))

def div(fig, div_id):
    return pio.to_html(fig, full_html=False, include_plotlyjs=False, div_id=div_id,
                       config={'displayModeBar': False})

import plotly.offline as pyo
plotly_js = pyo.get_plotlyjs()

cards = "\n".join(
    f'<div class="card"><div class="kpi">{v}</div><div class="label">{k}</div>'
    f'<div class="sub">{s}</div></div>' for k, v, s in kpis)

adj = opp["overlap_adjustment"]
html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Olist E-Commerce - Executive Dashboard</title>
<script>{plotly_js}</script>
<style>
 body {{ font-family: -apple-system, 'Segoe UI', Arial, sans-serif; margin: 0; background: #f8f9fa; color: {NAVY}; }}
 header {{ background: {NAVY}; color: white; padding: 28px 40px; }}
 header h1 {{ margin: 0 0 6px; font-size: 26px; }}
 header p {{ margin: 0; color: #adb5bd; font-size: 14px; }}
 .cards {{ display: flex; flex-wrap: wrap; gap: 14px; padding: 24px 40px 8px; }}
 .card {{ background: white; border-radius: 10px; padding: 18px 22px; flex: 1 1 150px;
         box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
 .kpi {{ font-size: 26px; font-weight: 700; }}
 .label {{ font-size: 13px; font-weight: 600; margin-top: 2px; }}
 .sub {{ font-size: 11.5px; color: {GRAY}; margin-top: 3px; }}
 .grid {{ display: grid; grid-template-columns: 1fr; gap: 14px; padding: 16px 40px 40px; }}
 .panel {{ background: white; border-radius: 10px; padding: 14px;
          box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
 @media (min-width: 1000px) {{ .grid {{ grid-template-columns: 1fr 1fr; }} .wide {{ grid-column: 1 / -1; }} }}
 footer {{ padding: 0 40px 30px; color: {GRAY}; font-size: 12px; }}
 .impact {{ background: #fff4e6; border-left: 4px solid {ACCENT}; margin: 16px 40px 0;
           padding: 14px 18px; border-radius: 6px; font-size: 14px; }}
</style></head><body>
<header>
 <h1>Olist E-Commerce: Sales &amp; Operations Dashboard</h1>
 <p>96,478 delivered orders &middot; Sep 2016 - Aug 2018 &middot; Brazilian public dataset</p>
</header>
<div class="cards">{cards}</div>
<div class="impact"><b>Combined scenario illustration: R$ {adj['adjusted_total_annual_impact_brl']:,.0f}/yr</b>
 ({adj['adjusted_total_vs_annual_revenue_pct']}% of last-12-month revenue) - modeled revenue opportunities
 (delivery reliability, retention) plus conditional freight savings. Distinct bases, not a single guaranteed
 benefit; assumptions documented in the project report.</div>
<div class="grid">
 <div class="panel wide">{div(f1, 'c1')}</div>
 <div class="panel">{div(f2, 'c2')}</div>
 <div class="panel">{div(f3, 'c3')}</div>
 <div class="panel">{div(f4, 'c4')}</div>
 <div class="panel">{div(f5, 'c5')}</div>
</div>
<footer>Source: Olist Brazilian E-Commerce Public Dataset (Kaggle). Revenue = product value of
delivered orders, excluding freight. Analysis: Python (Pandas), SQL (SQLite), dashboard in Plotly.</footer>
</body></html>"""

out = Path(__file__).resolve().parent / "index.html"
out.write_text(html, encoding="utf-8")
print("dashboard written:", out, f"{out.stat().st_size/1e6:.1f} MB")
