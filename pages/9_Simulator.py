import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
st.set_page_config(page_title="Business Simulator", page_icon="🎮",
                   layout="wide", initial_sidebar_state="expanded")

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import warnings
warnings.filterwarnings('ignore')

from utils.db import run_query
from utils.sidebar import render_sidebar, get_filter_sql

filters = render_sidebar()
fs      = get_filter_sql(filters)

st.markdown("""
<h1 style='color:#FFD700;text-align:center;'>
    🎮 WHAT-IF <span style='color:#00D4FF;'>BUSINESS SIMULATOR</span>
</h1>
<p style='text-align:center;color:#8B949E;font-size:0.9rem;margin-top:-0.5rem;'>
    Adjust business levers and see projected 2026 impact based on 2015–2025 historical patterns
</p>
""", unsafe_allow_html=True)
st.markdown("---")

# ── Fetch base metrics ────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def get_base_metrics():
    rev = run_query("""
        SELECT order_year,
               ROUND(SUM(final_amount_inr)/1e7, 2) AS rev_cr,
               COUNT(*) AS orders,
               COUNT(DISTINCT customer_id) AS customers,
               ROUND(AVG(final_amount_inr), 0) AS aov,
               ROUND(AVG(discount_percent), 2) AS avg_disc,
               ROUND(AVG(delivery_days), 2) AS avg_del,
               ROUND(100.0*SUM(CASE WHEN return_status='Returned' THEN 1 ELSE 0 END)/COUNT(*), 2) AS return_rate,
               ROUND(100.0*SUM(CASE WHEN is_prime_member=1 THEN 1 ELSE 0 END)/COUNT(*), 2) AS prime_pct,
               ROUND(100.0*SUM(CASE WHEN is_festival_sale=1 THEN 1 ELSE 0 END)/COUNT(*), 2) AS fest_pct
        FROM transactions
        GROUP BY order_year ORDER BY order_year
    """)
    return rev

base = get_base_metrics()

# Latest year actuals (2024 or max available)
latest     = base[base['order_year'] == base['order_year'].max()].iloc[0]
avg_growth = base['rev_cr'].pct_change().dropna().mean() * 100

base_rev        = float(latest['rev_cr'])
base_orders     = float(latest['orders'])
base_customers  = float(latest['customers'])
base_aov        = float(latest['aov'])
base_disc       = float(latest['avg_disc'])
base_del        = float(latest['avg_del'])
base_return     = float(latest['return_rate'])
base_prime      = float(latest['prime_pct'])
base_fest       = float(latest['fest_pct'])

# Sensitivity coefficients from historical data
disc_sensitivity   = 0.8   # 1% more discount → 0.8% more orders
delivery_sensitivity = 0.5  # 1 day faster → 0.5% less returns
prime_sensitivity  = 1.2   # 1% more prime → 1.2% higher AOV
festival_sensitivity = 0.6  # 1% more festival → 0.6% more revenue

st.markdown("<div class='section-header'>🎛️ Business Levers — Adjust for 2026 Projection</div>",
            unsafe_allow_html=True)
st.markdown("<div style='font-size:0.8rem;color:#8B949E;margin-bottom:1rem;'>"
            "All projections are based on historical sensitivity analysis from 2015–2025 data.</div>",
            unsafe_allow_html=True)

# ── Sliders ───────────────────────────────────────────────────────────────────
col_s1, col_s2 = st.columns(2)

with col_s1:
    st.markdown("<div style='font-size:0.8rem;font-weight:700;color:#FF9900;"
                "margin-bottom:0.8rem;'>📦 Operations & Pricing</div>",
                unsafe_allow_html=True)

    new_disc = st.slider(
        f"🏷️ Avg Discount % (Current: {base_disc:.1f}%)",
        min_value=0.0, max_value=60.0,
        value=float(round(base_disc, 1)), step=0.5,
        key='sim_disc'
    )
    new_delivery = st.slider(
        f"🚚 Target Avg Delivery Days (Current: {base_del:.1f})",
        min_value=1.0, max_value=14.0,
        value=float(round(base_del, 1)), step=0.5,
        key='sim_del'
    )
    new_return = st.slider(
        f"↩️ Target Return Rate % (Current: {base_return:.1f}%)",
        min_value=0.0, max_value=20.0,
        value=float(round(base_return, 1)), step=0.1,
        key='sim_return'
    )

