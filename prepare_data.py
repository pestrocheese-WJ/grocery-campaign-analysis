"""
Step 1: Download The Complete Journey (84.51°) data and save it as Parquet files.

Run once:
    pip install pyreadr pandas pyarrow requests
    python prepare_data.py

Creates a data/ folder with 7 Parquet files (about 30 MB in total),
small enough to push to GitHub and deploy on Streamlit Community Cloud.

Source: https://github.com/bradleyboehmke/completejourney (license CC0)
"""

import tempfile
from pathlib import Path

import pandas as pd
import pyreadr
import requests

BASE = "https://github.com/bradleyboehmke/completejourney/raw/master/data/"
FILES = {
    "transactions": "transactions.rds",          # full data, 1.47M rows
    "products": "products.rda",
    "demographics": "demographics.rda",
    "campaigns": "campaigns.rda",
    "campaign_descriptions": "campaign_descriptions.rda",
    "coupons": "coupons.rda",
    "coupon_redemptions": "coupon_redemptions.rda",
}

OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)

for name, filename in FILES.items():
    print(f"Downloading {filename} ...")
    resp = requests.get(BASE + filename, timeout=300)
    resp.raise_for_status()

    with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as tmp:
        tmp.write(resp.content)
        tmp_path = tmp.name

    result = pyreadr.read_r(tmp_path)
    df = next(iter(result.values()))  # each file holds one table

    # Ordered factors (age, income, campaign_type) -> plain text, keeping missing values as missing
    for col in df.select_dtypes(include="category").columns:
        df[col] = df[col].astype(object)

    df.to_parquet(OUT / f"{name}.parquet", index=False)
    print(f"  saved {name}.parquet  ({len(df):,} rows, {df.shape[1]} columns)")
    Path(tmp_path).unlink()

print("\nDone. Next: streamlit run app.py")
