import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
st.set_page_config(page_title="Predictive & Advanced", page_icon="🔮", layout="wide", initial_sidebar_state="expanded")


import pandas as pd, numpy as np, warnings
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
from prophet import Prophet
warnings.filterwarnings('ignore')

from utils.db import run_query
from utils.sidebar import render_sidebar, get_filter_sql, fix_heatmap_text

filters = render_sidebar()
fs = get_filter_sql(filters)

st.markdown("<h1 style='color:#FFD700;text-align:center;'>🔮 PREDICTIVE & <span style='color:#00D4FF;'>ADVANCED ANALYTICS</span></h1>", unsafe_allow_html=True)
st.markdown("---")

# ── Revenue Forecast ──────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>📈 AI-Driven Revenue Forecasting (Prophet Model)</div>", unsafe_allow_html=True)

# Fetch monthly data instead of yearly for better seasonality modeling
monthly_rev = run_query("""
    SELECT 
        date(order_date, 'start of month') as ds, 
        SUM(final_amount_inr)/1e6 AS y 
    FROM transactions 
    GROUP BY ds 
    ORDER BY ds
""")

# Ensure correct datetime format
monthly_rev['ds'] = pd.to_datetime(monthly_rev['ds'])

# Initialize and fit the Prophet model
m = Prophet(seasonality_mode='multiplicative', yearly_seasonality=True)
m.fit(monthly_rev)

# Predict the next 24 months (2 years)
future = m.make_future_dataframe(periods=24, freq='M')
forecast = m.predict(future)

# Plotting with Plotly for a sleek, dark-themed UI
fig_fc = go.Figure()

# Add confidence intervals
fig_fc.add_trace(go.Scatter(
    x=list(forecast['ds']) + list(forecast['ds'])[::-1],
    y=list(forecast['yhat_upper']) + list(forecast['yhat_lower'])[::-1],
    fill='toself', fillcolor='rgba(168,85,247,0.15)',
    line=dict(color='rgba(0,0,0,0)'), name='80% Confidence Interval'
))

# Add Actual Data
fig_fc.add_trace(go.Scatter(
    x=monthly_rev['ds'], y=monthly_rev['y'], mode='lines+markers', name='Actual Revenue',
    line=dict(color='#FF9900', width=2), marker=dict(size=4)
))

# Add Forecasted Data
fig_fc.add_trace(go.Scatter(
    x=forecast['ds'].iloc[-24:], y=forecast['yhat'].iloc[-24:], mode='lines',
    name='AI Forecast', line=dict(color='#A855F7', width=2.5, dash='dash')
))

fig_fc.update_layout(
    template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
    height=450, yaxis=dict(title='Revenue (₹ Millions)'),
    xaxis=dict(title='Date'), legend=dict(orientation='h', y=1.1)
)
st.plotly_chart(fig_fc, use_container_width=True)

# ── Churn Gauge + CLV Distribution ───────────────────────────────────────────
col_l, col_r = st.columns([1,2])
with col_l:
    st.markdown("<div class='section-header'>⚠️ Churn Risk Score</div>", unsafe_allow_html=True)
    ch = run_query(f"""
        SELECT AVG(CAST(julianday('now')-julianday(last_date) AS REAL)/30.0) AS months_inactive
        FROM (SELECT customer_id, MAX(order_date) AS last_date FROM transactions WHERE {fs['w']} {fs['wsub']} GROUP BY customer_id)
    """)
    months = float(ch['months_inactive'].iloc[0]) if len(ch)>0 else 0
    score = min(100, months*8)
    fig_ch = go.Figure(go.Indicator(
        mode='gauge+number', value=round(score,2),
        title={'text':'Avg Churn Risk Score','font':{'color':'#FF9900','size':13}},
        number={'font':{'color':'white','size':42},'suffix':'/100'},
        gauge={'axis':{'range':[0,100],'tickcolor':'#8B949E'},
               'bar':{'color':'#F85149' if score>60 else '#FF9900' if score>30 else '#3FB950'},
               'bgcolor':'#1C2333','bordercolor':'#30363D',
               'steps':[{'range':[0,30],'color':'#0D4A1F'},{'range':[30,60],'color':'#4D2600'},{'range':[60,100],'color':'#4D0F0F'}]}))
    fig_ch.update_layout(template='plotly_dark', paper_bgcolor='#0E1117',
                          height=320, margin=dict(t=30,b=10,l=20,r=20))
    st.plotly_chart(fig_ch, use_container_width=True)
    risk = 'High' if score>60 else 'Moderate' if score>30 else 'Low'
    st.markdown(f"<div class='insight-box'>⚠️ <b>{risk} risk</b> — avg {months:.1f} months inactive. {'Initiate win-back campaigns.' if score>30 else 'Maintain engagement.'}</div>", unsafe_allow_html=True)