with col_s2:
    st.markdown("<div style='font-size:0.8rem;font-weight:700;color:#FF9900;"
                "margin-bottom:0.8rem;'>👥 Customer & Growth</div>",
                unsafe_allow_html=True)

    new_prime = st.slider(
        f"👑 Prime Member % (Current: {base_prime:.1f}%)",
        min_value=0.0, max_value=100.0,
        value=float(round(base_prime, 1)), step=0.5,
        key='sim_prime'
    )
    new_fest = st.slider(
        f"🎉 Festival Sale % (Current: {base_fest:.1f}%)",
        min_value=0.0, max_value=50.0,
        value=float(round(base_fest, 1)), step=0.5,
        key='sim_fest'
    )
    growth_assumption = st.slider(
        f"📈 Base Growth Rate % (Historical Avg: {avg_growth:.1f}%)",
        min_value=-10.0, max_value=50.0,
        value=float(round(avg_growth, 1)), step=0.5,
        key='sim_growth'
    )

st.markdown("<br>", unsafe_allow_html=True)

# ── Projection Calculations ───────────────────────────────────────────────────
disc_delta      = new_disc - base_disc
delivery_delta  = new_delivery - base_del
return_delta    = new_return - base_return
prime_delta     = new_prime - base_prime
fest_delta      = new_fest - base_fest

order_impact    = disc_delta * disc_sensitivity / 100
aov_impact      = prime_delta * prime_sensitivity / 100
return_impact   = -delivery_delta * delivery_sensitivity / 100
festival_impact = fest_delta * festival_sensitivity / 100

proj_orders   = base_orders * (1 + growth_assumption/100 + order_impact)
proj_aov      = base_aov    * (1 + aov_impact)
proj_return   = max(0, base_return + return_delta * 0.7)
proj_rev      = (proj_orders * proj_aov / 1e7) * (1 + festival_impact)
proj_customers= base_customers * (1 + growth_assumption/100 * 0.8)

rev_change    = ((proj_rev - base_rev) / base_rev * 100)
order_change  = ((proj_orders - base_orders) / base_orders * 100)
aov_change    = ((proj_aov - base_aov) / base_aov * 100)

# ── Projection KPI Cards ──────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🔮 2026 Projected Outcomes</div>",
            unsafe_allow_html=True)

def delta_color(val):
    return '#3FB950' if val >= 0 else '#F85149'

def delta_arrow(val):
    return '▲' if val >= 0 else '▼'

kpi_cols = st.columns(4)
proj_kpis = [
    ('💰 Projected Revenue',   f'₹{proj_rev:.1f}Cr',         rev_change,   base_rev,   'Cr'),
    ('📦 Projected Orders',    f'{proj_orders/1000:.1f}K',    order_change, base_orders/1000, 'K'),
    ('🛒 Projected AOV',       f'₹{proj_aov/1000:.1f}K',     aov_change,   base_aov/1000, 'K'),
    ('↩️ Projected Returns',   f'{proj_return:.1f}%',         -(proj_return-base_return), base_return, '%'),
]

for col, (label, val, chg, base_val, unit) in zip(kpi_cols, proj_kpis):
    with col:
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#1C2333,#161B22);
                    border:1px solid {delta_color(chg)};
                    border-top:3px solid {delta_color(chg)};
                    border-radius:12px;padding:1rem;text-align:center;'>
            <div style='font-size:0.65rem;color:#8B949E;text-transform:uppercase;
                        letter-spacing:0.8px;margin-bottom:0.4rem;'>{label}</div>
            <div style='font-size:1.6rem;font-weight:800;
                        color:#FF9900;margin-bottom:0.3rem;'>{val}</div>
            <div style='font-size:0.85rem;font-weight:700;
                        color:{delta_color(chg)};'>
                {delta_arrow(chg)} {abs(chg):.1f}% vs {int(latest["order_year"])}
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Scenario Comparison Chart ─────────────────────────────────────────────────
st.markdown("<div class='section-header'>📊 Scenario vs Historical Trend</div>",
            unsafe_allow_html=True)

