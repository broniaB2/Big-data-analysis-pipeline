'''''
=====================================================
 PatentsView Technology Trends - Data Pipeline
=====================================================
'''

import argparse
import os
import sys
import json
import zipfile
import sqlite3
import pandas as pd # type: ignore
from datetime import datetime
from pathlib import Path

# ── Paths ────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
DATA_DIR   = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "Reports"
DB_PATH = BASE_DIR / "patents.db"
SQL_DIR = BASE_DIR / "SQL"

REPORTS_DIR.mkdir(exist_ok=True)

# ── Helpers ──────────────────────────────────────
def banner(text):
    line = "=" * 55
    print(f"\n{line}\n  {text}\n{line}")

def info(msg):  print(f"  [INFO] {msg}")
def warn(msg):  print(f"  [WARN] {msg}")
def step(msg):  print(f"\n-> {msg}")

def read_tsv_zip(zip_path, usecols=None, nrows=None):
    """Read a .tsv.zip file into a DataFrame."""
    zip_path = Path(zip_path)
    if not zip_path.exists():
        raise FileNotFoundError(f"File not found: {zip_path}")
    with zipfile.ZipFile(zip_path) as z:
        tsv_name = [n for n in z.namelist() if n.endswith(".tsv")][0]
        with z.open(tsv_name) as f:
            df = pd.read_csv(
                f, sep="\t", low_memory=False,
                usecols=usecols, nrows=nrows,
                on_bad_lines="skip"
            )
    return df


# ══════════════════════════════════════════════════
#  STEP 1 – LOAD RAW DATA
# ══════════════════════════════════════════════════
def load_raw_data(sample_size=None):
    banner("STEP 1 — Loading Raw Data")

    # ── Patents ──────────────────────────────────
    step("Loading g_patent.tsv.zip...")
    patents_raw = read_tsv_zip(
        DATA_DIR / "g_patent.tsv.zip",
        usecols=["patent_id", "patent_title", "patent_date",
                 "patent_type", "num_claims", "withdrawn"],
        nrows=sample_size
    )
    info(f"Patents loaded: {len(patents_raw):,} rows")

    # ── WIPO Technology ───────────────────────────
    step("Loading g_wipo_technology.tsv.zip...")
    wipo_raw = read_tsv_zip(
        DATA_DIR / "g_wipo_technology.tsv.zip",
        usecols=["patent_id", "wipo_field_id",
                 "wipo_sector_title", "wipo_field_title"],
        nrows=sample_size
    )
    info(f"WIPO records loaded: {len(wipo_raw):,} rows")

    # ── Assignees (companies) ─────────────────────
    step("Loading g_assignee_disambiguated.tsv.zip...")
    assignee_raw = read_tsv_zip(
        DATA_DIR / "g_assignee_disambiguated.tsv.zip",
        usecols=["patent_id", "assignee_id",
                 "disambig_assignee_organization",
                 "disambig_assignee_individual_name_first",
                 "disambig_assignee_individual_name_last",
                 "assignee_type", "location_id"],
        nrows=sample_size
    )
    info(f"Assignee records loaded: {len(assignee_raw):,} rows")

    return patents_raw, wipo_raw, assignee_raw


# ══════════════════════════════════════════════════
#  STEP 2 – CLEAN DATA
# ══════════════════════════════════════════════════
def clean_patents(df):
    step("Cleaning patents...")
    df = df.copy()

    # Rename columns
    df.rename(columns={
        "patent_id":    "patent_id",
        "patent_title": "title",
        "patent_date":  "grant_date",
        "patent_type":  "patent_type",
        "num_claims":   "num_claims",
        "withdrawn":    "withdrawn"
    }, inplace=True)

    # Drop rows with no patent_id or title
    before = len(df)
    df.dropna(subset=["patent_id", "title"], inplace=True)
    info(f"Dropped {before - len(df):,} rows missing patent_id/title")

    # Parse dates and extract year
    df["grant_date"] = pd.to_datetime(df["grant_date"], errors="coerce")
    df["year"] = df["grant_date"].dt.year

    # Keep only reasonable years
    df = df[df["year"].between(1976, datetime.now().year)]

    # Clean title text
    df["title"] = df["title"].str.strip().str.title()

    # Fill missing
    df["num_claims"]  = pd.to_numeric(df["num_claims"], errors="coerce").fillna(0).astype(int)
    df["withdrawn"]   = df["withdrawn"].fillna(0).astype(int)
    df["patent_type"] = df["patent_type"].fillna("unknown")

    df["abstract"] = ""
    df["filing_date"] = ""
    df["grant_date"] = df["grant_date"].dt.strftime("%Y-%m-%d")

    info(f"Clean patents: {len(df):,} rows")
    return df[["patent_id", "title", "abstract", "filing_date", "year",
               "patent_type", "num_claims", "withdrawn"]]


