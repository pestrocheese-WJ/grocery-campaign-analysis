"""
Grocery Sales & Campaign Effectiveness Dashboard
Data: The Complete Journey 2.0 (84.51°) — 2,469 households, one year of transactions.

Run:
    python prepare_data.py      # once, downloads the data
    streamlit run app.py
"""

import pandas as pd
import plotly.express as px
import streamlit as st

import analysis as an

st.set_page_config(page_title="Grocery Campaign Dashboard", page_icon="🛒", layout="wide")


@st.cache_data(show_spinner="Loading data...")
def load():
    d = an.load_all()
    hh = an.household_summary(d["transactions"], d["demographics"])
    camp = an.campaign_summary(d["campaigns"], d["campaign_descriptions"], d["coupon_redemptions"])
    return d, hh, camp


@st.cache_data(show_spinner="Estimating lift for all campaigns...")
def all_lifts():
    d, _, _ = load()
    return an.all_campaign_lifts(d["transactions"], d["campaigns"], d["campaign_descriptions"])


try:
    d, hh, camp = load()
except FileNotFoundError:
    st.error("Data not found. Run `python prepare_data.py` first to download it into the data/ folder.")
    st.stop()

tx = d["transactions"]

st.title("🛒 Grocery Sales & Campaign Effectiveness")
st.caption("The Complete Journey 2.0 by 84.51° · 2,469 households · 1 year of transactions")

# ✏️ Replace these with YOUR findings once you've explored the data
with st.container(border=True):
    st.markdown("**📌 Key findings**")
    st.markdown(
        "1. **Top 25% of households drive 61.9% of revenue**, mainly by shopping 9× more often (132 vs 14 trips/year), not by bigger baskets.\n"
        "2. **Type A campaigns get 2× the redemption** (15% vs 7%) while reaching ~6.5× more households.\n"
        "3. **Campaigns did not measurably lift spending.** Targeted households already spent $237 more *before* campaigns; "
        "after adjusting, the average lift is −$5.46 (≈0%).\n\n"
        "**Recommendation:** measure campaigns with random holdout groups instead of redemption rate, "
        "and target mid-tier households where visit frequency can grow."
    )

tab_sales, tab_cust, tab_camp = st.tabs(["📈 Sales", "👥 Customers", "🎯 Campaigns & Coupons"])

