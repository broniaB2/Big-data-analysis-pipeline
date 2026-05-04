-- =====================================================
--  PatentsView Technology Trends — Database Schema
-- =====================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS technologies;
DROP TABLE IF EXISTS patent_companies;
DROP TABLE IF EXISTS companies;
DROP TABLE IF EXISTS patents;

-- ── Patents ───────────────────────────────────────
CREATE TABLE IF NOT EXISTS patents (
    patent_id    TEXT PRIMARY KEY,
    title        TEXT,
    abstract     TEXT,
    filing_date  TEXT,
    year         INTEGER,
    patent_type  TEXT,
    num_claims   INTEGER DEFAULT 0,
    withdrawn    INTEGER DEFAULT 0
);

-- ── Companies (assignees) ─────────────────────────
CREATE TABLE IF NOT EXISTS companies (
    company_id TEXT PRIMARY KEY,
    name       TEXT
);

-- ── Patent to company relationships ───────────────
CREATE TABLE IF NOT EXISTS patent_companies (
    patent_id TEXT,
    company_id TEXT,
    FOREIGN KEY (patent_id) REFERENCES patents(patent_id),
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

-- ── Technologies (WIPO classification) ───────────
CREATE TABLE IF NOT EXISTS technologies (
    patent_id         TEXT PRIMARY KEY,
    wipo_field_id     TEXT,
    wipo_sector_title TEXT,
    wipo_field_title  TEXT,
    FOREIGN KEY (patent_id) REFERENCES patents(patent_id)
);

-- ── Indexes for query performance ─────────────────
CREATE INDEX IF NOT EXISTS idx_patents_year               ON patents(year);
CREATE INDEX IF NOT EXISTS idx_patent_companies_patent    ON patent_companies(patent_id);
CREATE INDEX IF NOT EXISTS idx_patent_companies_company   ON patent_companies(company_id);
CREATE INDEX IF NOT EXISTS idx_companies_name             ON companies(name);
CREATE INDEX IF NOT EXISTS idx_tech_sector         ON technologies(wipo_sector_title);
CREATE INDEX IF NOT EXISTS idx_tech_field          ON technologies(wipo_field_title);