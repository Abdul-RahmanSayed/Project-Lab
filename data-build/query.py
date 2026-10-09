"""Read-only SQLite selection and overview aggregation; standard library only."""

import argparse
import json
from pathlib import Path
import sqlite3

from schema import SCHEMA_HASH, SCHEMA_VERSION


def read_metadata(connection):
    return {row["key"]: json.loads(row["value"])
            for row in connection.execute("SELECT key, value FROM snapshot_metadata")}


def open_database(database):
    connection = sqlite3.connect(Path(database).resolve().as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA query_only = ON")
        connection.execute("PRAGMA cache_size = -8192")
        connection.execute("PRAGMA temp_store = MEMORY")
        metadata = read_metadata(connection)
        if (metadata.get("schemaVersion") != SCHEMA_VERSION or metadata.get("schemaHash") != SCHEMA_HASH
                or connection.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION):
            raise ValueError("Unsupported prepared schema or schema hash.")
        return connection
    except BaseException:
        connection.close()
        raise


def selection(connection, filters):
    start, end, product = filters["startYear"], filters["endYear"], filters["productFilter"]
    metadata = read_metadata(connection)
    if type(start) is not int or type(end) is not int or not (
            int(metadata["coverageStart"][:4]) <= start <= end <= int(metadata["coverageEnd"][:4])):
        raise ValueError("Year range is outside the snapshot or reversed.")
    if product is not None and (not isinstance(product, str) or not product.strip()):
        raise ValueError("Product search must be nonblank text or None.")
    params = {"start": start, "end": end, "product": product.casefold() if product is not None else None}
    predicate = ""
    if product is not None:
        predicate = """AND EXISTS (SELECT 1 FROM report_products p WHERE p.rid = r.rid
                         AND p.role = 'SUSPECT' AND instr(p.search_text, :product) > 0)"""
    if product is not None and end - start >= 4:
        cte = """WITH matched_products AS MATERIALIZED (
            SELECT DISTINCT rid, canonical FROM report_products
            WHERE role = 'SUSPECT' AND instr(search_text, :product) > 0), selected AS MATERIALIZED (
            SELECT r.rid, r.year, r.age_years, r.gender FROM reports r
            WHERE r.year BETWEEN :start AND :end AND r.rid IN (SELECT rid FROM matched_products)) """
        return cte, params
    cte = f"""WITH selected AS MATERIALIZED (
        SELECT r.rid, r.year, r.age_years, r.gender FROM reports r
        WHERE r.year BETWEEN :start AND :end {predicate}) """
    return cte, params


def selected_ids(connection, filters):
    cte, params = selection(connection, filters)
    return [row[0] for row in connection.execute(cte + """SELECT r.report_id FROM selected s
        JOIN reports r ON r.rid = s.rid ORDER BY r.report_id""", params)]


def _memberships(filters):
    if filters["productFilter"] is None:
        return "SELECT p.rid, p.canonical FROM report_suspect_products p JOIN selected s ON s.rid = p.rid"
    if filters["endYear"] - filters["startYear"] >= 4:
        return "SELECT p.rid, p.canonical FROM matched_products p JOIN selected s ON s.rid = p.rid WHERE p.canonical IS NOT NULL"
    return """SELECT DISTINCT p.rid, p.canonical FROM report_products p JOIN selected s ON s.rid = p.rid
        WHERE p.role = 'SUSPECT' AND p.canonical IS NOT NULL AND instr(p.search_text, :product) > 0"""


def ranking_ctes(filters):
    return f""", product_memberships AS MATERIALIZED ({_memberships(filters)}),
        product_counts AS (SELECT canonical, COUNT(*) AS count FROM product_memberships GROUP BY canonical),
        outcome_counts AS (SELECT p.canonical, COUNT(*) AS count FROM report_outcomes p
                          JOIN selected s ON s.rid = p.rid GROUP BY p.canonical),
        reaction_counts AS (SELECT p.canonical, COUNT(*) AS count FROM report_reactions p
                           JOIN selected s ON s.rid = p.rid GROUP BY p.canonical) """


def _ranking_json(table):
    return f"""(SELECT json_group_array(json_array(canonical, count)) FROM (
        SELECT canonical, count FROM {table} ORDER BY count DESC, canonical COLLATE BINARY ASC LIMIT :limit))"""


def rankings(connection, filters, limit=25):
    cte, params = selection(connection, filters)
    params["limit"] = limit
    sql = cte + ranking_ctes(filters) + "SELECT json_object(" + ",".join(
        f"'{key}', {_ranking_json(table)}" for key, table in (
            ("products", "product_counts"), ("outcomes", "outcome_counts"), ("reactions", "reaction_counts"))) + ")"
    return json.loads(connection.execute(sql, params).fetchone()[0])


def overview_sql(cte, filters):
    if filters["productFilter"] is None:
        return annual_overview_sql()
    return cte + ranking_ctes(filters) + f"""SELECT json_object(
        'selectedCount', COUNT(*), 'validAgeCount', COUNT(age_years),
        'ageMeans', json_object('total', AVG(age_years),
            'female', AVG(CASE WHEN gender = 'Female' THEN age_years END),
            'male', AVG(CASE WHEN gender = 'Male' THEN age_years END)),
        'yearCounts', (SELECT json_group_array(json_array(year, count)) FROM (
            SELECT year, COUNT(*) AS count FROM selected GROUP BY year ORDER BY year)),
        'ageHistogram', (SELECT json_group_array(json_array(bin, count)) FROM (
            SELECT CAST(age_years AS INTEGER) AS bin, COUNT(*) AS count FROM selected
            WHERE age_years IS NOT NULL GROUP BY bin ORDER BY bin)),
        'genderCounts', (SELECT json_group_array(json_array(gender, count)) FROM (
            SELECT gender, COUNT(*) AS count FROM selected GROUP BY gender ORDER BY gender)),
        'rankings', json_object('products', {_ranking_json('product_counts')},
            'outcomes', {_ranking_json('outcome_counts')}, 'reactions', {_ranking_json('reaction_counts')})
        ) FROM selected"""


def annual_overview_sql():
    return """WITH product_counts AS (SELECT canonical, SUM(count) AS count FROM annual_terms
                WHERE field = 'product' AND year BETWEEN :start AND :end GROUP BY canonical),
            outcome_counts AS (SELECT canonical, SUM(count) AS count FROM annual_terms
                WHERE field = 'outcome' AND year BETWEEN :start AND :end GROUP BY canonical),
            reaction_counts AS (SELECT canonical, SUM(count) AS count FROM annual_terms
                WHERE field = 'reaction' AND year BETWEEN :start AND :end GROUP BY canonical)
        SELECT json_object(
            'selectedCount', COALESCE(SUM(report_count), 0), 'validAgeCount', COALESCE(SUM(valid_age_count), 0),
            'ageMeans', json_object('total', 1.0 * SUM(age_sum) / SUM(valid_age_count),
                'female', 1.0 * SUM(female_age_sum) / SUM(female_age_count),
                'male', 1.0 * SUM(male_age_sum) / SUM(male_age_count)),
            'yearCounts', (SELECT json_group_array(json_array(year, report_count)) FROM (
                SELECT year, report_count FROM annual_stats WHERE year BETWEEN :start AND :end ORDER BY year)),
            'ageHistogram', (SELECT json_group_array(json_array(bin, count)) FROM (
                SELECT bin, SUM(count) AS count FROM annual_histogram WHERE year BETWEEN :start AND :end GROUP BY bin ORDER BY bin)),
            'genderCounts', (SELECT json_group_array(json_array(gender, count)) FROM (
                SELECT gender, SUM(count) AS count FROM annual_gender WHERE year BETWEEN :start AND :end GROUP BY gender ORDER BY gender)),
            'rankings', json_object('products', %s, 'outcomes', %s, 'reactions', %s))
        FROM annual_stats WHERE year BETWEEN :start AND :end""" % (
            _ranking_json('product_counts'), _ranking_json('outcome_counts'), _ranking_json('reaction_counts'))


def explore(connection, filters):
    cte, params = selection(connection, filters)
    params["limit"] = 25
    result = json.loads(connection.execute(overview_sql(cte, filters), params).fetchone()[0])
    for key, labels in (("yearCounts", range(filters["startYear"], filters["endYear"] + 1)),
                        ("ageHistogram", range(126)), ("genderCounts", ("Female", "Male", "Unknown"))):
        counts = dict(result[key])
        result[key] = [[label, counts.get(label, 0)] for label in labels]
    metadata = read_metadata(connection)
    return {"datasetId": metadata["datasetId"], "policyVersion": metadata["policyVersion"],
            "appliedFilters": dict(filters), **result,
            "missingAgeCount": result["selectedCount"] - result["validAgeCount"],
            "coverageNotes": metadata["notes"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--start-year", type=int, default=2002)
    parser.add_argument("--end-year", type=int, default=2026)
    parser.add_argument("--product")
    args = parser.parse_args()
    connection = open_database(args.database)
    try:
        print(json.dumps(explore(connection, {"startYear": args.start_year, "endYear": args.end_year,
                                              "productFilter": args.product}), indent=2, allow_nan=False))
    finally:
        connection.close()