def clean_wipo(df):
    step("Cleaning WIPO technology...")
    df = df.copy()
    df.dropna(subset=["patent_id", "wipo_field_title"], inplace=True)
    df["wipo_sector_title"] = df["wipo_sector_title"].str.strip()
    df["wipo_field_title"]  = df["wipo_field_title"].str.strip()
    # Keep one tech field per patent (first occurrence)
    df = df.drop_duplicates(subset=["patent_id"], keep="first")
    info(f"Clean WIPO: {len(df):,} rows")
    return df[["patent_id", "wipo_field_id",
               "wipo_sector_title", "wipo_field_title"]]


def clean_companies(df):
    step("Cleaning companies...")
    df = df.copy()
    df.dropna(subset=["patent_id", "assignee_id"], inplace=True)

    # Build a unified 'name' column: prefer org name over individual
    df["name"] = df["disambig_assignee_organization"].fillna("")
    mask = df["name"] == ""
    first = df.loc[mask, "disambig_assignee_individual_name_first"].fillna("")
    last  = df.loc[mask, "disambig_assignee_individual_name_last"].fillna("")
    df.loc[mask, "name"] = (first + " " + last).str.strip()

    df = df[df["name"] != ""].copy()

    companies = (df[["assignee_id", "name"]]
                 .drop_duplicates(subset=["assignee_id"]))
    companies.rename(columns={"assignee_id": "company_id"}, inplace=True)

    # Create patent_companies ONLY with companies that exist in the companies table
    valid_company_ids = set(companies['company_id'].values)
    patent_companies = (df[["patent_id", "assignee_id"]]
                        .dropna(subset=["patent_id", "assignee_id"])
                        [df["assignee_id"].isin(valid_company_ids)]  # Only valid companies
                        .drop_duplicates()
                        .rename(columns={"assignee_id": "company_id"}))

    info(f"Clean companies: {len(companies):,} unique companies")
    info(f"Clean patent-company relationships: {len(patent_companies):,}")
    return companies, patent_companies


def clean_inventors(df, location_df=None):
    step("Cleaning inventors...")
    if df is None or df.empty:
        warn("No inventor data available. Inventor-based queries will be empty.")
        empty = pd.DataFrame(columns=["inventor_id", "name", "country"])
        links = pd.DataFrame(columns=["patent_id", "inventor_id"])
        return empty, links

    df = df.copy()
    if "inventor_id" not in df.columns:
        raise ValueError("Inventor file must include inventor_id")

    if "inventor_name" in df.columns:
        df["name"] = df["inventor_name"].fillna("")
    else:
        first = df.get("inventor_first_name", pd.Series("", index=df.index)).fillna("")
        last  = df.get("inventor_last_name", pd.Series("", index=df.index)).fillna("")
        df["name"] = (first + " " + last).str.strip()

    df["name"] = df["name"].replace("", df["inventor_id"].astype(str)).str.title()
    df["country"] = ""

    if location_df is not None and not location_df.empty and "location_id" in df.columns:
        country_col = next((c for c in ["location_country", "country", "country_code", "country_name"]
                            if c in location_df.columns), None)
        if country_col is not None:
            location = location_df[["location_id", country_col]].drop_duplicates(subset=["location_id"])
            df = df.merge(location, on="location_id", how="left")
            df["country"] = df[country_col].fillna("")
        else:
            warn("Location file loaded, but no country column found.")

    df["country"] = df["country"].fillna("").astype(str).str.title()

    inventors = df[["inventor_id", "name", "country"]].drop_duplicates(subset=["inventor_id"])
    links = df[["patent_id", "inventor_id"]].dropna(subset=["patent_id", "inventor_id"]).drop_duplicates()

    info(f"Clean inventors: {len(inventors):,} unique inventors")
    return inventors, links


