"""Validation pass: join grain, denominators, payment-vs-item consistency, scenario overlap."""
import pandas as pd
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
RAW = BASE / "data" / "raw"
CLEAN = BASE / "data" / "clean"

m = pd.read_csv(CLEAN / "orders_master.csv")
items = pd.read_csv(CLEAN / "order_items_full.csv")
raw_orders = pd.read_csv(RAW / "olist_orders_dataset.csv")
raw_items = pd.read_csv(RAW / "olist_order_items_dataset.csv")
raw_pay = pd.read_csv(RAW / "olist_order_payments_dataset.csv")

v = {}
# 1. grain: one row per order in master?
v["master_rows"] = len(m)
v["master_unique_orders"] = m["order_id"].nunique()
v["grain_ok"] = bool(len(m) == m["order_id"].nunique())

# 2. delivered orders lost in item join
delivered = raw_orders[raw_orders["order_status"] == "delivered"]["order_id"].nunique()
with_items = m["order_id"].nunique()
v["delivered_orders"] = int(delivered)
v["delivered_with_items"] = int(with_items)
v["delivered_missing_items"] = int(delivered - with_items)

# 3. revenue: item price vs payment value (payments include freight)
v["revenue_item_price_brl"] = round(m["total_price"].sum(), 2)
v["revenue_payments_total_brl"] = round(m["total_paid"].sum(), 2)
v["freight_total_brl"] = round(m["total_freight"].sum(), 2)
v["definition"] = "revenue = sum(order_items.price), excludes freight; payments = price + freight"
diff = (m["total_paid"] - (m["total_price"] + m["total_freight"])).abs()
v["orders_payment_mismatch_gt_1brl"] = int((diff > 1).sum())
v["payment_mismatch_share_pct"] = round((diff > 1).mean() * 100, 2)

# 4. denominators
v["denom_late_rate"] = int(m["delivery_days"].notna().sum())
v["denom_review_stats"] = int((m["delivery_days"].notna() & m["review_score"].notna()).sum())
v["denom_repeat_rate"] = int(m["customer_unique_id"].nunique())

# 5. payment types present
v["payment_types"] = m["main_payment_type"].value_counts(dropna=False).to_dict()

# 6. scenario overlap: opp1 protected reorders vs opp2 newly-repeat customers
opp = json.loads((BASE / "analysis" / "opportunities.json").read_text())
aov = opp["basis"]["aov_brl"]
opp1_reorders = opp["delivery_reliability"]["modeled_annual_impact_brl"] / aov
opp2_customers = opp["retention"]["newly_repeat_customers"]
v["overlap_note"] = (
    f"opp1 models ~{opp1_reorders:.0f} protected reorders/yr; opp2 models {opp2_customers} "
    "newly-repeat customers/yr. A late-order customer recovered by better delivery could also "
    "be captured by the retention program, so the two scenarios are not fully additive.")
v["opp1_protected_reorders"] = round(opp1_reorders)
v["opp2_newly_repeat"] = opp2_customers
v["opp2_adjusted_excluding_opp1"] = opp2_customers - round(opp1_reorders)
v["opp2_adjusted_impact_brl"] = round((opp2_customers - round(opp1_reorders)) * aov, 2)
v["adjusted_total_impact_brl"] = round(
    opp["delivery_reliability"]["modeled_annual_impact_brl"]
    + v["opp2_adjusted_impact_brl"]
    + opp["freight"]["modeled_annual_impact_brl"], 2)

# 7. time coverage of opportunity basis
v["basis_window"] = opp["basis"]["window"]
v["basis_annual_revenue_brl"] = opp["basis"]["annual_revenue_brl"]

print(json.dumps(v, indent=2, default=str))
(BASE / "analysis" / "validation.json").write_text(json.dumps(v, indent=2, default=str))
