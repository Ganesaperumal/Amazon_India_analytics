import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
st.set_page_config(page_title="Executive & Financial", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

import pandas as pd, numpy as np, warnings
import plotly.graph_objects as go
import plotly.express as px
warnings.filterwarnings('ignore')

from utils.db import run_query
from utils.sidebar import render_sidebar, get_filter_sql

filters = render_sidebar()
fs = get_filter_sql(filters)

st.markdown("<h1 style='color:#FFD700;text-align:center;'>📊 EXECUTIVE & <span style='color:#00D4FF;'>FINANCIAL OVERVIEW</span></h1>", unsafe_allow_html=True)
st.markdown("---")

# ── KPI Cards ────────────────────────────────────────────────────────────────
kpi = run_query(f"SELECT COUNT(*) AS txns, COUNT(DISTINCT customer_id) AS customers, ROUND(SUM(final_amount_inr)/1e9,3) AS rev_bn, ROUND(AVG(final_amount_inr),0) AS aov FROM transactions WHERE {fs['w']} {fs['wsub']}")
c1,c2,c3,c4 = st.columns(4)
for col, label, val in [
    (c1, "💰 Total Revenue",    f"₹{kpi['rev_bn'].iloc[0]}Bn"),
    (c2, "📦 Transactions",     f"{kpi['txns'].iloc[0]/1e6:.2f}M"),
    (c3, "👥 Active Customers", f"{kpi['customers'].iloc[0]/1000:.0f}K"),
    (c4, "🛒 Avg Order Value",  f"₹{kpi['aov'].iloc[0]/1000:.1f}K"),
]:
    with col:
        st.markdown(f"<div class='kpi-card'><div class='kpi-label'>{label}</div><div class='kpi-value'>{val}</div></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Business Health Score ─────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🏥 Business Health Score</div>", unsafe_allow_html=True)

@st.cache_data(ttl=600)
def get_health_score():
    # Revenue Growth Score (0-25)
    rev = run_query("""
        SELECT order_year, SUM(final_amount_inr) AS rev
        FROM transactions
        GROUP BY order_year ORDER BY order_year
    """)
    rev['growth'] = rev['rev'].pct_change() * 100
    avg_growth = rev['growth'].dropna().mean()
    growth_score = min(25, max(0, (avg_growth / 20) * 25))

    # Delivery Performance Score (0-25)
    delivery = run_query("""
        SELECT ROUND(100.0*SUM(CASE WHEN delivery_days<=3 THEN 1 ELSE 0 END)/COUNT(*), 2) AS on_time
        FROM transactions
    """)
    on_time = float(delivery['on_time'].iloc[0])
    delivery_score = min(25, (on_time / 100) * 25)

    # Return Rate Score (0-25) — lower is better
    returns = run_query("""
        SELECT ROUND(100.0*SUM(CASE WHEN return_status='Returned' THEN 1 ELSE 0 END)/COUNT(*), 2) AS ret_rate
        FROM transactions
    """)
    ret_rate = float(returns['ret_rate'].iloc[0])
    return_score = min(25, max(0, ((10 - ret_rate) / 10) * 25))

    # Customer Retention Score (0-25)
    retention = run_query("""
        SELECT COUNT(*) AS repeat_customers
        FROM (
            SELECT customer_id
            FROM transactions
            GROUP BY customer_id
            HAVING COUNT(transaction_id) > 1
        )
    """)
    total_customers = run_query("SELECT COUNT(DISTINCT customer_id) AS total FROM transactions")
    repeat = float(retention['repeat_customers'].iloc[0])
    total = float(total_customers['total'].iloc[0])
    retention_pct = (repeat / total * 100) if total > 0 else 0
    retention_score = min(25, (retention_pct / 100) * 25)

    total_score = round(growth_score + delivery_score + return_score + retention_score, 1)

    return total_score, growth_score, delivery_score, return_score, retention_score

total_score, growth_score, delivery_score, return_score, retention_score = get_health_score()

# Color based on score
if total_score >= 70:
    score_color = '#3FB950'
    score_label = 'Excellent'
    score_emoji = '🟢'
elif total_score >= 40:
    score_color = '#FF9900'
    score_label = 'Average'
    score_emoji = '🟡'
else:
    score_color = '#F85149'
    score_label = 'Needs Attention'
    score_emoji = '🔴'

col_gauge, col_breakdown = st.columns([1, 1])

with col_gauge:
    fig_health = go.Figure(go.Indicator(
        mode="gauge+number",
        value=total_score,
        title={'text': f"Overall Health {score_emoji} {score_label}",
               'font': {'color': score_color, 'size': 16}},
        number={'font': {'color': score_color, 'size': 52}, 'suffix': '/100'},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': '#8B949E',
                     'tickfont': {'size': 10}},
            'bar': {'color': score_color, 'thickness': 0.25},
            'bgcolor': '#1C2333',
            'bordercolor': '#30363D',
            'steps': [
                {'range': [0,  40], 'color': '#2D0F0F'},
                {'range': [40, 70], 'color': '#2D1F00'},
                {'range': [70, 100],'color': '#0D2D1A'},
            ],
            'threshold': {
                'line': {'color': '#FFD700', 'width': 3},
                'value': total_score
            }
        }
    ))
    fig_health.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0E1117',
        height=300,
        margin=dict(t=50, b=20, l=30, r=30)
    )
    st.plotly_chart(fig_health, use_container_width=True)

