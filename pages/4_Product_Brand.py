import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
st.set_page_config(page_title="Product & Brand", page_icon="🛍️", layout="wide", initial_sidebar_state="expanded")


import pandas as pd, numpy as np, warnings
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
warnings.filterwarnings('ignore')

from utils.db import run_query
from utils.sidebar import render_sidebar, get_filter_sql

filters = render_sidebar()
fs = get_filter_sql(filters)

st.markdown("<h1 style='color:#FFD700;text-align:center;'>🛍️ PRODUCT, BRAND <span style='color:#00D4FF;'>& INVENTORY</span></h1>", unsafe_allow_html=True)
st.markdown("---")

cat_df = run_query(f"""
    SELECT p.subcategory, p.category,
           ROUND(SUM(t.final_amount_inr)/1e7,2) AS rev_cr,
           COUNT(t.transaction_id) AS orders,
           ROUND(AVG(t.discount_percent),1) AS avg_disc,
           ROUND(100.0*SUM(CASE WHEN t.return_status='Returned' THEN 1 ELSE 0 END)/COUNT(*),1) AS return_pct
    FROM transactions t JOIN products p ON t.product_id=p.product_id
    WHERE {fs['wt']} {fs['wsub']}
    GROUP BY p.subcategory, p.category ORDER BY rev_cr DESC
""")
brand_df = run_query(f"""
    SELECT p.brand, ROUND(SUM(t.final_amount_inr)/1e7,2) AS rev_cr, COUNT(t.transaction_id) AS orders,
           ROUND(AVG(p.product_rating),2) AS avg_rating, ROUND(AVG(t.discount_percent),1) AS avg_disc,
           ROUND(100.0*SUM(CASE WHEN t.return_status='Returned' THEN 1 ELSE 0 END)/COUNT(*),1) AS return_pct
    FROM transactions t JOIN products p ON t.product_id=p.product_id
    WHERE {fs['wt']} {fs['wsub']}
    GROUP BY p.brand ORDER BY rev_cr DESC LIMIT 20
""")

# ── Treemap + Top Products ─────────────────────────────────────────────────────
col_l, col_r = st.columns([3,2])
with col_l:
    st.markdown("<div class='section-header'>🗺️ Revenue Treemap by Subcategory</div>", unsafe_allow_html=True)
    # ── VISIBILITY FIX: use dark-start colorscale so small boxes are readable ──
    dark_purple_scale = [
        [0.0, '#1A0A3E'], [0.2, '#2D1B69'], [0.4, '#4C1D95'],
        [0.6, '#6D28D9'], [0.8, '#8B5CF6'], [1.0, '#A855F7']
    ]
    fig_tree = px.treemap(cat_df, path=['category','subcategory'], values='rev_cr',
                           color='rev_cr', color_continuous_scale=dark_purple_scale,
                           hover_data={'orders':True,'avg_disc':True},
                           labels={'rev_cr':'Revenue (₹Cr)'})
    fig_tree.update_traces(
        textinfo='label+value',
        textfont=dict(size=13, color='white'),
        insidetextfont=dict(size=13, color='white'),
        outsidetextfont=dict(size=13, color='white')
    )
    fig_tree.update_layout(template='plotly_dark', paper_bgcolor='#0E1117',
                            height=420, margin=dict(t=20,b=10), coloraxis_showscale=False)
    st.plotly_chart(fig_tree, use_container_width=True)

with col_r:
    st.markdown("<div class='section-header'>🏆 Top Products by Revenue</div>", unsafe_allow_html=True)
    top_prod = run_query(f"""
        SELECT p.product_name, ROUND(SUM(t.final_amount_inr)/1e7,2) AS rev_cr
        FROM transactions t JOIN products p ON t.product_id=p.product_id
        WHERE {fs['wt']} {fs['wsub']}
        GROUP BY p.product_name ORDER BY rev_cr DESC LIMIT 10
    """)
    top_prod['short'] = top_prod['product_name'].apply(lambda x: x[:22]+'...' if len(str(x))>22 else x)
    fig_top = px.bar(top_prod, x='rev_cr', y='short', orientation='h',
                      color='rev_cr', color_continuous_scale='Plasma',
                      text=[f'₹{v:.1f}Cr' for v in top_prod['rev_cr']],
                      labels={'rev_cr':'Revenue (₹Cr)','short':''})
    fig_top.update_traces(textposition='outside', textfont_color='white', textfont_size=10)
    fig_top.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                           height=420, coloraxis_showscale=False, showlegend=False, margin=dict(t=20,b=20,r=60))
    st.plotly_chart(fig_top, use_container_width=True)

# ── Brand Pie + Rating Dist ───────────────────────────────────────────────────
col_l2, col_r2 = st.columns(2)
with col_l2:
    st.markdown("<div class='section-header'>🥧 Brand-wise Market Share</div>", unsafe_allow_html=True)
    top8 = brand_df.head(8)
    others = brand_df['rev_cr'].iloc[8:].sum()
    pie_d = pd.concat([top8[['brand','rev_cr']], pd.DataFrame({'brand':['Others'],'rev_cr':[others]})], ignore_index=True)
    fig_pie = px.pie(pie_d, values='rev_cr', names='brand',
                      color_discrete_sequence=px.colors.qualitative.Plotly, hole=0.3)
    fig_pie.update_traces(textinfo='label+percent', textfont=dict(color='white',size=11))
    fig_pie.update_layout(template='plotly_dark', paper_bgcolor='#0E1117',
                           height=380, margin=dict(t=20,b=20))
    st.plotly_chart(fig_pie, use_container_width=True)

