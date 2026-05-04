# Deployment Guide

## Local Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Data Pipeline
Process 8,000 records per file (default):
```bash
python data_pipeline.py --sample
```

Or specify a custom sample size:
```bash
python data_pipeline.py --sample --sample-size 2000
```

To process the full dataset:
```bash
python data_pipeline.py
```

### 3. Launch Dashboard
```bash
streamlit run dashboard.py
```

The dashboard will open at `http://localhost:8501`

---

## GitHub Deployment

### 1. Create GitHub Repository
```bash
# Initialize local repository
git init

# Add all files
git add .

# Commit initial version
git commit -m "Initial commit: Patent data pipeline with 8K sample and Streamlit dashboard"
```

### 2. Connect to Remote Repository
```bash
# Add remote (replace USERNAME and REPO_NAME)
git remote add origin https://github.com/USERNAME/REPO_NAME.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### 3. Deploy Streamlit App

#### Option A: Streamlit Cloud (Free)
1. Sign up at https://streamlit.io/cloud
2. Click "New app" and select your GitHub repository
3. Select `dashboard.py` as the entry point
4. Streamlit will automatically deploy and provide a public URL

#### Option B: Heroku
1. Create `Procfile`:
```
web: streamlit run dashboard.py --logger.level=error
```

2. Deploy:
```bash
heroku login
heroku create your-app-name
git push heroku main
```

#### Option C: Railway, Render, or AWS
Follow platform-specific documentation for Python/Streamlit apps.

---

## File Structure

```
.
├── data_pipeline.py          # Main ETL pipeline
├── dashboard.py              # Streamlit dashboard
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
├── DEPLOYMENT.md             # This file
├── .gitignore                # Git ignore rules
├── .streamlit/
│   └── config.toml           # Streamlit configuration
├── SQL/
│   ├── schema.sql            # Database schema
│   └── queries.sql           # Analytical queries
├── data/                     # Input ZIP files
├── Reports/                  # Generated output files (CSV/JSON)
└── patents.db                # SQLite database (auto-generated)
```

---

## Troubleshooting

### Database not found error
Run the pipeline first: `python data_pipeline.py --sample`

### Encoding errors on Windows
Ensure you're using Python 3.7+ with UTF-8 encoding support.

### Streamlit "No module named" errors
Reinstall dependencies: `pip install -r requirements.txt --force-reinstall`

### Permission denied on GitHub
Generate SSH key: `ssh-keygen -t ed25519 -C "your-email@example.com"`
Add to GitHub account and use SSH URL for remote.

---

## Performance Notes

- **Sample size 8,000**: ~10-15 minutes processing time
- **Full dataset**: Varies by file size (1-2 hours typical)
- **Dashboard load**: ~2-3 seconds after database is ready

## Next Steps

1. Update SQL queries in `SQL/queries.sql` for custom analysis
2. Add more visualizations to `dashboard.py`
3. Configure database backups for production use
4. Set up CI/CD pipeline with GitHub Actions

