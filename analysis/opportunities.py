"""
Olist E-Commerce - Business Opportunities (modeled impact)
=========================================================
Each opportunity = observed finding -> lever -> modeled annual impact.
All impacts are MODELS with explicit assumptions, computed on the last
12 complete months of data (Sep 2017 - Aug 2018), not realized gains.
Outputs: analysis/opportunities.json
"""
import pandas as pd
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
m = pd.read_csv(BASE / "data" / "clean" / "orders_master.csv",
                parse_dates=["order_purchase_timestamp", "order_delivered_customer_date",
                             "order_estimated_delivery_date"])

# last 12 complete months
y = m[(m["purchase_month"] >= "2017-09") & (m["purchase_month"] <= "2018-08")]
annual_rev = y["total_price"].sum()
annual_orders = len(y)
aov = y["total_price"].sum() / len(y)

opp = {"basis": {
    "window": "2017-09 to 2018-08 (last 12 complete months)",
    "annual_revenue_brl": round(annual_rev, 2),
    "annual_orders": int(annual_orders),
    "aov_brl": round(aov, 2)}}

# --- Opportunity 1: delivery reliability protects revenue & ratings ---
y2 = y.dropna(subset=["delivery_days"])
late = y2[y2["is_late"]]
late_rev = late["total_price"].sum()
opp["delivery_reliability"] = {
    "finding": f"{y2['is_late'].mean()*100:.1f}% of orders in the last 12 complete months arrived after "
               "the promised date (8.1% over the full dataset); "
               f"those orders averaged review {late['review_score'].mean():.2f} vs "
               f"{y2[~y2['is_late']]['review_score'].mean():.2f} for on-time, and "
               f"{(late['review_score']==1).mean()*100:.0f}% of late orders earned 1 star "
               f"(vs {(y2[~y2['is_late']]['review_score']==1).mean()*100:.0f}% on-time).",
    "revenue_touched_by_late_orders_brl": round(late_rev, 2),
    "lever": "Cut late rate from "
             f"{y2['is_late'].mean()*100:.1f}% to 4.0% via earlier carrier handoff and "
             "realistic promise dates on long routes.",
    "model": "Halving late deliveries protects the repeat purchase of roughly half the "
             "currently-late customers. Assumption: 10% of customers with a late order "
             "would otherwise have reordered at AOV within a year.",
    "modeled_annual_impact_brl": round(late_rev / aov * 0.5 * 0.10 * aov, 2),
}
opp["delivery_reliability"]["modeled_annual_impact_note"] = (
    "late_orders x 50% reduction x 10% reorder probability x AOV")

# --- Opportunity 2: retention / repeat purchase ---
cust_orders = m.groupby("customer_unique_id")["order_id"].count()
repeat_rate = (cust_orders > 1).mean()
target = 0.06
extra_customers = int((target - repeat_rate) * m["customer_unique_id"].nunique())
opp["retention"] = {
    "finding": f"Only {repeat_rate*100:.1f}% of {m['customer_unique_id'].nunique():,} customers "
               "placed a second observed order within the dataset window "
               "(Sep 2016 - Aug 2018); late cohorts had little time to reorder, "
               "so the true lifetime rate cannot be established from this window.",
    "lever": "Post-purchase journey: delivery tracking, review request, category-based "
             "cross-sell email 30 days after delivery.",
    "model": f"Lift the observed repeat rate from {repeat_rate*100:.1f}% to {target*100:.0f}% - "
             "a modest target for a retention program. "
             "Each newly-repeat customer buys once more at AOV.",
    "newly_repeat_customers": extra_customers,
    "modeled_annual_impact_brl": round(extra_customers * aov, 2),
}

# --- Opportunity 3: freight cost burden ---
y4 = y[y["total_price"] > 0]
freight_share = (y4["total_freight"] / y4["total_price"]).mean()
total_freight = y4["total_freight"].sum()
opp["freight"] = {
    "finding": f"Freight averages {freight_share*100:.1f}% of order value "
               f"(R$ {total_freight:,.0f} paid in freight per year).",
    "lever": "Renegotiate carrier rates and consolidate multi-item shipments on the "
             "highest-freight routes.",
    "model": "If merchants bear the freight charge, a 10% reduction is worth this much to margin; if customers bear it, the benefit is a lower total order cost (conversion lift not modeled). The dataset records freight as a charge on the order, so who bears the cost is an explicit assumption.",
    "modeled_annual_impact_brl": round(total_freight * 0.10, 2),
}

total_impact = sum(o["modeled_annual_impact_brl"] for k, o in opp.items() if k != "basis")
opp["total_modeled_annual_impact_brl"] = round(total_impact, 2)
opp["total_vs_annual_revenue_pct"] = round(total_impact / annual_rev * 100, 1)

# Overlap adjustment: opp1's protected reorders are a subset of opp2's newly-repeat
# customers (a late-order customer saved by better delivery could also be won by the
# retention program). Deduct opp1's cohort from opp2 so scenarios are additive.
opp1_reorders = opp["delivery_reliability"]["modeled_annual_impact_brl"] / aov
opp2_adj_customers = opp["retention"]["newly_repeat_customers"] - round(opp1_reorders)
opp2_adj_impact = opp2_adj_customers * aov
adj_total = (opp["delivery_reliability"]["modeled_annual_impact_brl"]
             + opp2_adj_impact
             + opp["freight"]["modeled_annual_impact_brl"])
opp["overlap_adjustment"] = {
    "note": "Delivery and retention scenarios overlap; opp1's ~{:.0f} protected reorders/yr "
            "are deducted from opp2's newly-repeat customers so the total is not double-counted.".format(opp1_reorders),
    "retention_adjusted_customers": int(opp2_adj_customers),
    "retention_adjusted_impact_brl": round(opp2_adj_impact, 2),
    "adjusted_total_annual_impact_brl": round(adj_total, 2),
    "adjusted_total_vs_annual_revenue_pct": round(adj_total / annual_rev * 100, 1),
    "total_basis": ("Combined scenario illustration: retention and delivery figures are modeled "
                    "revenue opportunities; the freight figure is conditional cost savings. "
                    "Distinct bases - not a single guaranteed annual benefit."),
}

out = BASE / "analysis" / "opportunities.json"
out.write_text(json.dumps(opp, indent=2))
print(json.dumps(opp, indent=2))
