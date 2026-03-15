"""
app.py — Amazon.in: A Decade of Sales Analytics
Run with: streamlit run app.py
"""
import streamlit as st
st.set_page_config(
    page_title="Amazon.in Analytics", 
    page_icon="https://upload.wikimedia.org/wikipedia/commons/d/de/Amazon_icon.png", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)
st.markdown("""
    <style>
        [data-testid="collapsedControl"] { display: none !important; }
        [data-testid="stSidebar"] { display: none !important; }
    </style>
""", unsafe_allow_html=True)

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.sidebar import render_sidebar
from utils.db import run_query

filters = render_sidebar()

st.markdown("""
<div style='text-align:center;padding:3rem 0 2rem 0;'>
    <img src="https://www.pngplay.com/wp-content/uploads/3/White-Amazon-Logo-PNG-HD-Quality.png" style="width: 250px; margin-bottom: 5px;" alt="Amazon Logo">
    <h2 style='color:#00D4FF;font-size:1.4rem;font-weight:600;letter-spacing:4px;margin:0;'>A DECADE OF SALES ANALYTICS</h2>
    <p style='color:#8B949E;margin-top:1rem;font-size:1rem;'>2015 – 2025 · ~1 Million Transactions · 11 Pages · 100+ Charts · 12 Filters · AI Powered</p>
</div>
""", unsafe_allow_html=True)

try:
    kpi = run_query("SELECT COUNT(*) AS txns, COUNT(DISTINCT customer_id) AS customers, ROUND(SUM(final_amount_inr)/1e9,2) AS rev_bn, ROUND(AVG(final_amount_inr)/1000,1) AS aov_k FROM transactions")
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("💰 Total Revenue",    f"₹{kpi['rev_bn'].iloc[0]}Bn")
    with c2: st.metric("📦 Transactions",     f"{kpi['txns'].iloc[0]/1e6:.2f}M")
    with c3: st.metric("👥 Active Customers", f"{kpi['customers'].iloc[0]/1000:.0f}K")
    with c4: st.metric("🛒 Avg Order Value",  f"₹{kpi['aov_k'].iloc[0]}K")
except Exception as e:
    st.warning(f"⚠️ Could not load KPIs — update DB_PATH in utils/db.py\n\n`{e}`")

st.markdown("---")
st.markdown("<h3 style='color:#FF9900;text-align:center;'>📋 Dashboard Pages</h3>", unsafe_allow_html=True)

pages_info = [
    ("🧹", "Data Quality", "Cleaning Pipeline · Before/After · Quality Score", "pages/0_Data_Quality.py"),
    ("📊","Executive & Financial","KPIs · Revenue · Forecasting · Cost vs Revenue","pages/1_Executive_Financial.py"),
    ("📈","Revenue Analytics","Yearly · Monthly · Seasonal · Category Trends","pages/2_Revenue_Analytics.py"),
    ("👥","Customer Analytics","RFM · Cohort · Prime · CLV · Demographics","pages/3_Customer_Analytics.py"),
    ("🛍️","Product & Brand","Treemap · Lifecycle · Inventory · Profit Margin","pages/4_Product_Brand.py"),
    ("🗺️","Geographic","India Map · State · City · Tier Analysis","pages/5_Geographic.py"),
    ("💳","Payment & Operations","UPI Trends · Delivery · Returns · Supplier","pages/6_Payment_Operations.py"),
    ("🎉","Festival & Seasonal","Diwali · Prime Day · Festival ROI · Planning","pages/7_Festival_Seasonal.py"),
    ("🔮","Predictive & Advanced","Forecasting · Churn · Cross-sell · BI Command Center","pages/8_Predictive_Advanced.py"),
    ("🎮", "Business Simulator", "What-If · Scenarios · 2026 Projections · Lever Analysis", "pages/9_Simulator.py"),
    ("🤖", "AI Insights", "Ask the Data · Groq AI · Live Analysis · Business Q&A", "pages/10_AI_Insights.py")
]
# --- Add this CSS style block right before the loop for hover effects ---
st.markdown("""
<style>
.card-link {
    text-decoration: none !important;
    display: block;
}
.dashboard-card {
    background: linear-gradient(135deg,#1C2333,#161B22);
    border: 1px solid #30363D;
    border-radius: 12px;
    padding: 1.2rem;
    margin-bottom: 1rem;
    transition: all 0.2s ease-in-out;
    cursor: pointer;
}
.dashboard-card:hover {
    border-color: #FF9900;
    transform: translateY(-3px);
    box-shadow: 0 4px 12px rgba(255, 153, 0, 0.1);
}
</style>
""", unsafe_allow_html=True)

# --- Updated Card Loop ---
for i in range(0, len(pages_info), 2):
    cols = st.columns(2)
    for j, col in enumerate(cols):
        if i+j < len(pages_info):
            icon, title, desc, link = pages_info[i+j]
            
            # Extract the Streamlit URL path from the file name
            # Example: "pages/1_Executive_Financial.py" -> "Executive_Financial"
            page_url = link.split('/')[-1].replace('.py', '')
            if '_' in page_url and page_url.split('_')[0].isdigit():
                page_url = page_url.split('_', 1)[1]
            
            with col:
                # Wrap the card in an <a> tag pointing to the page URL
                st.markdown(f"""
                <a href="{page_url}" target="_self" class="card-link">
                    <div class="dashboard-card">
                        <div style='font-size:1.8rem;'>{icon}</div>
                        <div style='font-size:1rem;font-weight:700;color:#FF9900;margin:0.3rem 0;'>{title}</div>
                        <div style='font-size:0.8rem;color:#8B949E;'>{desc}</div>
                    </div>
                </a>
                """, unsafe_allow_html=True)

st.markdown("<br><hr><div style='text-align:center;color:#8B949E;font-size:0.75rem;'>Built with Python · Streamlit · Plotly · Seaborn · SQLite · Pandas</div>", unsafe_allow_html=True)
