import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
st.set_page_config(page_title="Customer Analytics", page_icon="👥", layout="wide", initial_sidebar_state="expanded")


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

st.markdown("<h1 style='color:#FFD700;text-align:center;'>👥 CUSTOMER <span style='color:#00D4FF;'>ANALYTICS</span></h1>", unsafe_allow_html=True)
st.markdown("---")

SEG_COLORS = {'Champions':'#FFD700','Loyal Customers':'#3FB950','Potential Loyalists':'#58A6FF',
              'Recent Customers':'#A855F7','At Risk':'#FF9900','Others':'#8B949E'}

@st.cache_data(ttl=600)
def build_rfm(w, wsub):
    rfm_raw = run_query(f"""
        SELECT customer_id, MAX(order_date) AS last_date,
               COUNT(transaction_id) AS frequency, ROUND(SUM(final_amount_inr),2) AS monetary
        FROM transactions WHERE {w} {wsub}
        GROUP BY customer_id
    """)
    max_date = pd.to_datetime(rfm_raw['last_date']).max() + pd.Timedelta(days=1)
    rfm_raw['recency'] = (max_date - pd.to_datetime(rfm_raw['last_date'])).dt.days
    for col, label, asc in [('recency','r',False),('frequency','f',True),('monetary','m',True)]:
        try:
            vals = rfm_raw[col] if asc else -rfm_raw[col]
            rfm_raw[f'{label}_score'] = pd.qcut(vals, 5, labels=[1,2,3,4,5], duplicates='drop').astype(int)
        except: rfm_raw[f'{label}_score'] = 3
    rfm_raw['rfm_score'] = rfm_raw['r_score']+rfm_raw['f_score']+rfm_raw['m_score']
    def seg(r):
        s = r['rfm_score']
        if s>=12: return 'Champions'
        elif s>=9: return 'Loyal Customers'
        elif s>=7: return 'Potential Loyalists'
        elif s>=5: return 'Recent Customers'
        elif s>=3: return 'At Risk'
        else: return 'Others'
    rfm_raw['segment'] = rfm_raw.apply(seg, axis=1)
    return rfm_raw

rfm = build_rfm(fs['w'], fs['wsub'])

# ── RFM Scatter + Donut ───────────────────────────────────────────────────────
col_l, col_r = st.columns([2,1])
with col_l:
    st.markdown("<div class='section-header'>🎯 RFM Segmentation — Recency vs Monetary</div>", unsafe_allow_html=True)
    samp = rfm.sample(min(3000, len(rfm)), random_state=42)
    fig_rfm = px.scatter(samp, x='recency', y='monetary', color='segment', size='frequency',
                          color_discrete_map=SEG_COLORS, opacity=0.6,
                          labels={'recency':'Recency (days)','monetary':'Total Spend (₹)'})
    fig_rfm.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                           height=420, margin=dict(t=20,b=20),
                           legend=dict(orientation='h',y=1.1,font=dict(size=9)))
    st.plotly_chart(fig_rfm, use_container_width=True)

with col_r:
    st.markdown("<div class='section-header'>🍩 Segment Distribution</div>", unsafe_allow_html=True)
    sc = rfm['segment'].value_counts().reset_index(); sc.columns = ['segment','count']
    fig_donut = go.Figure(go.Pie(values=sc['count'], labels=sc['segment'], hole=0.55,
                                  marker=dict(colors=[SEG_COLORS.get(s,'#8B949E') for s in sc['segment']]),
                                  textinfo='label+percent', textfont=dict(color='white',size=10)))
    fig_donut.update_layout(template='plotly_dark', paper_bgcolor='#0E1117',
                             height=420, margin=dict(t=20,b=20,l=10,r=10))
    st.plotly_chart(fig_donut, use_container_width=True)

# ── Customer Persona Cards ────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🎭 Customer Persona Cards</div>", unsafe_allow_html=True)

PERSONA_META = {
    'Champions':           {'emoji': '👑', 'color': '#FFD700', 'desc': 'Your best customers. Buy often, spend big, bought recently.'},
    'Loyal Customers':     {'emoji': '⭐', 'color': '#3FB950', 'desc': 'Regular buyers with strong engagement and trust.'},
    'Potential Loyalists': {'emoji': '🌱', 'color': '#58A6FF', 'desc': 'Recent customers with good frequency — nurture them.'},
    'Recent Customers':    {'emoji': '🆕', 'color': '#A855F7', 'desc': 'Bought recently but not yet frequent — engage now.'},
    'At Risk':             {'emoji': '⚠️', 'color': '#F85149', 'desc': 'Used to buy often but gone quiet — win them back.'},
    'Others':              {'emoji': '💤', 'color': '#8B949E', 'desc': 'Low engagement across all RFM dimensions.'},
}

