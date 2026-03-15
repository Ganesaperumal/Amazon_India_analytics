import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
st.set_page_config(page_title="Festival & Seasonal", page_icon="🎉", layout="wide", initial_sidebar_state="expanded")


import pandas as pd, numpy as np, warnings
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
warnings.filterwarnings('ignore')

from utils.db import run_query
from utils.sidebar import render_sidebar, get_filter_sql, fix_heatmap_text

filters = render_sidebar()
fs = get_filter_sql(filters)
MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

st.markdown("<h1 style='color:#FFD700;text-align:center;'>🎉 FESTIVAL & <span style='color:#00D4FF;'>SEASONAL ANALYTICS</span></h1>", unsafe_allow_html=True)
st.markdown("---")

fest_df = run_query(f"""
    SELECT is_festival_sale, festival_name, COUNT(*) AS orders,
           ROUND(SUM(final_amount_inr)/1e7,2) AS rev_cr,
           ROUND(AVG(final_amount_inr),0) AS avg_order, ROUND(AVG(discount_percent),1) AS avg_disc
    FROM transactions WHERE {fs['w']} {fs['wsub']}
    GROUP BY is_festival_sale, festival_name ORDER BY rev_cr DESC
""")

fest_rev = float(fest_df[fest_df['is_festival_sale']==1]['rev_cr'].sum())
norm_rev = float(fest_df[fest_df['is_festival_sale']==0]['rev_cr'].sum())
fest_ord = int(fest_df[fest_df['is_festival_sale']==1]['orders'].sum())
lift_pct = round((fest_rev/norm_rev*100-100), 1) if norm_rev>0 else 0

c1,c2,c3,c4 = st.columns(4)
with c1: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>🎉 Festival Revenue</div><div class='kpi-value'>₹{fest_rev:.1f}Cr</div></div>", unsafe_allow_html=True)
with c2: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>📦 Festival Orders</div><div class='kpi-value'>{fest_ord/1000:.0f}K</div></div>", unsafe_allow_html=True)
with c3: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>🏪 Normal Revenue</div><div class='kpi-value'>₹{norm_rev:.1f}Cr</div></div>", unsafe_allow_html=True)
with c4: st.markdown(f"<div class='kpi-card'><div class='kpi-label'>📈 Festival Lift</div><div class='kpi-value'>{lift_pct:+.1f}%</div></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Festival vs Normal + Per-Festival ────────────────────────────────────────
col_l, col_r = st.columns([1,2])
with col_l:
    st.markdown("<div class='section-header'>🎊 Festival vs Normal</div>", unsafe_allow_html=True)
    comp = fest_df.groupby('is_festival_sale').agg(rev_cr=('rev_cr','sum')).reset_index()
    comp['label'] = comp['is_festival_sale'].map({1:'Festival Sale',0:'Normal Sale'})
    fig_c = go.Figure(go.Bar(x=comp['label'], y=comp['rev_cr'],
                              marker_color=['#FFD700','#8B949E'],
                              text=[f'₹{v:.1f}Cr' for v in comp['rev_cr']],
                              textposition='outside', textfont=dict(color='white',size=14), width=0.5))
    fig_c.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                         height=380, showlegend=False, yaxis=dict(title='Revenue (₹ Crores)'), margin=dict(t=40,b=20))
    st.plotly_chart(fig_c, use_container_width=True)

with col_r:
    st.markdown("<div class='section-header'>🎯 Per-Festival Revenue</div>", unsafe_allow_html=True)
    pf = fest_df[(fest_df['is_festival_sale']==1) & (fest_df['festival_name'].notna()) & (fest_df['festival_name'].str.strip()!='')].sort_values('rev_cr', ascending=False)
    if len(pf)>0:
        fig_pf = go.Figure(go.Bar(x=pf['festival_name'], y=pf['rev_cr'],
                                   marker_color=px.colors.qualitative.Set2[:len(pf)],
                                   text=[f'₹{v:.1f}Cr' for v in pf['rev_cr']],
                                   textposition='outside', textfont=dict(color='white',size=10)))
        fig_pf.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                               height=380, showlegend=False, yaxis=dict(title='Revenue (₹ Crores)'),
                               xaxis=dict(tickangle=-20), margin=dict(t=40,b=20))
        st.plotly_chart(fig_pf, use_container_width=True)

