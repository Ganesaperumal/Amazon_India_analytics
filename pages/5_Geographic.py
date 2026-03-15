import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
st.set_page_config(page_title="Geographic", page_icon="🗺️", layout="wide", initial_sidebar_state="expanded")


import numpy as np, warnings
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
warnings.filterwarnings('ignore')

from utils.db import run_query
from utils.sidebar import render_sidebar, get_filter_sql

filters = render_sidebar()
fs = get_filter_sql(filters)

st.markdown("<h1 style='color:#FFD700;text-align:center;'>🗺️ GEOGRAPHIC <span style='color:#00D4FF;'>ANALYSIS</span></h1>", unsafe_allow_html=True)
st.markdown("---")

CITY_COORDS = {
    'Mumbai':(19.076,72.877),'New Delhi':(28.613,77.209),'Delhi':(28.704,77.102),
    'Bengaluru':(12.972,77.594),'Bangalore':(12.972,77.594),'Chennai':(13.083,80.270),
    'Kolkata':(22.572,88.364),'Hyderabad':(17.387,78.491),'Ahmedabad':(23.023,72.572),
    'Pune':(18.520,73.857),'Jaipur':(26.912,75.787),'Surat':(21.170,72.831),
    'Lucknow':(26.847,80.947),'Kanpur':(26.449,80.331),'Nagpur':(21.146,79.088),
    'Patna':(25.594,85.137),'Indore':(22.719,75.857),'Thane':(19.218,72.978),
    'Bhopal':(23.259,77.413),'Visakhapatnam':(17.686,83.218),'Vadodara':(22.307,73.181),
    'Ludhiana':(30.901,75.857),'Agra':(27.176,78.008),'Nashik':(19.997,73.789),
    'Faridabad':(28.408,77.317),'Meerut':(28.984,77.706),'Rajkot':(22.303,70.802),
    'Varanasi':(25.317,82.974),'Srinagar':(34.083,74.797),'Aurangabad':(19.877,75.343),
    'Amritsar':(31.634,74.872),'Navi Mumbai':(19.033,73.030),'Allahabad':(25.435,81.846),
    'Howrah':(22.588,88.313),'Coimbatore':(11.017,76.955),'Jabalpur':(23.166,79.937),
    'Gwalior':(26.219,78.182),'Vijayawada':(16.506,80.648),'Jodhpur':(26.292,73.017),
    'Madurai':(9.925,78.120),'Raipur':(21.251,81.630),'Kota':(25.182,75.839),
    'Chandigarh':(30.733,76.779),'Guwahati':(26.145,91.736),'Mysore':(12.296,76.640),
    'Bareilly':(28.367,79.415),'Ghaziabad':(28.668,77.449),'Kochi':(9.932,76.267),
    'Bhubaneswar':(20.296,85.825),'Thiruvananthapuram':(8.524,76.936),
}
TIER_COLORS = {'Metro':'#FFD700','Tier1':'#A855F7','Tier2':'#58A6FF','Rural':'#3FB950'}

city_df = run_query(f"""
    SELECT c.customer_city, c.customer_state, c.customer_tier,
           COUNT(t.transaction_id) AS orders,
           ROUND(SUM(t.final_amount_inr)/1e7,2) AS rev_cr,
           COUNT(DISTINCT t.customer_id) AS customers
    FROM transactions t JOIN customers c ON t.customer_id=c.customer_id
    WHERE {fs['wt']} {fs['wc']}
    GROUP BY c.customer_city, c.customer_state, c.customer_tier ORDER BY rev_cr DESC
""")
state_df = run_query(f"""
    SELECT c.customer_state, COUNT(t.transaction_id) AS orders,
           ROUND(SUM(t.final_amount_inr)/1e7,2) AS rev_cr
    FROM transactions t JOIN customers c ON t.customer_id=c.customer_id
    WHERE {fs['wt']} {fs['wc']}
    GROUP BY c.customer_state ORDER BY rev_cr DESC
""")
tier_df = run_query(f"""
    SELECT c.customer_tier, ROUND(SUM(t.final_amount_inr)/1e7,2) AS rev_cr, COUNT(*) AS orders
    FROM transactions t JOIN customers c ON t.customer_id=c.customer_id
    WHERE {fs['wt']} {fs['wc']}
    GROUP BY c.customer_tier
""")

# ── Map Visualizations (Side-by-Side) ─────────────────────────────────────────
map_col1, map_col2 = st.columns(2)