with col_r:
    st.markdown("<div class='section-header'>💰 Customer Lifetime Value Distribution</div>", unsafe_allow_html=True)
    clv = run_query(f"SELECT customer_id, ROUND(SUM(final_amount_inr)/1000,1) AS clv_k FROM transactions WHERE {fs['w']} {fs['wsub']} GROUP BY customer_id")
    fig_clv, ax_clv = plt.subplots(figsize=(10,4))
    fig_clv.patch.set_facecolor('#0E1117'); ax_clv.set_facecolor('#0E1117')
    clip = clv['clv_k'].clip(upper=clv['clv_k'].quantile(0.99))
    ax_clv.hist(clip, bins=50, color='#A855F7', alpha=0.85, edgecolor='#1C2333')
    ax_clv.axvline(clv['clv_k'].mean(), color='#FFD700', linestyle='--', linewidth=2, label=f"Mean: ₹{clv['clv_k'].mean():.1f}K")
    ax_clv.axvline(clv['clv_k'].median(), color='#3FB950', linestyle='--', linewidth=2, label=f"Median: ₹{clv['clv_k'].median():.1f}K")
    ax_clv.set_xlabel('CLV (₹K)', color='#8B949E', fontsize=9); ax_clv.set_ylabel('Customers', color='#8B949E', fontsize=9)
    ax_clv.tick_params(colors='#8B949E', labelsize=8)
    ax_clv.legend(facecolor='#1C2333', edgecolor='#30363D', labelcolor='white', fontsize=9)
    for sp in ax_clv.spines.values(): sp.set_color('#30363D')
    plt.tight_layout(); st.pyplot(fig_clv, use_container_width=True); plt.close()

# ── Correlation Matrix ────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🔗 Correlation Matrix — Key Business Metrics</div>", unsafe_allow_html=True)
corr_df = run_query(f"""
    SELECT t.original_price_inr, t.discount_percent, t.final_amount_inr,
           t.delivery_days, t.customer_rating, COALESCE(t.quantity,1) AS quantity
    FROM transactions t WHERE {fs['w']} {fs['wsub']} LIMIT 50000
""")
corr_m = corr_df.corr().round(2)
corr_m.index = corr_m.columns = ['Price','Disc%','FinalAmt','Del.Days','Rating','Qty']
fig_corr, ax_corr = plt.subplots(figsize=(9,7))
fig_corr.patch.set_facecolor('#0E1117'); ax_corr.set_facecolor('#0E1117')
mask = np.triu(np.ones_like(corr_m, dtype=bool))
sns.heatmap(corr_m, annot=True, fmt='.2f', cmap='RdYlGn', ax=ax_corr,
            vmin=-1, vmax=1, center=0, square=True, mask=mask,
            linewidths=0.5, linecolor='#1C2333', annot_kws={'size':11,'weight':'bold'})
