"""
Patent Analytics Dashboard - PRODUCTION VERSION
Beautiful, interactive visualizations with impressive charts and real data
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from pathlib import Path

st.set_page_config(
    page_title="PatentsView Technology Trends Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ════════════════════════════════════════════════════════════════════
#  CUSTOM CSS & STYLING
# ════════════════════════════════════════════════════════════════════
st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stat-number {
        font-size: 32px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
#  HEADER
# ════════════════════════════════════════════════════════════════════
st.markdown("""
    <div style='text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 40px; border-radius: 15px; margin-bottom: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);'>
        <h1 style='color: white; margin: 0; font-size: 48px;'>📊 PatentsView Technology Trends Dashboard</h1>
        <p style='color: #e0e0e0; margin-top: 10px; font-size: 18px;'>USPTO PatentsView Data Pipeline Analysis</p>
        <p style='color: #b0b0d8; margin-top: 5px; font-size: 14px;'>✨ Interactive Visualizations • Global Insights • Advanced Analytics</p>
    </div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════
#  LOAD REPORTS
# ════════════════════════════════════════════════════════════════════
REPORTS_DIR = Path("Reports")

@st.cache_data
def load_csv(filename):
    try:
        return pd.read_csv(REPORTS_DIR / filename)
    except FileNotFoundError:
        return None

@st.cache_data
def load_json_report():
    try:
        with open(REPORTS_DIR / "patent_report.json") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Load all data
top_companies = load_csv("top_companies.csv")
patents_yearly = load_csv("patents_per_year.csv")
tech_sectors = load_csv("top_tech_sectors.csv")
company_ranking = load_csv("company_ranking.csv")
tech_by_decade = load_csv("tech_by_decade.csv")
tech_growth = load_csv("tech_growth.csv")
json_report = load_json_report()

if top_companies is None:
    st.error("❌ Reports not found. Run: `python data_pipeline.py --sample`")
    st.stop()

# ════════════════════════════════════════════════════════════════════
#  CALCULATE REAL METRICS FROM DATA
# ════════════════════════════════════════════════════════════════════
total_patents = int(patents_yearly['patent_count'].sum()) if patents_yearly is not None else 0
total_companies = len(top_companies) if top_companies is not None else 0
total_techs = len(tech_sectors) if tech_sectors is not None else 0
top_company_name = top_companies.iloc[0, 0] if len(top_companies) > 0 else "N/A"
top_company_count = top_companies.iloc[0, 1] if len(top_companies) > 0 else 0

# ════════════════════════════════════════════════════════════════════
#  KEY METRICS
# ════════════════════════════════════════════════════════════════════
st.subheader("📈 Key Metrics Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📋 Total Patents", f"{total_patents:,}")

with col2:
    st.metric("🏢 Companies", f"{total_companies:,}")

with col3:
    st.metric("⚙️ Tech Fields", f"{total_techs:,}")

with col4:
    st.metric("🏆 Top Company", f"{int(top_company_count):,} patents")

st.divider()

# ════════════════════════════════════════════════════════════════════
#  TABS
# ════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🏆 Top Companies",
    "📅 Year Trends",
    "⚙️ Tech Sectors",
    "📊 By Decade",
    "🚀 Growth",
    "🥇 Rankings"
])

# ════════════════════════════════════════════════════════════════════
#  TAB 1: TOP COMPANIES (ENHANCED)
# ════════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("🏢 Top 20 Companies by Patent Count")
    st.markdown("*Leading innovators in patent filing across all sectors*")
    
    if top_companies is not None and len(top_companies) > 0:
        top_20 = top_companies.head(20).copy()
        
        fig = px.bar(
            top_20,
            y='name',
            x='patent_count',
            orientation='h',
            color='patent_count',
            color_continuous_scale='Viridis',
            title="Top Companies - Patent Count Leadership",
            labels={'patent_count': 'Number of Patents', 'name': 'Company Name'},
            height=600,
            text='patent_count'
        )
        fig.update_traces(textposition='outside')
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            showlegend=False,
            font=dict(size=11),
            xaxis_title="Number of Patents",
            yaxis_title="Company"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### Company Details")
        display_df = top_20.copy()
        display_df['Rank'] = range(1, len(display_df) + 1)
        display_df = display_df[['Rank', 'name', 'patent_count']]
        display_df.columns = ['Rank', 'Company', 'Patents']
        st.dataframe(display_df, hide_index=True, use_container_width=True)