with map_col1:
    st.markdown("<div class='section-header'>🗺️ City-wise Revenue — India Bubble Map</div>", unsafe_allow_html=True)
    city_df['lat'] = city_df['customer_city'].map(lambda c: CITY_COORDS.get(c,(None,None))[0])
    city_df['lon'] = city_df['customer_city'].map(lambda c: CITY_COORDS.get(c,(None,None))[1])
    city_map = city_df.dropna(subset=['lat','lon'])

    fig_city_map = go.Figure()
    for tier in city_map['customer_tier'].dropna().unique():
        sub = city_map[city_map['customer_tier']==tier]
        fig_city_map.add_trace(go.Scattergeo(
            lat=sub['lat'], lon=sub['lon'], mode='markers', name=str(tier),
            marker=dict(size=np.sqrt(sub['rev_cr'])*3, color=TIER_COLORS.get(str(tier),'#8B949E'),
                        opacity=0.75, line=dict(color='white',width=0.5)),
            text=[f"<b>{r['customer_city']}</b><br>State: {r['customer_state']}<br>Revenue: ₹{r['rev_cr']:.1f}Cr<br>Orders: {r['orders']:,}" for _,r in sub.iterrows()],
            hoverinfo='text'))
    fig_city_map.update_geos(scope='asia', center=dict(lat=22,lon=82), projection_scale=4,
                        showland=True,landcolor='#1C2333', showocean=True,oceancolor='#0E1117',
                        showlakes=True,lakecolor='#161B22', showcountries=True,countrycolor='#30363D',
                        showsubunits=True,subunitcolor='#30363D', showcoastlines=True,coastlinecolor='#30363D',
                        bgcolor='#0E1117', lataxis_range=[6,38], lonaxis_range=[65,100])
    fig_city_map.update_layout(template='plotly_dark', paper_bgcolor='#0E1117', height=600,
                           margin=dict(t=10,b=10,l=0,r=0),
                           legend=dict(title='Customer Tier', orientation='v',
                                       font=dict(color='white',size=11), bgcolor='#1C2333', bordercolor='#30363D'))
    st.plotly_chart(fig_city_map, use_container_width=True)

with map_col2:
    st.markdown("<div class='section-header'>🗺️ Geographic Expansion Time-Lapse (2015-2025)</div>", unsafe_allow_html=True)

    # 1. Fetch geographic revenue data grouped by year using a JOIN
    geo_data = run_query("""
        SELECT 
            t.order_year, 
            c.customer_state, 
            SUM(t.final_amount_inr)/1e7 AS revenue_cr,
            COUNT(t.transaction_id) AS total_orders
        FROM transactions t
        JOIN customers c ON t.customer_id = c.customer_id
        GROUP BY t.order_year, c.customer_state
        ORDER BY t.order_year ASC
    """)

    # 2. Dictionary of approximate coordinates for Indian States
    state_coords = {
        'Maharashtra': [19.7515, 75.7139], 'Karnataka': [15.3173, 75.7139],
        'Tamil Nadu': [11.1271, 78.6569], 'Delhi': [28.7041, 77.1025],
        'Gujarat': [22.2587, 71.1924], 'Uttar Pradesh': [26.8467, 80.9462],
        'West Bengal': [22.9868, 87.8550], 'Telangana': [18.1124, 79.0193],
        'Kerala': [10.8505, 76.2711], 'Rajasthan': [27.0238, 74.2179],
        'Andhra Pradesh': [15.9129, 79.7400], 'Haryana': [29.0588, 76.0856],
        'Punjab': [31.1471, 75.3412], 'Madhya Pradesh': [22.9734, 78.6569],
        'Bihar': [25.0961, 85.3131]
    }

    # Map the coordinates to the dataframe
    geo_data['lat'] = geo_data['customer_state'].map(lambda x: state_coords.get(x, [0,0])[0])
    geo_data['lon'] = geo_data['customer_state'].map(lambda x: state_coords.get(x, [0,0])[1])
    geo_data = geo_data[geo_data['lat'] != 0]
    
    # FIX: Sort the years chronologically, then cast to string for the Plotly animation frame
    geo_data = geo_data.sort_values('order_year')
    geo_data['order_year'] = geo_data['order_year'].astype(str)

    # 3. Create the Animated Map
    fig_time_map = px.scatter_mapbox(
        geo_data, 
        lat="lat", lon="lon", 
        color="revenue_cr", size="total_orders",
        color_continuous_scale=px.colors.sequential.Plasma,
        size_max=50, zoom=3.5, 
        animation_frame="order_year",
        animation_group="customer_state",
        hover_name="customer_state",
        hover_data={"lat": False, "lon": False, "revenue_cr": ':.2f', "total_orders": True},
        mapbox_style="carto-darkmatter",
    )

    fig_time_map.update_layout(
        margin={"r":0,"t":10,"l":0,"b":0},
        paper_bgcolor='#0E1117',
        plot_bgcolor='#0E1117',
        height=600
    )

    st.plotly_chart(fig_time_map, use_container_width=True)
    # st.info("⏱️ **Press 'Play'** on the bottom left of the map to watch expansion.")