# ── Monthly Spike Overlay ─────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📅 Monthly Revenue — Festival Spike Overlay</div>", unsafe_allow_html=True)
mt = run_query(f"SELECT CAST(strftime('%m',order_date) AS INTEGER) AS month, ROUND(SUM(final_amount_inr)/1e7,2) AS rev FROM transactions WHERE {fs['w']} {fs['wsub']} GROUP BY month ORDER BY month")
mf = run_query(f"SELECT CAST(strftime('%m',order_date) AS INTEGER) AS month, ROUND(SUM(final_amount_inr)/1e7,2) AS fest FROM transactions WHERE {fs['w']} {fs['wsub']} AND is_festival_sale=1 GROUP BY month ORDER BY month")
mm = mt.merge(mf, on='month', how='left').fillna(0)
fig_spike = go.Figure()
fig_spike.add_trace(go.Bar(x=[MONTH_NAMES[m-1] for m in mm['month']], y=mm['rev'],
                            name='Total Revenue', marker_color='#A855F7', opacity=0.7))
fig_spike.add_trace(go.Scatter(x=[MONTH_NAMES[m-1] for m in mm['month']], y=mm['fest'],
                                name='Festival Revenue', mode='lines+markers',
                                line=dict(color='#FFD700',width=2.5), marker=dict(size=9,color='#FFD700')))
fig_spike.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                         height=380, yaxis=dict(title='Revenue (₹ Crores)'),
                         legend=dict(orientation='h',y=1.1), margin=dict(t=20,b=20))
st.plotly_chart(fig_spike, use_container_width=True)

# ── Festival Donut + Discount Scatter ────────────────────────────────────────
col_l2, col_r2 = st.columns(2)
with col_l2:
    st.markdown("<div class='section-header'>🍩 Festival Orders Distribution</div>", unsafe_allow_html=True)
    if len(pf)>0:
        fig_fd = go.Figure(go.Pie(values=pf['orders'], labels=pf['festival_name'], hole=0.5,
                                   marker=dict(colors=px.colors.qualitative.Set2[:len(pf)]),
                                   textinfo='label+percent', textfont=dict(color='white',size=11)))
        fig_fd.update_layout(template='plotly_dark', paper_bgcolor='#0E1117',
                              height=380, margin=dict(t=20,b=20))
        st.plotly_chart(fig_fd, use_container_width=True)

with col_r2:
    st.markdown("<div class='section-header'>💸 Discount % vs Sales Volume (Festival)</div>", unsafe_allow_html=True)
    df_d = run_query(f"""
        SELECT ROUND(discount_percent,0) AS disc, COUNT(*) AS orders, ROUND(AVG(final_amount_inr),0) AS avg_order
        FROM transactions WHERE {fs['w']} {fs['wsub']} AND is_festival_sale=1 AND discount_percent IS NOT NULL
        GROUP BY disc ORDER BY disc
    """)
    fig_ds, ax_ds = plt.subplots(figsize=(8,4.5))
    fig_ds.patch.set_facecolor('#0E1117'); ax_ds.set_facecolor('#0E1117')
    sc = ax_ds.scatter(df_d['disc'], df_d['orders']/1000, s=df_d['avg_order']/200,
                        c=df_d['avg_order'], cmap='plasma', alpha=0.8, edgecolors='white', linewidths=0.5)
    cbar = plt.colorbar(sc, ax=ax_ds)
    cbar.set_label('Avg Order (₹)', color='#8B949E', fontsize=8); cbar.ax.tick_params(colors='#8B949E', labelsize=7)
    ax_ds.set_xlabel('Discount %', color='#8B949E', fontsize=9); ax_ds.set_ylabel('Orders (K)', color='#8B949E', fontsize=9)
    ax_ds.tick_params(colors='#8B949E', labelsize=8)
    for sp in ax_ds.spines.values(): sp.set_color('#30363D')
    plt.tight_layout(); st.pyplot(fig_ds, use_container_width=True); plt.close()

