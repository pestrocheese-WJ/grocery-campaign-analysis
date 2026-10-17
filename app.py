"""
Grocery Sales & Campaign Effectiveness Dashboard
Data: The Complete Journey 2.0 (84.51°) — 2,469 households, one year of transactions.

Run:
    python prepare_data.py      # once, downloads the data
    python -m streamlit run app.py

All styling (flat pastel theme) lives in this file — no extra config needed.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

import analysis as an

st.set_page_config(page_title="Grocery Campaign Dashboard", page_icon="🛒", layout="wide")

# =============================================================== THEME (flat · pastel · clean font)
INK, MUTED, LINE, BG, CARD = "#2F3542", "#6B7280", "#ECE7E1", "#FBF8F4", "#FFFFFF"
SKY, PEACH, MINT, LAVENDER, BUTTER, ROSE = "#A7C7E7", "#F6C9B4", "#B8E0D2", "#CDB4DB", "#F5E1A4", "#F4B6C2"
SKY_DEEP, PEACH_DEEP = "#6F9BD1", "#E8956F"          # deeper tones for thin lines
SKY_STEPS = ["#DCE8F5", "#C2D7EE", "#A7C7E7", "#7FA9DA"]  # light -> deep, for ordered groups
CAMPAIGN_COLORS = {"Type A": ROSE, "Type B": SKY, "Type C": MINT}
FONT = "DM Sans, -apple-system, Segoe UI, sans-serif"

pio.templates["pastel_flat"] = go.layout.Template(layout=dict(
    font=dict(family=FONT, color=INK, size=13),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    colorway=[SKY, PEACH, MINT, LAVENDER, BUTTER, ROSE],
    margin=dict(t=16, r=8, b=8, l=8),
    xaxis=dict(showgrid=False, linecolor=LINE, ticks="", title_font=dict(color=MUTED, size=12)),
    yaxis=dict(gridcolor=LINE, zeroline=False, linecolor=LINE, ticks="", title_font=dict(color=MUTED, size=12)),
    legend=dict(bgcolor="rgba(0,0,0,0)", title_text="", orientation="h", yanchor="bottom", y=1.02, x=0),
    hoverlabel=dict(bgcolor=CARD, bordercolor=LINE, font=dict(family=FONT, color=INK)),
    bargap=0.35,
))
pio.templates.default = "plotly_white+pastel_flat"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');

/* Force the light pastel look even if the viewer's computer is in dark mode */
.stApp, [data-testid="stAppViewContainer"] {{ background:{BG}; color:{INK}; font-family:{FONT}; }}
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp li, .stApp label, .stApp summary,
[data-testid="stMarkdownContainer"] {{ color:{INK}; font-family:{FONT} !important; }}
.stApp h1 {{ font-weight:700 !important; letter-spacing:-0.02em; }}
.stApp h3 {{ font-weight:600 !important; font-size:1.15rem !important; margin-top:1.2rem; }}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{ color:{MUTED} !important; }}
header[data-testid="stHeader"] {{ background:transparent; }}
header[data-testid="stHeader"] * {{ color:{INK}; }}
[data-testid="stDecoration"] {{ display:none; }}

/* Flat: no shadows anywhere */
* {{ box-shadow:none !important; text-shadow:none !important; }}

/* Hero + findings */
.hero-eyebrow {{ display:inline-block; background:{BUTTER}; color:{INK}; font-size:.75rem; font-weight:600;
                padding:4px 10px; border-radius:999px; letter-spacing:.04em; }}
.findings {{ background:{CARD}; border:1px solid {LINE}; border-radius:16px; padding:20px 24px; margin:8px 0 20px; }}
.findings h4 {{ margin:0 0 12px; font-size:1rem; font-weight:700; }}
.finding {{ display:flex; gap:12px; align-items:flex-start; margin:10px 0; line-height:1.5; color:{INK}; }}
.finding .num {{ flex:0 0 28px; height:28px; border-radius:8px; display:flex; align-items:center;
                justify-content:center; font-weight:700; font-size:.85rem; color:{INK}; }}
.reco {{ background:{MINT}40; border-radius:12px; padding:12px 16px; margin-top:14px; color:{INK}; }}

/* KPI cards: flat pastel blocks, colour cycles across a row */
[data-testid="stMetric"] {{ border-radius:14px; padding:14px 18px; background:{SKY}55; }}
[data-testid="stHorizontalBlock"] > div:nth-child(5n+2) [data-testid="stMetric"] {{ background:{PEACH}66; }}
[data-testid="stHorizontalBlock"] > div:nth-child(5n+3) [data-testid="stMetric"] {{ background:{MINT}66; }}
[data-testid="stHorizontalBlock"] > div:nth-child(5n+4) [data-testid="stMetric"] {{ background:{LAVENDER}66; }}
[data-testid="stHorizontalBlock"] > div:nth-child(5n+5) [data-testid="stMetric"] {{ background:{BUTTER}77; }}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {{ color:{MUTED} !important; font-weight:500; font-size:.85rem; }}
[data-testid="stMetricValue"] {{ font-family:{FONT}; font-weight:700; color:{INK} !important; font-size:1.7rem; }}

/* Tabs as flat pills */
.stTabs [data-baseweb="tab-list"] {{ gap:6px; border-bottom:none; }}
.stTabs [data-baseweb="tab"] {{ background:{CARD}; border:1px solid {LINE}; border-radius:999px; padding:6px 16px; height:auto; }}
.stTabs [data-baseweb="tab"] p {{ color:{MUTED}; }}
.stTabs [aria-selected="true"] {{ background:{SKY}; border-color:{SKY}; }}
.stTabs [aria-selected="true"] p {{ color:{INK}; font-weight:600; }}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] {{ display:none; }}

/* Inputs, dropdowns, tags */
[data-baseweb="select"] > div {{ background:{CARD} !important; border:1px solid {LINE} !important; border-radius:10px; }}
[data-baseweb="select"] > div:focus-within {{ border-color:{SKY_DEEP} !important; }}
[data-baseweb="select"] *, [data-baseweb="select"] input {{ color:{INK} !important; }}
[data-baseweb="select"] svg {{ fill:{MUTED}; }}
[data-baseweb="tag"] {{ background:{SKY} !important; border-radius:8px; }}
[data-baseweb="tag"] * {{ color:{INK} !important; }}
[data-baseweb="popover"] > div {{ border:1px solid {LINE}; border-radius:10px; overflow:hidden; }}
[data-baseweb="popover"] ul, [data-baseweb="popover"] li, [role="listbox"] {{ background:{CARD} !important; color:{INK} !important; }}
[data-baseweb="popover"] li:hover, [role="option"][aria-selected="true"] {{ background:{BG} !important; }}

/* Expander */
[data-testid="stExpander"] details {{ background:{CARD}; border:1px solid {LINE}; border-radius:12px; }}
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * {{ color:{INK}; }}
[data-testid="stAlert"] {{ border-radius:12px; }}

/* Tables (st.table is HTML, so it follows our colours in light and dark mode) */
[data-testid="stTable"] table, .stTable table {{ background:{CARD}; color:{INK}; border-collapse:separate;
    border-spacing:0; border:1px solid {LINE}; border-radius:12px; overflow:hidden; width:100%; font-size:.9rem; }}
[data-testid="stTable"] th, .stTable th {{ background:{BG}; color:{MUTED}; font-weight:600; border:none;
    border-bottom:1px solid {LINE}; text-align:left; }}
[data-testid="stTable"] td, .stTable td {{ border:none; border-bottom:1px solid {LINE}; color:{INK}; }}
[data-testid="stTable"] tr:last-child td, .stTable tr:last-child td {{ border-bottom:none; }}
</style>
""", unsafe_allow_html=True)