with col_r2:
    st.markdown("<div class='section-header'>⭐ Product Rating Distribution</div>", unsafe_allow_html=True)
    rat_df = run_query(f"""
        SELECT ROUND(customer_rating,1) AS rating, COUNT(*) AS cnt
        FROM transactions WHERE {fs['w']} {fs['wsub']} AND customer_rating IS NOT NULL
        GROUP BY rating ORDER BY rating
    """)
    fig_rat, ax_r = plt.subplots(figsize=(8,4.5))
    fig_rat.patch.set_facecolor('#0E1117'); ax_r.set_facecolor('#0E1117')
    bars = ax_r.bar(rat_df['rating'].astype(str), rat_df['cnt']/1000,
                     color='#A855F7', alpha=0.88, edgecolor='#1C2333', width=0.6)
    for bar, val in zip(bars, rat_df['cnt']):
        ax_r.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
                  f'{val/1000:.0f}K', ha='center', va='bottom', color='white', fontsize=9)
    ax_r.set_xlabel('Rating', color='#8B949E', fontsize=9); ax_r.set_ylabel('Count (K)', color='#8B949E', fontsize=9)
    ax_r.tick_params(colors='#8B949E', labelsize=9)
    for sp in ax_r.spines.values(): sp.set_color('#30363D')
    plt.tight_layout(); st.pyplot(fig_rat, use_container_width=True); plt.close()

# ── Lifecycle + Order Status ───────────────────────────────────────────────────
col_l3, col_r3 = st.columns(2)
with col_l3:
    st.markdown("<div class='section-header'>🔄 Product Lifecycle Stage</div>", unsafe_allow_html=True)
    life_df = run_query(f"""
        SELECT order_year, ROUND(SUM(final_amount_inr)/1e7,2) AS rev_cr
        FROM transactions WHERE {fs['w']} {fs['wsub']}
        GROUP BY order_year ORDER BY order_year
    """)
    mx = life_df['rev_cr'].max()
    stages = ['Decline' if v/mx<0.3 else 'Growth' if v/mx<0.6 else 'Maturity' if v/mx<0.85 else 'Peak' for v in life_df['rev_cr']]
    stage_c = {'Decline':'#F85149','Growth':'#FF9900','Maturity':'#3FB950','Peak':'#FFD700'}
    fig_life = go.Figure(go.Scatter(x=life_df['order_year'], y=life_df['rev_cr'],
                                     fill='tozeroy', mode='lines+markers+text',
                                     line=dict(color='#FF9900',width=2.5), marker=dict(size=8),
                                     text=stages, textposition='top center',
                                     textfont=dict(color=[stage_c[s] for s in stages],size=10),
                                     fillcolor='rgba(255,153,0,0.15)'))
    fig_life.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                            height=350, showlegend=False, yaxis=dict(title='Revenue (₹ Crores)'),
                            xaxis=dict(title='Year',tickmode='linear',dtick=1), margin=dict(t=30,b=20))
    st.plotly_chart(fig_life, use_container_width=True)

with col_r3:
    st.markdown("<div class='section-header'>📦 Order Status Overview</div>", unsafe_allow_html=True)
    stat_df = run_query(f"SELECT return_status, COUNT(*) AS cnt FROM transactions WHERE {fs['w']} {fs['wsub']} GROUP BY return_status")
    sc_map = {'Delivered':'#3FB950','Returned':'#FF9900','Cancelled':'#F85149'}
    fig_st = go.Figure(go.Bar(x=stat_df['return_status'], y=stat_df['cnt']/1000,
                               marker_color=[sc_map.get(s,'#8B949E') for s in stat_df['return_status']],
                               text=[f'{v/1000:.0f}K' for v in stat_df['cnt']],
                               textposition='outside', textfont=dict(color='white',size=13)))
    fig_st.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                          height=350, showlegend=False, yaxis=dict(title='Orders (K)'), margin=dict(t=30,b=20))
    st.plotly_chart(fig_st, use_container_width=True)

