"""
PatentsView Technology Trends Dashboard
Interactive dashboard for patent data analysis using Streamlit
"""

import streamlit as st
import pandas as pd
import json
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Patent Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Paths
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "patents.db"
REPORTS_DIR = BASE_DIR / "Reports"
REPORT_JSON = REPORTS_DIR / "patent_report.json"

@st.cache_data
def load_data():
    """Load data from database and JSON report."""
    if not DB_PATH.exists():
        st.error("Database not found. Please run data_pipeline.py first.")
        return None, None
    
    con = sqlite3.connect(str(DB_PATH))
    
    # Load from database
    patents_df = pd.read_sql("SELECT * FROM patents LIMIT 1000", con)
    companies_df = pd.read_sql("SELECT * FROM companies", con)
    technologies_df = pd.read_sql("SELECT * FROM technologies", con)
    yearly_df = pd.read_sql("SELECT year, COUNT(*) AS patent_count FROM patents WHERE year IS NOT NULL GROUP BY year ORDER BY year", con)
    top_companies_df = pd.read_sql(
        "SELECT c.name, COUNT(pc.patent_id) AS patent_count FROM companies c JOIN patent_companies pc ON c.company_id = pc.company_id GROUP BY c.company_id ORDER BY patent_count DESC LIMIT 20",
        con
    )
    
    con.close()
    
    # Load JSON report
    report_data = {}
    if REPORT_JSON.exists():
        with open(REPORT_JSON, 'r') as f:
            report_data = json.load(f)
    
    return {
        'patents': patents_df,
        'companies': companies_df,
        'technologies': technologies_df,
        'yearly': yearly_df,
        'top_companies': top_companies_df,
        'report': report_data
    }, report_data

# Main dashboard
st.markdown("<div class='main-header'>📊 Patent Analytics Dashboard</div>", unsafe_allow_html=True)
st.markdown("Interactive analysis of PatentsView technology trends data")
st.markdown("---")

# Load data
data, report = load_data()

if data is None:
    st.stop()

# Key metrics in columns
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_patents = report.get("total_patents", 0)
    st.metric("Total Patents", f"{total_patents:,}")

with col2:
    total_companies = len(data['companies'])
    st.metric("Companies/Assignees", f"{total_companies:,}")

with col3:
    total_technologies = len(data['technologies'])
    st.metric("Technology Records", f"{total_technologies:,}")

with col4:
    avg_year = int(data['patents']['year'].mean()) if 'year' in data['patents'].columns else "N/A"
    st.metric("Avg Patent Year", avg_year)

st.markdown("---")

# Tabs for different views
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Trends", "🏢 Top Companies", "🔬 Technologies", "📊 Data", "📋 Summary"])

# TAB 1: Trends
with tab1:
    st.subheader("Patents Over Time")
    
    if not data['yearly'].empty:
        fig = px.line(
            data['yearly'],
            x='year',
            y='patent_count',
            title="Patent Count by Year",
            markers=True,
            line_shape="spline"
        )
        fig.update_layout(
            xaxis_title="Year",
            yaxis_title="Number of Patents",
            hovermode="x unified",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Growth statistics
        col1, col2 = st.columns(2)
        with col1:
            earliest_year = int(data['yearly']['year'].min())
            latest_year = int(data['yearly']['year'].max())
            st.info(f"**Time Range:** {earliest_year} - {latest_year}")
        
        with col2:
            recent_avg = data['yearly'].tail(5)['patent_count'].mean()
            st.success(f"**Recent Avg (last 5 years):** {recent_avg:.0f} patents/year")

# TAB 2: Top Companies
with tab2:
    st.subheader("Top 20 Companies by Patent Count")
    
    if not data['top_companies'].empty:
        fig = px.bar(
            data['top_companies'],
            x='patent_count',
            y='name',
            orientation='h',
            title="Top Companies by Patents",
            color='patent_count',
            color_continuous_scale='Blues'
        )
        fig.update_layout(
            xaxis_title="Number of Patents",
            yaxis_title="Company Name",
            height=600,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.dataframe(data['top_companies'], use_container_width=True, hide_index=True)

# TAB 3: Technologies
with tab3:
    st.subheader("Technology Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        tech_summary = data['technologies'].groupby('wipo_sector_title').size().reset_index(name='count')
        tech_summary = tech_summary.sort_values('count', ascending=False).head(15)
        
        if not tech_summary.empty:
            fig = px.pie(
                tech_summary,
                values='count',
                names='wipo_sector_title',
                title="Distribution of Technology Sectors"
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.metric("Unique Tech Sectors", tech_summary.shape[0])
        st.metric("Total Tech Records", len(data['technologies']))

# TAB 4: Data Explorer
with tab4:
    st.subheader("Data Explorer")
    
    view_option = st.radio("Select data to view:", ["Patents", "Companies", "Technologies"], horizontal=True)
    
    if view_option == "Patents":
        st.write(f"**Showing first 100 of {len(data['patents'])} patents**")
        st.dataframe(data['patents'].head(100), use_container_width=True, height=400)
    
    elif view_option == "Companies":
        st.write(f"**All {len(data['companies'])} companies/assignees**")
        st.dataframe(data['companies'], use_container_width=True, height=400)
    
    else:
        st.write(f"**Showing first 100 of {len(data['technologies'])} technology records**")
        st.dataframe(data['technologies'].head(100), use_container_width=True, height=400)

# TAB 5: Summary Report
with tab5:
    st.subheader("Analysis Summary")
    
    summary_cols = st.columns(2)
    
    with summary_cols[0]:
        st.markdown("### Dataset Overview")
        st.write(f"- **Total Patents:** {report.get('total_patents', 0):,}")
        st.write(f"- **Total Companies:** {total_companies:,}")
        st.write(f"- **Technology Records:** {total_technologies:,}")
        st.write(f"- **Report Generated:** {report.get('generated_at', 'N/A')}")
    
    with summary_cols[1]:
        st.markdown("### Data Quality")
        null_patents = data['patents'].isnull().sum().sum()
        null_companies = data['companies'].isnull().sum().sum()
        st.write(f"- **Patent Records:** {len(data['patents']):,}")
        st.write(f"- **Company Records:** {len(data['companies']):,}")
        st.write(f"- **NULL values (Patents):** {null_patents}")
        st.write(f"- **NULL values (Companies):** {null_companies}")
    
    st.markdown("---")
    st.markdown("### Top Companies")
    if report.get("top_companies"):
        top_10 = pd.DataFrame(report["top_companies"][:10])
        st.dataframe(top_10, use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #999; font-size: 0.8rem;'>
    PatentsView Technology Trends Dashboard | Data Pipeline Mini Project
</div>
""", unsafe_allow_html=True)
