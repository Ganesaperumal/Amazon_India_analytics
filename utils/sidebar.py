"""
utils/sidebar.py
Shared sidebar: Amazon nav + 12 filters + SQL builder + heatmap text fix.
Import render_sidebar() and get_filter_sql() in every page.
"""
import streamlit as st
import matplotlib.pyplot as plt
from utils.db import run_query

# ── Static option lists ───────────────────────────────────────────────────────
ALL_TIERS    = ['Metro', 'Tier1', 'Tier2', 'Rural']
ALL_AGES     = ['18-25', '26-35', '36-45', '46-55', '55+']
ALL_STATUSES = ['Delivered', 'Returned', 'Cancelled']
ALL_QUARTERS = ['Q1', 'Q2', 'Q3', 'Q4']
ALL_PAYMENTS = ['UPI', 'Cash on Delivery', 'Credit Card',
                'Debit Card', 'Net Banking', 'Wallet', 'BNPL']

NAV_ITEMS = [
    ("app.py",                              "🏠 Home"),
    ("pages/0_Data_Quality.py",             "🧹 Data Quality"),
    ("pages/1_Executive_Financial.py",      "📊 Executive & Financial"),
    ("pages/2_Revenue_Analytics.py",        "📈 Revenue Analytics"),
    ("pages/3_Customer_Analytics.py",       "👥 Customer Analytics"),
    ("pages/4_Product_Brand.py",            "🛍️ Product & Brand"),
    ("pages/5_Geographic.py",               "🗺️ Geographic"),
    ("pages/6_Payment_Operations.py",       "💳 Payment & Operations"),
    ("pages/7_Festival_Seasonal.py",        "🎉 Festival & Seasonal"),
    ("pages/8_Predictive_Advanced.py",      "🔮 Predictive & Advanced"),
    ("pages/9_Simulator.py",                "🎮 Business Simulator"),
    ("pages/10_AI_Insights.py",             "🤖 AI Insights")
]

# ── DB helpers (cached) ───────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def _states():
    df = run_query("SELECT DISTINCT customer_state FROM customers WHERE customer_state IS NOT NULL ORDER BY customer_state")
    return df['customer_state'].tolist()

@st.cache_data(ttl=3600)
def _cities(states_key):
    states = list(states_key)
    if states:
        s = "','".join(states)
        df = run_query(f"SELECT DISTINCT customer_city FROM customers WHERE customer_state IN ('{s}') AND customer_city IS NOT NULL ORDER BY customer_city")
    else:
        df = run_query("SELECT DISTINCT customer_city FROM customers WHERE customer_city IS NOT NULL ORDER BY customer_city")
    return df['customer_city'].tolist()

@st.cache_data(ttl=3600)
def _festivals():
    df = run_query("SELECT DISTINCT festival_name FROM transactions WHERE festival_name IS NOT NULL AND TRIM(festival_name) != '' ORDER BY festival_name")
    return df['festival_name'].tolist()

# ── CSS loader ────────────────────────────────────────────────────────────────
def _load_css():
    st.markdown("""
    <style>
    /* ── Hide Streamlit default nav ── */
    [data-testid="stSidebarNav"]          { display: none !important; }
    section[data-testid="stSidebarNav"]   { display: none !important; }
    [data-testid="stSidebarNavItems"]     { display: none !important; }
    [data-testid="stSidebarNavSeparator"] { display: none !important; }
    div[data-testid="stSidebarUserContent"] > div:first-child ul { display: none !important; }

    /* ── App background ── */
    [data-testid="stAppViewContainer"] { background-color: #0E1117; }
    [data-testid="stSidebar"]          { background-color: #161B22; border-right: 1px solid #30363D; }
    [data-testid="stHeader"]           { background-color: #0E1117; }

    /* ── KPI cards ── */
    .kpi-card {
        background: linear-gradient(135deg, #1C2333, #161B22);
        border: 1px solid #30363D;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .kpi-card:hover { border-color: #FF9900; }
    .kpi-label {
        font-size: .76rem;
        color: #8B949E;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: .8px;
        margin-bottom: .4rem;
    }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 800;
        color: #FF9900;
        line-height: 1.1;
    }

    /* ── Section headers ── */
    .section-header {
        font-size: .95rem;
        font-weight: 700;
        color: #FF9900;
        margin: 1rem 0 .5rem 0;
        padding-bottom: 4px;
        border-bottom: 2px solid #FF9900;
        display: inline-block;
    }

    /* ── Insight box ── */
    .insight-box {
        background: #1C2333;
        border-left: 4px solid #FF9900;
        border-radius: 0 8px 8px 0;
        padding: .8rem 1rem;
        margin: .5rem 0;
        font-size: .84rem;
        color: #C9D1D9;
    }

    /* ── Metric overrides ── */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #1C2333, #161B22);
        border: 1px solid #30363D;
        border-radius: 10px;
        padding: 1rem;
    }
    [data-testid="metric-container"] label {
        color: #8B949E !important;
        font-size: .72rem !important;
        text-transform: uppercase;
    }
    [data-testid="stMetricValue"] {
        color: #FF9900 !important;
        font-size: 1.5rem !important;
        font-weight: 800 !important;
    }

    /* ── Divider ── */
    hr { border-color: #30363D !important; margin: 1rem 0 !important; }

    /* ── Sidebar filter labels ── */
    [data-testid="stSelectbox"] label,
    [data-testid="stMultiSelect"] label {
        color: #8B949E !important;
        font-size: .75rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
    }

    /* ── Sidebar links ── */
    [data-testid="stSidebar"] a { color: #C9D1D9 !important; font-size: .84rem; }
    [data-testid="stSidebar"] a:hover { color: #FF9900 !important; }
    </style>
    """, unsafe_allow_html=True)