# ══════════════════════════════════════════════════
#  STEP 3 – STORE IN SQLite
# ══════════════════════════════════════════════════
def store_in_db(patents, wipo, companies, patent_companies):
    banner("STEP 3 — Storing in SQLite Database")

    schema_sql = (SQL_DIR / "schema.sql").read_text()
    # Remove foreign key pragma from schema since we manage it manually
    schema_sql = schema_sql.replace("PRAGMA foreign_keys = ON;", "-- PRAGMA foreign_keys disabled during insert\n")

    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = OFF")
    cur = con.cursor()
    cur.executescript(schema_sql)
    con.execute("PRAGMA foreign_keys = OFF")  # Ensure it's still off after script
    con.commit()

    step("Writing patents table...")
    patents.to_sql("patents", con, if_exists="append",
                   index=False, chunksize=50_000)
    info(f"Inserted {len(patents):,} patent rows")

    step("Writing companies table...")
    companies.to_sql("companies", con, if_exists="append",
                     index=False, chunksize=50_000)
    info(f"Inserted {len(companies):,} company rows")

    # Debug patent_companies
    step("Verifying patent_companies data...")
    nulls = patent_companies.isnull().sum()
    info(f"NULL values - patent_id: {nulls['patent_id']}, company_id: {nulls['company_id']}")
    unique_patents = patent_companies['patent_id'].nunique()
    unique_companies = patent_companies['company_id'].nunique()
    info(f"Unique patents: {unique_patents}, Unique companies: {unique_companies}")

    step("Writing patent_companies table...")
    try:
        patent_companies.to_sql("patent_companies", con, if_exists="append",
                                 index=False, chunksize=1000)
    except Exception as e:
        # Fallback: insert row by row
        info(f"Fallback insertion due to: {str(e)[:100]}")
        cur = con.cursor()
        for idx, row in patent_companies.iterrows():
            cur.execute(
                "INSERT INTO patent_companies (patent_id, company_id) VALUES (?, ?)",
                (row['patent_id'], row['company_id'])
            )
        con.commit()
    info(f"Inserted {len(patent_companies):,} patent-company rows")

    step("Writing technologies table...")
    wipo.to_sql("technologies", con, if_exists="append",
                index=False, chunksize=50_000)
    info(f"Inserted {len(wipo):,} technology rows")

    con.execute("PRAGMA foreign_keys = ON")
    con.close()
    info(f"Database saved -> {DB_PATH}")


