"""
Olist E-Commerce - Business Analysis
====================================
Computes the KPIs and findings behind the dashboard and the report.
Outputs: analysis/stats.json (all numbers cited in the report).
"""
import pandas as pd
import numpy as np
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
CLEAN = BASE / "data" / "clean"

m = pd.read_csv(CLEAN / "orders_master.csv", parse_dates=[
    "order_purchase_timestamp", "order_delivered_customer_date",
    "order_estimated_delivery_date"])
items = pd.read_csv(CLEAN / "order_items_full.csv")

stats = {}

# ---------- headline KPIs ----------
rev = m["total_price"].sum()
stats["total_revenue_brl"] = round(rev, 2)
stats["total_orders"] = int(len(m))
stats["unique_customers"] = int(m["customer_unique_id"].nunique())
stats["avg_order_value_brl"] = round(rev / len(m), 2)
stats["date_range"] = [str(m["order_purchase_timestamp"].min().date()),
                       str(m["order_purchase_timestamp"].max().date())]

# ---------- monthly revenue trend (complete months only) ----------
monthly = m.groupby("purchase_month").agg(
    revenue=("total_price", "sum"), orders=("order_id", "count")).reset_index()
monthly = monthly[monthly["purchase_month"] < "2018-09"]  # partial tail month
monthly = monthly[monthly["revenue"] > 10000]  # drop 2016 stub months
monthly["mom_growth_pct"] = monthly["revenue"].pct_change() * 100
stats["monthly_revenue"] = monthly.round(2).to_dict("records")
first, last = monthly.iloc[0], monthly.iloc[-1]
stats["revenue_growth_first_last_pct"] = round(
    (last["revenue"] / first["revenue"] - 1) * 100, 1)

# ---------- top categories ----------
cat = items.groupby("category_en").agg(revenue=("price", "sum")).reset_index()
cat = cat.sort_values("revenue", ascending=False)
total_cat_rev = cat["revenue"].sum()
cat["share_pct"] = cat["revenue"] / total_cat_rev * 100
stats["top_categories"] = cat.head(10).round(2).to_dict("records")
stats["top5_category_share_pct"] = round(cat["share_pct"].head(5).sum(), 1)

# ---------- delivery performance ----------
m2 = m.dropna(subset=["delivery_days"])
stats["avg_delivery_days"] = round(m2["delivery_days"].mean(), 1)
stats["median_delivery_days"] = round(m2["delivery_days"].median(), 1)
late_rate = m2["is_late"].mean() * 100
stats["late_delivery_rate_pct"] = round(late_rate, 1)

# ---------- reviews vs delivery ----------
mr = m2.dropna(subset=["review_score"])
stats["avg_review_score"] = round(mr["review_score"].mean(), 2)
late = mr[mr["is_late"]]
ontime = mr[~mr["is_late"]]
stats["avg_review_late"] = round(late["review_score"].mean(), 2)
stats["avg_review_ontime"] = round(ontime["review_score"].mean(), 2)
stats["share_1star_when_late_pct"] = round((late["review_score"] == 1).mean() * 100, 1)
stats["share_1star_when_ontime_pct"] = round((ontime["review_score"] == 1).mean() * 100, 1)

# revenue at risk from late orders
stats["late_orders_revenue_brl"] = round(m2[m2["is_late"]]["total_price"].sum(), 2)

# ---------- payments ----------
paymix = m.groupby("main_payment_type").agg(
    orders=("order_id", "count"), revenue=("total_paid", "sum")).reset_index()
paymix["order_share_pct"] = paymix["orders"] / len(m) * 100
stats["payment_mix"] = paymix.round(2).to_dict("records")
cc = m[m["main_payment_type"] == "credit_card"]
stats["credit_card_installments_avg"] = round(cc["payment_installments"].mean(), 1)
stats["credit_card_multi_installment_share_pct"] = round(
    (cc["payment_installments"] > 1).mean() * 100, 1)

# ---------- customer retention ----------
first_order = m.groupby("customer_unique_id")["order_purchase_timestamp"].min()
m3 = m.merge(first_order.rename("first_order_date"), on="customer_unique_id")
m3["is_repeat"] = m3["order_purchase_timestamp"] > m3["first_order_date"]
cust_orders = m3.groupby("customer_unique_id")["order_id"].count()
stats["repeat_customer_rate_pct"] = round((cust_orders > 1).mean() * 100, 1)

# ---------- freight burden ----------
m4 = m[m["total_price"] > 0]
stats["avg_freight_share_of_order_pct"] = round(
    (m4["total_freight"] / m4["total_price"]).mean() * 100, 1)

# ---------- states ----------
st = m.groupby("customer_state").agg(revenue=("total_price", "sum")).reset_index()
st["share_pct"] = st["revenue"] / st["revenue"].sum() * 100
stats["top_states"] = st.sort_values("revenue", ascending=False).head(5).round(2).to_dict("records")

out = BASE / "analysis" / "stats.json"
out.write_text(json.dumps(stats, indent=2))
print(json.dumps(stats, indent=2)[:3500])
