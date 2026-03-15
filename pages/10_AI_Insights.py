import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
st.set_page_config(page_title="AI Insights", page_icon="🤖",
                   layout="wide", initial_sidebar_state="expanded")

import json
import requests
import warnings
warnings.filterwarnings('ignore')

from utils.db import run_query
from utils.sidebar import render_sidebar, get_filter_sql

filters = render_sidebar()
fs      = get_filter_sql(filters)

st.markdown("""
<h1 style='color:#FFD700;text-align:center;'>
    🤖 ASK THE <span style='color:#00D4FF;'>DATA — AI INSIGHTS</span>
</h1>
<p style='text-align:center;color:#8B949E;font-size:0.9rem;margin-top:-0.5rem;'>
    Powered by AI · Ask any business question about Amazon India 2015–2025
</p>
""", unsafe_allow_html=True)
st.markdown("---")

# ── Fetch live context from DB ────────────────────────────────────────────────
@st.cache_data(ttl=1800)
def get_data_context():
    kpi = run_query("""
        SELECT
            COUNT(*) AS total_txns,
            COUNT(DISTINCT customer_id) AS total_customers,
            ROUND(SUM(final_amount_inr)/1e9, 2) AS total_rev_bn,
            ROUND(AVG(final_amount_inr), 0) AS avg_order,
            ROUND(AVG(discount_percent), 1) AS avg_disc,
            ROUND(AVG(delivery_days), 1) AS avg_del,
            ROUND(100.0*SUM(CASE WHEN is_prime_member=1 THEN 1 ELSE 0 END)/COUNT(*),1) AS prime_pct,
            ROUND(100.0*SUM(CASE WHEN return_status='Returned' THEN 1 ELSE 0 END)/COUNT(*),1) AS return_rate,
            ROUND(100.0*SUM(CASE WHEN is_festival_sale=1 THEN 1 ELSE 0 END)/COUNT(*),1) AS fest_pct
        FROM transactions
    """)

    yearly = run_query("""
        SELECT order_year,
               ROUND(SUM(final_amount_inr)/1e9, 2) AS rev_bn,
               COUNT(*) AS orders
        FROM transactions
        GROUP BY order_year ORDER BY order_year
    """)

    top_cats = run_query("""
        SELECT p.category,
               ROUND(SUM(t.final_amount_inr)/1e9, 2) AS rev_bn
        FROM transactions t JOIN products p ON t.product_id=p.product_id
        GROUP BY p.category ORDER BY rev_bn DESC LIMIT 5
    """)

    top_cities = run_query("""
        SELECT c.customer_city,
               ROUND(SUM(t.final_amount_inr)/1e7, 1) AS rev_cr
        FROM transactions t JOIN customers c ON t.customer_id=c.customer_id
        GROUP BY c.customer_city ORDER BY rev_cr DESC LIMIT 5
    """)

    payment = run_query("""
        SELECT payment_method,
               ROUND(100.0*COUNT(*)/SUM(COUNT(*)) OVER(), 1) AS pct
        FROM transactions
        GROUP BY payment_method ORDER BY pct DESC LIMIT 5
    """)

    festivals = run_query("""
        SELECT festival_name,
               ROUND(SUM(final_amount_inr)/1e7, 1) AS rev_cr
        FROM transactions
        WHERE is_festival_sale=1
        AND festival_name IS NOT NULL AND TRIM(festival_name) != ''
        GROUP BY festival_name ORDER BY rev_cr DESC LIMIT 5
    """)

    prime_comp = run_query("""
        SELECT is_prime_member,
               ROUND(AVG(final_amount_inr), 0) AS avg_order,
               COUNT(*) AS orders
        FROM transactions GROUP BY is_prime_member
    """)

    return {
        'kpi':        kpi.iloc[0].to_dict(),
        'yearly':     yearly.to_dict(orient='records'),
        'top_cats':   top_cats.to_dict(orient='records'),
        'top_cities': top_cities.to_dict(orient='records'),
        'payment':    payment.to_dict(orient='records'),
        'festivals':  festivals.to_dict(orient='records'),
        'prime_comp': prime_comp.to_dict(orient='records'),
    }

ctx = get_data_context()

# Build system prompt with live data
system_prompt = f"""
You are an expert e-commerce business analyst for Amazon India.
You have access to the following LIVE data from Amazon India's 
transactional database (2015–2025, ~1M transactions):

=== KEY METRICS ===
- Total Revenue: ₹{ctx['kpi']['total_rev_bn']}Bn
- Total Transactions: {ctx['kpi']['total_txns']:,}
- Total Customers: {ctx['kpi']['total_customers']:,}
- Average Order Value: ₹{ctx['kpi']['avg_order']:,.0f}
- Average Discount: {ctx['kpi']['avg_disc']}%
- Average Delivery Days: {ctx['kpi']['avg_del']}
- Prime Member %: {ctx['kpi']['prime_pct']}%
- Return Rate: {ctx['kpi']['return_rate']}%
- Festival Sale %: {ctx['kpi']['fest_pct']}%

=== YEARLY REVENUE (₹Bn) ===
{json.dumps(ctx['yearly'], indent=2)}

=== TOP CATEGORIES BY REVENUE ===
{json.dumps(ctx['top_cats'], indent=2)}

=== TOP CITIES BY REVENUE ===
{json.dumps(ctx['top_cities'], indent=2)}

=== PAYMENT METHODS ===
{json.dumps(ctx['payment'], indent=2)}

=== TOP FESTIVALS BY REVENUE ===
{json.dumps(ctx['festivals'], indent=2)}

=== PRIME VS NON-PRIME ===
{json.dumps(ctx['prime_comp'], indent=2)}

=== YOUR ROLE ===
Answer business questions clearly and concisely.
Always reference specific numbers from the data above.
Structure answers with:
1. Direct answer in first sentence
2. Supporting data points
3. One actionable business recommendation
Keep responses under 200 words.
Use ₹ symbol for Indian Rupees.
Be confident and data-driven.
"""