# ── Main render ───────────────────────────────────────────────────────────────
def render_sidebar():
    """
    Call at the top of every page.
    Renders: Amazon logo + nav links + 12 filter widgets.
    Returns: filters dict.
    """
    _load_css()

    with st.sidebar:

        # ── Logo ──────────────────────────────────────────────────────────────
        st.markdown("""
        <div style='text-align:center;padding:3rem 0 2rem 0;'>
            <img src="https://www.pngplay.com/wp-content/uploads/3/White-Amazon-Logo-PNG-HD-Quality.png" style="width: 150px; margin-bottom: 5px;" alt="Amazon Logo">
            <div style='font-size:0.62rem;color:#8B949E;letter-spacing:2px;margin-top:2px;'>A DECADE OF ANALYTICS</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<hr style='border-color:#30363D;margin:0.4rem 0;'>", unsafe_allow_html=True)

        # ── Navigation ────────────────────────────────────────────────────────
        st.markdown("<p style='font-size:0.62rem;color:#8B949E;text-transform:uppercase;letter-spacing:1.5px;font-weight:700;margin:0.4rem 0 0.2rem 0;'>📌 Navigate</p>", unsafe_allow_html=True)
        for path, label in NAV_ITEMS:
            st.page_link(path, label=label)

        st.markdown("<hr style='border-color:#30363D;margin:0.5rem 0;'>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.62rem;color:#8B949E;text-transform:uppercase;letter-spacing:1.5px;font-weight:700;margin:0.2rem 0;'>🎛️ Filters</p>", unsafe_allow_html=True)

        # ── Group 1: Time ─────────────────────────────────────────────────────
        with st.expander("⏱️ Time", expanded=True):
            year_range = st.slider("📅 Year Range", 2015, 2025, (2015, 2025), key='f_year')
            quarters   = st.multiselect("📅 Quarter", ALL_QUARTERS, default=[], key='f_quarter', placeholder="All Quarters")

        # ── Group 2: Location ─────────────────────────────────────────────────
        with st.expander("📍 Location", expanded=False):
            customer_tier = st.multiselect("🗺️ Customer Tier", ALL_TIERS, default=[], key='f_tier', placeholder="All Tiers")
            all_states    = _states()
            states        = st.multiselect("🏛️ State", all_states, default=[], key='f_state', placeholder="All States")
            avail_cities  = _cities(tuple(sorted(states)))
            cities        = st.multiselect("🏙️ City", avail_cities, default=[], key='f_city',
                                           placeholder="All Cities" if not states else f"Cities in {len(states)} state(s)")

        # ── Group 3: Customer ─────────────────────────────────────────────────
        with st.expander("👤 Customer", expanded=False):
            prime      = st.radio("👑 Prime Member", ["All", "Prime Only", "Non-Prime Only"], key='f_prime', horizontal=False)
            age_groups = st.multiselect("👶 Age Group", ALL_AGES, default=[], key='f_age', placeholder="All Ages")

        # ── Group 4: Transaction ──────────────────────────────────────────────
        with st.expander("💰 Transaction", expanded=False):
            payment_methods = st.multiselect("💳 Payment Method", ALL_PAYMENTS, default=[], key='f_payment', placeholder="All Methods")
            return_status   = st.multiselect("↩️ Return Status", ALL_STATUSES, default=[], key='f_return', placeholder="All Statuses")
            discount_band   = st.slider("🏷️ Discount %", 0, 80, (0, 80), key='f_discount')

        # ── Group 5: Festival ─────────────────────────────────────────────────
        with st.expander("🎉 Festival", expanded=False):
            festival_sale  = st.radio("🎉 Festival Sale", ["All", "Festival Only", "Normal Only"], key='f_fest_sale')
            festival_names = []
            if festival_sale != "Normal Only":
                all_fests      = _festivals()
                festival_names = st.multiselect("🎊 Festival Name", all_fests, default=[], key='f_fest_name', placeholder="All Festivals")

        # ── Top 5 Findings ───────────────────────────────────────────────────
        st.markdown("<hr style='border-color:#30363D;margin:0.5rem 0;'>", unsafe_allow_html=True)

        with st.expander("🔍 Top 5 Quick Findings", expanded=False):
            try:
                findings = run_query("""
                    SELECT
                        -- Best year
                        (SELECT order_year FROM transactions
                         GROUP BY order_year
                         ORDER BY SUM(final_amount_inr) DESC LIMIT 1) AS best_year,

                        -- Best category
                        (SELECT p.category
                         FROM transactions t JOIN products p ON t.product_id=p.product_id
                         GROUP BY p.category
                         ORDER BY SUM(t.final_amount_inr) DESC LIMIT 1) AS best_cat,

                        -- Prime vs Non-Prime AOV ratio
                        ROUND(
                            (SELECT AVG(final_amount_inr) FROM transactions WHERE is_prime_member=1) /
                            (SELECT AVG(final_amount_inr) FROM transactions WHERE is_prime_member=0)
                        , 1) AS prime_ratio,

                        -- Top city
                        (SELECT c.customer_city
                         FROM transactions t JOIN customers c ON t.customer_id=c.customer_id
                         GROUP BY c.customer_city
                         ORDER BY SUM(t.final_amount_inr) DESC LIMIT 1) AS top_city,

                        -- Festival lift
                        ROUND(
                            (SELECT AVG(final_amount_inr) FROM transactions WHERE is_festival_sale=1) /
                            (SELECT AVG(final_amount_inr) FROM transactions WHERE is_festival_sale=0) * 100 - 100
                        , 1) AS fest_lift
                """)

                best_year  = int(findings['best_year'].iloc[0])
                best_cat   = findings['best_cat'].iloc[0]
                prime_ratio= findings['prime_ratio'].iloc[0]
                top_city   = findings['top_city'].iloc[0]
                fest_lift  = findings['fest_lift'].iloc[0]

                items = [
                    ('🏆', f'{best_year} was the highest revenue year'),
                    ('🛍️', f'{best_cat} is the top revenue category'),
                    ('👑', f'Prime members spend {prime_ratio}x more than non-Prime'),
                    ('🏙️', f'{top_city} is the #1 revenue city'),
                    ('🎉', f'Festival sales generate {fest_lift:+.1f}% higher AOV'),
                ]

                for emoji, text in items:
                    st.markdown(f"""
                    <div style='display:flex;align-items:flex-start;
                                margin-bottom:0.5rem;padding:0.4rem;
                                background:#0E1117;border-radius:6px;
                                border-left:2px solid #FF9900;'>
                        <span style='margin-right:0.4rem;font-size:0.9rem;'>{emoji}</span>
                        <span style='font-size:0.72rem;color:#C9D1D9;
                                     line-height:1.4;'>{text}</span>
                    </div>
                    """, unsafe_allow_html=True)

            except Exception:
                st.markdown("<div style='font-size:0.72rem;color:#8B949E;'>"
                            "Connect DB to see findings</div>",
                            unsafe_allow_html=True)
    
        # st.markdown("<hr style='border-color:#30363D;margin:0.5rem 0;'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center;font-size:0.62rem;color:#8B949E;'>2015–2025 · ~1M Transactions</div>", unsafe_allow_html=True)


    return {
        'year_range':     year_range,
        'quarters':       quarters,
        'customer_tier':  customer_tier,
        'states':         states,
        'cities':         cities,
        'prime':          prime,
        'age_groups':     age_groups,
        'payment_methods':payment_methods,
        'return_status':  return_status,
        'festival_sale':  festival_sale,
        'festival_names': festival_names,
        'discount_band':  discount_band,
    }


# ── SQL builder ───────────────────────────────────────────────────────────────
def get_filter_sql(f):
    """
    Returns dict of SQL WHERE strings built from the filters dict.

    Keys:
      w    – conditions for transactions (no alias)
      wt   – conditions for transactions aliased as t
      wc   – ' AND c.xxx...' for queries that JOIN customers AS c
      wsub – ' AND customer_id IN (...)' subquery (when no customer JOIN)
    """
    yr_min, yr_max   = f['year_range']
    disc_min, disc_max = f['discount_band']

    def _build(prefix=''):
        """Build condition list for a given column prefix ('t.' or '')."""
        p = prefix  # e.g. 't.' or ''
        parts = [f"{p}order_year BETWEEN {yr_min} AND {yr_max}"]

        if f['prime'] == 'Prime Only':
            parts.append(f"{p}is_prime_member = 1")
        elif f['prime'] == 'Non-Prime Only':
            parts.append(f"{p}is_prime_member = 0")

        if f['festival_sale'] == 'Festival Only':
            parts.append(f"{p}is_festival_sale = 1")
        elif f['festival_sale'] == 'Normal Only':
            parts.append(f"{p}is_festival_sale = 0")

        if f['festival_names']:
            n = "','".join(f['festival_names'])
            parts.append(f"{p}festival_name IN ('{n}')")

        if f['payment_methods']:
            m = "','".join(f['payment_methods'])
            parts.append(f"{p}payment_method IN ('{m}')")

        if f['return_status']:
            s = "','".join(f['return_status'])
            parts.append(f"{p}return_status IN ('{s}')")

        if disc_min > 0 or disc_max < 80:
            parts.append(f"{p}discount_percent BETWEEN {disc_min} AND {disc_max}")

        if f['quarters']:
            q_map = {'Q1': (1, 3), 'Q2': (4, 6), 'Q3': (7, 9), 'Q4': (10, 12)}
            q_conds = []
            for q in f['quarters']:
                ms, me = q_map[q]
                col = f"CAST(strftime('%m', {p}order_date) AS INTEGER)"
                q_conds.append(f"({col} BETWEEN {ms} AND {me})")
            parts.append(f"({' OR '.join(q_conds)})")

        return " AND ".join(parts)

    w  = _build('')
    wt = _build('t.')

    # Customer conditions (c alias)
    wc_parts = []
    if f['customer_tier']:
        t = "','".join(f['customer_tier']); wc_parts.append(f"c.customer_tier IN ('{t}')")
    if f['states']:
        s = "','".join(f['states']);        wc_parts.append(f"c.customer_state IN ('{s}')")
    if f['cities']:
        c = "','".join(f['cities']);        wc_parts.append(f"c.customer_city IN ('{c}')")
    if f['age_groups']:
        a = "','".join(f['age_groups']);    wc_parts.append(f"c.customer_age_group IN ('{a}')")
    wc = (" AND " + " AND ".join(wc_parts)) if wc_parts else ""

    # Customer subquery (no JOIN)
    sub_parts = []
    if f['customer_tier']:
        t = "','".join(f['customer_tier']); sub_parts.append(f"customer_tier IN ('{t}')")
    if f['states']:
        s = "','".join(f['states']);        sub_parts.append(f"customer_state IN ('{s}')")
    if f['cities']:
        c = "','".join(f['cities']);        sub_parts.append(f"customer_city IN ('{c}')")
    if f['age_groups']:
        a = "','".join(f['age_groups']);    sub_parts.append(f"customer_age_group IN ('{a}')")
    wsub = (f" AND customer_id IN (SELECT customer_id FROM customers WHERE {' AND '.join(sub_parts)})"
            if sub_parts else "")

    return {'w': w, 'wt': wt, 'wc': wc, 'wsub': wsub}


# ── Heatmap text visibility fix ───────────────────────────────────────────────
def fix_heatmap_text(ax, cmap_name, vmin, vmax):
    """
    Auto-color seaborn heatmap annotation text based on cell background luminance.
    Call AFTER sns.heatmap(). Prevents white-on-white and black-on-black.
    """
    cmap = plt.get_cmap(cmap_name)
    for text in ax.texts:
        try:
            val = float(str(text.get_text()).replace(',', '').replace('%', '').strip())
            norm = max(0.0, min(1.0, (val - vmin) / max(vmax - vmin, 1e-8)))
            r, g, b, _ = cmap(norm)
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            text.set_color('white' if lum < 0.55 else '#111111')
        except Exception:
            text.set_color('white')