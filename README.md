# 📊 PatentsView Technology Trends — Data Pipeline

A complete data engineering pipeline that ingests USPTO PatentsView data,
cleans it, stores it in SQLite, runs analytical SQL queries, and produces
CSV, JSON, and console reports.

---

## 📁 Project Structure

```
data_pipeline_project/
├── data/                         ← Put your downloaded .tsv.zip files here
│   ├── g_patent.tsv.zip
│   ├── g_wipo_technology.tsv.zip
│   └── g_assignee_disambiguated.tsv.zip
│
├── SQL/
│   ├── schema.sql                ← Database table definitions
│   └── queries.sql               ← All 7 analytical SQL queries
│
├── Reports/                      ← Auto-generated output files
│   ├── clean_patents.csv
│   ├── clean_technologies.csv
│   ├── clean_companies.csv
│   ├── top_companies.csv
│   ├── patents_per_year.csv
│   ├── top_tech_sectors.csv
│   ├── company_ranking.csv
│   ├── tech_growth.csv
│   ├── tech_by_decade.csv
│   └── patent_report.json
│
├── data_pipeline.py             ← Main pipeline (run this)
├── patents.db                    ← SQLite database (auto-created)
└── README.md
```

---

## ⚙️ Setup

### 1. Install Python dependencies

```bash
pip install pandas
```

### 2. Download the data files

Go to: https://patentsview.org/download/data-download-tables

Download these 3 files and place them in the `data/` folder:

| File | What it contains |
|---|---|
| `g_patent.tsv.zip` | Patent titles, dates, types |
| `g_wipo_technology.tsv.zip` | Technology sector classification |
| `g_assignee_disambiguated.tsv.zip` | Company (assignee) names |

### 3. Run the pipeline

```bash
python data_pipeline.py
```

---

## 🔄 Pipeline Steps

```
data/*.tsv.zip
      ↓
  STEP 1: Load raw TSV files into pandas DataFrames
      ↓
  STEP 2: Clean data (fix missing values, parse dates, normalize names)
      ↓
  STEP 3: Store in SQLite database (patents.db)
      ↓
  STEP 4: Run 7 analytical SQL queries
      ↓
  STEP 5: Export CSV + JSON reports
      ↓
  STEP 6: Print console report
```

---

## 🗃️ Database Tables

| Table | Description |
|---|---|
| `patents` | Core patent records (id, title, date, year, type) |
| `technologies` | WIPO tech classification per patent |
| `companies` | Unique assignee/company records |
| `patent_companies` | Relationship: which company owns which patent |

---

## 📊 SQL Queries Included

| Query | Description |
|---|---|
| Q1 | Total patents in the database |
| Q2 | Top 20 companies by patent count |
| Q3 | Patents per year (trend over time) |
| Q4 | Top technology fields |
| Q5 | JOIN — patents + tech + company |
| Q6 | CTE — top tech sector per decade |
| Q7 | RANKING — companies ranked with window function |
| BONUS | Tech field growth (recent vs older era) |

---

## 📂 Output Files

| File | Description |
|---|---|
| `clean_patents.csv` | Cleaned patent records |
| `clean_technologies.csv` | Cleaned WIPO tech data |
| `clean_companies.csv` | Cleaned company data |
| `top_companies.csv` | Top companies by patent count |
| `patents_per_year.csv` | Patent count per year |
| `top_tech_sectors.csv` | Most active technology fields |
| `company_ranking.csv` | Companies ranked by patents |
| `tech_growth.csv` | Fastest growing tech fields |
| `tech_by_decade.csv` | Dominant tech per decade |
| `patent_report.json` | Full JSON report |

---

---

## 📊 Interactive Dashboard

**Streamlit-powered visualization** — Run to explore data interactively:

```bash
streamlit run dashboard.py
```

Opens at `http://localhost:8501`

