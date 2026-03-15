import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
st.set_page_config(page_title="Revenue Analytics", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

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

st.markdown("<h1 style='color:#FFD700;text-align:center;'>📈 REVENUE <span style='color:#00D4FF;'>ANALYTICS</span></h1>", unsafe_allow_html=True)
st.markdown("---")

# ── Year Comparison Toggle ────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🔀 Year-over-Year Comparison Mode</div>",
            unsafe_allow_html=True)

compare_mode = st.toggle("Enable Year Comparison Mode", value=False, key='compare_toggle')

if compare_mode:
    col_ya, col_yb = st.columns(2)
    all_years = list(range(2015, 2026))
    with col_ya:
        year_a = st.selectbox("📅 Year A", all_years, index=5,  key='year_a')
    with col_yb:
        year_b = st.selectbox("📅 Year B", all_years, index=10, key='year_b')

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Monthly Revenue Comparison ────────────────────────────────────────────
    st.markdown("<div class='section-header'>📊 Monthly Revenue — Year A vs Year B</div>",
                unsafe_allow_html=True)

    @st.cache_data(ttl=600)
    def get_monthly_rev(year):
        return run_query(f"""
            SELECT CAST(strftime('%m', order_date) AS INTEGER) AS month,
                   ROUND(SUM(final_amount_inr)/1e7, 2) AS rev_cr,
                   COUNT(*) AS orders,
                   ROUND(AVG(final_amount_inr), 0) AS aov
            FROM transactions
            WHERE order_year = {year}
            GROUP BY month ORDER BY month
        """)

    df_a = get_monthly_rev(year_a)
    df_b = get_monthly_rev(year_b)

    fig_cmp = go.Figure()
    fig_cmp.add_trace(go.Bar(
        x=[MONTH_NAMES[m-1] for m in df_a['month']],
        y=df_a['rev_cr'],
        name=f'📅 {year_a}',
        marker_color='#A855F7',
        opacity=0.85,
        text=[f'₹{v:.0f}Cr' for v in df_a['rev_cr']],
        textposition='outside',
        textfont=dict(color='white', size=9),
    ))
    fig_cmp.add_trace(go.Bar(
        x=[MONTH_NAMES[m-1] for m in df_b['month']],
        y=df_b['rev_cr'],
        name=f'📅 {year_b}',
        marker_color='#FFD700',
        opacity=0.85,
        text=[f'₹{v:.0f}Cr' for v in df_b['rev_cr']],
        textposition='outside',
        textfont=dict(color='white', size=9),
    ))
    fig_cmp.update_layout(
        template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
        barmode='group', height=400,
        yaxis=dict(title='Revenue (₹ Crores)'),
        legend=dict(orientation='h', y=1.1),
        margin=dict(t=40, b=20)
    )
    st.plotly_chart(fig_cmp, use_container_width=True)

    # ── AOV + Orders Comparison ───────────────────────────────────────────────
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("<div class='section-header'>🛒 Avg Order Value Comparison</div>",
                    unsafe_allow_html=True)
        fig_aov = go.Figure()
        fig_aov.add_trace(go.Scatter(
            x=[MONTH_NAMES[m-1] for m in df_a['month']],
            y=df_a['aov']/1000,
            name=f'{year_a}', mode='lines+markers',
            line=dict(color='#A855F7', width=2.5),
            marker=dict(size=8)
        ))
        fig_aov.add_trace(go.Scatter(
            x=[MONTH_NAMES[m-1] for m in df_b['month']],
            y=df_b['aov']/1000,
            name=f'{year_b}', mode='lines+markers',
            line=dict(color='#FFD700', width=2.5),
            marker=dict(size=8)
        ))
        fig_aov.update_layout(
            template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
            height=320, yaxis=dict(title='AOV (₹K)'),
            legend=dict(orientation='h', y=1.1),
            margin=dict(t=30, b=20)
        )
        st.plotly_chart(fig_aov, use_container_width=True)

    with col_r:
        st.markdown("<div class='section-header'>📦 Monthly Orders Comparison</div>",
                    unsafe_allow_html=True)
        fig_ord = go.Figure()
        fig_ord.add_trace(go.Scatter(
            x=[MONTH_NAMES[m-1] for m in df_a['month']],
            y=df_a['orders']/1000,
            name=f'{year_a}', mode='lines+markers',
            line=dict(color='#A855F7', width=2.5),
            marker=dict(size=8), fill='tozeroy',
            fillcolor='rgba(168,85,247,0.1)'
        ))
        fig_ord.add_trace(go.Scatter(
            x=[MONTH_NAMES[m-1] for m in df_b['month']],
            y=df_b['orders']/1000,
            name=f'{year_b}', mode='lines+markers',
            line=dict(color='#FFD700', width=2.5),
            marker=dict(size=8), fill='tozeroy',
            fillcolor='rgba(255,215,0,0.1)'
        ))
        fig_ord.update_layout(
            template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
            height=320, yaxis=dict(title='Orders (K)'),
            legend=dict(orientation='h', y=1.1),
            margin=dict(t=30, b=20)
        )
        st.plotly_chart(fig_ord, use_container_width=True)

    # ── Category Revenue Comparison ───────────────────────────────────────────
    st.markdown("<div class='section-header'>🛍️ Category Revenue — Year A vs Year B</div>",
                unsafe_allow_html=True)

    @st.cache_data(ttl=600)
    def get_category_rev(year):
        return run_query(f"""
            SELECT p.category,
                   ROUND(SUM(t.final_amount_inr)/1e7, 2) AS rev_cr
            FROM transactions t
            JOIN products p ON t.product_id = p.product_id
            WHERE t.order_year = {year}
            GROUP BY p.category ORDER BY rev_cr DESC
        """)

    cat_a = get_category_rev(year_a)
    cat_b = get_category_rev(year_b)
    cat_merged = cat_a.merge(cat_b, on='category', how='outer',
                              suffixes=(f'_{year_a}', f'_{year_b}')).fillna(0)
    cat_merged = cat_merged.sort_values(f'rev_cr_{year_a}', ascending=True)

    fig_cat = go.Figure()
    fig_cat.add_trace(go.Bar(
        y=cat_merged['category'],
        x=cat_merged[f'rev_cr_{year_a}'],
        name=f'{year_a}',
        orientation='h',
        marker_color='#A855F7',
        text=[f'₹{v:.0f}Cr' for v in cat_merged[f'rev_cr_{year_a}']],
        textposition='outside',
        textfont=dict(color='white', size=10),
    ))
    fig_cat.add_trace(go.Bar(
        y=cat_merged['category'],
        x=cat_merged[f'rev_cr_{year_b}'],
        name=f'{year_b}',
        orientation='h',
        marker_color='#FFD700',
        text=[f'₹{v:.0f}Cr' for v in cat_merged[f'rev_cr_{year_b}']],
        textposition='outside',
        textfont=dict(color='white', size=10),
    ))
    fig_cat.update_layout(
        template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
        barmode='group', height=400,
        xaxis=dict(title='Revenue (₹ Crores)'),
        legend=dict(orientation='h', y=1.1),
        margin=dict(t=30, b=20, r=80)
    )
    st.plotly_chart(fig_cat, use_container_width=True)

    # ── Summary Scorecard ─────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>🏆 Year Comparison Scorecard</div>",
                unsafe_allow_html=True)

    total_a = df_a['rev_cr'].sum()
    total_b = df_b['rev_cr'].sum()
    orders_a = df_a['orders'].sum()
    orders_b = df_b['orders'].sum()
    aov_a = df_a['aov'].mean()
    aov_b = df_b['aov'].mean()
    diff_rev = ((total_b - total_a) / total_a * 100) if total_a > 0 else 0
    diff_ord = ((orders_b - orders_a) / orders_a * 100) if orders_a > 0 else 0
    diff_aov = ((aov_b - aov_a) / aov_a * 100) if aov_a > 0 else 0

    sc1, sc2, sc3 = st.columns(3)
    for col, label, val_a, val_b, diff, fmt in [
        (sc1, '💰 Total Revenue',   f'₹{total_a:.1f}Cr',  f'₹{total_b:.1f}Cr',  diff_rev, ''),
        (sc2, '📦 Total Orders',    f'{orders_a/1000:.1f}K', f'{orders_b/1000:.1f}K', diff_ord, ''),
        (sc3, '🛒 Avg Order Value', f'₹{aov_a/1000:.1f}K', f'₹{aov_b/1000:.1f}K', diff_aov, ''),
    ]:
        color = '#3FB950' if diff >= 0 else '#F85149'
        arrow = '▲' if diff >= 0 else '▼'
        with col:
            st.markdown(f"""
            <div style='background:linear-gradient(135deg,#1C2333,#161B22);
                        border:1px solid #30363D;border-radius:12px;
                        padding:1rem;text-align:center;'>
                <div style='font-size:0.75rem;color:#8B949E;
                            text-transform:uppercase;margin-bottom:0.5rem;'>{label}</div>
                <div style='display:flex;justify-content:space-around;
                            align-items:center;margin-bottom:0.5rem;'>
                    <div>
                        <div style='font-size:0.65rem;color:#A855F7;'>Year {year_a}</div>
                        <div style='font-size:1.1rem;font-weight:700;
                                    color:#A855F7;'>{val_a}</div>
                    </div>
                    <div style='font-size:1.5rem;color:#8B949E;'>→</div>
                    <div>
                        <div style='font-size:0.65rem;color:#FFD700;'>Year {year_b}</div>
                        <div style='font-size:1.1rem;font-weight:700;
                                    color:#FFD700;'>{val_b}</div>
                    </div>
                </div>
                <div style='font-size:1rem;font-weight:700;color:{color};'>
                    {arrow} {abs(diff):.1f}% change
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

# ── Monthly Heatmap Year × Month ──────────────────────────────────────────────
st.markdown("<div class='section-header'>🌡️ Monthly Revenue Heatmap — Year × Month (₹ Crores)</div>", unsafe_allow_html=True)
hm_df = run_query(f"""
    SELECT order_year, CAST(strftime('%m',order_date) AS INTEGER) AS month,
           ROUND(SUM(final_amount_inr)/1e7,1) AS rev_cr
    FROM transactions WHERE {fs['w']} {fs['wsub']}
    GROUP BY order_year, month ORDER BY order_year, month
""")
hm_pivot = hm_df.pivot_table(index='order_year', columns='month', values='rev_cr', aggfunc='sum').fillna(0)
hm_pivot.columns = MONTH_NAMES[:len(hm_pivot.columns)]

fig_hm, ax = plt.subplots(figsize=(16, max(4, len(hm_pivot)*0.7)))
fig_hm.patch.set_facecolor('#0E1117'); ax.set_facecolor('#0E1117')
vmin, vmax = hm_pivot.values.min(), hm_pivot.values.max()
sns.heatmap(hm_pivot, annot=True, fmt='.0f', cmap='YlOrRd', ax=ax,
            linewidths=0.5, linecolor='#1C2333', annot_kws={'size':10},
            cbar_kws={'label':'Revenue (₹ Cr)','shrink':0.8})
fix_heatmap_text(ax, 'YlOrRd', vmin, vmax)   # ← visibility fix
ax.tick_params(colors='#8B949E', labelsize=10)
ax.set_xlabel('Month', color='#8B949E'); ax.set_ylabel('Year', color='#8B949E')
cbar = ax.collections[0].colorbar
cbar.ax.yaxis.label.set_color('#8B949E'); cbar.ax.tick_params(colors='#8B949E')
plt.tight_layout()
st.pyplot(fig_hm, use_container_width=True); plt.close()

# ── Avg by Month + Trend Lines ────────────────────────────────────────────────
col_l, col_r = st.columns(2)
with col_l:
    st.markdown("<div class='section-header'>📊 Avg Revenue by Month</div>", unsafe_allow_html=True)
    monthly_avg = hm_pivot.mean(); peak_m = monthly_avg.idxmax()
    fig_avg = go.Figure(go.Bar(
        x=monthly_avg.index, y=monthly_avg.values,
        marker_color=['#F85149' if m==peak_m else '#A855F7' for m in monthly_avg.index],
        text=[f'₹{v:.0f}Cr' for v in monthly_avg.values],
        textposition='outside', textfont=dict(color='white',size=10)))
    fig_avg.add_annotation(x=peak_m, y=monthly_avg[peak_m],
                            text=f"🔝 Peak: {peak_m}", showarrow=True,
                            arrowhead=2, arrowcolor='#FFD700',
                            font=dict(color='#FFD700',size=11), ax=0, ay=-40)
    fig_avg.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                           height=350, margin=dict(t=40,b=20), showlegend=False,
                           yaxis=dict(title='Avg Revenue (₹ Crores)'))
    st.plotly_chart(fig_avg, use_container_width=True)

with col_r:
    st.markdown("<div class='section-header'>📉 Monthly Trend Lines by Year</div>", unsafe_allow_html=True)
    fig_trend = go.Figure()
    colors_yr = px.colors.sequential.Plasma
    for i, year in enumerate(sorted(hm_pivot.index)):
        clr = colors_yr[int(i*len(colors_yr)/max(len(hm_pivot.index),1))]
        fig_trend.add_trace(go.Scatter(x=MONTH_NAMES[:len(hm_pivot.columns)],
                                        y=hm_pivot.loc[year].values,
                                        mode='lines+markers', name=str(year),
                                        line=dict(width=2,color=clr), marker=dict(size=5)))
    fig_trend.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                             height=350, margin=dict(t=30,b=20), yaxis=dict(title='Revenue (₹ Crores)'),
                             legend=dict(orientation='h',y=1.15,font=dict(size=9)))
    st.plotly_chart(fig_trend, use_container_width=True)

# ── Subcategory × Month Heatmap ───────────────────────────────────────────────
st.markdown("<div class='section-header'>🗂️ Subcategory × Month Revenue Heatmap</div>", unsafe_allow_html=True)
sub_df = run_query(f"""
    SELECT p.subcategory, CAST(strftime('%m',t.order_date) AS INTEGER) AS month,
           ROUND(SUM(t.final_amount_inr)/1e7,1) AS rev_cr
    FROM transactions t JOIN products p ON t.product_id=p.product_id
    WHERE {fs['wt']} {fs['wsub']}
    GROUP BY p.subcategory, month
""")
sub_pivot = sub_df.pivot_table(index='subcategory', columns='month', values='rev_cr', aggfunc='sum').fillna(0)
sub_pivot.columns = MONTH_NAMES[:len(sub_pivot.columns)]
sub_pivot = sub_pivot.loc[sub_pivot.sum(axis=1).sort_values(ascending=False).index]

fig_sub, ax2 = plt.subplots(figsize=(16, max(5, len(sub_pivot)*0.65)))
fig_sub.patch.set_facecolor('#0E1117'); ax2.set_facecolor('#0E1117')
sv_min, sv_max = sub_pivot.values.min(), sub_pivot.values.max()
sns.heatmap(sub_pivot, annot=True, fmt='.0f', cmap='Blues', ax=ax2,
            linewidths=0.4, linecolor='#1C2333', annot_kws={'size':9})
fix_heatmap_text(ax2, 'Blues', sv_min, sv_max)   # ← visibility fix
ax2.tick_params(colors='#8B949E', labelsize=9)
ax2.set_xlabel('Month', color='#8B949E'); ax2.set_ylabel('Subcategory', color='#8B949E')
cbar2 = ax2.collections[0].colorbar
cbar2.ax.yaxis.label.set_color('#8B949E'); cbar2.ax.tick_params(colors='#8B949E')
plt.tight_layout()
st.pyplot(fig_sub, use_container_width=True); plt.close()

# ── Stacked Area + YoY Growth ─────────────────────────────────────────────────
cat_yr = run_query(f"""
    SELECT t.order_year, p.category, ROUND(SUM(t.final_amount_inr)/1e7,2) AS rev_cr
    FROM transactions t JOIN products p ON t.product_id=p.product_id
    WHERE {fs['wt']} {fs['wsub']}
    GROUP BY t.order_year, p.category ORDER BY t.order_year
""")
cat_pivot = cat_yr.pivot_table(index='order_year', columns='category', values='rev_cr', aggfunc='sum').fillna(0)

col_l2, col_r2 = st.columns(2)
with col_l2:
    st.markdown("<div class='section-header'>📊 Revenue by Category (Stacked Area)</div>", unsafe_allow_html=True)
    fig_area = go.Figure()
    for i, cat in enumerate(cat_pivot.columns):
        clr = px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)]
        fig_area.add_trace(go.Scatter(x=cat_pivot.index, y=cat_pivot[cat], mode='lines',
                                       name=cat, stackgroup='one',
                                       fillcolor=clr, line=dict(width=0.5, color=clr)))
    fig_area.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                            height=380, margin=dict(t=30,b=20), yaxis=dict(title='Revenue (₹ Crores)'),
                            legend=dict(orientation='h',y=1.15,font=dict(size=9)))
    st.plotly_chart(fig_area, use_container_width=True)

with col_r2:
    st.markdown("<div class='section-header'>📈 Category YoY Growth Rate</div>", unsafe_allow_html=True)
    if len(cat_pivot) >= 2:
        growth = ((cat_pivot.iloc[-1]-cat_pivot.iloc[0])/cat_pivot.iloc[0].replace(0,np.nan)*100).dropna().sort_values()
        fig_growth = go.Figure(go.Bar(
            x=growth.values, y=growth.index, orientation='h',
            marker_color=['#3FB950' if v>=0 else '#F85149' for v in growth.values],
            text=[f'{v:+.1f}%' for v in growth.values],
            textposition='outside', textfont=dict(color='white',size=11)))
        fig_growth.add_vline(x=0, line_color='#8B949E', line_width=1)
        fig_growth.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                                  height=380, margin=dict(t=30,b=20,r=60), showlegend=False,
                                  xaxis=dict(title='Growth %'))
        st.plotly_chart(fig_growth, use_container_width=True)

# ── Price vs Demand + Discount vs Revenue ────────────────────────────────────
col_l3, col_r3 = st.columns(2)
with col_l3:
    st.markdown("<div class='section-header'>💸 Price vs Demand (Subcategory)</div>", unsafe_allow_html=True)
    price_df = run_query(f"""
        SELECT p.subcategory,
               ROUND(AVG(t.original_price_inr)/1000,1) AS avg_price_k,
               COUNT(t.transaction_id) AS demand,
               ROUND(SUM(t.final_amount_inr)/1e7,1) AS rev_cr
        FROM transactions t JOIN products p ON t.product_id=p.product_id
        WHERE {fs['wt']} {fs['wsub']}
        GROUP BY p.subcategory
    """)
    fig_sc = px.scatter(price_df, x='avg_price_k', y='demand', size='rev_cr', color='rev_cr',
                         text='subcategory', color_continuous_scale='Plasma',
                         labels={'avg_price_k':'Avg Price (₹K)','demand':'Orders','rev_cr':'Revenue (₹Cr)'})
    fig_sc.update_traces(textposition='top center', textfont=dict(size=9,color='white'))
    fig_sc.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                          height=380, margin=dict(t=30,b=20), coloraxis_showscale=False)
    st.plotly_chart(fig_sc, use_container_width=True)

with col_r3:
    st.markdown("<div class='section-header'>🏷️ Discount % vs Revenue</div>", unsafe_allow_html=True)
    disc_df = run_query(f"""
        SELECT CASE WHEN discount_percent=0 THEN '0% None'
                    WHEN discount_percent<=10 THEN '1-10%'
                    WHEN discount_percent<=20 THEN '11-20%'
                    WHEN discount_percent<=30 THEN '21-30%'
                    WHEN discount_percent<=50 THEN '31-50%'
                    ELSE '50%+' END AS band,
               COUNT(*) AS orders, ROUND(SUM(final_amount_inr)/1e7,2) AS rev_cr,
               ROUND(AVG(final_amount_inr),0) AS avg_aov
        FROM transactions WHERE {fs['w']} {fs['wsub']}
        GROUP BY band ORDER BY MIN(discount_percent)
    """)
    fig_disc, ax_d = plt.subplots(figsize=(8,5))
    fig_disc.patch.set_facecolor('#0E1117'); ax_d.set_facecolor('#0E1117')
    ax_d.bar(disc_df['band'], disc_df['rev_cr'], color='#A855F7', alpha=0.85, edgecolor='#1C2333')
    ax2_d = ax_d.twinx()
    ax2_d.plot(disc_df['band'], disc_df['avg_aov']/1000, 'o-', color='#FFD700', linewidth=2.5, markersize=8, label='AOV (₹K)')
    ax_d.set_xlabel('Discount Band', color='#8B949E', fontsize=9); ax_d.set_ylabel('Revenue (₹ Cr)', color='#8B949E', fontsize=9)
    ax2_d.set_ylabel('AOV (₹K)', color='#FFD700', fontsize=9)
    ax_d.tick_params(colors='#8B949E', labelsize=8); ax_d.set_xticklabels(disc_df['band'], rotation=20, ha='right')
    ax2_d.tick_params(colors='#FFD700', labelsize=8)
    for spine in ax_d.spines.values(): spine.set_color('#30363D')
    ax2_d.legend(loc='upper right', facecolor='#1C2333', edgecolor='#30363D', labelcolor='white', fontsize=8)
    plt.tight_layout()
    st.pyplot(fig_disc, use_container_width=True); plt.close()

# ── Seasonal Radar ─────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🕸️ Seasonal Revenue Pattern (Radar)</div>", unsafe_allow_html=True)
sea_df = run_query(f"""
    SELECT CAST(strftime('%m',order_date) AS INTEGER) AS month, ROUND(AVG(rev),1) AS avg_cr
    FROM (SELECT order_date, ROUND(SUM(final_amount_inr)/1e7,1) AS rev FROM transactions WHERE {fs['w']} {fs['wsub']} GROUP BY order_date)
    GROUP BY month ORDER BY month
""")
if len(sea_df)>0:
    mths = [MONTH_NAMES[int(m)-1] for m in sea_df['month']]
    vals = sea_df['avg_cr'].tolist(); vals.append(vals[0]); mths.append(mths[0])
    fig_r = go.Figure(go.Scatterpolar(r=vals, theta=mths, fill='toself',
                                        fillcolor='rgba(168,85,247,0.25)',
                                        line=dict(color='#A855F7',width=2.5)))
    fig_r.update_layout(template='plotly_dark', paper_bgcolor='#0E1117',
                         polar=dict(bgcolor='#1C2333',
                                    radialaxis=dict(visible=True,color='#8B949E'),
                                    angularaxis=dict(color='#8B949E')),
                         height=400, margin=dict(t=30,b=30))
    st.plotly_chart(fig_r, use_container_width=True)

st.markdown("---")
c1,c2,c3 = st.columns(3)
with c1: st.markdown("<div class='insight-box'>🎃 <b>Oct-Nov consistently peak</b> driven by Diwali — up to 40% higher than average months.</div>", unsafe_allow_html=True)
with c2: st.markdown("<div class='insight-box'>💸 <b>20-30% discount band</b> drives highest revenue volume while 0% discount products have highest AOV.</div>", unsafe_allow_html=True)
with c3: st.markdown("<div class='insight-box'>📱 <b>Smartphones lead all subcategories</b> but show highest price-to-demand inverse relationship.</div>", unsafe_allow_html=True)