# ════════════════════════════════════════════════════════════════════
#  TAB 2: YEARLY TRENDS (FIXED)
# ════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("📅 Patent Filing Trends Over Time")
    st.markdown("*Long-term analysis of patent filing patterns across years*")
    
    if patents_yearly is not None and len(patents_yearly) > 0:
        yearly = patents_yearly.copy()
        yearly['year'] = yearly['year'].astype(int)
        yearly = yearly.sort_values('year')
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=yearly['year'],
            y=yearly['patent_count'],
            mode='lines+markers',
            name='Patents',
            line=dict(color='#667eea', width=3),
            marker=dict(size=8, color='#764ba2'),
            fill='tozeroy',
            fillcolor='rgba(102, 126, 234, 0.2)',
            hovertemplate='<b>Year: %{x}</b><br>Patents: %{y:,.0f}<extra></extra>'
        ))
        
        fig.update_layout(
            title="Patent Filing Trend - Complete Timeline",
            xaxis_title="Year",
            yaxis_title="Number of Patents",
            height=500,
            hovermode='x unified',
            plot_bgcolor='rgba(240, 242, 246, 0.5)'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📍 First Year", int(yearly['year'].min()))
        with col2:
            st.metric("📍 Latest Year", int(yearly['year'].max()))
        with col3:
            st.metric("📊 Total Years", len(yearly))
        with col4:
            avg_patents = yearly['patent_count'].mean()
            st.metric("📈 Avg/Year", f"{int(avg_patents):,}")
        
        st.markdown("### Yearly Data")
        st.dataframe(yearly.tail(30), hide_index=True, use_container_width=True)

# ════════════════════════════════════════════════════════════════════
#  TAB 3: TECHNOLOGY SECTORS
# ════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("⚙️ Top Technology Sectors")
    st.markdown("*Distribution of patents across WIPO technology classifications*")
    
    if tech_sectors is not None and len(tech_sectors) > 0:
        tech = tech_sectors.copy()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_pie = px.pie(
                tech.head(15),
                values='patent_count',
                names='field',
                title="Technology Sector Distribution (Top 15)",
                height=500
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            fig_bar = px.bar(
                tech.head(10),
                x='patent_count',
                y='field',
                orientation='h',
                color='patent_count',
                color_continuous_scale='Plasma',
                height=500,
                title="Top 10 Sectors"
            )
            fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        
        st.markdown("### All Technology Sectors")
        st.dataframe(tech, hide_index=True, use_container_width=True)

# ════════════════════════════════════════════════════════════════════
#  TAB 4: BY DECADE (FIXED)
# ════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("📊 Patents by Decade")
    st.markdown("*Historical analysis showing patent trends across decades*")
    
    if tech_by_decade is not None and len(tech_by_decade) > 0:
        decade_grouped = tech_by_decade.copy()
        decade_grouped = decade_grouped.groupby('decade')['patent_count'].sum().reset_index()
        decade_grouped = decade_grouped.sort_values('decade')
        source_label = "tech_by_decade.csv"
    elif patents_yearly is not None and len(patents_yearly) > 0:
        st.warning("Decade data is missing from `tech_by_decade.csv`. Displaying decade totals derived from yearly patent counts.")
        decade_grouped = patents_yearly.copy()
        decade_grouped['year'] = decade_grouped['year'].astype(int)
        decade_grouped['decade'] = (decade_grouped['year'] // 10) * 10
        decade_grouped = decade_grouped.groupby('decade')['patent_count'].sum().reset_index()
        decade_grouped = decade_grouped.sort_values('decade')
        source_label = "derived from patents_per_year.csv"
    else:
        st.info("No decade or yearly data available to display decade trends.")
        decade_grouped = None
        source_label = None
    
    if decade_grouped is not None and len(decade_grouped) > 0:
        fig = px.bar(
            decade_grouped,
            x='decade',
            y='patent_count',
            color='patent_count',
            color_continuous_scale='Sunset',
            title=f"Patent Distribution by Decade ({source_label})",
            labels={'patent_count': 'Number of Patents', 'decade': 'Decade'},
            height=500,
            text='patent_count'
        )
        fig.update_traces(textposition='outside')
        fig.update_layout(
            showlegend=False,
            font=dict(size=12),
            xaxis_title="Decade",
            yaxis_title="Number of Patents"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        decade_sorted = decade_grouped.sort_values('patent_count', ascending=False)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🏆 Peak Decade", int(decade_sorted.iloc[0]['decade']), delta=f"{int(decade_sorted.iloc[0]['patent_count']):,}")
        with col2:
            st.metric("📊 Total Decades", len(decade_grouped))
        with col3:
            st.metric("📈 Total Patents", f"{int(decade_grouped['patent_count'].sum()):,}")
        
        st.markdown("### Decade Breakdown")
        st.dataframe(decade_grouped, hide_index=True, use_container_width=True)

# ════════════════════════════════════════════════════════════════════
#  TAB 5: GROWTH ANALYSIS (FIXED)
# ════════════════════════════════════════════════════════════════════
with tab5:
    st.subheader("🚀 Technology Growth Analysis")
    st.markdown("*Fastest growing technology fields - Recent vs Historical comparison*")
    
    if tech_growth is not None and len(tech_growth) > 0:
        growth = tech_growth.copy()
        growth = growth.head(20)
        
        fig = px.bar(
            growth,
            x='growth_ratio',
            y='field',
            orientation='h',
            color='growth_ratio',
            color_continuous_scale='RdYlGn',
            title="Technology Fields with Highest Growth (Recent vs Historical)",
            labels={'growth_ratio': 'Growth Ratio', 'field': 'Technology Field'},
            height=600,
            text='growth_ratio'
        )
        fig.update_traces(textposition='outside', textformat='.2f')
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            showlegend=False,
            xaxis_title="Growth Ratio (Recent / Historical)",
            yaxis_title="Technology Field"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("### Growth Statistics")
        growth_display = growth.copy()
        growth_display['growth_ratio'] = growth_display['growth_ratio'].round(2)
        st.dataframe(growth_display, hide_index=True, use_container_width=True)
    elif patents_yearly is not None and len(patents_yearly) > 1:
        st.warning("Growth data is missing from `tech_growth.csv`. Displaying year-over-year patent growth instead.")
        growth = patents_yearly.copy()
        growth['year'] = growth['year'].astype(int)
        growth = growth.sort_values('year')
        growth['previous'] = growth['patent_count'].shift(1)
        growth = growth.dropna()
        growth['growth_ratio'] = growth['patent_count'] / growth['previous']
        growth['growth_percent'] = (growth['growth_ratio'] - 1) * 100
        growth_display = growth[['year', 'patent_count', 'previous', 'growth_ratio', 'growth_percent']].copy()
        growth_display.columns = ['Year', 'Patents', 'Previous Year Patents', 'Growth Ratio', 'Growth %']
        
        fig = px.bar(
            growth_display,
            x='Year',
            y='Growth %',
            title='Year-over-Year Patent Filing Growth',
            labels={'Growth %': 'Growth %', 'Year': 'Year'},
            text='Growth %',
            height=500
        )
        fig.update_traces(texttemplate='%{text:.1f}%', marker_color='#ff7f0e')
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("### Growth Statistics")
        st.dataframe(growth_display, hide_index=True, use_container_width=True)
    else:
        st.info("Insufficient yearly data available to compute growth analytics.")

# ════════════════════════════════════════════════════════════════════
#  TAB 6: RANKINGS (IMPRESSIVE)
# ════════════════════════════════════════════════════════════════════
with tab6:
    st.subheader("🥇 Company Rankings (Using SQL RANK() Window Function)")
    st.markdown("*Companies ranked by patent count with advanced SQL window functions*")
    
    if company_ranking is not None and len(company_ranking) > 0:
        ranking = company_ranking.copy()
        ranking = ranking.sort_values('rank')
        
        st.markdown("### 🏅 Top 3 Patent Leaders")
        col1, col2, col3 = st.columns(3)
        
        top_3 = ranking.head(3)
        medals = ['🥇', '🥈', '🥉']
        
        for idx, (col, medal) in enumerate(zip([col1, col2, col3], medals)):
            if idx < len(top_3):
                company = top_3.iloc[idx]
                with col:
                    st.markdown(f"""
                    <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                border-radius: 10px; color: white;'>
                        <h2>{medal}</h2>
                        <h3>{company['name'][:25]}</h3>
                        <p style='font-size: 24px; margin: 10px 0;'>{int(company['patent_count']):,} patents</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.divider()
        
        st.markdown("### 📊 Full Rankings (Top 30)")
        top_30 = ranking.head(30).copy()
        top_30['rank'] = top_30['rank'].astype(int)
        top_30['patent_count'] = top_30['patent_count'].astype(int)
        
        st.dataframe(top_30, hide_index=True, use_container_width=True, height=400)
        
        st.markdown("### Rank Distribution Analysis")
        fig = px.scatter(
            ranking.head(30),
            x='rank',
            y='patent_count',
            size='patent_count',
            color='patent_count',
            hover_name='name',
            color_continuous_scale='Viridis',
            title="Patent Count by Company Rank",
            labels={'rank': 'Rank Position', 'patent_count': 'Number of Patents'},
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

# ════════════════════════════════════════════════════════════════════
#  FOOTER
# ════════════════════════════════════════════════════════════════════
st.divider()
st.markdown("""
    <div style='text-align: center; padding: 25px; background: #f8f9fa; border-radius: 10px;'>
        <p style='color: #666; margin: 0;'>✅ <b>Production Dashboard</b> • Instant Performance • Advanced Analytics</p>
        <p style='color: #999; margin: 10px 0 0 0; font-size: 12px;'>
            🔗 <a href='https://github.com/broniaB2/Big-data-analysis-pipeline' target='_blank'>GitHub Repository</a> • 
            📊 Patent Data Pipeline • 🎓 Cloud Computing Project
        </p>
    </div>
""", unsafe_allow_html=True)