@st.cache_data(ttl=600)
def get_persona_details(w, wsub):
    return run_query(f"""
        SELECT 
            t.customer_id,
            MAX(t.order_date) AS last_date,
            COUNT(t.transaction_id) AS frequency,
            ROUND(SUM(t.final_amount_inr), 2) AS monetary,
            p.category AS top_category,
            t.payment_method AS top_payment,
            c.customer_tier AS tier
        FROM transactions t
        JOIN products p ON t.product_id = p.product_id
        JOIN customers c ON t.customer_id = c.customer_id
        WHERE {w} {wsub}
        GROUP BY t.customer_id, p.category, t.payment_method, c.customer_tier
    """)

persona_raw = get_persona_details(fs['w'], fs['wsub'])

# Merge with RFM segments
rfm_seg = rfm[['customer_id', 'segment', 'monetary', 'frequency']].copy()
persona_merged = persona_raw.merge(rfm_seg, on='customer_id', how='left')
persona_merged['segment'] = persona_merged['segment'].fillna('Others')

# Build persona summary per segment
persona_summary = []
for seg in PERSONA_META.keys():
    seg_df = persona_merged[persona_merged['segment'] == seg]
    if len(seg_df) == 0:
        continue

    top_cat     = seg_df['top_category'].mode()[0] if len(seg_df) > 0 else 'N/A'
    top_pay     = seg_df['top_payment'].mode()[0]  if len(seg_df) > 0 else 'N/A'
    top_tier    = seg_df['tier'].mode()[0]          if len(seg_df) > 0 else 'N/A'
    avg_spend   = seg_df['monetary_y'].mean()       if 'monetary_y' in seg_df else seg_df['monetary_x'].mean()
    count       = seg_df['customer_id'].nunique()

    persona_summary.append({
        'segment':  seg,
        'count':    count,
        'avg_spend': avg_spend,
        'top_cat':  top_cat,
        'top_pay':  top_pay,
        'top_tier': top_tier,
    })

# Render cards — 4 per row
for i in range(0, len(persona_summary), 4):
    cols = st.columns(4)
    for j, col in enumerate(cols):
        if i + j < len(persona_summary):
            p    = persona_summary[i + j]
            meta = PERSONA_META.get(p['segment'], {'emoji':'❓','color':'#8B949E','desc':''})
            with col:
                # Pushed the HTML entirely to the left to avoid Markdown code-block triggers
                html_card = f"""
<div style='background:linear-gradient(135deg,#1C2333,#161B22); border:1px solid {meta["color"]}; border-top:4px solid {meta["color"]}; border-radius:14px; padding:1.2rem; margin-bottom:1rem;'>
    <div style='display:flex;align-items:center;margin-bottom:0.8rem;'>
        <div style='font-size:2.2rem; margin-right:0.8rem; background:#0E1117; border-radius:50%; width:52px; height:52px; line-height:52px; text-align:center;'>{meta["emoji"]}</div>
        <div>
            <div style='font-size:0.95rem; font-weight:700; color:{meta["color"]};'>{p["segment"]}</div>
            <div style='font-size:0.7rem; color:#8B949E;'>{p["count"]:,} customers</div>
        </div>
    </div>
    <div style='font-size:0.75rem; color:#8B949E; font-style:italic; margin-bottom:0.8rem; border-left:3px solid {meta["color"]}; padding-left:0.5rem;'>{meta["desc"]}</div>
    <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 0.4rem;'>
        <div style='padding:0.4rem; background:#0E1117; border-radius:8px;'>
            <div style='font-size:0.6rem; color:#8B949E; text-transform:uppercase; letter-spacing:0.8px;'>Avg Spend</div>
            <div style='font-size:0.85rem; font-weight:700; color:#C9D1D9;'>₹{p["avg_spend"]/1000:.1f}K</div>
        </div>
        <div style='padding:0.4rem; background:#0E1117; border-radius:8px;'>
            <div style='font-size:0.6rem; color:#8B949E; text-transform:uppercase; letter-spacing:0.8px;'>Top Category</div>
            <div style='font-size:0.85rem; font-weight:700; color:#C9D1D9;'>{p["top_cat"]}</div>
        </div>
        <div style='padding:0.4rem; background:#0E1117; border-radius:8px;'>
            <div style='font-size:0.6rem; color:#8B949E; text-transform:uppercase; letter-spacing:0.8px;'>Payment</div>
            <div style='font-size:0.85rem; font-weight:700; color:#C9D1D9;'>{p["top_pay"]}</div>
        </div>
        <div style='padding:0.4rem; background:#0E1117; border-radius:8px;'>
            <div style='font-size:0.6rem; color:#8B949E; text-transform:uppercase; letter-spacing:0.8px;'>City Tier</div>
            <div style='font-size:0.85rem; font-weight:700; color:#C9D1D9;'>{p["top_tier"]}</div>
        </div>
    </div>
</div>
"""
                # Use st.html(html_card) here if your Streamlit version is recent enough!
                st.markdown(html_card, unsafe_allow_html=True)

