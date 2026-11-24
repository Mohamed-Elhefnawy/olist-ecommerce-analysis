"""Download the Olist Brazilian E-Commerce dataset (raw CSVs) into data/raw/.

Canonical source: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
This script pulls from a public GitHub mirror of the same CSVs, so no Kaggle
login is needed. If the mirror ever goes down, download the dataset from the
Kaggle link above and place the same 8 CSV files in data/raw/.

Verified working on 24 Nov 2026.
"""
import sys
import urllib.request
from pathlib import Path

BASE = "https://raw.githubusercontent.com/HariBabu0923/Olist-Brazilian-E-Commerce-Analysis-Project/main/dataset/raw/"
FILES = [
    "olist_customers_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
]

out = Path(__file__).parent / "data" / "raw"
out.mkdir(parents=True, exist_ok=True)

for name in FILES:
    dest = out / name
    if dest.exists() and dest.stat().st_size > 0:
        print(f"skip  {name} (already present)")
        continue
    url = BASE + name
    print(f"fetch {name} ...", flush=True)
    try:
        urllib.request.urlretrieve(url, dest)
    except Exception as exc:
        print(f"FAILED {name}: {exc}")
        print("Fallback: download from https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce")
        sys.exit(1)
    print(f"  ok  {dest.stat().st_size/1e6:.1f} MB")

print("Done. Next: python python/clean_data.py")