# =============================================================== SALES
with tab_sales:
    depts = sorted(tx["department"].dropna().unique())
    pick = st.multiselect("Filter departments", depts, placeholder="All departments")
    f = tx[tx["department"].isin(pick)] if pick else tx

    k = an.kpis(f)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Revenue", f"${k['revenue']:,.0f}")
    c2.metric("Households", f"{k['households']:,}")
    c3.metric("Baskets", f"{k['baskets']:,}")
    c4.metric("Avg basket", f"${k['avg_basket']:,.2f}")
    c5.metric("Discount share", f"{k['discount_share']:.1%}",
              help="Total discounts ÷ (revenue + discounts)")

    st.subheader("How do sales move week by week?")
    st.plotly_chart(px.line(an.weekly_sales(f), x="week", y="revenue", markers=True,
                            labels={"revenue": "Revenue ($)", "week": "Week"}),
                    use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.subheader("Top departments")
        top_d = an.top_n(f, "department", 10).sort_values("revenue")
        st.plotly_chart(px.bar(top_d, x="revenue", y="department", orientation="h",
                               labels={"revenue": "Revenue ($)", "department": ""}),
                        use_container_width=True)
    with right:
        st.subheader("Top product categories")
        top_c = an.top_n(f, "product_category", 10).sort_values("revenue")
        st.plotly_chart(px.bar(top_c, x="revenue", y="product_category", orientation="h",
                               labels={"revenue": "Revenue ($)", "product_category": ""}),
                        use_container_width=True)

# =============================================================== CUSTOMERS
with tab_cust:
    st.subheader("How concentrated is revenue?")
    ts = an.tier_share(hh)
    left, right = st.columns([2, 3])
    with left:
        st.plotly_chart(px.bar(ts, x="spend_tier", y="revenue_share", text_auto=".0%",
                               labels={"spend_tier": "", "revenue_share": "Share of revenue"}),
                        use_container_width=True)
    with right:
        show = ts.copy()
        show["revenue_share"] = (show["revenue_share"] * 100).round(1)
        show["avg_baskets"] = show["avg_baskets"].round(0)
        show["avg_basket"] = show["avg_basket"].round(2)
        st.dataframe(show.rename(columns={"spend_tier": "tier", "revenue_share": "revenue %",
                                          "avg_baskets": "trips / year", "avg_basket": "avg basket $"}),
                     hide_index=True, use_container_width=True)

    st.subheader("Who spends more?")
    st.caption("Demographics are available for about a third of households, so read these as indicative.")
    demo_col = st.radio("Break down by", ["income", "age", "household_size", "kids_count", "marital_status"],
                        horizontal=True)
    sd = an.spend_by_demo(hh, demo_col)
    st.plotly_chart(px.bar(sd, x=demo_col, y="avg_spend", hover_data=["households"],
                           labels={"avg_spend": "Avg annual spend per household ($)"}),
                    use_container_width=True)

# =============================================================== CAMPAIGNS
with tab_camp:
    st.subheader("Which campaigns get customers to redeem?")
    fig = px.bar(camp, x="campaign_id", y="redemption_rate",  # camp is sorted by start date
                 color="campaign_type", hover_data=["households_targeted", "duration_days", "start_date"],
                 labels={"redemption_rate": "Households that redeemed", "campaign_id": "Campaign (by start date)"})
    fig.update_xaxes(type="category")
    fig.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig, use_container_width=True)

    by_type = (camp.groupby("campaign_type")
                   .agg(campaigns=("campaign_id", "count"),
                        avg_households_targeted=("households_targeted", "mean"),
                        avg_redemption_rate=("redemption_rate", "mean"),
                        avg_duration_days=("duration_days", "mean"))
                   .round(2).reset_index())
    st.dataframe(by_type, hide_index=True, use_container_width=True)

    st.subheader("Did a campaign actually increase spending?")
    st.markdown(
        "Targeted households usually spent more **before** the campaign too, so a simple "
        "targeted-vs-not comparison overstates the effect. This uses **difference-in-differences**: "
        "the change in spend for targeted households minus the change for everyone else."
    )
    cid = st.selectbox("Campaign", camp["campaign_id"].tolist(),
                       format_func=lambda c: f"Campaign {c} ({camp.set_index('campaign_id').loc[c, 'campaign_type']})")
    lift = an.campaign_lift(tx, d["campaigns"], d["campaign_descriptions"], cid)

    c1, c2, c3 = st.columns(3)
    c1.metric("Households targeted", f"{lift['n_targeted']:,}")
    c2.metric("Naive gap (during campaign)", f"${lift['naive_gap']:,.2f}",
              help="Targeted minus non-targeted avg spend during the campaign")
    c3.metric("Estimated lift (DiD)", f"${lift['did_lift']:,.2f}" if lift["valid"] else "n/a",
              help="Extra spend per targeted household after removing the pre-existing gap")
    if not lift["valid"]:
        st.warning("This campaign starts too close to the beginning of the data, so there is no full "
                   "'before' period to compare against. The lift can't be estimated for it.")

    chart = pd.DataFrame({
        "period": ["Before", "During", "Before", "During"],
        "group": ["Targeted", "Targeted", "Not targeted", "Not targeted"],
        "avg_spend": [lift["targeted_pre"], lift["targeted_during"],
                      lift["control_pre"], lift["control_during"]],
    })
    st.plotly_chart(px.line(chart, x="period", y="avg_spend", color="group", markers=True,
                            labels={"avg_spend": "Avg spend per household ($)", "period": ""}),
                    use_container_width=True)
    st.caption(f"Campaign: {lift['start']:%d %b %Y} – {lift['end']:%d %b %Y} · "
               f"Comparison window: {lift['pre_start']:%d %b} – {lift['pre_end']:%d %b %Y} (same length, just before). "
               "Campaigns that start in the first weeks of the data have little or no 'before' period.")

    st.subheader("Lift for every campaign")
    lifts = all_lifts()
    ok = lifts[lifts["valid"]]
    c1, c2, c3 = st.columns(3)
    c1.metric("Campaigns with a valid estimate", f"{len(ok)} of {len(lifts)}")
    c2.metric("Avg pre-existing gap", f"${ok['pre_gap'].mean():,.2f}",
              help="How much more targeted households already spent BEFORE the campaign")
    c3.metric("Avg estimated lift (DiD)", f"${ok['did_lift'].mean():,.2f}")
    by_type_lift = (ok.groupby("campaign_type")
                      .agg(campaigns=("campaign_id", "count"), avg_pre_gap=("pre_gap", "mean"),
                           avg_naive_gap=("naive_gap", "mean"), avg_did_lift=("did_lift", "mean"),
                           avg_lift_pct=("lift_pct", "mean"))
                      .reset_index())
    by_type_lift["avg_lift_pct"] = (by_type_lift["avg_lift_pct"] * 100).round(1)
    st.dataframe(by_type_lift.round(2).rename(columns={"avg_lift_pct": "avg lift %"}),
                 hide_index=True, use_container_width=True)
    with st.expander("See all campaigns"):
        show = lifts.copy()
        show["lift_pct"] = (show["lift_pct"] * 100).round(1)
        st.dataframe(show.round(2).rename(columns={"lift_pct": "lift %"}),
                     hide_index=True, use_container_width=True)

    st.subheader("Do coupon users spend more?")
    st.dataframe(an.coupon_user_comparison(hh, d["coupon_redemptions"]).round(2),
                 hide_index=True, use_container_width=True)
    st.caption("Correlation, not causation: loyal high-spenders are also more likely to clip coupons.")