def chart(fig, height=None):
    """Show a Plotly figure in the pastel theme (theme=None stops Streamlit overriding colours)."""
    fig.update_traces(selector=dict(type="bar"), marker_line_width=0)
    fig.update_traces(selector=dict(type="scatter"), line_width=3, marker_size=7)
    if height:
        fig.update_layout(height=height)
    st.plotly_chart(fig, use_container_width=True, theme=None, config={"displayModeBar": False})


def table(df, formats=None):
    """Show a small table with nicely formatted numbers; first column becomes the row label."""
    out = df.copy()
    for col, f in (formats or {}).items():
        out[col] = out[col].map(lambda v, f=f: "–" if pd.isna(v) else f.format(v))
    out = out.set_index(out.columns[0])
    out.index.name = ""
    st.table(out)


# =============================================================== DATA
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

# =============================================================== HEADER
st.markdown('<span class="hero-eyebrow">MARKETING ANALYTICS · PORTFOLIO PROJECT</span>', unsafe_allow_html=True)
st.title("Grocery Sales & Campaign Effectiveness")
st.caption("The Complete Journey 2.0 by 84.51° · 2,469 households · 1 year of transactions")

# Key findings as HTML so we control the look. &#36; = "$" (stops Streamlit reading it as a math formula)
st.markdown(f"""
<div class="findings">
  <h4>📌 Key findings</h4>
  <div class="finding"><span class="num" style="background:{SKY}">1</span>
    <div><b>Top 25% of households drive 61.9% of revenue</b>, mainly by shopping 9× more often
    (132 vs 14 trips/year), not by bigger baskets.</div></div>
  <div class="finding"><span class="num" style="background:{PEACH}">2</span>
    <div><b>Type A campaigns get 2× the redemption</b> (15% vs 7%) while reaching ~6.5× more households.</div></div>
  <div class="finding"><span class="num" style="background:{LAVENDER}">3</span>
    <div><b>Campaigns did not measurably lift spending.</b> Targeted households already spent &#36;237 more
    <i>before</i> campaigns; after adjusting, the average lift is −&#36;5.46 (≈0%).</div></div>
  <div class="reco"><b>Recommendation:</b> measure campaigns with random holdout groups instead of redemption rate,
    and target mid-tier households where visit frequency can grow.</div>
</div>
""", unsafe_allow_html=True)

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
    c5.metric("Discount share", f"{k['discount_share']:.1%}", help="Total discounts ÷ (revenue + discounts)")

    st.subheader("How do sales move week by week?")
    fig = px.line(an.weekly_sales(f), x="week", y="revenue", markers=True,
                  labels={"revenue": "Revenue", "week": "Week"}, color_discrete_sequence=[SKY_DEEP])
    fig.update_yaxes(tickprefix="$")
    chart(fig, height=320)

    left, right = st.columns(2)
    with left:
        st.subheader("Top departments")
        top_d = an.top_n(f, "department", 10).sort_values("revenue")
        fig = px.bar(top_d, x="revenue", y="department", orientation="h",
                     labels={"revenue": "Revenue", "department": ""}, color_discrete_sequence=[SKY])
        fig.update_xaxes(tickprefix="$")
        chart(fig, height=380)
    with right:
        st.subheader("Top product categories")
        top_c = an.top_n(f, "product_category", 10).sort_values("revenue")
        fig = px.bar(top_c, x="revenue", y="product_category", orientation="h",
                     labels={"revenue": "Revenue", "product_category": ""}, color_discrete_sequence=[PEACH])
        fig.update_xaxes(tickprefix="$")
        chart(fig, height=380)