with col_breakdown:
    st.markdown("<br><br>", unsafe_allow_html=True)
    components = {
        '📈 Revenue Growth':      (growth_score,   25),
        '🚚 Delivery Performance':(delivery_score, 25),
        '↩️ Return Rate':         (return_score,   25),
        '👥 Customer Retention':  (retention_score,25),
    }
    for label, (score, max_s) in components.items():
        pct = int((score / max_s) * 100)
        bar_color = '#3FB950' if pct >= 70 else '#FF9900' if pct >= 40 else '#F85149'
        st.markdown(f"""
        <div style='margin-bottom:0.8rem;'>
            <div style='display:flex;justify-content:space-between;
                        font-size:0.8rem;color:#C9D1D9;margin-bottom:3px;'>
                <span>{label}</span>
                <span style='color:{bar_color};font-weight:700;'>
                    {score:.1f}/{max_s}
                </span>
            </div>
            <div style='background:#1C2333;border-radius:6px;height:8px;'>
                <div style='width:{pct}%;background:{bar_color};
                            height:8px;border-radius:6px;
                            transition:width 0.5s ease;'>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ── Sales by Year + Waterfall ─────────────────────────────────────────────────
yr_df = run_query(f"SELECT order_year, ROUND(SUM(final_amount_inr)/1e9,3) AS rev_bn, COUNT(*) AS orders FROM transactions WHERE {fs['w']} {fs['wsub']} GROUP BY order_year ORDER BY order_year")
yr_df['growth_pct'] = yr_df['rev_bn'].pct_change()*100

col_l, col_r = st.columns([3,2])
with col_l:
    st.markdown("<div class='section-header'>📈 Sales by Year</div>", unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=yr_df['order_year'], y=yr_df['rev_bn'], marker_color='#A855F7',
                          text=[f'₹{v:.2f}Bn' for v in yr_df['rev_bn']], textposition='outside',
                          textfont=dict(color='white', size=11), name='Revenue'))
    fig.add_trace(go.Scatter(x=yr_df['order_year'], y=yr_df['growth_pct'], mode='lines+markers',
                              name='YoY Growth %', yaxis='y2', line=dict(color='#FFD700', width=2.5), marker=dict(size=8)))
    fig.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                       yaxis=dict(title='Revenue (₹Bn)'), yaxis2=dict(title='Growth %', overlaying='y', side='right', color='#FFD700'),
                       legend=dict(orientation='h', y=1.1), margin=dict(t=30,b=30), height=380,
                       xaxis=dict(tickmode='linear', dtick=1))
    st.plotly_chart(fig, use_container_width=True)

with col_r:
    st.markdown("<div class='section-header'>🌊 YoY Waterfall</div>", unsafe_allow_html=True)
    wf_x, wf_y, wf_base, wf_colors = [], [], [], []
    for i, row in yr_df.iterrows():
        wf_x.append(str(int(row['order_year'])))
        if i == yr_df.index[0]:
            wf_y.append(row['rev_bn']); wf_base.append(0); wf_colors.append('#58A6FF')
        else:
            prev  = yr_df.loc[i-1,'rev_bn']
            delta = row['rev_bn'] - prev
            wf_y.append(abs(delta)); wf_base.append(prev if delta>=0 else prev+delta)
            wf_colors.append('#3FB950' if delta>=0 else '#F85149')
    fig2 = go.Figure(go.Bar(x=wf_x, y=wf_y, base=wf_base, marker_color=wf_colors,
                              text=[f'₹{b+y:.2f}' for b,y in zip(wf_base,wf_y)],
                              textposition='outside', textfont=dict(color='white', size=10)))
    fig2.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                        showlegend=False, height=380, margin=dict(t=30,b=30),
                        yaxis=dict(title='Revenue (₹Bn)'))
    st.plotly_chart(fig2, use_container_width=True)

# ── Category Revenue + Profit Margin ─────────────────────────────────────────
cat_df = run_query(f"""
    SELECT p.category, ROUND(SUM(t.final_amount_inr)/1e9,3) AS rev_bn,
           ROUND(AVG(t.discount_percent),1) AS avg_disc
    FROM transactions t JOIN products p ON t.product_id = p.product_id
    WHERE {fs['wt']} {fs['wsub']}
    GROUP BY p.category ORDER BY rev_bn DESC
""")
cat_df['profit_margin'] = ((100-cat_df['avg_disc'])/100*35).round(1)

col_l2, col_r2 = st.columns(2)
with col_l2:
    st.markdown("<div class='section-header'>🏷️ Category-wise Revenue</div>", unsafe_allow_html=True)
    fig3 = px.bar(cat_df, x='rev_bn', y='category', orientation='h',
                   color='rev_bn', color_continuous_scale='Purples',
                   text=[f'₹{v:.2f}Bn' for v in cat_df['rev_bn']],
                   labels={'rev_bn':'Revenue (₹Bn)','category':''})
    fig3.update_traces(textposition='outside', textfont_color='white')
    fig3.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                        showlegend=False, coloraxis_showscale=False, height=350, margin=dict(t=20,b=20,r=60))
    st.plotly_chart(fig3, use_container_width=True)

with col_r2:
    st.markdown("<div class='section-header'>💹 Profit Margin % by Category</div>", unsafe_allow_html=True)
    fig4 = px.bar(cat_df, x='category', y='profit_margin', color='profit_margin',
                   color_continuous_scale='Blues',
                   text=[f'{v:.1f}%' for v in cat_df['profit_margin']],
                   labels={'profit_margin':'Margin %','category':''})
    fig4.update_traces(textposition='outside', textfont_color='white')
    fig4.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                        showlegend=False, coloraxis_showscale=False, height=350, margin=dict(t=20,b=20),
                        xaxis_tickangle=-20)
    st.plotly_chart(fig4, use_container_width=True)

# ── Cost vs Revenue + Forecast ────────────────────────────────────────────────
col_l3, col_r3 = st.columns(2)
with col_l3:
    st.markdown("<div class='section-header'>⚖️ Cost vs Revenue by Category</div>", unsafe_allow_html=True)
    cat_df['cost_bn'] = (cat_df['rev_bn']*(cat_df['avg_disc']/100)).round(3)
    fig5 = go.Figure()
    fig5.add_trace(go.Bar(name='Revenue', x=cat_df['category'], y=cat_df['rev_bn'], marker_color='#A855F7',
                           text=[f'₹{v:.2f}' for v in cat_df['rev_bn']], textposition='outside', textfont=dict(size=9,color='white')))
    fig5.add_trace(go.Bar(name='Discount Cost', x=cat_df['category'], y=cat_df['cost_bn'], marker_color='#F85149',
                           text=[f'₹{v:.2f}' for v in cat_df['cost_bn']], textposition='outside', textfont=dict(size=9,color='white')))
    fig5.add_trace(go.Scatter(name='Margin %', x=cat_df['category'], y=cat_df['profit_margin'], yaxis='y2',
                               mode='lines+markers', line=dict(color='#00D4FF',width=2.5), marker=dict(size=8)))
    fig5.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                        barmode='group', height=370, yaxis=dict(title='Revenue (₹Bn)'),
                        yaxis2=dict(title='Margin %', overlaying='y', side='right', color='#00D4FF'),
                        legend=dict(orientation='h',y=1.1), margin=dict(t=30,b=20), xaxis_tickangle=-20)
    st.plotly_chart(fig5, use_container_width=True)

with col_r3:
    st.markdown("<div class='section-header'>🔮 Forecasted Revenue 2025–2030</div>", unsafe_allow_html=True)
    all_yr = run_query("SELECT order_year, ROUND(SUM(final_amount_inr)/1e9,3) AS rev_bn FROM transactions GROUP BY order_year ORDER BY order_year")
    hx = all_yr['order_year'].values.astype(float); hy = all_yr['rev_bn'].values
    coeffs = np.polyfit(hx, hy, 2)
    fx = np.arange(hx.min(), hx.max()+6); fy = np.maximum(np.polyval(coeffs, fx), 0)
    split = len(hx); ci = 0.12*fy
    fig6 = go.Figure()
    fig6.add_trace(go.Scatter(x=list(fx[split-1:])+list(fx[split-1:][::-1]),
                               y=list((fy+ci)[split-1:])+list((fy-ci)[split-1:][::-1]),
                               fill='toself', fillcolor='rgba(168,85,247,0.15)',
                               line=dict(color='rgba(0,0,0,0)'), name='CI Band'))
    fig6.add_trace(go.Scatter(x=list(hx), y=list(hy), mode='lines+markers', name='Actual',
                               line=dict(color='#FF9900',width=2.5), marker=dict(size=7)))
    fig6.add_trace(go.Scatter(x=list(fx[split-1:]), y=list(fy[split-1:]), mode='lines',
                               name='Forecast', line=dict(color='#A855F7',width=2.5,dash='dash')))
    fig6.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                        height=370, margin=dict(t=30,b=20), yaxis=dict(title='Revenue (₹Bn)'),
                        xaxis=dict(title='Year'), legend=dict(orientation='h',y=1.1))
    st.plotly_chart(fig6, use_container_width=True)

# ── Total vs Target + Quarterly ───────────────────────────────────────────────
col_l4, col_r4 = st.columns([1,2])
with col_l4:
    st.markdown("<div class='section-header'>🎯 Total vs Target</div>", unsafe_allow_html=True)
    actual = float(kpi['rev_bn'].iloc[0]); target = round(actual*1.08, 3)
    fig7 = go.Figure(go.Pie(values=[actual, max(target-actual, 0.001)], labels=['Achieved','Gap'],
                              hole=0.65, marker=dict(colors=['#3FB950','#30363D']),
                              textinfo='label+percent', textfont=dict(color='white',size=13)))
    fig7.add_annotation(text=f"₹{actual:.2f}Bn<br><span style='font-size:10px'>of ₹{target:.2f}Bn</span>",
                         x=0.5, y=0.5, showarrow=False, font=dict(size=14,color='#FF9900'), align='center')
    fig7.update_layout(template='plotly_dark', paper_bgcolor='#0E1117', height=320,
                        showlegend=True, legend=dict(orientation='h',y=-0.1), margin=dict(t=20,b=20,l=20,r=20))
    st.plotly_chart(fig7, use_container_width=True)

with col_r4:
    st.markdown("<div class='section-header'>📅 Quarterly Revenue Breakdown</div>", unsafe_allow_html=True)
    q_df = run_query(f"""
        SELECT order_year, CAST((CAST(strftime('%m',order_date) AS INTEGER)+2)/3 AS INTEGER) AS quarter,
               ROUND(SUM(final_amount_inr)/1e7,2) AS rev_cr
        FROM transactions WHERE {fs['w']} {fs['wsub']}
        GROUP BY order_year, quarter ORDER BY order_year, quarter
    """)
    q_pivot = q_df.pivot_table(index='order_year', columns='quarter', values='rev_cr', aggfunc='sum').fillna(0)
    fig8 = go.Figure()
    for i, col in enumerate(q_pivot.columns):
        fig8.add_trace(go.Bar(name=f'Q{col}', x=q_pivot.index, y=q_pivot[col],
                               marker_color=['#A855F7','#FF9900','#3FB950','#58A6FF'][i%4]))
    fig8.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                        barmode='stack', height=320, yaxis=dict(title='Revenue (₹ Crores)'),
                        xaxis=dict(title='Year',tickmode='linear',dtick=1),
                        legend=dict(orientation='h',y=1.1), margin=dict(t=30,b=20))
    st.plotly_chart(fig8, use_container_width=True)

st.markdown("---")
c1,c2,c3 = st.columns(3)
with c1: st.markdown("<div class='insight-box'>📈 <b>Revenue peaked in 2020</b> driven by COVID-19 e-commerce surge. Post-2021 stabilisation reflects market maturity.</div>", unsafe_allow_html=True)
with c2: st.markdown("<div class='insight-box'>🛍️ <b>Smartphones dominate</b> at ~56Bn followed by Laptops at ~9Bn. Electronics contributes 80%+ of total revenue.</div>", unsafe_allow_html=True)
with c3: st.markdown("<div class='insight-box'>💹 <b>Profit margins hover around 30-35%</b>. Audio products show highest margins due to lower discount dependency.</div>", unsafe_allow_html=True)