# ══════════════════════════════════════════════════
#  STEP 4 – SQL ANALYSIS QUERIES
# ══════════════════════════════════════════════════
def run_queries():
    banner("STEP 4 — Running SQL Queries")
    con = sqlite3.connect(DB_PATH)
    results = {}

    step("Q1 – Total patents")
    total = pd.read_sql("SELECT COUNT(*) AS total FROM patents", con)
    results["total_patents"] = int(total.iloc[0]["total"])
    info(f"Total patents: {results['total_patents']:,}")

    step("Q2 – Top companies")
    results["top_companies"] = pd.read_sql("""
        SELECT c.name, COUNT(pc.patent_id) AS patent_count
        FROM companies c
        JOIN patent_companies pc ON c.company_id = pc.company_id
        GROUP BY c.company_id
        ORDER BY patent_count DESC
        LIMIT 20
    """, con)

    step("Q3 – Patents per year")
    results["yearly_trends"] = pd.read_sql("""
        SELECT year, COUNT(*) AS patent_count
        FROM patents
        WHERE year IS NOT NULL
        GROUP BY year
        ORDER BY year
    """, con)

    step("Q4 – Top technology fields")
    results["top_sectors"] = pd.read_sql("""
        SELECT
            wipo_sector_title AS sector,
            wipo_field_title AS field,
            COUNT(*) AS patent_count
        FROM technologies
        GROUP BY wipo_sector_title, wipo_field_title
        ORDER BY patent_count DESC
        LIMIT 20
    """, con)

    step("Q5 – JOIN: patents + companies + technologies")
    results["joined_sample"] = pd.read_sql("""
        SELECT p.patent_id,
               p.title,
               p.year,
               c.name AS company,
               t.wipo_sector_title AS sector,
               t.wipo_field_title AS tech_field
        FROM patents p
        LEFT JOIN patent_companies pc ON p.patent_id = pc.patent_id
        LEFT JOIN companies c ON pc.company_id = c.company_id
        LEFT JOIN technologies t ON p.patent_id = t.patent_id
        ORDER BY p.year DESC
        LIMIT 100
    """, con)

    step("Q6 – Top tech sector per decade")
    results["tech_by_decade"] = pd.read_sql("""
        WITH decade_tech AS (
            SELECT
                (p.year / 10) * 10 AS decade,
                t.wipo_sector_title AS sector,
                COUNT(*) AS patent_count
            FROM patents p
            JOIN technologies t ON p.patent_id = t.patent_id
            WHERE p.year IS NOT NULL
            GROUP BY decade, sector
        ),
        ranked AS (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY decade
                       ORDER BY patent_count DESC
                   ) AS rank_in_decade
            FROM decade_tech
        )
        SELECT decade, sector, patent_count, rank_in_decade
        FROM ranked
        WHERE rank_in_decade <= 3
        ORDER BY decade, rank_in_decade
    """, con)

    step("Q7 – Company ranking")
    results["company_ranking"] = pd.read_sql("""
        SELECT
            c.name,
            COUNT(pc.patent_id) AS patent_count,
            RANK() OVER (ORDER BY COUNT(pc.patent_id) DESC) AS rank
        FROM companies c
        JOIN patent_companies pc ON c.company_id = pc.company_id
        GROUP BY c.company_id
        ORDER BY rank
        LIMIT 25
    """, con)

    step("Bonus – Tech growth")
    results["tech_growth"] = pd.read_sql("""
        WITH tech_counts AS (
            SELECT
                t.wipo_field_title AS field,
                SUM(CASE WHEN p.year >= strftime('%Y', 'now') - 4 THEN 1 ELSE 0 END) AS recent_count,
                SUM(CASE WHEN p.year < strftime('%Y', 'now') - 4 THEN 1 ELSE 0 END) AS earlier_count
            FROM patents p
            JOIN technologies t ON p.patent_id = t.patent_id
            WHERE p.year IS NOT NULL
            GROUP BY t.wipo_field_title
        )
        SELECT
            field,
            recent_count,
            earlier_count,
            CASE
                WHEN earlier_count = 0 THEN NULL
                ELSE ROUND(1.0 * recent_count / earlier_count, 2)
            END AS growth_ratio
        FROM tech_counts
        WHERE recent_count > 0
        ORDER BY growth_ratio DESC, recent_count DESC
        LIMIT 20
    """, con)

    con.close()
    return results


# ══════════════════════════════════════════════════
#  STEP 5 – EXPORT REPORTS
# ══════════════════════════════════════════════════
def export_reports(results, patents, wipo, companies):
    banner("STEP 5 — Exporting Reports")

    step("Exporting CSVs...")

    patents.to_csv(REPORTS_DIR / "clean_patents.csv", index=False)
    info("clean_patents.csv")

    wipo.to_csv(REPORTS_DIR / "clean_technologies.csv", index=False)
    info("clean_technologies.csv")

    companies.to_csv(REPORTS_DIR / "clean_companies.csv", index=False)
    info("clean_companies.csv")

    results["top_companies"].to_csv(
        REPORTS_DIR / "top_companies.csv", index=False)
    info("top_companies.csv")

    results["yearly_trends"].to_csv(
        REPORTS_DIR / "patents_per_year.csv", index=False)
    info("patents_per_year.csv")

    results["top_sectors"].to_csv(
        REPORTS_DIR / "top_tech_sectors.csv", index=False)
    info("top_tech_sectors.csv")

    results["company_ranking"].to_csv(
        REPORTS_DIR / "company_ranking.csv", index=False)
    info("company_ranking.csv")

    results["tech_by_decade"].to_csv(
        REPORTS_DIR / "tech_by_decade.csv", index=False)
    info("tech_by_decade.csv")

    results["tech_growth"].to_csv(
        REPORTS_DIR / "tech_growth.csv", index=False)
    info("tech_growth.csv")

    step("Exporting JSON report...")
    report = {
        "generated_at": datetime.now().isoformat(),
        "total_patents": results["total_patents"],
        "top_companies": results["top_companies"].head(10).to_dict(orient="records"),
        "patents_per_year": results["yearly_trends"].to_dict(orient="records"),
        "top_sectors": results["top_sectors"].head(10).to_dict(orient="records"),
        "top_growth_fields": results["tech_growth"].head(10).to_dict(orient="records"),
    }
    json_path = REPORTS_DIR / "patent_report.json"
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    info("patent_report.json")

    return report


