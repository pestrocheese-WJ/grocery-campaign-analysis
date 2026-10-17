"""
Grocery Sales & Campaign Effectiveness Dashboard
Data: The Complete Journey 2.0 (84.51°) — 2,469 households, one year of transactions.

Run:
    python prepare_data.py      # once, downloads the data
    python -m streamlit run app.py

Style: flat dashboard — deep teal sidebar, white bordered cards, apricot and sage accents,
Plus Jakarta Sans throughout. No shadows, no gradients, no emoji.
"""

from contextlib import contextmanager

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

import analysis as an

st.set_page_config(page_title="Grocery Campaign Dashboard", layout="wide", initial_sidebar_state="expanded")

# =============================================================== THEME
DARK, DARK_SOFT = "#1F3B3D", "#2C4D4F"                 # deep teal: sidebar, main bars, lines
ACCENT, ACCENT_LIGHT = "#E98A5B", "#FBE3D6"            # apricot: highlights
SAGE, SAGE_LIGHT = "#6FA67A", "#E1EEE2"                # sage: secondary
BUTTER_LIGHT = "#FBF0D0"
BG, CARD, LINE = "#F5F2ED", "#FFFFFF", "#E8E3DC"
INK, MUTED = "#1F2A2B", "#6F7776"
STEPS = ["#D5E1E0", "#A6BFBE", "#5E8483", DARK]        # light -> dark, for ordered groups
CAMPAIGN_COLORS = {"Type A": ACCENT, "Type B": DARK, "Type C": SAGE}
FONT = "'Plus Jakarta Sans', -apple-system, 'Segoe UI', sans-serif"

pio.templates["flat_teal"] = go.layout.Template(layout=dict(
    font=dict(family=FONT, color=INK, size=12),
    paper_bgcolor=CARD, plot_bgcolor=CARD,
    colorway=[DARK, ACCENT, SAGE],
    margin=dict(t=10, r=10, b=10, l=10),
    xaxis=dict(showgrid=False, linecolor=LINE, ticks="", title_font=dict(color=MUTED, size=11),
               tickfont=dict(color=MUTED)),
    yaxis=dict(gridcolor=LINE, zeroline=False, linecolor=LINE, ticks="", title_font=dict(color=MUTED, size=11),
               tickfont=dict(color=MUTED)),
    legend=dict(bgcolor="rgba(0,0,0,0)", title_text="", orientation="h", yanchor="bottom", y=1.02, x=0,
                font=dict(color=INK)),
    hoverlabel=dict(bgcolor=CARD, bordercolor=LINE, font=dict(family=FONT, color=INK)),
    bargap=0.4,
))
pio.templates.default = "plotly_white+flat_teal"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

/* Base */
.stApp, [data-testid="stAppViewContainer"] {{ background:{BG}; color:{INK}; font-family:{FONT}; }}
.stApp p, .stApp li, .stApp label, .stApp span, .stApp td, .stApp th, [data-testid="stMarkdownContainer"] {{
    font-family:{FONT} !important; }}
.stApp p, .stApp li {{ color:{INK}; }}
.block-container {{ max-width:1240px; padding-top:1.8rem; padding-bottom:3rem; }}
header[data-testid="stHeader"] {{ background:transparent; }}
[data-testid="stDecoration"] {{ display:none; }}
* {{ box-shadow:none !important; text-shadow:none !important; }}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{ color:{MUTED} !important; font-size:.8rem; }}
[data-testid="stIconMaterial"] {{ font-family:'Material Symbols Rounded' !important; }}