# =============================================================== CUSTOMERS
with tab_cust:
    st.subheader("How concentrated is revenue?")
    ts = an.tier_share(hh)
    left, right = st.columns([2, 3])
    with left:
        fig = px.bar(ts, x="spend_tier", y="revenue_share", text_auto=".0%", color="spend_tier",
                     color_discrete_sequence=SKY_STEPS, labels={"spend_tier": "", "revenue_share": "Share of revenue"})
        fig.update_layout(showlegend=False)
        fig.update_yaxes(tickformat=".0%")
        fig.update_traces(textposition="outside", textfont=dict(color=INK, size=13), cliponaxis=False)
        chart(fig, height=340)
    with right:
        st.write("")
        table(ts[["spend_tier", "households", "revenue", "avg_baskets", "avg_basket", "revenue_share"]]
              .rename(columns={"spend_tier": "Tier", "households": "Households", "revenue": "Revenue",
                               "avg_baskets": "Trips / year", "avg_basket": "Avg basket",
                               "revenue_share": "Share of revenue"}),
              {"Households": "{:,}", "Revenue": "${:,.0f}", "Trips / year": "{:.0f}",
               "Avg basket": "${:.2f}", "Share of revenue": "{:.1%}"})

    st.subheader("Who spends more?")
    st.caption("Demographics are available for about a third of households, so read these as indicative.")
    demo_labels = {"Income": "income", "Age": "age", "Household size": "household_size",
                   "Number of kids": "kids_count", "Marital status": "marital_status"}
    demo_col = demo_labels[st.selectbox("Break down by", list(demo_labels))]
    sd = an.spend_by_demo(hh, demo_col)
    fig = px.bar(sd, x=demo_col, y="avg_spend", hover_data=["households"],
                 labels={"avg_spend": "Avg annual spend per household", demo_col: ""},
                 color_discrete_sequence=[MINT])
    fig.update_xaxes(type="category")
    fig.update_yaxes(tickprefix="$")
    chart(fig, height=340)

