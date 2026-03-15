import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
st.set_page_config(page_title="Payment & Operations", page_icon="💳", layout="wide", initial_sidebar_state="expanded")

import numpy as np, warnings
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
warnings.filterwarnings('ignore')

from utils.db import run_query
from utils.sidebar import render_sidebar, get_filter_sql

filters = render_sidebar()
fs = get_filter_sql(filters)

st.markdown("<h1 style='color:#FFD700;text-align:center;'>💳 PAYMENT & <span style='color:#00D4FF;'>OPERATIONS</span></h1>", unsafe_allow_html=True)
st.markdown("---")

ops = run_query(f"""
    SELECT ROUND(AVG(delivery_days),2) AS avg_del,
           ROUND(100.0*SUM(CASE WHEN delivery_days<=3 THEN 1 ELSE 0 END)/COUNT(*),2) AS on_time_pct,
           ROUND(100.0*SUM(CASE WHEN return_status='Returned'  THEN 1 ELSE 0 END)/COUNT(*),2) AS return_rate,
           ROUND(100.0*SUM(CASE WHEN return_status='Cancelled' THEN 1 ELSE 0 END)/COUNT(*),2) AS cancel_rate
    FROM transactions WHERE {fs['w']} {fs['wsub']}
""")

# ── 4 KPI Gauges ──────────────────────────────────────────────────────────────
c1,c2,c3,c4 = st.columns(4)
gauge_configs = [
    ('On-Time Delivery %',   float(ops['on_time_pct'].iloc[0]),  100, 90, False, c1),
    ('Avg Delivery Days',    float(ops['avg_del'].iloc[0]),       10,  3, True,  c2),
    ('Return Rate %',        float(ops['return_rate'].iloc[0]),   20,  5, True,  c3),
    ('Cancellation Rate %',  float(ops['cancel_rate'].iloc[0]),   20,  5, True,  c4),
]
for title, value, max_val, target, inverse, col in gauge_configs:
    with col:
        good = '#3FB950' if not inverse else '#F85149'
        bad  = '#F85149' if not inverse else '#3FB950'
        bar_c = good if (value<=target if inverse else value>=target) else bad
        fig_g = go.Figure(go.Indicator(
            mode='gauge+number+delta', value=value,
            delta={'reference':target,'valueformat':'.1f',
                   'increasing':{'color':'#3FB950' if not inverse else '#F85149'},
                   'decreasing':{'color':'#F85149' if not inverse else '#3FB950'}},
            title={'text':title,'font':{'color':'#FF9900','size':12}},
            number={'font':{'color':'white','size':32},'valueformat':'.1f'},
            gauge={'axis':{'range':[0,max_val],'tickcolor':'#8B949E','tickfont':{'size':9}},
                   'bar':{'color':bar_c,'thickness':0.25},
                   'bgcolor':'#1C2333','bordercolor':'#30363D',
                   'steps':[{'range':[0,target],'color':'#0D4A1F' if not inverse else '#4D0F0F'},
                              {'range':[target,max_val],'color':'#4D0F0F' if not inverse else '#0D4A1F'}],
                   'threshold':{'line':{'color':'#FFD700','width':2},'value':target}}))
        fig_g.update_layout(template='plotly_dark', paper_bgcolor='#0E1117',
                             height=220, margin=dict(t=30,b=10,l=10,r=10))
        st.plotly_chart(fig_g, use_container_width=True)
        st.markdown(f"<div style='text-align:center;font-size:0.7rem;color:#8B949E;margin-top:-10px;'>Target: {'<' if inverse else '>'}{target}</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Payment Evolution ─────────────────────────────────────────────────────────
pay_df = run_query(f"""
    SELECT order_year, payment_method, COUNT(*) AS orders,
           ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER (PARTITION BY order_year),2) AS share_pct
    FROM transactions WHERE {fs['w']} {fs['wsub']}
    GROUP BY order_year, payment_method ORDER BY order_year
""")
pay_pivot = pay_df.pivot_table(index='order_year', columns='payment_method', values='share_pct', aggfunc='sum').fillna(0)
PAY_C = {'UPI':'#3FB950','Cash on Delivery':'#F85149','Credit Card':'#58A6FF',
          'Debit Card':'#FF9900','Net Banking':'#A855F7','Wallet':'#FFD700','BNPL':'#00D4FF'}

col_l, col_r = st.columns(2)
with col_l:
    st.markdown("<div class='section-header'>📊 Payment Method — Stacked Area</div>", unsafe_allow_html=True)
    fig_area = go.Figure()
    for m in pay_pivot.columns:
        clr = PAY_C.get(m,'#8B949E')
        fig_area.add_trace(go.Scatter(x=pay_pivot.index, y=pay_pivot[m], mode='lines',
                                       name=m, stackgroup='one', line=dict(width=0.5,color=clr), fillcolor=clr))
    fig_area.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                            height=380, yaxis=dict(title='Market Share %'),
                            xaxis=dict(title='Year',tickmode='linear',dtick=1),
                            legend=dict(orientation='h',y=1.15,font=dict(size=9)), margin=dict(t=20,b=20))
    st.plotly_chart(fig_area, use_container_width=True)