**Dashboard Features:**
- 📈 KPI metrics (total patents, companies, tech fields, links)
- 🏢 Top 20 companies bar chart
- 📅 Patent trends over time (line chart)
- ⚙️ Technology field distribution (pie chart)
- 🔬 Top technology sectors (bar chart)
- 📊 Patents by decade analysis
- 🔍 Raw data explorer (4 tabs: Patents, Companies, Technologies, Relationships)

---

## 🚀 Usage Examples

### Process Different Data Sizes

```bash
# Quick test (8,000 records)
python data_pipeline.py --sample --sample-size 8000

# Medium dataset (500,000 records) - default sample
python data_pipeline.py --sample

# Full dataset (1M+) - no limit
python data_pipeline.py
```

### Query Results Directly

```python
import sqlite3
import pandas as pd

con = sqlite3.connect('patents.db')
df = pd.read_sql("SELECT * FROM companies LIMIT 10", con)
con.close()
```

---

## ⏱️ Performance Metrics

| Sample Size | Time | DB Size | Notes |
|-----------|------|---------|-------|
| 8,000 | ~2 min | ~30 MB | Quick test |
| 100,000 | ~10 min | ~100 MB | Development |
| 500,000 | ~20-30 min | ~200-300 MB | **Current default** |
| 1M+ | ~30+ min | ~1-2 GB | Full dataset |

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| Database not found | Run: `python data_pipeline.py --sample` |
| Out of memory | Reduce sample: `python data_pipeline.py --sample --sample-size 100000` |
| Streamlit not available | Install: `pip install streamlit plotly` |
| Foreign key error | Pipeline auto-retries with row-by-row insertion |

---

## 📌 Notes

- **Inventors table**: PatentsView's inventor data requires
  `g_inventor_disambiguated.tsv.zip`. This file was excluded to save
  storage. The pipeline is designed so you can add it later by
  downloading that file and extending the pipeline.

- **Countries**: Country data comes from the location tables
  (`g_location_disambiguated.tsv.zip`), also excluded for storage.
  The company assignee type field gives partial country signal.

- The database uses **SQLite** — no server needed. Open `patents.db`
  with [DB Browser for SQLite](https://sqlitebrowser.org/) to explore
  it visually.

---

## 🚀 GitHub & Deployment

### GitHub Setup

```bash
# 1. Initialize Git Repository
git init
git config user.name "Your Name"
git config user.email "your.email@example.com"

# 2. Add all files
git add .

# 3. Create initial commit
git commit -m "feat: Data pipeline with 500k+ sample processing and Streamlit dashboard

- Increased sample size from 8,000 to 500,000 records per file
- Added interactive Streamlit dashboard with 7 visualizations
- Full dataset processing available (1M+ records without --sample flag)"

# 4. Add remote repository
git remote add origin https://github.com/yourusername/data-pipeline.git

# 5. Push to GitHub
git branch -M main
git push -u origin main
```

### Deployment Options

**Option A: Local Streamlit**
```bash
streamlit run dashboard.py
# Visit: http://localhost:8501
```

**Option B: Streamlit Cloud (Free)**
1. Push code to GitHub
2. Visit https://streamlit.io/cloud
3. Click "New App" and select your GitHub repo
4. Choose `dashboard.py` as main file
5. Deploy with one click

**Option C: Alternative Cloud Platforms**
- Railway.app
- Replit
- Vercel (with Flask wrapper)

---

## 🎯 Next Steps

1. **Deploy to Production**:
   - Choose a deployment option above
   - Monitor performance and user feedback
   - Scale database to PostgreSQL if needed

2. **Advanced Features**:
   - Add interactive filters to dashboard
   - Export to PostgreSQL for production
   - Add company search functionality
   - Implement real-time data updates

3. **Scale to Production**:
   - Use PostgreSQL instead of SQLite
   - Implement parallel data loading
   - Add caching layer with Redis
   - Set up CI/CD pipeline

---

## 📜 Data Source

U.S. Patent and Trademark Office — PatentsView
https://patentsview.org/download/data-download-tables
License: Creative Commons Attribution 4.0

**Last Updated:** May 2026 | **Status:** Production Ready