fix_heatmap_text(ax_corr, 'RdYlGn', -1, 1)
ax_corr.tick_params(colors='#8B949E', labelsize=10)
ax_corr.set_xticklabels(ax_corr.get_xticklabels(), rotation=30, ha='right')
cbar_cr = ax_corr.collections[0].colorbar
cbar_cr.ax.yaxis.label.set_color('#8B949E'); cbar_cr.ax.tick_params(colors='#8B949E')
plt.tight_layout()
col_cc, _ = st.columns([2,1])
with col_cc: st.pyplot(fig_corr, use_container_width=True)
plt.close()

# ── Cross-sell Matrix ─────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>🔀 Cross-sell Opportunity Matrix</div>", unsafe_allow_html=True)
cross_df = run_query(f"""
    SELECT p.subcategory, COUNT(t.transaction_id) AS orders
    FROM transactions t JOIN products p ON t.product_id=p.product_id
    WHERE {fs['wt']} {fs['wsub']}
    GROUP BY p.subcategory ORDER BY orders DESC LIMIT 8
""")
if len(cross_df) >= 3:
    cats = cross_df['subcategory'].tolist()
    ords = cross_df['orders'].values
    matrix = np.outer(ords, ords) / (ords.max()**2) * 100
    np.fill_diagonal(matrix, 0)
    cross_mat = pd.DataFrame(np.round(matrix,1), index=cats, columns=cats)
    fig_cs, ax_cs = plt.subplots(figsize=(11,8))
    fig_cs.patch.set_facecolor('#0E1117'); ax_cs.set_facecolor('#0E1117')
    cs_min, cs_max = cross_mat.values[cross_mat.values>0].min() if (cross_mat.values>0).any() else 0, cross_mat.values.max()
    sns.heatmap(cross_mat, annot=True, fmt='.1f', cmap='Blues', ax=ax_cs,
                linewidths=0.4, linecolor='#1C2333', annot_kws={'size':11})
    fix_heatmap_text(ax_cs, 'Blues', cs_min, cs_max)   # ← visibility fix
    ax_cs.tick_params(colors='#8B949E', labelsize=9)
    ax_cs.set_xticklabels(ax_cs.get_xticklabels(), rotation=30, ha='right')
    cbar_cs = ax_cs.collections[0].colorbar
    cbar_cs.set_label('Co-purchase Score', color='#8B949E', fontsize=9)
    cbar_cs.ax.tick_params(colors='#8B949E')
    plt.tight_layout()
    col_mx, _ = st.columns([2,1])
    with col_mx: st.pyplot(fig_cs, use_container_width=True)
    plt.close()

# ── Demand Forecast + Bundle ──────────────────────────────────────────────────
col_l2, col_r2 = st.columns(2)
with col_l2:
    st.markdown("<div class='section-header'>📊 Demand Forecast by Category</div>", unsafe_allow_html=True)
    cat_yr = run_query("SELECT p.category, t.order_year, COUNT(*) AS orders FROM transactions t JOIN products p ON t.product_id=p.product_id GROUP BY p.category, t.order_year ORDER BY t.order_year")
    fig_dem = go.Figure()
    fc_c = px.colors.qualitative.Plotly
    for i, cat in enumerate(cat_yr['category'].unique()):
        sub = cat_yr[cat_yr['category']==cat].sort_values('order_year')
        x = sub['order_year'].values.astype(float); y = sub['orders'].values
        if len(x)<2: continue
        c = np.polyfit(x,y,1)
        fut = np.array([x.max()+1,x.max()+2,x.max()+3])
        clr = fc_c[i%len(fc_c)]
        fig_dem.add_trace(go.Scatter(x=list(x),y=list(y),mode='lines+markers',name=cat,
                                      line=dict(width=2,color=clr),marker=dict(size=6)))
        fig_dem.add_trace(go.Scatter(x=list(fut),y=list(np.polyval(c,fut)),mode='lines',
                                      line=dict(width=1.5,dash='dash',color=clr),showlegend=False))
    fig_dem.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                           height=400, yaxis=dict(title='Orders'),
                           xaxis=dict(title='Year',tickmode='linear',dtick=1),
                           legend=dict(orientation='h',y=1.15,font=dict(size=9)), margin=dict(t=20,b=20))
    st.plotly_chart(fig_dem, use_container_width=True)