# ── Suggested Questions ───────────────────────────────────────────────────────
st.markdown("<div class='section-header'>💡 Suggested Questions</div>",
            unsafe_allow_html=True)

suggested = [
    "Which year had the highest revenue growth?",
    "How does Prime membership affect order value?",
    "Which city should Amazon focus on for expansion?",
    "What is the impact of festival sales on revenue?",
    "Which product category has the best performance?",
    "What payment method is most popular and why does it matter?",
    "Is the return rate a concern? What could be causing it?",
    "What strategy would you recommend for 2026?",
]

cols = st.columns(4)
for i, q in enumerate(suggested):
    with cols[i % 4]:
        if st.button(q, key=f'sq_{i}', use_container_width=True):
            st.session_state['ai_question'] = q

st.markdown("<br>", unsafe_allow_html=True)

# ── Chat Interface ────────────────────────────────────────────────────────────
st.markdown("<div class='section-header'>💬 Ask Your Question</div>",
            unsafe_allow_html=True)

# Initialize chat history
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Pre-fill from suggested question click
default_q = st.session_state.pop('ai_question', '')

user_input = st.text_input(
    "Type your business question here...",
    value=default_q,
    placeholder="e.g. Which city grew the fastest between 2020 and 2023?",
    key='ai_input'
)

col_ask, col_clear, col_empty = st.columns([2, 2, 8])
with col_ask:
    ask_clicked = st.button("🔍 Ask AI", use_container_width=True)
with col_clear:
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()

if ask_clicked and user_input.strip():
    with st.spinner("🤖 Analyzing your data..."):
        try:
            # Build messages with history
            messages = []
            for turn in st.session_state.chat_history[-6:]:  # last 3 turns
                messages.append({"role": "user",      "content": turn['q']})
                messages.append({"role": "assistant", "content": turn['a']})
            messages.append({"role": "user", "content": user_input})

            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {st.secrets['GROQ_API_KEY']}",
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "max_tokens": 1000,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        *messages
                    ],
                },
                timeout=30
            )

            data   = response.json()
            answer = data['choices'][0]['message']['content']

            if answer:
                st.session_state.chat_history.append({
                    'q': user_input,
                    'a': answer
                })
            else:
                st.error("No response received. Please try again.")

        except Exception as e:
            st.error(f"Error connecting to AI: {e}")

# ── Render Chat History ───────────────────────────────────────────────────────
if st.session_state.chat_history:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>📜 Conversation</div>",
                unsafe_allow_html=True)

    for i, turn in enumerate(reversed(st.session_state.chat_history)):
        # User message
        st.markdown(f"""
        <div style='background:#1C2333;border:1px solid #30363D;
                    border-radius:12px;padding:0.8rem 1rem;
                    margin-bottom:0.5rem;
                    border-left:4px solid #58A6FF;'>
            <div style='font-size:0.65rem;color:#58A6FF;
                        text-transform:uppercase;font-weight:700;
                        margin-bottom:0.3rem;'>🧑 You</div>
            <div style='font-size:0.88rem;color:#C9D1D9;'>{turn['q']}</div>
        </div>
        """, unsafe_allow_html=True)

        # AI response
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#1C2333,#161B22);
                    border:1px solid #30363D;border-radius:12px;
                    padding:0.8rem 1rem 0.4rem 1rem;
                    margin-bottom:0.3rem;
                    border-left:4px solid #FF9900;'>
            <div style='font-size:0.65rem;color:#FF9900;
                        text-transform:uppercase;font-weight:700;
                        margin-bottom:0.3rem;'>🤖 AI Analyst</div>
        </div>
        """, unsafe_allow_html=True)
        with st.container():
            st.markdown(turn['a'])
        st.markdown("<br>", unsafe_allow_html=True)


# ── Empty state ───────────────────────────────────────────────────────────────
else:
    st.markdown("""
    <div style='background:linear-gradient(135deg,#1C2333,#161B22);
                border:1px solid #30363D;border-radius:14px;
                padding:2rem;text-align:center;margin-top:1rem;'>
        <div style='font-size:3rem;margin-bottom:1rem;'>🤖</div>
        <div style='font-size:1rem;font-weight:700;color:#FF9900;
                    margin-bottom:0.5rem;'>Ready to Analyze Your Data</div>
        <div style='font-size:0.85rem;color:#8B949E;'>
            Click a suggested question above or type your own.<br>
            The AI has access to live metrics from your entire 2015–2025 dataset.
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ── Live Data Snapshot ────────────────────────────────────────────────────────
with st.expander("📊 View Live Data Context (what the AI can see)", expanded=False):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**📈 Yearly Revenue**")
        import pandas as pd
        st.dataframe(
            pd.DataFrame(ctx['yearly']).rename(
                columns={'order_year':'Year','rev_bn':'Revenue (₹Bn)','orders':'Orders'}),
            hide_index=True, use_container_width=True
        )
    with c2:
        st.markdown("**🛍️ Top Categories**")
        st.dataframe(
            pd.DataFrame(ctx['top_cats']).rename(
                columns={'category':'Category','rev_bn':'Revenue (₹Bn)'}),
            hide_index=True, use_container_width=True
        )
    with c3:
        st.markdown("**💳 Payment Methods**")
        st.dataframe(
            pd.DataFrame(ctx['payment']).rename(
                columns={'payment_method':'Method','pct':'Share %'}),
            hide_index=True, use_container_width=True
        )