# ── Segment Avg Metrics ───────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📊 Avg Metrics per RFM Segment</div>", unsafe_allow_html=True)
seg_stats = rfm.groupby('segment').agg(Avg_Spend=('monetary','mean'), Avg_Freq=('frequency','mean'), Count=('customer_id','count')).reset_index().sort_values('Avg_Spend')
fig_seg, axes = plt.subplots(1,2,figsize=(14,4))
fig_seg.patch.set_facecolor('#0E1117')
for ax in axes: ax.set_facecolor('#0E1117')
clrs = [SEG_COLORS.get(s,'#8B949E') for s in seg_stats['segment']]
axes[0].barh(seg_stats['segment'], seg_stats['Avg_Spend']/1000, color=clrs, alpha=0.88)
axes[0].set_xlabel('Avg Spend (₹K)', color='#8B949E', fontsize=9); axes[0].tick_params(colors='#8B949E', labelsize=8)
for sp in axes[0].spines.values(): sp.set_color('#30363D')
axes[1].barh(seg_stats['segment'], seg_stats['Avg_Freq'], color=clrs, alpha=0.88)
axes[1].set_xlabel('Avg Frequency', color='#8B949E', fontsize=9); axes[1].tick_params(colors='#8B949E', labelsize=8)
for sp in axes[1].spines.values(): sp.set_color('#30363D')
plt.tight_layout()
st.pyplot(fig_seg, use_container_width=True); plt.close()

# ── Prime vs Non-Prime ────────────────────────────────────────────────────────
prime_df = run_query(f"""
    SELECT is_prime_member, COUNT(*) AS orders, COUNT(DISTINCT customer_id) AS customers,
           ROUND(SUM(final_amount_inr)/1e7,2) AS rev_cr, ROUND(AVG(final_amount_inr),0) AS avg_aov,
           ROUND(AVG(customer_rating),2) AS avg_rating, ROUND(AVG(delivery_days),2) AS avg_del
    FROM transactions WHERE {fs['w']} {fs['wsub']}
    GROUP BY is_prime_member
""")
prime_df['label'] = prime_df['is_prime_member'].map({1:'Prime',0:'Non-Prime'})

col_l2, col_m2, col_r2 = st.columns(3)
with col_l2:
    st.markdown("<div class='section-header'>👑 Prime vs Non-Prime</div>", unsafe_allow_html=True)
    fig_p = go.Figure(go.Pie(values=prime_df['customers'], labels=prime_df['label'],
                               hole=0.55, marker=dict(colors=['#FFD700','#3FB950']),
                               textinfo='label+percent', textfont=dict(color='white',size=12)))
    fig_p.update_layout(template='plotly_dark', paper_bgcolor='#0E1117',
                         height=300, margin=dict(t=20,b=20), showlegend=False)
    st.plotly_chart(fig_p, use_container_width=True)
with col_m2:
    st.markdown("<div class='section-header'>💰 AOV Comparison</div>", unsafe_allow_html=True)
    fig_aov = go.Figure(go.Bar(x=prime_df['label'], y=prime_df['avg_aov']/1000,
                                marker_color=['#FFD700','#3FB950'],
                                text=[f'₹{v/1000:.1f}K' for v in prime_df['avg_aov']],
                                textposition='outside', textfont=dict(color='white',size=12)))
    fig_aov.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                           height=300, showlegend=False, yaxis=dict(title='AOV (₹K)'), margin=dict(t=30,b=20))
    st.plotly_chart(fig_aov, use_container_width=True)
with col_r2:
    st.markdown("<div class='section-header'>⚡ Avg Delivery Days</div>", unsafe_allow_html=True)
    fig_del = go.Figure(go.Bar(x=prime_df['label'], y=prime_df['avg_del'],
                                marker_color=['#FFD700','#3FB950'],
                                text=[f'{v:.1f}d' for v in prime_df['avg_del']],
                                textposition='outside', textfont=dict(color='white',size=12)))
    fig_del.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                           height=300, showlegend=False, yaxis=dict(title='Avg Days'), margin=dict(t=30,b=20))
    st.plotly_chart(fig_del, use_container_width=True)

