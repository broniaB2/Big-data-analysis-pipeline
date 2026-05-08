"""
Patent Analytics Dashboard - OPTIMIZED for SPEED
Loads from pre-generated CSV/JSON reports for instant performance (no database queries)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import json
from pathlib import Path

st.set_page_config(
    page_title="PatentsView Technology Trends Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ════════════════════════════════════════════════════════════════════
#  HEADER
# ════════════════════════════════════════════════════════════════════
st.markdown("""
    <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 20px;'>
        <h1 style='color: white; margin: 0;'>📊 Patent Analytics Dashboard</h1>
        <p style='color: #e0e0e0; margin: 5px 0 0 0;'>USPTO PatentsView Pipeline Analysis</p>
    </div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
#  LOAD REPORTS (FAST - FROM CSV FILES)
# ════════════════════════════════════════════════════════════════════
REPORTS_DIR = Path("Reports")

@st.cache_data
def load_csv(filename):
    """Load CSV file with error handling"""
    try:
        return pd.read_csv(REPORTS_DIR / filename)
    except FileNotFoundError:
        st.error(f"❌ Missing: {filename}\nRun: `python data_pipeline.py --sample`")
        return None

@st.cache_data
def load_json_report():
    """Load JSON summary"""
    try:
        with open(REPORTS_DIR / "patent_report.json") as f:
            return json.load(f)
    except FileNotFoundError:
        st.warning("JSON report not found. Run data_pipeline.py first.")
        return {}

# Load all reports
top_companies = load_csv("top_companies.csv")
patents_yearly = load_csv("patents_per_year.csv")
tech_sectors = load_csv("top_tech_sectors.csv")
company_ranking = load_csv("company_ranking.csv")
tech_by_decade = load_csv("tech_by_decade.csv")
tech_growth = load_csv("tech_growth.csv")
json_report = load_json_report()

if top_companies is None:
    st.stop()

# ════════════════════════════════════════════════════════════════════
#  KEY METRICS
# ════════════════════════════════════════════════════════════════════
st.subheader("📈 Summary Statistics")

col1, col2, col3, col4 = st.columns(4)

stats = json_report.get('summary', {})
with col1:
    st.metric("📋 Total Patents", f"{stats.get('total_patents', 0):,}")
with col2:
    st.metric("🏢 Companies", f"{stats.get('total_companies', 0):,}")
with col3:
    st.metric("⚙️ Tech Fields", f"{stats.get('total_technologies', 0):,}")
with col4:
    date_gen = json_report.get('generated_at', 'N/A')
    st.metric("📅 Report Date", date_gen[:10] if date_gen != 'N/A' else 'N/A')

st.divider()

# ════════════════════════════════════════════════════════════════════
#  TABS
# ════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏢 Top Companies",
    "📅 Year Trends",
    "⚙️ Tech Sectors",
    "📊 By Decade",
    "🚀 Growth",
    "🏆 Rankings"
])

# ════════════════════════════════════════════════════════════════════
#  TAB 1: TOP COMPANIES
# ════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Top 20 Companies by Patent Count")
    
    if top_companies is not None and len(top_companies) > 0:
        fig = px.bar(
            top_companies.head(20),
            x=top_companies.columns[1],
            y=top_companies.columns[0],
            orientation='h',
            color=top_companies.columns[1],
            color_continuous_scale='Blues',
            title="Top Companies"
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(top_companies.head(15), use_container_width=True, hide_index=True)

# ════════════════════════════════════════════════════════════════════
#  TAB 2: YEARLY TRENDS
# ════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Patents Filed Per Year")
    
    if patents_yearly is not None and len(patents_yearly) > 0:
        fig = px.line(
            patents_yearly,
            x=patents_yearly.columns[0],
            y=patents_yearly.columns[1],
            markers=True,
            title="Patent Filing Trend",
            labels={patents_yearly.columns[0]: 'Year', patents_yearly.columns[1]: 'Count'}
        )
        fig.update_layout(height=400, hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("First Year", int(patents_yearly.iloc[0, 0]))
        with col2:
            st.metric("Recent Year Count", int(patents_yearly.iloc[-1, 1]))
        
        st.dataframe(patents_yearly.tail(20), use_container_width=True, hide_index=True)

# ════════════════════════════════════════════════════════════════════
#  TAB 3: TECHNOLOGY SECTORS
# ════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Top Technology Sectors")
    
    if tech_sectors is not None and len(tech_sectors) > 0:
        fig = px.bar(
            tech_sectors.head(15),
            x=tech_sectors.columns[1],
            y=tech_sectors.columns[0],
            orientation='h',
            color=tech_sectors.columns[1],
            color_continuous_scale='Viridis',
            title="Technology Sectors"
        )
        fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=500, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(tech_sectors.head(20), use_container_width=True, hide_index=True)

# ════════════════════════════════════════════════════════════════════
#  TAB 4: BY DECADE
# ════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("Patents by Decade")
    
    if tech_by_decade is not None and len(tech_by_decade) > 0:
        fig = px.bar(
            tech_by_decade,
            x=tech_by_decade.columns[0],
            y=tech_by_decade.columns[1],
            color=tech_by_decade.columns[1],
            color_continuous_scale='Oranges',
            title="Decade Distribution"
        )
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(tech_by_decade, use_container_width=True, hide_index=True)

# ════════════════════════════════════════════════════════════════════
#  TAB 5: GROWTH ANALYSIS
# ════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("Technology Growth Analysis")
    
    if tech_growth is not None and len(tech_growth) > 0:
        st.info("Shows fastest growing technology fields (recent vs historical)")
        st.dataframe(tech_growth.head(25), use_container_width=True, hide_index=True)

# ════════════════════════════════════════════════════════════════════
#  TAB 6: RANKINGS
# ════════════════════════════════════════════════════════════════════
with tab6:
    st.subheader("Company Rankings (RANK Window Function)")
    
    if company_ranking is not None and len(company_ranking) > 0:
        st.info("Companies ranked by patent count using SQL RANK() window function")
        st.dataframe(company_ranking.head(30), use_container_width=True, hide_index=True)

# ════════════════════════════════════════════════════════════════════
#  FOOTER
# ════════════════════════════════════════════════════════════════════
st.divider()
st.markdown("""
    <div style='text-align: center; color: #999; font-size: 12px; padding: 15px;'>
        <p>✅ Optimized Dashboard | Loads from Pre-Generated Reports</p>
        <p>🔗 GitHub: <a href='https://github.com/broniaB2/Big-data-analysis-pipeline' target='_blank'>Big-data-analysis-pipeline</a></p>
    </div>
""", unsafe_allow_html=True)
