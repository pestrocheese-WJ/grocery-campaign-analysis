"""
Analysis logic for The Complete Journey project (pure pandas, no Streamlit).
Keeping the analysis separate from the app makes it easy to test and reuse in a notebook.
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"

INCOME_ORDER = ["Under 15K", "15-24K", "25-34K", "35-49K", "50-74K", "75-99K",
                "100-124K", "125-149K", "150-174K", "175-199K", "200-249K", "250K+"]
AGE_ORDER = ["19-24", "25-34", "35-44", "45-54", "55-64", "65+"]


# ---------------------------------------------------------------- loading
def load_all(data_dir: Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    names = ["transactions", "products", "demographics", "campaigns",
             "campaign_descriptions", "coupons", "coupon_redemptions"]
    d = {n: pd.read_parquet(data_dir / f"{n}.parquet") for n in names}
    return prepare(d)


def prepare(d: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Parse dates, add helper columns and join product info onto transactions."""
    tx = d["transactions"]
    tx["transaction_timestamp"] = pd.to_datetime(tx["transaction_timestamp"])
    tx["date"] = tx["transaction_timestamp"].dt.normalize()
    tx["total_disc"] = tx["retail_disc"] + tx["coupon_disc"] + tx["coupon_match_disc"]
    d["transactions"] = tx.merge(
        d["products"][["product_id", "department", "product_category", "brand"]],
        on="product_id", how="left")

    cd = d["campaign_descriptions"]
    cd["start_date"] = pd.to_datetime(cd["start_date"])
    cd["end_date"] = pd.to_datetime(cd["end_date"])
    d["coupon_redemptions"]["redemption_date"] = pd.to_datetime(
        d["coupon_redemptions"]["redemption_date"])
    return d


# ---------------------------------------------------------------- sales
def kpis(tx: pd.DataFrame) -> dict:
    baskets = tx["basket_id"].nunique()
    revenue = tx["sales_value"].sum()
    return {
        "revenue": revenue,
        "households": tx["household_id"].nunique(),
        "baskets": baskets,
        "avg_basket": revenue / baskets if baskets else 0,
        "discount_share": tx["total_disc"].sum() / (revenue + tx["total_disc"].sum()) if revenue else 0,
    }


def weekly_sales(tx: pd.DataFrame) -> pd.DataFrame:
    return (tx.groupby("week")
              .agg(revenue=("sales_value", "sum"), baskets=("basket_id", "nunique"))
              .reset_index())


def top_n(tx: pd.DataFrame, by: str, n: int = 10) -> pd.DataFrame:
    out = (tx.groupby(by)
             .agg(revenue=("sales_value", "sum"), households=("household_id", "nunique"))
             .sort_values("revenue", ascending=False)
             .head(n)
             .reset_index())
    out["revenue_share"] = out["revenue"] / tx["sales_value"].sum()
    return out


# ---------------------------------------------------------------- customers
def household_summary(tx: pd.DataFrame, demo: pd.DataFrame) -> pd.DataFrame:
    hh = (tx.groupby("household_id")
            .agg(total_spend=("sales_value", "sum"),
                 baskets=("basket_id", "nunique"),
                 last_date=("date", "max"))
            .reset_index())
    hh["avg_basket"] = hh["total_spend"] / hh["baskets"]
    hh["spend_tier"] = pd.qcut(hh["total_spend"].rank(method="first"), 4,
                               labels=["Bottom 25%", "Lower-mid 25%", "Upper-mid 25%", "Top 25%"])
    return hh.merge(demo, on="household_id", how="left")


def tier_share(hh: pd.DataFrame) -> pd.DataFrame:
    out = (hh.groupby("spend_tier", observed=True)
             .agg(households=("household_id", "count"), revenue=("total_spend", "sum"),
                  avg_baskets=("baskets", "mean"), avg_basket=("avg_basket", "mean"))
             .reset_index())
    out["revenue_share"] = out["revenue"] / out["revenue"].sum()
    return out


def spend_by_demo(hh: pd.DataFrame, col: str) -> pd.DataFrame:
    """Average annual spend per household by a demographic column (households with demographics only)."""
    out = (hh.dropna(subset=[col])
             .groupby(col)
             .agg(households=("household_id", "count"), avg_spend=("total_spend", "mean"))
             .reset_index())
    order = {"income": INCOME_ORDER, "age": AGE_ORDER}.get(col)
    if order:
        out[col] = pd.Categorical(out[col], categories=order, ordered=True)
        out = out.sort_values(col)
    return out


