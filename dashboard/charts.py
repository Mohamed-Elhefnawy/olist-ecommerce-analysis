"""
Olist E-Commerce - Dashboard Charts
Generates the 6 report charts into dashboard/charts/*.png
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "charts"
OUT.mkdir(exist_ok=True)

m = pd.read_csv(BASE / "data" / "clean" / "orders_master.csv",
                parse_dates=["order_purchase_timestamp"])
items = pd.read_csv(BASE / "data" / "clean" / "order_items_full.csv")

NAVY = "#1b2a4a"
ACCENT = "#e8590c"
TEAL = "#0ca678"
GRAY = "#868e96"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11,
    "axes.edgecolor": "#dee2e6", "axes.linewidth": 0.8,
    "axes.titlesize": 15, "axes.titleweight": "bold",
    "figure.facecolor": "white", "axes.facecolor": "white",
})

def set_title(ax, title):
    ax.set_title(title, loc="left", color=NAVY, pad=26, fontsize=15, fontweight="bold")

def style(ax, subtitle):
    ax.spines[["top", "right"]].set_visible(False)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=10.5, color=GRAY)
    ax.grid(axis="y", color="#f1f3f5", linewidth=1)
    ax.set_axisbelow(True)

def savefig(fig, name):
    fig.text(0.99, -0.04, "Source: Olist public e-commerce dataset (96,478 delivered orders, 2016-2018)",
             ha="right", fontsize=8, color=GRAY)
    fig.savefig(OUT / name, dpi=160, bbox_inches="tight")
    plt.close(fig)

# ---- 1. Monthly revenue ----
monthly = m.groupby("purchase_month")["total_price"].sum().reset_index()
monthly = monthly[(monthly["purchase_month"] >= "2017-01") & (monthly["purchase_month"] <= "2018-08")]
fig, ax = plt.subplots(figsize=(9.5, 4.6))
ax.plot(monthly["purchase_month"], monthly["total_price"] / 1e6, color=NAVY, lw=2.5, marker="o", ms=4)
peak = monthly.loc[monthly["total_price"].idxmax()]
ax.annotate("Black Friday\nNov 2017", xy=(peak["purchase_month"], peak["total_price"] / 1e6),
            xytext=(-95, -38), textcoords="offset points", fontsize=10, color=ACCENT,
            arrowprops=dict(arrowstyle="->", color=ACCENT))
set_title(ax, "Revenue grew 8x in 2017, peaking on Black Friday")
style(ax, "Revenue from delivered orders, R$ millions per month")
ax.set_ylabel("R$ million")
ax.tick_params(axis="x", rotation=45)
savefig(fig, "01_revenue_trend.png")

# ---- 2. Top categories ----
cat = items.groupby("category_en")["price"].sum().sort_values(ascending=False).head(10) / 1e6
labels = {"health_beauty": "Health & Beauty", "watches_gifts": "Watches & Gifts",
          "bed_bath_table": "Bed, Bath & Table", "sports_leisure": "Sports & Leisure",
          "computers_accessories": "Computers & Accessories", "furniture_decor": "Furniture & Decor",
          "housewares": "Housewares", "cool_stuff": "Cool Stuff", "auto": "Auto",
          "garden_tools": "Garden & Tools", "telephony": "Telephony", "perfumery": "Perfumery",
          "baby": "Baby", "electronics": "Electronics", "stationery": "Stationery"}
fig, ax = plt.subplots(figsize=(9.5, 4.8))
names = [labels.get(c, c.replace("_", " ").title()) for c in cat.index][::-1]
ax.barh(names, cat.values[::-1], color=[ACCENT if i >= 7 else NAVY for i in range(10)])
for i, v in enumerate(cat.values[::-1]):
    ax.text(v + 0.02, i, f"R$ {v:.2f}M", va="center", fontsize=10, color=NAVY)
set_title(ax, "Top 10 product categories drive 62% of revenue")
style(ax, "Revenue by product category, R$ millions (2016-2018)")
ax.grid(axis="x", color="#f1f3f5", linewidth=1)
ax.grid(axis="y", visible=False)
savefig(fig, "02_top_categories.png")

# ---- 3. Late delivery vs reviews ----
m2 = m.dropna(subset=["delivery_days", "review_score"])
late = m2[m2["is_late"]]["review_score"]
ontime = m2[~m2["is_late"]]["review_score"]
fig, ax = plt.subplots(figsize=(9.5, 4.6))
x = np.arange(5)
w = 0.38
on_dist = [(ontime == s).mean() * 100 for s in range(1, 6)]
late_dist = [(late == s).mean() * 100 for s in range(1, 6)]
ax.bar(x - w / 2, on_dist, w, label=f"On time (avg {ontime.mean():.2f})", color=TEAL)
ax.bar(x + w / 2, late_dist, w, label=f"Late (avg {late.mean():.2f})", color=ACCENT)
ax.set_xticks(x, ["1 star", "2 stars", "3 stars", "4 stars", "5 stars"])
set_title(ax, "Late deliveries come with far lower ratings")
style(ax, "Review score distribution: 46% of late orders get 1 star vs 7% of on-time orders")
ax.set_ylabel("% of orders")
ax.legend(frameon=False)
savefig(fig, "03_late_vs_reviews.png")

# ---- 4. Delivery days distribution ----
fig, ax = plt.subplots(figsize=(9.5, 4.4))
m4 = m.dropna(subset=["delivery_days"])
days = m4["delivery_days"].clip(0, 40)
true_mean = m4["delivery_days"].mean()
ax.hist(days, bins=40, color=NAVY, alpha=0.85)
ax.axvline(true_mean, color=ACCENT, lw=2, ls="--")
ax.text(true_mean + 0.5, ax.get_ylim()[1] * 0.9, f"Average: {true_mean:.1f} days", color=ACCENT, fontsize=11)
set_title(ax, "Delivery takes 12.6 days on average")
style(ax, "Days from purchase to delivery (capped at 40 days)")
ax.set_xlabel("Delivery time (days)")
ax.set_ylabel("Orders")
savefig(fig, "04_delivery_days.png")

# ---- 5. Payment mix ----
paymix = m.groupby("main_payment_type")["order_id"].count().sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(7.5, 4.6))
colors = [NAVY, ACCENT, TEAL, GRAY][:len(paymix)]
wedges, _, autotexts = ax.pie(paymix.values, labels=None, colors=colors, autopct=lambda p: f"{p:.0f}%" if p >= 4 else "",
                              pctdistance=0.78, startangle=90,
                              wedgeprops=dict(width=0.42, edgecolor="white"))
for t in autotexts:
    t.set_color("white"); t.set_fontweight("bold")
nice = {"credit_card": "Credit card", "boleto": "Boleto", "voucher": "Voucher", "debit_card": "Debit card"}
ax.legend([nice.get(p, p) for p in paymix.index], frameon=False, loc="center left", bbox_to_anchor=(0.98, 0.5))
ax.set_title("Credit cards drive 75% of orders", loc="left", color=NAVY, fontsize=15, fontweight="bold")
ax.text(-1.25, 1.12, "68% of credit-card orders are paid in installments (avg 3.5x)", fontsize=10.5, color=GRAY)
savefig(fig, "05_payment_mix.png")

# ---- 6. Retention gap ----
cust_orders = m.groupby("customer_unique_id")["order_id"].count()
fig, ax = plt.subplots(figsize=(9.5, 4.2))
one = (cust_orders == 1).mean() * 100
two = (cust_orders == 2).mean() * 100
three = (cust_orders >= 3).mean() * 100
bars = ax.bar(["1 order", "2 orders", "3+ orders"], [one, two, three],
              color=[GRAY, NAVY, ACCENT], width=0.55)
for b, v in zip(bars, [one, two, three]):
    ax.text(b.get_x() + b.get_width() / 2, v + 1, f"{v:.1f}%", ha="center", fontsize=12, fontweight="bold", color=NAVY)
set_title(ax, "Only 3% of customers ordered again in the window")
style(ax, "Share of 93,358 unique customers by observed orders, Sep 2016 - Aug 2018")
ax.set_ylabel("% of customers")
ax.set_ylim(0, 105)
savefig(fig, "06_retention_gap.png")

print("charts:", sorted(p.name for p in OUT.glob("*.png")))