with col_r2:
    st.markdown("<div class='section-header'>🎁 Bundle Opportunity by Subcategory</div>", unsafe_allow_html=True)
    bun = run_query(f"""
        SELECT p.subcategory, ROUND(SUM(t.final_amount_inr)/1e7,2) AS rev_cr, ROUND(AVG(t.discount_percent),1) AS avg_disc
        FROM transactions t JOIN products p ON t.product_id=p.product_id
        WHERE {fs['wt']} {fs['wsub']}
        GROUP BY p.subcategory ORDER BY rev_cr DESC LIMIT 10
    """)
    fig_bun = go.Figure()
    fig_bun.add_trace(go.Bar(name='Revenue (₹Cr)', x=bun['subcategory'], y=bun['rev_cr'], marker_color='#A855F7'))
    fig_bun.add_trace(go.Scatter(name='Avg Disc %', x=bun['subcategory'], y=bun['avg_disc'],
                                  mode='lines+markers', yaxis='y2',
                                  line=dict(color='#FFD700',width=2.5), marker=dict(size=8)))
    fig_bun.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                           height=400, yaxis=dict(title='Revenue (₹Cr)'),
                           yaxis2=dict(title='Avg Disc %',overlaying='y',side='right',color='#FFD700'),
                           legend=dict(orientation='h',y=1.1), xaxis=dict(tickangle=-25), margin=dict(t=20,b=20))
    st.plotly_chart(fig_bun, use_container_width=True)

# ── Prescriptive Price Simulator ──────────────────────────────────────────────
st.markdown("---")
st.markdown("<div class='section-header'>🧮 Prescriptive Analytics — Price Elasticity & Discount Simulator</div>", unsafe_allow_html=True)

# Fetch categories for the dropdown
categories = run_query("SELECT DISTINCT category FROM products")['category'].tolist()
selected_cat = st.selectbox("Select Product Category to Simulate", categories)

# Fetch baseline data dynamically based on the selected category AND the sidebar filters
base_data = run_query(f"""
    SELECT 
        AVG(t.original_price_inr) as avg_price,
        AVG(t.discount_percent) as avg_discount,
        COUNT(t.transaction_id) as total_orders,
        SUM(t.final_amount_inr) as total_revenue
    FROM transactions t
    JOIN products p ON t.product_id = p.product_id
    WHERE p.category = '{selected_cat}' AND {fs['wt']} {fs['wsub']}
""")

baseline = base_data.iloc[0]

# Ensure we actually have data for the selection before rendering metrics
if pd.notna(baseline['total_orders']) and baseline['total_orders'] > 0:
    col_sim1, col_sim2 = st.columns(2)
    
    with col_sim1:
        st.markdown(f"### 📊 Current Baseline ({selected_cat})")
        st.metric("Average Discount", f"{baseline['avg_discount']:.1f}%")
        st.metric("Total Revenue", f"₹{baseline['total_revenue']/1e7:.2f} Cr")
        st.metric("Total Orders", f"{baseline['total_orders']:,}")

    with col_sim2:
        st.markdown("### 🎚️ Simulate Strategy")
        
        # Interactive slider for the business user
        current_disc = int(baseline['avg_discount']) if pd.notna(baseline['avg_discount']) else 0
        sim_discount = st.slider("Simulate New Average Discount (%)", min_value=0, max_value=80, value=current_disc)
        
        # Mathematical simulation of Price Elasticity 
        # Using a standard assumed elasticity coefficient of -1.5 (a 1% drop in price increases demand by 1.5%)
        elasticity = -1.5  
        price_change_pct = (sim_discount - current_disc) / 100
        demand_change_pct = price_change_pct * elasticity * -100 
        
        sim_orders = int(baseline['total_orders'] * (1 + (demand_change_pct/100)))
        sim_avg_price = baseline['avg_price'] * (1 - (sim_discount/100))
        sim_revenue = sim_orders * sim_avg_price

        revenue_diff = sim_revenue - baseline['total_revenue']
        
        # Render simulated metrics with dynamic delta colors
        st.metric("Simulated Revenue", f"₹{sim_revenue/1e7:.2f} Cr", delta=f"₹{revenue_diff/1e7:.2f} Cr")
        st.metric("Simulated Orders", f"{sim_orders:,}", delta=int(sim_orders - baseline['total_orders']))

    # st.info("💡 **Prescriptive Insight:** This mathematical model uses an assumed price elasticity coefficient (-1.5) to dynamically calculate how aggressive discounting impacts top-line revenue versus order volume.")
