"""Versioned prepared schema; changing this SQL changes the release identity."""

import hashlib

SCHEMA_VERSION = 2
SCHEMA = """
PRAGMA foreign_keys = ON;
PRAGMA user_version = 2;
CREATE TABLE snapshot_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL) WITHOUT ROWID;
CREATE TABLE reports (
  rid INTEGER PRIMARY KEY, report_id TEXT NOT NULL UNIQUE,
  event_date TEXT NOT NULL, year INTEGER NOT NULL,
  age_years REAL CHECK(age_years IS NULL OR age_years BETWEEN 0 AND 125),
  gender TEXT NOT NULL CHECK(gender IN ('Female', 'Male', 'Unknown')),
  source_page TEXT NOT NULL, source_index INTEGER NOT NULL
);
CREATE TABLE report_products (
  rid INTEGER NOT NULL REFERENCES reports(rid), ordinal INTEGER NOT NULL,
  role TEXT NOT NULL, raw_name TEXT NOT NULL, search_text TEXT NOT NULL,
  canonical TEXT, PRIMARY KEY(rid, ordinal)
) WITHOUT ROWID;
CREATE TABLE report_suspect_products (
  rid INTEGER NOT NULL REFERENCES reports(rid), canonical TEXT NOT NULL,
  PRIMARY KEY(rid, canonical)
) WITHOUT ROWID;
CREATE TABLE report_reactions (
  rid INTEGER NOT NULL REFERENCES reports(rid), canonical TEXT NOT NULL,
  PRIMARY KEY(rid, canonical)
) WITHOUT ROWID;
CREATE TABLE report_outcomes (
  rid INTEGER NOT NULL REFERENCES reports(rid), canonical TEXT NOT NULL,
  PRIMARY KEY(rid, canonical)
) WITHOUT ROWID;
CREATE TABLE term_dictionary (
  field TEXT NOT NULL, canonical TEXT NOT NULL, display_label TEXT NOT NULL,
  disclosure TEXT, PRIMARY KEY(field, canonical)
) WITHOUT ROWID;
CREATE TABLE annual_stats (
  year INTEGER PRIMARY KEY, report_count INTEGER NOT NULL, valid_age_count INTEGER NOT NULL,
  age_sum REAL, female_age_count INTEGER NOT NULL, female_age_sum REAL,
  male_age_count INTEGER NOT NULL, male_age_sum REAL
);
CREATE TABLE annual_histogram (
  year INTEGER NOT NULL, bin INTEGER NOT NULL, count INTEGER NOT NULL,
  PRIMARY KEY(year, bin)
) WITHOUT ROWID;
CREATE TABLE annual_gender (
  year INTEGER NOT NULL, gender TEXT NOT NULL, count INTEGER NOT NULL,
  PRIMARY KEY(year, gender)
) WITHOUT ROWID;
CREATE TABLE annual_terms (
  field TEXT NOT NULL, year INTEGER NOT NULL, canonical TEXT NOT NULL, count INTEGER NOT NULL,
  PRIMARY KEY(field, year, canonical)
) WITHOUT ROWID;
"""
SCHEMA_HASH = hashlib.sha256(SCHEMA.encode()).hexdigest()