# ---------------------------------------------------------------- campaigns & coupons
def campaign_summary(campaigns, desc, redemptions) -> pd.DataFrame:
    targeted = campaigns.groupby("campaign_id")["household_id"].nunique().rename("households_targeted")
    redeemed = (redemptions.groupby("campaign_id")
                .agg(households_redeemed=("household_id", "nunique"),
                     coupons_redeemed=("coupon_upc", "count")))
    out = desc.set_index("campaign_id").join(targeted).join(redeemed).fillna(
        {"households_redeemed": 0, "coupons_redeemed": 0}).reset_index()
    out["duration_days"] = (out["end_date"] - out["start_date"]).dt.days + 1
    out["redemption_rate"] = out["households_redeemed"] / out["households_targeted"]
    return out.sort_values("start_date")


def campaign_lift(tx, campaigns, desc, campaign_id) -> dict:
    """
    Difference-in-differences: did targeted households increase spending during the
    campaign MORE than non-targeted households did over the same period?

    Comparing targeted vs non-targeted during the campaign alone is misleading,
    because the retailer usually targets customers who already spend more.
    """
    row = desc.loc[desc["campaign_id"] == campaign_id].iloc[0]
    data_start, data_end = tx["date"].min(), tx["date"].max()
    # Clip the campaign to the period the data actually covers
    start, end = max(row["start_date"], data_start), min(row["end_date"], data_end)
    length = end - start
    pre_start, pre_end = start - length - pd.Timedelta(days=1), start - pd.Timedelta(days=1)
    # DiD needs a full "before" window inside the data; otherwise the before-spend is 0 and the result is meaningless
    valid = pre_start >= data_start

    targeted_ids = set(campaigns.loc[campaigns["campaign_id"] == campaign_id, "household_id"])
    all_ids = tx["household_id"].unique()

    def avg_spend(ids, s, e):
        window = tx[(tx["date"] >= s) & (tx["date"] <= e) & tx["household_id"].isin(ids)]
        per_hh = window.groupby("household_id")["sales_value"].sum().reindex(list(ids), fill_value=0)
        return per_hh.mean() if len(per_hh) else 0.0

    control_ids = [h for h in all_ids if h not in targeted_ids]
    t_pre, t_during = avg_spend(targeted_ids, pre_start, pre_end), avg_spend(targeted_ids, start, end)
    c_pre, c_during = avg_spend(control_ids, pre_start, pre_end), avg_spend(control_ids, start, end)

    return {
        "campaign_type": row["campaign_type"], "start": start, "end": end,
        "pre_start": pre_start, "pre_end": pre_end,
        "n_targeted": len(targeted_ids), "n_control": len(control_ids),
        "targeted_pre": t_pre, "targeted_during": t_during,
        "control_pre": c_pre, "control_during": c_during,
        "naive_gap": t_during - c_during,
        "did_lift": (t_during - t_pre) - (c_during - c_pre) if valid else float("nan"),
        "valid": valid,
    }


def all_campaign_lifts(tx, campaigns, desc) -> pd.DataFrame:
    """Run campaign_lift for every campaign; returns one row per campaign."""
    rows = []
    for cid in desc["campaign_id"]:
        r = campaign_lift(tx, campaigns, desc, cid)
        rows.append({
            "campaign_id": cid, "campaign_type": r["campaign_type"],
            "start": r["start"].date(), "households_targeted": r["n_targeted"],
            "pre_gap": r["targeted_pre"] - r["control_pre"],
            "naive_gap": r["naive_gap"], "did_lift": r["did_lift"],
            "lift_pct": r["did_lift"] / r["targeted_pre"] if r["valid"] and r["targeted_pre"] else float("nan"),
            "valid": r["valid"],
        })
    return pd.DataFrame(rows)


def coupon_user_comparison(hh: pd.DataFrame, redemptions: pd.DataFrame) -> pd.DataFrame:
    users = set(redemptions["household_id"])
    tmp = hh.assign(group=hh["household_id"].isin(users).map(
        {True: "Redeemed a coupon", False: "Never redeemed"}))
    return (tmp.groupby("group")
               .agg(households=("household_id", "count"), avg_spend=("total_spend", "mean"),
                    avg_baskets=("baskets", "mean"), avg_basket=("avg_basket", "mean"))
               .reset_index())