# ── Seasonal Planning ─────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📅 Seasonal Planning — Quarterly Revenue by Year</div>", unsafe_allow_html=True)
q_df = run_query(f"""
    SELECT order_year, CAST((CAST(strftime('%m',order_date) AS INTEGER)+2)/3 AS INTEGER) AS quarter,
           ROUND(SUM(final_amount_inr)/1e7,2) AS rev_cr
    FROM transactions WHERE {fs['w']} {fs['wsub']}
    GROUP BY order_year, quarter ORDER BY order_year, quarter
""")
clrs_yr = px.colors.qualitative.Plotly
fig_sea = go.Figure()
for i, yr in enumerate(sorted(q_df['order_year'].unique())):
    sub = q_df[q_df['order_year']==yr]
    fig_sea.add_trace(go.Scatter(x=sub['quarter'], y=sub['rev_cr'], mode='lines+markers',
                                  name=str(yr), line=dict(width=2,color=clrs_yr[i%len(clrs_yr)]),
                                  marker=dict(size=7)))
fig_sea.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                       height=400, xaxis=dict(title='Quarter',tickvals=[1,2,3,4],ticktext=['Q1','Q2','Q3','Q4']),
                       yaxis=dict(title='Revenue (₹ Crores)'),
                       legend=dict(orientation='h',y=1.1,font=dict(size=9)), margin=dict(t=20,b=20))
st.plotly_chart(fig_sea, use_container_width=True)

# ── Festival Impact Heatmap ────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🌡️ Festival Revenue Impact by Category</div>", unsafe_allow_html=True)
fcat = run_query(f"""
    SELECT p.subcategory, is_festival_sale, ROUND(SUM(t.final_amount_inr)/1e7,1) AS rev_cr
    FROM transactions t JOIN products p ON t.product_id=p.product_id
    WHERE {fs['wt']} {fs['wsub']}
    GROUP BY p.subcategory, is_festival_sale
""")
fp = fcat.pivot_table(index='subcategory', columns='is_festival_sale', values='rev_cr', aggfunc='sum').fillna(0)
fp.columns = ['Normal Sale','Festival Sale']
fp['Festival Uplift %'] = ((fp['Festival Sale']/fp['Normal Sale'].replace(0,np.nan)*100-100).fillna(0)).round(1)
fp = fp.sort_values('Festival Uplift %', ascending=False)

fig_fhm, ax_fhm = plt.subplots(figsize=(10, max(4, len(fp)*0.5)))
fig_fhm.patch.set_facecolor('#0E1117'); ax_fhm.set_facecolor('#0E1117')
dv = fp[['Normal Sale','Festival Sale','Festival Uplift %']]
vmin_f, vmax_f = dv.values.min(), dv.values.max()
sns.heatmap(dv, annot=True, fmt='.1f', cmap='YlOrRd', ax=ax_fhm,
            linewidths=0.4, linecolor='#1C2333', annot_kws={'size':10})
fix_heatmap_text(ax_fhm, 'YlOrRd', vmin_f, vmax_f)   # ← visibility fix
ax_fhm.tick_params(colors='#8B949E', labelsize=9)
ax_fhm.set_xlabel('', color='#8B949E'); ax_fhm.set_ylabel('Subcategory', color='#8B949E')
cbar_f = ax_fhm.collections[0].colorbar
cbar_f.ax.yaxis.label.set_color('#8B949E'); cbar_f.ax.tick_params(colors='#8B949E')
plt.tight_layout(); st.pyplot(fig_fhm, use_container_width=True); plt.close()

st.markdown("---")
c1,c2,c3 = st.columns(3)
with c1: st.markdown("<div class='insight-box'>🪔 <b>Diwali Sale</b> is the single biggest event — ~30% of annual festival revenue in one week.</div>", unsafe_allow_html=True)
with c2: st.markdown("<div class='insight-box'>📱 <b>Electronics see 200%+ uplift</b> during festivals. 20-30% discount is the sweet spot for revenue.</div>", unsafe_allow_html=True)
with c3: st.markdown("<div class='insight-box'>📦 <b>Q4 (Oct-Dec)</b> is consistently the strongest quarter — ideal window for inventory and marketing.</div>", unsafe_allow_html=True)