# ── Top States + Top Cities ────────────────────────────────────────────────────
col_l, col_r = st.columns(2)
with col_l:
    st.markdown("<div class='section-header'>🏛️ Top 15 States by Revenue</div>", unsafe_allow_html=True)
    top_s = state_df.head(15)
    fig_s = px.bar(top_s, x='rev_cr', y='customer_state', orientation='h',
                    color='rev_cr', color_continuous_scale='Blues',
                    text=[f'₹{v:.1f}Cr' for v in top_s['rev_cr']],
                    labels={'rev_cr':'Revenue (₹Cr)','customer_state':''})
    fig_s.update_traces(textposition='outside', textfont_color='white', textfont_size=10)
    fig_s.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                         height=500, coloraxis_showscale=False, showlegend=False, margin=dict(t=20,b=20,r=70))
    st.plotly_chart(fig_s, use_container_width=True)

with col_r:
    st.markdown("<div class='section-header'>🏙️ Top 20 Cities by Revenue</div>", unsafe_allow_html=True)
    top_c = city_df.head(20)
    fig_c = go.Figure(go.Bar(
        x=top_c['rev_cr'], y=top_c['customer_city'], orientation='h',
        marker_color=[TIER_COLORS.get(str(t),'#8B949E') for t in top_c['customer_tier']],
        text=[f'₹{v:.1f}Cr' for v in top_c['rev_cr']],
        textposition='outside', textfont=dict(color='white',size=10)))
    for tier, color in TIER_COLORS.items():
        fig_c.add_trace(go.Bar(x=[None],y=[None],name=tier,marker_color=color,orientation='h'))
    fig_c.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                         height=500, barmode='overlay',
                         legend=dict(title='Tier',orientation='v',font=dict(size=9)),
                         xaxis=dict(title='Revenue (₹ Crores)'), margin=dict(t=20,b=20,r=70))
    st.plotly_chart(fig_c, use_container_width=True)

# ── Tier Donut + Tier Trend ────────────────────────────────────────────────────
col_l2, col_r2 = st.columns([1,2])
with col_l2:
    st.markdown("<div class='section-header'>🍩 Revenue by Customer Tier</div>", unsafe_allow_html=True)
    fig_td = go.Figure(go.Pie(values=tier_df['rev_cr'], labels=tier_df['customer_tier'],
                               hole=0.55, marker=dict(colors=[TIER_COLORS.get(str(t),'#8B949E') for t in tier_df['customer_tier']]),
                               textinfo='label+percent', textfont=dict(color='white',size=12)))
    fig_td.update_layout(template='plotly_dark', paper_bgcolor='#0E1117',
                          height=350, showlegend=False, margin=dict(t=20,b=20))
    st.plotly_chart(fig_td, use_container_width=True)

with col_r2:
    st.markdown("<div class='section-header'>📈 Revenue by Tier over Years</div>", unsafe_allow_html=True)
    tier_yr = run_query(f"""
        SELECT t.order_year, c.customer_tier, ROUND(SUM(t.final_amount_inr)/1e7,2) AS rev_cr
        FROM transactions t JOIN customers c ON t.customer_id=c.customer_id
        WHERE {fs['wt']} {fs['wc']}
        GROUP BY t.order_year, c.customer_tier ORDER BY t.order_year
    """)
    fig_tyr = go.Figure()
    for tier in tier_yr['customer_tier'].dropna().unique():
        sub = tier_yr[tier_yr['customer_tier']==tier]
        fig_tyr.add_trace(go.Scatter(x=sub['order_year'], y=sub['rev_cr'], mode='lines+markers',
                                      name=str(tier), line=dict(width=2.5,color=TIER_COLORS.get(str(tier),'#8B949E')),
                                      marker=dict(size=8)))
    fig_tyr.update_layout(template='plotly_dark', plot_bgcolor='#0E1117', paper_bgcolor='#0E1117',
                           height=350, yaxis=dict(title='Revenue (₹ Crores)'),
                           xaxis=dict(title='Year',tickmode='linear',dtick=1),
                           legend=dict(orientation='h',y=1.1), margin=dict(t=20,b=20))
    st.plotly_chart(fig_tyr, use_container_width=True)

st.markdown("---")
c1,c2,c3 = st.columns(3)
with c1: st.markdown("<div class='insight-box'>🏙️ <b>Metro cities</b> drive 60%+ of total revenue despite being fewer in number.</div>", unsafe_allow_html=True)
with c2: st.markdown("<div class='insight-box'>📈 <b>Tier 2 cities show fastest growth</b> — rising smartphone penetration and improved logistics.</div>", unsafe_allow_html=True)
with c3: st.markdown("<div class='insight-box'>🌾 <b>Rural markets remain underserved</b> — significant expansion opportunity for Prime.</div>", unsafe_allow_html=True)