# =============================================================== CAMPAIGNS
with tab_camp:
    st.subheader("Which campaigns get customers to redeem?")
    fig = px.bar(camp, x="campaign_id", y="redemption_rate",  # camp is sorted by start date
                 color="campaign_type", color_discrete_map=CAMPAIGN_COLORS,
                 category_orders={"campaign_type": ["Type A", "Type B", "Type C"]},
                 hover_data=["households_targeted", "duration_days", "start_date"],
                 labels={"redemption_rate": "Households that redeemed", "campaign_id": "Campaign (by start date)"})
    fig.update_xaxes(type="category")
    fig.update_yaxes(tickformat=".0%")
    chart(fig, height=360)

    by_type = (camp.groupby("campaign_type")
                   .agg(campaigns=("campaign_id", "count"), targeted=("households_targeted", "mean"),
                        redemption=("redemption_rate", "mean"), duration=("duration_days", "mean"))
                   .reset_index())
    table(by_type.rename(columns={"campaign_type": "Type", "campaigns": "Campaigns",
                                  "targeted": "Avg households targeted", "redemption": "Avg redemption rate",
                                  "duration": "Avg duration (days)"}),
          {"Avg households targeted": "{:,.0f}", "Avg redemption rate": "{:.1%}", "Avg duration (days)": "{:.0f}"})

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

    before_after = pd.DataFrame({
        "period": ["Before", "During", "Before", "During"],
        "group": ["Targeted", "Targeted", "Not targeted", "Not targeted"],
        "avg_spend": [lift["targeted_pre"], lift["targeted_during"], lift["control_pre"], lift["control_during"]],
    })
    fig = px.line(before_after, x="period", y="avg_spend", color="group", markers=True,
                  color_discrete_map={"Targeted": PEACH_DEEP, "Not targeted": SKY_DEEP},
                  labels={"avg_spend": "Avg spend per household", "period": ""})
    fig.update_yaxes(tickprefix="$")
    chart(fig, height=320)
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

    money = "${:,.2f}"
    by_type_lift = (ok.groupby("campaign_type")
                      .agg(campaigns=("campaign_id", "count"), pre_gap=("pre_gap", "mean"),
                           naive_gap=("naive_gap", "mean"), did_lift=("did_lift", "mean"),
                           lift_pct=("lift_pct", "mean"))
                      .reset_index())
    table(by_type_lift.rename(columns={"campaign_type": "Type", "campaigns": "Campaigns",
                                       "pre_gap": "Gap before", "naive_gap": "Gap during",
                                       "did_lift": "Estimated lift", "lift_pct": "Lift %"}),
          {"Gap before": money, "Gap during": money, "Estimated lift": money, "Lift %": "{:.1%}"})

    with st.expander("See all campaigns"):
        all_c = lifts[["campaign_id", "campaign_type", "start", "households_targeted",
                       "pre_gap", "naive_gap", "did_lift", "lift_pct"]].copy()
        all_c["campaign_id"] = "Campaign " + all_c["campaign_id"].astype(str)
        table(all_c.rename(columns={"campaign_id": "Campaign", "campaign_type": "Type", "start": "Start",
                                    "households_targeted": "Targeted", "pre_gap": "Gap before",
                                    "naive_gap": "Gap during", "did_lift": "Estimated lift", "lift_pct": "Lift %"}),
              {"Targeted": "{:,}", "Gap before": money, "Gap during": money,
               "Estimated lift": money, "Lift %": "{:.1%}"})
        st.caption("– = no full 'before' period in the data, so lift can't be estimated.")

    st.subheader("Do coupon users spend more?")
    table(an.coupon_user_comparison(hh, d["coupon_redemptions"])
            .rename(columns={"group": "Group", "households": "Households", "avg_spend": "Avg annual spend",
                             "avg_baskets": "Trips / year", "avg_basket": "Avg basket"}),
          {"Households": "{:,}", "Avg annual spend": "${:,.0f}", "Trips / year": "{:.0f}", "Avg basket": "${:.2f}"})
    st.caption("Correlation, not causation: loyal high-spenders are also more likely to clip coupons.")