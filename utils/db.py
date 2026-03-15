"""utils/db.py — SQLite connection + cached query runner."""
import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

# Update this path to point to your amazon_india.db
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'data', 'amazon_india.db'
)



@st.cache_resource
def get_engine():
    if not os.path.exists(DB_PATH):
        st.error(f"❌ DB not found: {DB_PATH}\nUpdate DB_PATH in utils/db.py")
        st.stop()
    return create_engine(f'sqlite:///{DB_PATH}', echo=False)


@st.cache_data(ttl=300)
def run_query(sql: str) -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn)