# ── Prime Revenue Trend ────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📈 Prime vs Non-Prime Revenue Trend</div>", unsafe_allow_html=True)
prime_yr = run_query(f"""
    SELECT order_year, is_prime_member, ROUND(SUM(final_amount_inr)/1e7,2) AS rev_cr
    FROM transactions WHERE {fs['w']} {fs['wsub']}
    GROUP BY order_year, is_prime_member ORDER BY order_year
""")
prime_yr['label'] = prime_yr['is_prime_member'].map({1:'Prime',0:'Non-Prime'})
fig_pyr = px.area(prime_yr, x='order_year', y='rev_cr', color='label',
                   color_discrete_map={'Prime':'#FFD700','Non-Prime':'#3FB950'},
                   labels={'rev_cr':'Revenue (₹Cr)','order_year':'Year'})
fig_pyr.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                       height=350, margin=dict(t=20,b=20), legend=dict(orientation='h',y=1.1))
st.plotly_chart(fig_pyr, use_container_width=True)

# ── Age Group + Funnel ────────────────────────────────────────────────────────
col_l3, col_r3 = st.columns(2)
with col_l3:
    st.markdown("<div class='section-header'>👶 Age Group Spending Patterns</div>", unsafe_allow_html=True)
    age_df = run_query(f"""
        SELECT c.customer_age_group, COUNT(t.transaction_id) AS orders,
               COUNT(DISTINCT t.customer_id) AS customers, ROUND(AVG(t.final_amount_inr),0) AS avg_spend
        FROM transactions t JOIN customers c ON t.customer_id=c.customer_id
        WHERE {fs['wt']} {fs['wc']}
        GROUP BY c.customer_age_group ORDER BY avg_spend DESC
    """)
    age_order = ['18-25','26-35','36-45','46-55','55+']
    age_df = age_df[age_df['customer_age_group'].isin(age_order)].copy()
    age_df['sort'] = age_df['customer_age_group'].map({a:i for i,a in enumerate(age_order)})
    age_df = age_df.sort_values('sort')
    fig_age = go.Figure()
    fig_age.add_trace(go.Bar(name='Customers (K)', x=age_df['customer_age_group'], y=age_df['customers']/1000,
                              marker_color='#A855F7', yaxis='y'))
    fig_age.add_trace(go.Scatter(name='Avg Spend (₹K)', x=age_df['customer_age_group'], y=age_df['avg_spend']/1000,
                                  mode='lines+markers', yaxis='y2',
                                  line=dict(color='#FFD700',width=2.5), marker=dict(size=9)))
    fig_age.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                           height=380, margin=dict(t=30,b=20),
                           yaxis=dict(title='Customers (K)'),
                           yaxis2=dict(title='Avg Spend (₹K)', overlaying='y', side='right', color='#FFD700'),
                           legend=dict(orientation='h',y=1.1))
    st.plotly_chart(fig_age, use_container_width=True)

with col_r3:
    st.markdown("<div class='section-header'>🔀 Customer Journey Funnel</div>", unsafe_allow_html=True)
    total = rfm['customer_id'].nunique()
    funnel = {'All Customers': total, 'New (1 Order)': int((rfm['frequency']==1).sum()),
              'Engaged (2-5)': int(((rfm['frequency']>=2)&(rfm['frequency']<=5)).sum()),
              'Loyal (6+)': int((rfm['frequency']>5).sum()),
              'Champions': int((rfm['segment']=='Champions').sum())}
    fig_fn = go.Figure(go.Funnel(y=list(funnel.keys()), x=list(funnel.values()),
                                  textinfo='value+percent initial',
                                  marker=dict(color=['#FF9900','#A855F7','#58A6FF','#3FB950','#FFD700']),
                                  textfont=dict(color='white',size=12)))
    fig_fn.update_layout(template='plotly_dark', paper_bgcolor='#0E1117',
                          height=380, margin=dict(t=20,b=20))
    st.plotly_chart(fig_fn, use_container_width=True)

