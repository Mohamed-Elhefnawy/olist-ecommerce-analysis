"""
Olist E-Commerce - Data Cleaning & Preparation
==============================================
Cleans the 8 raw Olist CSVs and produces analysis-ready tables.

Cleaning decisions (documented for the project README):
1. Parse all timestamp columns to datetime.
2. Keep only orders with status 'delivered' for revenue analysis
   (canceled/unavailable orders have no completed payment value).
3. Order items: aggregate to order level (items count, total price, total freight).
4. Payments: aggregate to order level (total paid, main payment type, installments).
5. Reviews: keep the latest review per order.
6. Products: translate Portuguese category names to English; fill missing as 'unknown'.
7. Delivery metrics computed only where actual delivery date exists.
"""
import pandas as pd
import numpy as np
from pathlib import Path

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT = Path(__file__).resolve().parents[1] / "data" / "clean"
OUT.mkdir(parents=True, exist_ok=True)

TS_COLS = [
    "order_purchase_timestamp", "order_approved_at",
    "order_delivered_carrier_date", "order_delivered_customer_date",
    "order_estimated_delivery_date",
]

def load(name):
    return pd.read_csv(RAW / name)

# ---------- orders ----------
orders = load("olist_orders_dataset.csv")
n_raw_orders = len(orders)
for c in TS_COLS:
    orders[c] = pd.to_datetime(orders[c], errors="coerce")
orders = orders.drop_duplicates(subset="order_id")
status_counts = orders["order_status"].value_counts()
orders_d = orders[orders["order_status"] == "delivered"].copy()

# delivery metrics
orders_d["delivery_days"] = (
    orders_d["order_delivered_customer_date"] - orders_d["order_purchase_timestamp"]
).dt.total_seconds() / 86400
orders_d["late_vs_estimate_days"] = (
    orders_d["order_delivered_customer_date"] - orders_d["order_estimated_delivery_date"]
).dt.total_seconds() / 86400
orders_d["is_late"] = orders_d["late_vs_estimate_days"] > 0
orders_d["purchase_month"] = orders_d["order_purchase_timestamp"].dt.to_period("M").astype(str)

# ---------- items ----------
items = load("olist_order_items_dataset.csv")
items = items.drop_duplicates()
items_agg = (
    items.groupby("order_id")
    .agg(n_items=("order_item_id", "count"),
         total_price=("price", "sum"),
         total_freight=("freight_value", "sum"))
    .reset_index()
)

# ---------- payments ----------
pay = load("olist_order_payments_dataset.csv")
pay = pay.drop_duplicates()
pay_main = (
    pay.sort_values("payment_value", ascending=False)
    .drop_duplicates(subset="order_id")
    [["order_id", "payment_type", "payment_installments"]]
    .rename(columns={"payment_type": "main_payment_type"})
)
pay_agg = pay.groupby("order_id").agg(total_paid=("payment_value", "sum")).reset_index()
pay_agg = pay_agg.merge(pay_main, on="order_id", how="left")

# ---------- reviews (latest per order) ----------
rev = load("olist_order_reviews_dataset.csv")
rev["review_creation_date"] = pd.to_datetime(rev["review_creation_date"], errors="coerce")
rev = rev.sort_values("review_creation_date").drop_duplicates(subset="order_id", keep="last")
rev = rev[["order_id", "review_score"]]

# ---------- products + translation ----------
prod = load("olist_products_dataset.csv")
trans = load("product_category_name_translation.csv")
prod = prod.merge(trans, on="product_category_name", how="left")
prod["category_en"] = prod["product_category_name_english"].fillna("unknown")
prod = prod[["product_id", "category_en"]]

# ---------- customers / sellers ----------
cust = load("olist_customers_dataset.csv")[["customer_id", "customer_unique_id", "customer_state"]]
sellers = load("olist_sellers_dataset.csv")[["seller_id", "seller_state"]]

# ---------- master order-level table ----------
master = (
    orders_d
    .merge(items_agg, on="order_id", how="left")
    .merge(pay_agg, on="order_id", how="left")
    .merge(rev, on="order_id", how="left")
    .merge(cust, on="customer_id", how="left")
)

# order-item level table with categories (for category analysis)
items_full = items.merge(prod, on="product_id", how="left").merge(
    orders_d[["order_id", "purchase_month", "is_late"]], on="order_id", how="inner"
)

# data-quality notes
dq = {
    "raw_orders": int(n_raw_orders),
    "order_status_counts": status_counts.to_dict(),
    "delivered_orders_kept": int(len(orders_d)),
    "orders_missing_delivery_date": int(orders_d["order_delivered_customer_date"].isna().sum()),
    "orders_missing_payment": int(master["total_paid"].isna().sum()),
    "orders_missing_review": int(master["review_score"].isna().sum()),
    "duplicate_order_ids_removed": int(n_raw_orders - len(orders)),
    "products_without_category_translation": int(
        (prod["category_en"] == "unknown").sum()
    ),
}

master.to_csv(OUT / "orders_master.csv", index=False)
items_full.to_csv(OUT / "order_items_full.csv", index=False)
cust.to_csv(OUT / "customers.csv", index=False)
sellers.to_csv(OUT / "sellers.csv", index=False)

import json
print(json.dumps(dq, indent=2))
print("\nMaster shape:", master.shape)
print("Items full shape:", items_full.shape)