with col_r:
    st.markdown("<div class='section-header'>📈 Payment Method Trends (Line)</div>", unsafe_allow_html=True)
    fig_line = go.Figure()
    for m in pay_pivot.columns:
        clr = PAY_C.get(m,'#8B949E')
        fig_line.add_trace(go.Scatter(x=pay_pivot.index, y=pay_pivot[m], mode='lines+markers',
                                       name=m, line=dict(width=2.5,color=clr), marker=dict(size=7)))
        fig_line.add_annotation(x=pay_pivot.index[-1], y=pay_pivot[m].iloc[-1],
                                  text=f'{pay_pivot[m].iloc[-1]:.1f}%', xanchor='left',
                                  font=dict(size=9,color=clr), showarrow=False, xshift=5)
    fig_line.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                            height=380, yaxis=dict(title='Market Share %'),
                            xaxis=dict(title='Year',tickmode='linear',dtick=1),
                            legend=dict(orientation='h',y=1.15,font=dict(size=9)), margin=dict(t=20,b=20,r=60))
    st.plotly_chart(fig_line, use_container_width=True)

# ── First vs Last Year + Current Donut ────────────────────────────────────────
col_l2, col_r2 = st.columns([2,1])
with col_l2:
    st.markdown("<div class='section-header'>📊 First vs Last Year Payment Mix</div>", unsafe_allow_html=True)
    if len(pay_pivot) >= 2:
        fy, ly = pay_pivot.index.min(), pay_pivot.index.max()
        methods = pay_pivot.columns
        x = np.arange(len(methods)); w = 0.35
        fig_comp, ax_c = plt.subplots(figsize=(10,4))
        fig_comp.patch.set_facecolor('#0E1117'); ax_c.set_facecolor('#0E1117')
        ax_c.bar(x-w/2, pay_pivot.loc[fy], w, label=str(fy), color='#8B949E', alpha=0.85, edgecolor='#30363D')
        ax_c.bar(x+w/2, pay_pivot.loc[ly], w, label=str(ly), color='#A855F7', alpha=0.88, edgecolor='#30363D')
        ax_c.set_xticks(x); ax_c.set_xticklabels(methods, rotation=20, ha='right', color='#8B949E', fontsize=8)
        ax_c.set_ylabel('Market Share %', color='#8B949E', fontsize=9); ax_c.tick_params(colors='#8B949E')
        ax_c.legend(facecolor='#1C2333', edgecolor='#30363D', labelcolor='white', fontsize=9)
        for sp in ax_c.spines.values(): sp.set_color('#30363D')
        plt.tight_layout(); st.pyplot(fig_comp, use_container_width=True); plt.close()

with col_r2:
    st.markdown("<div class='section-header'>🍩 Current Payment Mix</div>", unsafe_allow_html=True)
    cur = pay_df[pay_df['order_year']==pay_df['order_year'].max()]
    fig_dn = go.Figure(go.Pie(values=cur['orders'], labels=cur['payment_method'], hole=0.55,
                               marker=dict(colors=[PAY_C.get(m,'#8B949E') for m in cur['payment_method']]),
                               textinfo='label+percent', textfont=dict(color='white',size=10)))
    fig_dn.update_layout(template='plotly_dark', paper_bgcolor='#0E1117',
                          height=350, showlegend=False, margin=dict(t=20,b=20))
    st.plotly_chart(fig_dn, use_container_width=True)

# ── Delivery by Tier + Distribution ──────────────────────────────────────────
col_l3, col_r3 = st.columns(2)
TIER_C = {'Metro':'#FFD700','Tier1':'#A855F7','Tier2':'#58A6FF','Rural':'#3FB950'}
with col_l3:
    st.markdown("<div class='section-header'>🚚 Avg Delivery Days by Tier</div>", unsafe_allow_html=True)
    td = run_query(f"""
        SELECT c.customer_tier, ROUND(AVG(t.delivery_days),2) AS avg_days
        FROM transactions t JOIN customers c ON t.customer_id=c.customer_id
        WHERE {fs['wt']} {fs['wc']}
        GROUP BY c.customer_tier ORDER BY avg_days
    """)
    fig_td = go.Figure(go.Bar(x=td['customer_tier'], y=td['avg_days'],
                               marker_color=[TIER_C.get(str(t),'#8B949E') for t in td['customer_tier']],
                               text=[f'{v:.2f}d' for v in td['avg_days']],
                               textposition='outside', textfont=dict(color='white',size=12)))
    fig_td.add_hline(y=3, line_color='#FFD700', line_dash='dash',
                      annotation_text='Target: 3 days', annotation_font=dict(color='#FFD700',size=10))
    fig_td.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                          height=350, showlegend=False, yaxis=dict(title='Avg Delivery Days'),
                          xaxis=dict(title=''), margin=dict(t=30,b=20))
    st.plotly_chart(fig_td, use_container_width=True)

