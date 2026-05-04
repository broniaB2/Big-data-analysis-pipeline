import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path

st.set_page_config(page_title="Patent Dashboard", layout="wide")
st.title("🚀 Patent Analytics Dashboard")

# Load database
db_path = Path("patents.db")
if not db_path.exists():
    st.error("Database not found!")
    st.stop()

st.write("Loading data...")

con = sqlite3.connect(str(db_path))

# Simple metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    result = pd.read_sql("SELECT COUNT(*) as total FROM patents", con)
    st.metric("Total Patents", f"{int(result.iloc[0]['total']):,}")

with col2:
    result = pd.read_sql("SELECT COUNT(*) as total FROM companies", con)
    st.metric("Companies", f"{int(result.iloc[0]['total']):,}")

with col3:
    result = pd.read_sql("SELECT COUNT(*) as total FROM technologies", con)
    st.metric("Tech Fields", f"{int(result.iloc[0]['total']):,}")

with col4:
    result = pd.read_sql("SELECT COUNT(*) as total FROM patent_companies", con)
    st.metric("Links", f"{int(result.iloc[0]['total']):,}")

st.divider()
st.subheader("Top 10 Companies")

top_companies = pd.read_sql("""
    SELECT c.name, COUNT(pc.patent_id) as count
    FROM companies c
    JOIN patent_companies pc ON c.company_id = pc.company_id
    GROUP BY c.company_id
    ORDER BY count DESC
    LIMIT 10
""", con)

st.dataframe(top_companies, use_container_width=True)

con.close()
st.write("✅ Dashboard loaded successfully!")