# ── Cohort Retention Heatmap ──────────────────────────────────────────────────
st.markdown("<div class='section-header'>🔄 Customer Cohort Retention Heatmap</div>", unsafe_allow_html=True)
cohort_df = run_query(f"""
    SELECT strftime('%Y', MIN(order_date)) AS cohort_year,
           order_year AS active_year, COUNT(DISTINCT customer_id) AS customers
    FROM transactions WHERE {fs['w']} {fs['wsub']}
    GROUP BY customer_id, order_year
    LIMIT 50000
""")
if len(cohort_df) > 0:
    try:
        cohort_pivot = cohort_df.pivot_table(index='cohort_year', columns='active_year', values='customers', aggfunc='sum').fillna(0)
        cohort_pct = cohort_pivot.div(cohort_pivot.iloc[:,0], axis=0)*100
        fig_coh, ax_c = plt.subplots(figsize=(14, max(3,len(cohort_pct)*0.6)))
        fig_coh.patch.set_facecolor('#0E1117'); ax_c.set_facecolor('#0E1117')
        cv_min, cv_max = 0, 100
        sns.heatmap(cohort_pct.round(1), annot=True, fmt='.0f', cmap='Blues', ax=ax_c,
                    linewidths=0.4, linecolor='#1C2333', annot_kws={'size':10})
        fix_heatmap_text(ax_c, 'Blues', cv_min, cv_max)
        ax_c.tick_params(colors='#8B949E', labelsize=9)
        ax_c.set_xlabel('Active Year', color='#8B949E'); ax_c.set_ylabel('Cohort Year', color='#8B949E')
        cbar_c = ax_c.collections[0].colorbar
        cbar_c.ax.yaxis.label.set_color('#8B949E'); cbar_c.ax.tick_params(colors='#8B949E')
        plt.tight_layout()
        st.pyplot(fig_coh, use_container_width=True); plt.close()
    except Exception as e:
        st.info(f"Cohort data unavailable: {e}")

# ── Top 10 Customers + Retention/Churn ────────────────────────────────────────
col_l4, col_r4 = st.columns(2)
with col_l4:
    st.markdown("<div class='section-header'>🏆 Top 10 Customers by Revenue</div>", unsafe_allow_html=True)
    top_c = run_query(f"""
        SELECT customer_id, ROUND(SUM(final_amount_inr)/1e6,2) AS rev_mn
        FROM transactions WHERE {fs['w']} {fs['wsub']}
        GROUP BY customer_id ORDER BY rev_mn DESC LIMIT 10
    """)
    fig_tc = px.bar(top_c, x='rev_mn', y='customer_id', orientation='h',
                     color='rev_mn', color_continuous_scale='Purples',
                     text=[f'₹{v:.2f}M' for v in top_c['rev_mn']],
                     labels={'rev_mn':'Revenue (₹M)','customer_id':''})
    fig_tc.update_traces(textposition='outside', textfont_color='white')
    fig_tc.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                          height=380, coloraxis_showscale=False, showlegend=False, margin=dict(t=20,b=20,r=60))
    st.plotly_chart(fig_tc, use_container_width=True)

with col_r4:
    st.markdown("<div class='section-header'>📉 Retention & Churn Rate</div>", unsafe_allow_html=True)
    ret_df = run_query(f"""
        SELECT order_year, COUNT(DISTINCT customer_id) AS active
        FROM transactions WHERE {fs['w']} {fs['wsub']}
        GROUP BY order_year ORDER BY order_year
    """)
    ret_df['retention_pct'] = ret_df['active']/ret_df['active'].max()*100
    ret_df['churn_pct'] = 100-ret_df['retention_pct']
    fig_ret = go.Figure()
    fig_ret.add_trace(go.Scatter(x=ret_df['order_year'], y=ret_df['retention_pct'], mode='lines+markers',
                                  name='Retention %', line=dict(color='#3FB950',width=2.5), marker=dict(size=8)))
    fig_ret.add_trace(go.Scatter(x=ret_df['order_year'], y=ret_df['churn_pct'], mode='lines+markers',
                                  name='Churn %', line=dict(color='#F85149',width=2.5), marker=dict(size=8)))
    fig_ret.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                           height=380, yaxis=dict(title='Rate (%)'),
                           xaxis=dict(title='Year',tickmode='linear',dtick=1),
                           legend=dict(orientation='h',y=1.1), margin=dict(t=20,b=20))
    st.plotly_chart(fig_ret, use_container_width=True)

st.markdown("---")
st.markdown("<div class='section-header'>📋 RFM Segment Summary</div>", unsafe_allow_html=True)
rfm_s = rfm.groupby('segment').agg(Customers=('customer_id','count'), Avg_Recency=('recency','mean'),
                                     Avg_Frequency=('frequency','mean'), Avg_Spend=('monetary','mean')).round(1).reset_index().sort_values('Avg_Spend', ascending=False)
rfm_s['Avg_Spend'] = rfm_s['Avg_Spend'].apply(lambda x: f'₹{x/1000:.1f}K')
st.dataframe(rfm_s, use_container_width=True, hide_index=True)