with col_r3:
    st.markdown("<div class='section-header'>📊 Delivery Days Distribution</div>", unsafe_allow_html=True)
    dd = run_query(f"""
        SELECT delivery_days, COUNT(*) AS cnt FROM transactions
        WHERE {fs['w']} {fs['wsub']} AND delivery_days BETWEEN 0 AND 15
        GROUP BY delivery_days ORDER BY delivery_days
    """)
    fig_dd, ax_dd = plt.subplots(figsize=(8,4.2))
    fig_dd.patch.set_facecolor('#0E1117'); ax_dd.set_facecolor('#0E1117')
    ax_dd.bar(dd['delivery_days'], dd['cnt']/1000, color='#A855F7', alpha=0.88, edgecolor='#1C2333', width=0.7)
    ax_dd.axvline(x=3, color='#FFD700', linestyle='--', linewidth=2, label='Target 3 days')
    ax_dd.set_xlabel('Delivery Days', color='#8B949E', fontsize=9); ax_dd.set_ylabel('Orders (K)', color='#8B949E', fontsize=9)
    ax_dd.tick_params(colors='#8B949E', labelsize=8)
    ax_dd.legend(facecolor='#1C2333', edgecolor='#30363D', labelcolor='white', fontsize=8)
    for sp in ax_dd.spines.values(): sp.set_color('#30363D')
    plt.tight_layout(); st.pyplot(fig_dd, use_container_width=True); plt.close()

# ── Return Rate + Satisfaction Scatter ────────────────────────────────────────
col_l4, col_r4 = st.columns(2)
with col_l4:
    st.markdown("<div class='section-header'>↩️ Return Rate by Subcategory</div>", unsafe_allow_html=True)
    ret = run_query(f"""
        SELECT p.subcategory,
               ROUND(100.0*SUM(CASE WHEN t.return_status='Returned' THEN 1 ELSE 0 END)/COUNT(*),2) AS return_pct,
               COUNT(*) AS orders
        FROM transactions t JOIN products p ON t.product_id=p.product_id
        WHERE {fs['wt']} {fs['wsub']} GROUP BY p.subcategory HAVING orders>100
        ORDER BY return_pct DESC LIMIT 12
    """)
    fig_ret = px.bar(ret, x='return_pct', y='subcategory', orientation='h',
                      color='return_pct', color_continuous_scale='Reds',
                      text=[f'{v:.1f}%' for v in ret['return_pct']],
                      labels={'return_pct':'Return %','subcategory':''})
    fig_ret.update_traces(textposition='outside', textfont_color='white', textfont_size=10)
    fig_ret.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                           height=400, coloraxis_showscale=False, showlegend=False, margin=dict(t=20,b=20,r=60))
    st.plotly_chart(fig_ret, use_container_width=True)

with col_r4:
    st.markdown("<div class='section-header'>😊 Rating vs Delivery Speed</div>", unsafe_allow_html=True)
    rd = run_query(f"""
        SELECT delivery_days AS del_days, ROUND(AVG(customer_rating),2) AS avg_rating,
               COUNT(*) AS cnt, customer_tier
        FROM (SELECT t.delivery_days, t.customer_rating, c.customer_tier
              FROM transactions t JOIN customers c ON t.customer_id=c.customer_id
              WHERE {fs['wt']} {fs['wc']}
                AND t.delivery_days BETWEEN 0 AND 14 AND t.customer_rating IS NOT NULL)
        GROUP BY delivery_days, customer_tier
    """)
    fig_rd = px.scatter(rd, x='del_days', y='avg_rating', size='cnt', color='customer_tier',
                         color_discrete_map=TIER_C,
                         labels={'del_days':'Delivery Days','avg_rating':'Avg Rating','customer_tier':'Tier'})
    fig_rd.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                          height=400, legend=dict(orientation='h',y=1.1,font=dict(size=9)), margin=dict(t=20,b=20))
    st.plotly_chart(fig_rd, use_container_width=True)

# ── Supplier Table ─────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("<div class='section-header'>🏭 Supplier Performance (by Brand)</div>", unsafe_allow_html=True)
sup = run_query(f"""
    SELECT p.brand, COUNT(t.transaction_id) AS orders, ROUND(AVG(t.delivery_days),2) AS avg_del,
           ROUND(100.0*SUM(CASE WHEN t.delivery_days<=3 THEN 1 ELSE 0 END)/COUNT(*),1) AS on_time_pct,
           ROUND(100.0*SUM(CASE WHEN t.return_status='Returned' THEN 1 ELSE 0 END)/COUNT(*),1) AS ret_pct,
           ROUND(AVG(t.customer_rating),2) AS avg_rating
    FROM transactions t JOIN products p ON t.product_id=p.product_id
    WHERE {fs['wt']} {fs['wsub']}
    GROUP BY p.brand ORDER BY on_time_pct DESC LIMIT 20
""")
sup['Status'] = sup['avg_del'].apply(lambda x: '✅ On Time' if x<=3 else ('⚠️ Delay' if x<=5 else '❌ Critical'))
sup.columns = ['Brand','Orders','Avg Del.Days','On-Time %','Return %','Avg Rating','Status']
st.dataframe(sup, use_container_width=True, hide_index=True)