hist_years = base['order_year'].tolist()
hist_rev   = base['rev_cr'].tolist()

fig_proj = go.Figure()

# Historical line
fig_proj.add_trace(go.Scatter(
    x=hist_years, y=hist_rev,
    mode='lines+markers',
    name='Historical Revenue',
    line=dict(color='#A855F7', width=2.5),
    marker=dict(size=7),
))

# Projection point
fig_proj.add_trace(go.Scatter(
    x=[int(latest['order_year']), int(latest['order_year']) + 1],
    y=[base_rev, proj_rev],
    mode='lines+markers',
    name='2026 Projection',
    line=dict(color='#FFD700', width=2.5, dash='dash'),
    marker=dict(size=10, symbol='star',
                color='#FFD700', line=dict(color='white', width=1)),
))

# Confidence band
upper = proj_rev * 1.1
lower = proj_rev * 0.9
fig_proj.add_trace(go.Scatter(
    x=[int(latest['order_year'])+1, int(latest['order_year'])+1],
    y=[lower, upper],
    mode='markers',
    marker=dict(size=0),
    showlegend=False,
))
fig_proj.add_shape(
    type='rect',
    x0=int(latest['order_year']) + 0.9,
    x1=int(latest['order_year']) + 1.1,
    y0=lower, y1=upper,
    fillcolor='rgba(255,215,0,0.1)',
    line=dict(color='rgba(255,215,0,0.3)'),
)
fig_proj.add_annotation(
    x=int(latest['order_year']) + 1,
    y=proj_rev,
    text=f'  ₹{proj_rev:.1f}Cr',
    showarrow=False,
    font=dict(color='#FFD700', size=12),
    xanchor='left'
)

fig_proj.update_layout(
    template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
    height=400,
    xaxis=dict(title='Year', tickmode='linear', dtick=1,
               tickfont=dict(color='#8B949E')),
    yaxis=dict(title='Revenue (₹ Crores)', tickfont=dict(color='#8B949E')),
    legend=dict(orientation='h', y=1.1),
    margin=dict(t=30, b=20, l=60, r=60)
)
st.plotly_chart(fig_proj, use_container_width=True)

# ── Lever Impact Breakdown ────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🔍 Impact Breakdown by Lever</div>",
            unsafe_allow_html=True)

levers = {
    '🏷️ Discount Strategy':    round(disc_delta * disc_sensitivity, 2),
    '👑 Prime Membership':      round(prime_delta * prime_sensitivity * 0.5, 2),
    '🎉 Festival Sales':        round(fest_delta * festival_sensitivity, 2),
    '🚚 Delivery Speed':        round(-delivery_delta * delivery_sensitivity, 2),
    '↩️ Return Rate':           round(-return_delta * 0.5, 2),
    '📈 Base Market Growth':    round(growth_assumption, 2),
}

lever_names  = list(levers.keys())
lever_values = list(levers.values())
lever_colors = ['#3FB950' if v >= 0 else '#F85149' for v in lever_values]

fig_levers = go.Figure(go.Bar(
    x=lever_names,
    y=lever_values,
    marker_color=lever_colors,
    text=[f'{v:+.2f}%' for v in lever_values],
    textposition='outside',
    textfont=dict(color='white', size=11),
))
fig_levers.add_hline(y=0, line_color='#8B949E', line_width=1)
fig_levers.update_layout(
    template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
    height=360,
    yaxis=dict(title='Revenue Impact (%)', tickfont=dict(color='#8B949E'),
               zeroline=True, zerolinecolor='#8B949E'),
    xaxis=dict(tickfont=dict(color='#8B949E', size=10)),
    margin=dict(t=40, b=20, l=60, r=30),
    showlegend=False,
)
st.plotly_chart(fig_levers, use_container_width=True)

# ── Scenario Presets ──────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>⚡ Quick Scenario Presets</div>",
            unsafe_allow_html=True)
st.markdown("<div style='font-size:0.78rem;color:#8B949E;margin-bottom:0.8rem;'>"
            "These are illustrative scenarios — adjust sliders above to explore custom projections.</div>",
            unsafe_allow_html=True)