# ══════════════════════════════════════════════════
#  STEP 6 – CONSOLE REPORT
# ══════════════════════════════════════════════════
def console_report(results, report):
    W = 55
    line = "=" * W

    print(f"\n\n{line}")
    print("          [REPORT]  PATENT PIPELINE REPORT")
    print(f"          {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(line)

    print(f"\n  Total Patents in Database: {results['total_patents']:>12,}")

    print(f"\n{'─'*W}")
    print("  [COMPANIES]  TOP 10 COMPANIES")
    print(f"{'─'*W}")
    for i, row in results["top_companies"].head(10).iterrows():
        print(f"  {i+1:>2}. {row['name']:<30} {row['patent_count']:>7,}")

    print(f"\n{'─'*W}")
    print("  [TECH]  TOP 10 TECHNOLOGY FIELDS")
    print(f"{'─'*W}")
    for i, row in results["top_sectors"].head(10).iterrows():
        sector = row['sector'] or ''
        field = row['field'] or ''
        print(f"  {i+1:>2}. {sector:<18} {field:<25} {row['patent_count']:>7,}")

    print(f"\n{'─'*W}")
    print("  [TRENDS]  PATENTS PER YEAR (last 10 years)")
    print(f"{'─'*W}")
    recent = results["yearly_trends"].tail(10)
    max_count = results["yearly_trends"]["patent_count"].max() if not results["yearly_trends"].empty else 1
    for _, row in recent.iterrows():
        bar_len = int(row["patent_count"] / max_count * 30)
        bar = "█" * bar_len
        print(f"  {int(row['year']):>4}  {bar:<30} {int(row['patent_count']):>7,}")

    print(f"\n{'─'*W}")
    print(f"  [FILES]  Reports saved to: {REPORTS_DIR.name}/")
    print(f"  [DB]  Database:         {DB_PATH.name}")
    print(f"{line}\n")


# ══════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════
def main():
    banner("PatentsView Technology Trends Pipeline")
    print("  Starting full pipeline run...")

    parser = argparse.ArgumentParser(
        description="Run the PatentsView data pipeline."
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Run the pipeline in sample mode with a limited number of rows for faster testing."
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=500000,
        help="Number of rows to read from each TSV file when running in sample mode (default: 500,000 records per file)."
    )
    args = parser.parse_args()

    if args.sample:
        warn(f"Sample mode enabled: reading up to {args.sample_size:,} rows per file.")

    try:
        patents_raw, wipo_raw, assignees_raw = load_raw_data(
            sample_size=args.sample_size if args.sample else None
        )
    except FileNotFoundError as e:
        print(f"\n  ❌  {e}")
        print("  Please place the required .tsv.zip files in the data/ folder.")
        sys.exit(1)

    banner("STEP 2 — Cleaning Data")
    patents = clean_patents(patents_raw)
    wipo = clean_wipo(wipo_raw)
    companies, patent_companies = clean_companies(assignees_raw)

    store_in_db(patents, wipo, companies, patent_companies)

    results = run_queries()

    report = export_reports(results, patents, wipo, companies)

    console_report(results, report)


if __name__ == "__main__":
    main()