/* Sidebar */
[data-testid="stSidebar"] {{ background:{DARK}; }}
[data-testid="stSidebar"] * {{ color:#E8EFEE; }}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{ color:#A9BDBB !important; font-size:.84rem; line-height:1.55; }}
.brand {{ display:flex; align-items:center; gap:10px; margin:4px 0 28px; }}
.brand .mark {{ width:34px; height:34px; border-radius:10px; background:{ACCENT}; color:{DARK} !important;
               display:flex; align-items:center; justify-content:center; font-weight:800; font-size:1rem; }}
.brand .name {{ font-weight:700; font-size:.98rem; line-height:1.2; color:#FFFFFF !important; }}
.brand .name small {{ display:block; font-weight:500; font-size:.75rem; color:#A9BDBB !important; }}
.side-label {{ font-weight:600; font-size:.7rem; letter-spacing:.1em; color:#7F9997 !important; margin:24px 0 8px; }}
[data-testid="stSidebar"] [role="radiogroup"] {{ gap:2px; }}
[data-testid="stSidebar"] [role="radiogroup"] label {{ width:100%; box-sizing:border-box; padding:10px 12px; border-radius:8px;
    margin:0; cursor:pointer; border-left:3px solid transparent; }}
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child {{ display:none; }}
[data-testid="stSidebar"] [role="radiogroup"] label p {{ margin:0 !important; font-weight:500; font-size:.92rem; color:#C7D6D4 !important; }}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {{ background:{DARK_SOFT}; }}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{ background:{DARK_SOFT}; border-left-color:{ACCENT}; }}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p {{ color:#FFFFFF !important; font-weight:700; }}

/* Page header */
.eyebrow {{ font-weight:600; font-size:.75rem; letter-spacing:.08em; color:{ACCENT}; margin:0 0 4px; }}
.page-title {{ font-weight:800; font-size:1.9rem; letter-spacing:-0.02em; color:{INK}; margin:0; line-height:1.2; }}
.lead {{ color:{MUTED}; font-size:.95rem; margin:6px 0 20px; max-width:760px; line-height:1.55; }}

/* Cards: white, thin border, title row */
[class*="st-key-card"] {{ background:{CARD} !important; border:1px solid {LINE} !important; border-radius:12px !important;
                         padding:16px 20px 18px !important; gap:.5rem !important; }}
.card-head {{ display:flex; align-items:center; gap:10px; margin:0 0 calc(1rem - 6px); }}
.card-head .dot {{ width:10px; height:10px; border-radius:3px; flex:0 0 10px; }}
.card-head .t {{ font-weight:700; font-size:1.02rem; color:{INK}; }}
.card-head .tag {{ margin-left:auto; font-weight:600; font-size:.72rem; color:{MUTED}; background:{BG};
                  border:1px solid {LINE}; border-radius:999px; padding:2px 10px; }}
.note {{ color:{MUTED} !important; font-size:.86rem; line-height:1.5; margin:0 0 1rem !important; padding-bottom:2px; }}

/* KPI tiles */
.kpis {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin:4px 0 16px; }}
.kpi {{ background:{CARD}; border:1px solid {LINE}; border-radius:12px; padding:16px 18px; display:flex;
       justify-content:space-between; gap:10px; }}
.kpi-label {{ font-weight:600; font-size:.8rem; color:{MUTED}; }}
.kpi-val {{ font-weight:800; font-size:1.7rem; letter-spacing:-0.02em; color:{INK}; line-height:1.15; margin-top:6px;
           font-variant-numeric:tabular-nums; }}
.kpi-sub {{ font-size:.78rem; color:{MUTED}; margin-top:4px; }}
.kpi-icon {{ width:40px; height:40px; border-radius:10px; display:flex; align-items:center; justify-content:center; flex:0 0 40px; }}

/* Findings: one card, three columns */
.findings {{ background:{CARD}; border:1px solid {LINE}; border-radius:12px; display:grid;
            grid-template-columns:repeat(3,1fr); margin:0 0 14px; }}
.finding {{ padding:18px 20px; border-left:1px solid {LINE}; font-size:.9rem; line-height:1.55; color:{INK}; }}
.finding:first-child {{ border-left:none; }}
.finding .k {{ font-weight:600; font-size:.75rem; color:{MUTED}; letter-spacing:.04em; }}
.finding .big {{ display:block; font-weight:800; font-size:2.1rem; letter-spacing:-0.02em; margin:4px 0 6px; line-height:1.1; }}
.reco {{ background:{ACCENT_LIGHT}; border-left:4px solid {ACCENT}; border-radius:8px; padding:14px 18px;
        margin:0 0 22px; font-size:.92rem; line-height:1.6; color:{INK}; }}
@media (max-width: 900px) {{
  .kpis {{ grid-template-columns:repeat(2,1fr); }}
  .findings {{ grid-template-columns:1fr; }}
  .finding {{ border-left:none; border-top:1px solid {LINE}; }} .finding:first-child {{ border-top:none; }}
}}

/* Metrics used inside cards */
[data-testid="stMetric"] {{ background:{BG}; border-radius:10px; padding:12px 16px; }}
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p {{ font-weight:600 !important; font-size:.8rem !important;
    color:{MUTED} !important; }}
[data-testid="stMetricValue"] {{ font-weight:800; font-size:1.45rem; color:{INK} !important; font-family:{FONT}; }}

/* Inputs and dropdowns (forced light) */
.block-container label p {{ font-weight:600 !important; font-size:.8rem !important; color:{MUTED} !important; }}
[data-baseweb="select"] > div {{ background:{CARD} !important; border:1px solid {LINE} !important; border-radius:8px !important; }}
[data-baseweb="select"] > div:focus-within {{ border-color:{DARK} !important; }}
[data-baseweb="select"] div, [data-baseweb="select"] span, [data-baseweb="select"] input {{ color:{INK} !important; background-color:transparent !important; }}
[data-baseweb="select"] svg {{ fill:{MUTED} !important; color:{MUTED} !important; }}
[data-baseweb="select"] [data-baseweb="tag"] {{ background:{SAGE_LIGHT} !important; border-radius:6px !important; }}
[data-baseweb="select"] [data-baseweb="tag"] span, [data-baseweb="select"] [data-baseweb="tag"] svg {{ color:{DARK} !important; fill:{DARK} !important; }}
[data-baseweb="popover"] > div {{ border:1px solid {LINE} !important; border-radius:8px !important; overflow:hidden; }}
[data-baseweb="popover"] ul, [data-baseweb="popover"] li, [role="listbox"], [role="option"] {{ background:{CARD} !important; }}
[data-baseweb="popover"] li *, [role="option"], [role="option"] * {{ color:{INK} !important; }}
[data-baseweb="popover"] li:hover, [role="option"]:hover, [role="option"][aria-selected="true"] {{ background:{BG} !important; }}

/* Expander, alerts, charts */
[data-testid="stExpander"] details {{ background:{CARD}; border:1px solid {LINE}; border-radius:10px; }}
[data-testid="stExpander"] summary p {{ font-weight:600 !important; font-size:.88rem !important; color:{INK} !important; }}
[data-testid="stAlert"] {{ border-radius:10px; }}
[data-testid="stPlotlyChart"], [data-testid="stPlotlyChart"] > div {{ background:{CARD} !important; }}

/* Tables */
[data-testid="stTable"] table, .stTable table {{ background:{CARD}; color:{INK}; border-collapse:collapse; width:100%;
    font-size:.86rem; border:none; font-variant-numeric:tabular-nums; }}
[data-testid="stTable"] thead th, .stTable thead th {{ background:{CARD}; color:{MUTED}; font-weight:600; font-size:.76rem;
    border:none; border-bottom:1px solid {LINE}; text-align:left; }}
[data-testid="stTable"] td, .stTable td {{ border:none; border-bottom:1px solid {LINE}; color:{INK}; }}
[data-testid="stTable"] tbody th, .stTable tbody th {{ background:{CARD}; color:{INK}; font-weight:600;
    border:none; border-bottom:1px solid {LINE}; }}
[data-testid="stTable"] tr:last-child td, [data-testid="stTable"] tr:last-child th {{ border-bottom:none; }}
</style>
""", unsafe_allow_html=True)


def no_math(html):
    """Streamlit reads text between two $ signs as a math formula; &#36; shows a plain $ instead."""
    return html.replace("$", "&#36;")


# Simple line icons for KPI tiles
ICONS = {
    "trend": '<polyline points="3,17 9,11 13,15 21,7"/><polyline points="15,7 21,7 21,13"/>',
    "users": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.8-3.6 3.4-5.5 6.5-5.5s5.7 1.9 6.5 5.5"/>'
             '<path d="M16 4.8a3.5 3.5 0 0 1 0 6.4M18.5 14.8c1.6.8 2.6 2.6 3 5.2"/>',
    "basket": '<path d="M3 9h18l-1.8 10H4.8z"/><path d="M8 9l3-5M16 9l-3-5"/>',
    "dollar": '<path d="M12 3v18"/><path d="M16.5 7.5c-.8-1.3-2.4-2-4.5-2-2.6 0-4.3 1.3-4.3 3.2 0 4.6 9 2.4 9 7 0 '
              '2-1.8 3.3-4.7 3.3-2.3 0-4-.8-4.9-2.3"/>',
}
# icon colour scheme: (tile background, stroke colour)
TONES = {"dark": (SAGE_LIGHT, DARK), "accent": (ACCENT_LIGHT, ACCENT), "sage": (SAGE_LIGHT, SAGE),
         "butter": (BUTTER_LIGHT, "#B88A1E")}


def icon(name, tone):
    bg, stroke = TONES[tone]
    return (f'<div class="kpi-icon" style="background:{bg}"><svg width="20" height="20" viewBox="0 0 24 24" '
            f'fill="none" stroke="{stroke}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            f'{ICONS[name]}</svg></div>')


def kpi_tiles(items):
    """items: list of (label, value, sub_html, icon_name, tone)."""
    html = "".join(
        f'<div class="kpi"><div><div class="kpi-label">{label}</div><div class="kpi-val">{no_math(value)}</div>'
        f'<div class="kpi-sub">{no_math(sub)}</div></div>{icon(ic, tone)}</div>'
        for label, value, sub, ic, tone in items)
    st.markdown(f'<div class="kpis">{html}</div>', unsafe_allow_html=True)


@contextmanager
def card(key, title, tag="", dot=DARK):
    """White bordered card with a title row. Styled via the st-key-card... CSS class."""
    with st.container(key=f"card_{key}"):
        st.markdown(f'<div class="card-head"><span class="dot" style="background:{dot}"></span>'
                    f'<span class="t">{title}</span>{f"<span class=tag>{tag}</span>" if tag else ""}</div>',
                    unsafe_allow_html=True)
        yield


def note(text):
    st.markdown(f'<p class="note">{no_math(text)}</p>', unsafe_allow_html=True)


def chart(fig, height=None):
    """Plotly figure in the flat theme (theme=None stops Streamlit overriding colours)."""
    fig.update_traces(selector=dict(type="bar"), marker_line_width=0)
    fig.update_traces(selector=dict(type="scatter"), line_width=2.5, marker_size=7)
    fig.update_layout(paper_bgcolor=CARD, plot_bgcolor=CARD, legend_title_text="")
    if height:
        fig.update_layout(height=height)
    st.plotly_chart(fig, use_container_width=True, theme=None, config={"displayModeBar": False})


def table(df, formats=None):
    """Small HTML table with formatted numbers; first column becomes the row label."""
    out = df.copy()
    for col, f in (formats or {}).items():
        fmt = f if callable(f) else f.format
        out[col] = out[col].map(lambda v, fmt=fmt: "–" if pd.isna(v) else fmt(v))
    out = out.astype(str)
    out = out.set_index(out.columns[0])
    out.index.name = ""
    st.table(out)


def money(v):
    """$1,234.56 / −$2.20 (minus before the dollar sign)."""
    return f"−${abs(v):,.2f}" if v < 0 else f"${v:,.2f}"


def page_header(title, lead):
    st.markdown(f'<p class="eyebrow">GROCERY CAMPAIGN ANALYSIS</p><p class="page-title">{title}</p>'
                f'<p class="lead">{lead}</p>', unsafe_allow_html=True)


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

# =============================================================== SIDEBAR
with st.sidebar:
    st.markdown('<div class="brand"><div class="mark">G</div><div class="name">Grocery Campaigns<small>Portfolio project</small></div></div>',
                unsafe_allow_html=True)
    st.markdown('<div class="side-label">MENU</div>', unsafe_allow_html=True)
    page = st.radio("Page", ["Overview", "Customers", "Campaigns"], label_visibility="collapsed")
    st.markdown('<div class="side-label">ABOUT</div>', unsafe_allow_html=True)
    st.markdown("Do grocery marketing campaigns make customers spend more, or do they just reward "
                "shoppers who would have bought anyway?")
    st.markdown('<div class="side-label">DATA</div>', unsafe_allow_html=True)
    st.markdown("The Complete Journey 2.0 by 84.51°. 2,469 households, 1.47M transactions, one year.")

# =============================================================== OVERVIEW
if page == "Overview":
    page_header("Overview", "Which customers drive revenue, and do campaigns actually increase spending?")

    st.markdown(no_math(f"""
<div class="findings">
  <div class="finding"><span class="k">CUSTOMERS</span><span class="big" style="color:{DARK}">61.9%</span>
    of revenue comes from the <b>top 25% of households</b>, driven by visit frequency (132 vs 14 trips a year)
    more than basket size.</div>
  <div class="finding"><span class="k">REDEMPTION</span><span class="big" style="color:{SAGE}">2×</span>
    <b>Type A campaigns</b> get twice the redemption of Types B and C (15% vs 7%) while reaching about
    6.5× more households.</div>
  <div class="finding"><span class="k">IMPACT</span><span class="big" style="color:{ACCENT}">≈ 0%</span>
    <b>incremental lift from campaigns.</b> Targeted households already spent $237 more beforehand;
    after adjusting, the average lift is −$5.46.</div>
</div>
<div class="reco"><b>Recommendation.</b> Stop judging campaigns by redemption rate. Run each campaign with a random
holdout group to measure incremental sales, and focus on mid-tier households, where raising visit frequency has
the most room to grow revenue.</div>
"""), unsafe_allow_html=True)

    depts = sorted(tx["department"].dropna().unique())
    sel, _ = st.columns([2, 3])
    pick = sel.multiselect("Filter by department", depts, placeholder="All departments")
    f = tx[tx["department"].isin(pick)] if pick else tx
    k = an.kpis(f)
    weeks = f["week"].nunique()

    kpi_tiles([
        ("Total revenue", f"${k['revenue']/1e6:,.2f}M", f"≈ ${k['revenue']/weeks/1e3:,.0f}K per week", "trend", "dark"),
        ("Households", f"{k['households']:,}", "loyalty card members", "users", "sage"),
        ("Baskets", f"{k['baskets']:,}", f"≈ {k['baskets']/weeks:,.0f} per week", "basket", "accent"),
        ("Avg basket", f"${k['avg_basket']:,.2f}",
         f"<span style='color:{ACCENT}'>{k['discount_share']:.1%}</span> paid via discounts", "dollar", "dark"),
    ])

    with card("weekly", "Revenue by week", "Q1"):
        note("Steady at $80–100K a week, with a holiday peak in late December. Partial weeks at the edges are left out.")
        ws = an.weekly_sales(f)
        ws = ws[ws["baskets"] >= 0.5 * ws["baskets"].median()]
        fig = px.line(ws, x="week", y="revenue", markers=True, labels={"revenue": "", "week": "Week"})
        fig.update_traces(line_color=DARK, marker=dict(color=ACCENT, size=8))
        fig.update_yaxes(tickprefix="$")
        chart(fig, height=280)

    left, right = st.columns(2)
    with left:
        with card("depts", "Top departments", "Q1"):
            note("Grocery alone brings in about half of all revenue.")
            top_d = an.top_n(f, "department", 10).sort_values("revenue")
            fig = px.bar(top_d, x="revenue", y="department", orientation="h",
                         labels={"revenue": "", "department": ""}, color_discrete_sequence=[DARK])
            fig.update_xaxes(tickprefix="$")
            chart(fig, height=340)
    with right:
        with card("cats", "Top product categories", "Q1"):
            note('"Coupon/Misc items" likely holds fuel and gift cards rather than groceries.')
            top_c = an.top_n(f, "product_category", 10).sort_values("revenue")
            fig = px.bar(top_c, x="revenue", y="product_category", orientation="h",
                         labels={"revenue": "", "product_category": ""}, color_discrete_sequence=[ACCENT])
            fig.update_xaxes(tickprefix="$")
            chart(fig, height=340)

# =============================================================== CUSTOMERS
elif page == "Customers":
    page_header("Customers", "How concentrated is revenue, and which households spend the most?")
    ts = an.tier_share(hh)
    top, bottom = ts.iloc[-1], ts.iloc[0]
    kpi_tiles([
        ("Top 25% share", f"{top['revenue_share']:.1%}", "of total revenue", "trend", "dark"),
        ("Top 25% trips", f"{top['avg_baskets']:.0f}", f"vs {bottom['avg_baskets']:.0f} for bottom 25%", "basket", "accent"),
        ("Top 25% basket", f"${top['avg_basket']:.2f}", f"vs ${bottom['avg_basket']:.2f} for bottom 25%", "dollar", "sage"),
        ("With demographics", f"{hh['income'].notna().sum():,}", f"of {len(hh):,} households", "users", "dark"),
    ])

    with card("tiers", "Revenue by spend tier", "Q2"):
        note("Households split into four equal groups by annual spend.")
        left, right = st.columns([2, 3], gap="large")
        with left:
            fig = px.bar(ts, x="spend_tier", y="revenue_share", text_auto=".0%", color="spend_tier",
                         color_discrete_sequence=STEPS, labels={"spend_tier": "", "revenue_share": ""})
            fig.update_layout(showlegend=False)
            fig.update_yaxes(tickformat=".0%")
            fig.update_traces(textposition="outside", textfont=dict(color=INK, size=13), cliponaxis=False)
            fig.update_xaxes(tickangle=0)
            chart(fig, height=300)
        with right:
            table(ts[["spend_tier", "households", "revenue", "avg_baskets", "avg_basket", "revenue_share"]]
                  .rename(columns={"spend_tier": "Tier", "households": "Households", "revenue": "Revenue",
                                   "avg_baskets": "Trips / year", "avg_basket": "Avg basket",
                                   "revenue_share": "Share"}),
                  {"Households": "{:,}", "Revenue": "${:,.0f}", "Trips / year": "{:.0f}",
                   "Avg basket": "${:.2f}", "Share": "{:.1%}"})

    with card("demo", "Average annual spend by group", "Q3"):
        note("Demographics are available for about a third of households, so read these as indicative.")
        demo_labels = {"Income": "income", "Age": "age", "Household size": "household_size",
                       "Number of kids": "kids_count", "Marital status": "marital_status"}
        sel, _ = st.columns([1, 3])
        demo_col = demo_labels[sel.selectbox("Break down by", list(demo_labels))]
        sd = an.spend_by_demo(hh, demo_col)
        fig = px.bar(sd, x=demo_col, y="avg_spend", hover_data=["households"],
                     labels={"avg_spend": "", demo_col: ""}, color_discrete_sequence=[SAGE])
        fig.update_xaxes(type="category")
        fig.update_yaxes(tickprefix="$")
        chart(fig, height=320)

# =============================================================== CAMPAIGNS
else:
    page_header("Campaigns", "Which campaigns get redeemed, and did any of them actually increase spending?")
    lifts = all_lifts()
    ok = lifts[lifts["valid"]]
    type_a = camp.loc[camp["campaign_type"] == "Type A", "redemption_rate"].mean()
    other = camp.loc[camp["campaign_type"] != "Type A", "redemption_rate"].mean()
    kpi_tiles([
        ("Campaigns", f"{len(camp)}", f"{len(ok)} with a valid lift estimate", "trend", "dark"),
        ("Type A redemption", f"{type_a:.0%}", f"vs {other:.0%} for types B and C", "users", "sage"),
        ("Gap before campaigns", f"${ok['pre_gap'].mean():,.0f}", "targeted already spent more", "dollar", "dark"),
        ("Avg incremental lift", money(ok['did_lift'].mean()),
         f"<span style='color:{ACCENT}'>≈ 0%</span> per household", "basket", "accent"),
    ])

    with card("redeem", "Redemption rate by campaign", "Q4"):
        note("Share of targeted households that redeemed at least one coupon, ordered by start date. "
             "Campaign 24 started before the data begins, so its 0% is a data gap.")
        fig = px.bar(camp, x="campaign_id", y="redemption_rate", color="campaign_type",
                     color_discrete_map=CAMPAIGN_COLORS,
                     category_orders={"campaign_type": ["Type A", "Type B", "Type C"]},
                     hover_data=["households_targeted", "duration_days", "start_date"],
                     labels={"redemption_rate": "", "campaign_id": "Campaign"})
        fig.update_xaxes(type="category")
        fig.update_yaxes(tickformat=".0%")
        chart(fig, height=320)
        by_type = (camp.groupby("campaign_type")
                       .agg(campaigns=("campaign_id", "count"), targeted=("households_targeted", "mean"),
                            redemption=("redemption_rate", "mean"), duration=("duration_days", "mean"))
                       .reset_index())
        table(by_type.rename(columns={"campaign_type": "Type", "campaigns": "Campaigns",
                                      "targeted": "Avg households targeted", "redemption": "Avg redemption",
                                      "duration": "Avg duration (days)"}),
              {"Avg households targeted": "{:,.0f}", "Avg redemption": "{:.1%}", "Avg duration (days)": "{:.0f}"})

    with card("lift", "Incremental lift by campaign type", "Q5", dot=ACCENT):
        note("Targeted households already spent more before each campaign, so comparing them with everyone else "
             "overstates the effect. Difference-in-differences compares the change in spend instead.")
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
                                        "naive_gap": "Gap during", "did_lift": "Estimated lift",
                                        "lift_pct": "Lift %"}),
                  {"Targeted": "{:,}", "Gap before": money, "Gap during": money,
                   "Estimated lift": money, "Lift %": "{:.1%}"})
            st.caption("– means there is no full 'before' period in the data. "
                       "Small campaigns give noisy estimates; rely on the averages.")

    left, right = st.columns([3, 2])
    with left:
        with card("one", "Explore one campaign", "Q5"):
            cid = st.selectbox("Campaign", camp["campaign_id"].tolist(),
                               format_func=lambda c: f"Campaign {c} ({camp.set_index('campaign_id').loc[c, 'campaign_type']})")
            lift = an.campaign_lift(tx, d["campaigns"], d["campaign_descriptions"], cid)
            if not lift["valid"]:
                st.warning("This campaign starts too close to the beginning of the data, so there is no full "
                           "'before' period. The lift can't be estimated.")
            before_after = pd.DataFrame({
                "period": ["Before", "During", "Before", "During"],
                "group": ["Targeted", "Targeted", "Not targeted", "Not targeted"],
                "avg_spend": [lift["targeted_pre"], lift["targeted_during"],
                              lift["control_pre"], lift["control_during"]],
            })
            fig = px.line(before_after, x="period", y="avg_spend", color="group", markers=True,
                          color_discrete_map={"Targeted": ACCENT, "Not targeted": DARK},
                          labels={"avg_spend": "Avg spend per household", "period": ""})
            fig.update_yaxes(tickprefix="$")
            chart(fig, height=260)
            c1, c2, c3 = st.columns(3)
            c1.metric("Targeted", f"{lift['n_targeted']:,}")
            c2.metric("Gap during", f"${lift['naive_gap']:,.0f}")
            c3.metric("Est. lift", money(lift["did_lift"]) if lift["valid"] else "n/a")
            st.caption(f"{lift['start']:%d %b %Y} – {lift['end']:%d %b %Y}, compared with "
                       f"{lift['pre_start']:%d %b} – {lift['pre_end']:%d %b %Y}.")
    with right:
        with card("coupon", "Do coupon users spend more?", "Context"):
            note("Yes, but it's correlation, not causation: loyal high spenders are also more likely to clip coupons.")
            cu = an.coupon_user_comparison(hh, d["coupon_redemptions"]).set_index("group")
            rows = [("Households", "households", "{:,.0f}"), ("Avg annual spend", "avg_spend", "${:,.0f}"),
                    ("Trips / year", "avg_baskets", "{:.0f}"), ("Avg basket", "avg_basket", "${:.2f}")]
            tbl = pd.DataFrame({g: [fmt.format(cu.loc[g, col]) for _, col, fmt in rows] for g in cu.index},
                               index=[r[0] for r in rows])
            tbl.index.name = ""
            st.table(tbl)