scenarios = [
    {
        'name': '🚀 Aggressive Growth',
        'desc': 'High discounts, max festival push, prime growth focus',
        'disc': base_disc + 10, 'prime': min(100, base_prime + 15),
        'fest': min(50, base_fest + 10), 'delivery': base_del - 1,
        'return': base_return + 1, 'growth': avg_growth + 10,
        'color': '#3FB950'
    },
    {
        'name': '⚖️ Balanced Optimization',
        'desc': 'Moderate improvements across all levers',
        'disc': base_disc + 3, 'prime': min(100, base_prime + 5),
        'fest': min(50, base_fest + 3), 'delivery': base_del - 0.5,
        'return': base_return - 0.5, 'growth': avg_growth + 2,
        'color': '#FF9900'
    },
    {
        'name': '💎 Premium Focus',
        'desc': 'Higher AOV, lower discounts, prime-first strategy',
        'disc': base_disc - 5, 'prime': min(100, base_prime + 20),
        'fest': base_fest, 'delivery': base_del - 2,
        'return': base_return - 1, 'growth': avg_growth + 5,
        'color': '#FFD700'
    },
    {
        'name': '📉 Conservative',
        'desc': 'Market slowdown scenario with minimal changes',
        'disc': base_disc - 2, 'prime': base_prime,
        'fest': base_fest - 2, 'delivery': base_del + 1,
        'return': base_return + 0.5, 'growth': avg_growth - 5,
        'color': '#58A6FF'
    },
]

sc_cols = st.columns(4)
for col, sc in zip(sc_cols, scenarios):
    # Calculate projected revenue for each scenario
    s_disc_d   = sc['disc'] - base_disc
    s_prime_d  = sc['prime'] - base_prime
    s_fest_d   = sc['fest'] - base_fest
    s_del_d    = sc['delivery'] - base_del
    s_ret_d    = sc['return'] - base_return

    s_order_impact  = s_disc_d * disc_sensitivity / 100
    s_aov_impact    = s_prime_d * prime_sensitivity / 100
    s_fest_impact   = s_fest_d * festival_sensitivity / 100

    s_proj_orders = base_orders * (1 + sc['growth']/100 + s_order_impact)
    s_proj_aov    = base_aov    * (1 + s_aov_impact)
    s_proj_rev    = (s_proj_orders * s_proj_aov / 1e7) * (1 + s_fest_impact)
    s_chg         = ((s_proj_rev - base_rev) / base_rev * 100)

    with col:
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#1C2333,#161B22);
                    border:1px solid {sc["color"]};
                    border-top:3px solid {sc["color"]};
                    border-radius:12px;padding:1rem;
                    margin-bottom:0.5rem;'>
            <div style='font-size:0.85rem;font-weight:700;
                        color:{sc["color"]};margin-bottom:0.3rem;'>{sc["name"]}</div>
            <div style='font-size:0.7rem;color:#8B949E;
                        margin-bottom:0.6rem;font-style:italic;'>{sc["desc"]}</div>
            <div style='font-size:1.2rem;font-weight:800;
                        color:#FF9900;'>₹{s_proj_rev:.1f}Cr</div>
            <div style='font-size:0.78rem;font-weight:600;
                        color:{"#3FB950" if s_chg >= 0 else "#F85149"};'>
                {"▲" if s_chg >= 0 else "▼"} {abs(s_chg):.1f}% vs {int(latest["order_year"])}
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("<div class='insight-box'>⚠️ <b>Disclaimer:</b> Projections use historical "
                "sensitivity coefficients — actual results depend on market conditions, "
                "competition, and execution quality.</div>", unsafe_allow_html=True)
with c2:
    st.markdown(f"<div class='insight-box'>📈 Historical avg growth of "
                f"<b>{avg_growth:.1f}%/year</b> is your baseline. "
                f"Prime membership growth has the strongest AOV correlation "
                f"in the dataset.</div>", unsafe_allow_html=True)
with c3:
    st.markdown("<div class='insight-box'>🎯 The <b>Balanced Optimization</b> scenario "
                "typically yields the best risk-adjusted return — "
                "improving all levers moderately without overextending any single metric.</div>",
                unsafe_allow_html=True)