# ── Sentiment Gauge + Inventory Turnover ──────────────────────────────────────
col_l4, col_r4 = st.columns(2)
with col_l4:
    st.markdown("<div class='section-header'>😊 Review Sentiment Score</div>", unsafe_allow_html=True)
    avg_r = run_query(f"SELECT ROUND(AVG(customer_rating)*20,2) AS score FROM transactions WHERE {fs['w']} {fs['wsub']}")
    score = float(avg_r['score'].iloc[0])
    fig_g = go.Figure(go.Indicator(
        mode='gauge+number', value=score, domain={'x':[0,1],'y':[0,1]},
        title={'text':'Sentiment Score','font':{'color':'#8B949E','size':14}},
        number={'font':{'color':'#FF9900','size':48}},
        gauge={'axis':{'range':[0,100],'tickcolor':'#8B949E'}, 'bar':{'color':'#FF9900'},
               'bgcolor':'#1C2333', 'bordercolor':'#30363D',
               'steps':[{'range':[0,40],'color':'#4D0F0F'},{'range':[40,70],'color':'#4D2600'},{'range':[70,100],'color':'#0D4A1F'}],
               'threshold':{'line':{'color':'#FFD700','width':3},'value':score}}))
    fig_g.update_layout(template='plotly_dark', paper_bgcolor='#0E1117',
                         height=300, margin=dict(t=30,b=10,l=30,r=30))
    st.plotly_chart(fig_g, use_container_width=True)

with col_r4:
    st.markdown("<div class='section-header'>📦 Inventory Turnover by Month</div>", unsafe_allow_html=True)
    inv = run_query(f"""
        SELECT CAST(strftime('%m',order_date) AS INTEGER) AS month, SUM(COALESCE(quantity,1)) AS units
        FROM transactions WHERE {fs['w']} {fs['wsub']}
        GROUP BY month ORDER BY month
    """)
    fig_inv = go.Figure(go.Scatter(x=inv['month'], y=inv['units']/1000,
                                    mode='lines+markers+text', line=dict(color='#A855F7',width=2.5),
                                    marker=dict(size=9,color='#A855F7'),
                                    text=[f'{v/1000:.0f}K' for v in inv['units']],
                                    textposition='top center', textfont=dict(color='white',size=9),
                                    fill='tozeroy', fillcolor='rgba(168,85,247,0.15)'))
    fig_inv.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                           height=300, showlegend=False, yaxis=dict(title='Units Sold (K)'),
                           xaxis=dict(title='Month',tickmode='linear',dtick=1,
                                      tickvals=list(range(1,13)),
                                      ticktext=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']),
                           margin=dict(t=30,b=20))
    st.plotly_chart(fig_inv, use_container_width=True)

# ── Competitive Pricing Box Plot ──────────────────────────────────────────────
st.markdown("<div class='section-header'>📊 Competitive Pricing — Price Distribution by Brand</div>", unsafe_allow_html=True)
if len(brand_df) > 0:
    top_brands_list = brand_df['brand'].head(10).tolist()
    brands_str = ','.join(f"'{b}'" for b in top_brands_list)
    price_raw = run_query(f"""
        SELECT p.brand, t.original_price_inr FROM transactions t JOIN products p ON t.product_id=p.product_id
        WHERE {fs['wt']} {fs['wsub']} AND p.brand IN ({brands_str})
          AND t.original_price_inr BETWEEN 1000 AND 500000
    """)
    if len(price_raw) > 0:
        fig_box, ax_b = plt.subplots(figsize=(14,5))
        fig_box.patch.set_facecolor('#0E1117'); ax_b.set_facecolor('#0E1117')
        brand_ord = price_raw.groupby('brand')['original_price_inr'].median().sort_values(ascending=False).index.tolist()
        valid_brands = [b for b in brand_ord if b in price_raw['brand'].values]
        bp = ax_b.boxplot([price_raw[price_raw['brand']==b]['original_price_inr'].values/1000 for b in valid_brands],
                           labels=valid_brands, patch_artist=True,
                           medianprops=dict(color='#FFD700',linewidth=2))
        clrs_bp = plt.cm.Purples(np.linspace(0.4,0.9,len(bp['boxes'])))
        for patch, c in zip(bp['boxes'], clrs_bp):
            patch.set_facecolor(c); patch.set_edgecolor('#30363D')
        for w in bp['whiskers']: w.set_color('#8B949E')
        for c in bp['caps']: c.set_color('#8B949E')
        for f in bp['fliers']: f.set(marker='o',color='#FF9900',alpha=0.3,markersize=3)
        ax_b.set_xlabel('Brand', color='#8B949E', fontsize=9); ax_b.set_ylabel('Price (₹K)', color='#8B949E', fontsize=9)
        ax_b.tick_params(colors='#8B949E', labelsize=8); ax_b.set_xticklabels(ax_b.get_xticklabels(), rotation=20, ha='right')
        for sp in ax_b.spines.values(): sp.set_color('#30363D')
        plt.tight_layout(); st.pyplot(fig_box, use_container_width=True); plt.close()

# ── Profit Margin Table ────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("<div class='section-header'>💹 Product Profit Margin % by Brand</div>", unsafe_allow_html=True)
brand_df['profit_margin'] = ((100-brand_df['avg_disc'])/100*35).round(1)
show = brand_df[['brand','orders','rev_cr','avg_rating','avg_disc','return_pct','profit_margin']].copy()
show.columns = ['Brand','Orders','Revenue (₹Cr)','Avg Rating','Avg Disc %','Return %','Est. Margin %']
show['Revenue (₹Cr)'] = show['Revenue (₹Cr)'].apply(lambda x: f'₹{x:.2f}Cr')
st.dataframe(show, use_container_width=True, hide_index=True)