else:
    st.warning("Not enough data for the selected category based on your current sidebar filters.")

# ── BI Command Center ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("<h2 style='color:#FFD700;text-align:center;'>🎛️ BI COMMAND CENTER</h2>", unsafe_allow_html=True)
kpis = run_query(f"""
    SELECT COUNT(*) AS txns, COUNT(DISTINCT customer_id) AS customers,
           ROUND(SUM(final_amount_inr)/1e9,3) AS rev_bn, ROUND(AVG(final_amount_inr)/1000,1) AS aov_k,
           ROUND(AVG(delivery_days),2) AS avg_del,
           ROUND(100.0*SUM(CASE WHEN delivery_days<=3 THEN 1 ELSE 0 END)/COUNT(*),1) AS on_time_pct,
           ROUND(100.0*SUM(CASE WHEN return_status='Returned' THEN 1 ELSE 0 END)/COUNT(*),1) AS ret_pct,
           ROUND(100.0*SUM(CASE WHEN is_festival_sale=1 THEN 1 ELSE 0 END)/COUNT(*),1) AS fest_pct,
           ROUND(100.0*SUM(CASE WHEN is_prime_member=1 THEN 1 ELSE 0 END)/COUNT(*),1) AS prime_pct,
           ROUND(AVG(customer_rating),2) AS avg_rating, ROUND(AVG(discount_percent),1) AS avg_disc
    FROM transactions WHERE {fs['w']} {fs['wsub']}
""")
k = kpis.iloc[0]
cmd_m = [
    ("💰 Total Revenue",    f"₹{k['rev_bn']:.3f}Bn",""),
    ("📦 Transactions",     f"{k['txns']/1e6:.2f}M",""),
    ("👥 Customers",        f"{k['customers']/1000:.0f}K",""),
    ("🛒 AOV",              f"₹{k['aov_k']:.1f}K",""),
    ("⚡ Avg Del.Days",     f"{k['avg_del']:.2f}","Target < 3"),
    ("✅ On-Time Rate",     f"{k['on_time_pct']:.1f}%","Target 90%"),
    ("↩️ Return Rate",      f"{k['ret_pct']:.1f}%","Target < 5%"),
    ("🎉 Festival Orders",  f"{k['fest_pct']:.1f}%","of Total"),
    ("👑 Prime Members",    f"{k['prime_pct']:.1f}%","of Customers"),
    ("⭐ Avg Rating",       f"{k['avg_rating']:.2f}/5","Customer Score"),
    ("🏷️ Avg Discount",     f"{k['avg_disc']:.1f}%","Discount Rate"),
]
cols = st.columns(4)
for i,(label,val,sub) in enumerate(cmd_m):
    with cols[i%4]:
        st.markdown(f"<div class='kpi-card' style='margin-bottom:0.8rem;'><div class='kpi-label'>{label}</div><div class='kpi-value' style='font-size:1.5rem;'>{val}</div><div style='font-size:0.7rem;color:#8B949E;margin-top:3px;'>{sub}</div></div>", unsafe_allow_html=True)

st.markdown("<br><hr><div style='text-align:center;color:#8B949E;font-size:0.75rem;'>🔮 Forecasting uses polynomial regression + bootstrap CI on 10-year historical data</div>", unsafe_allow_html=True)
