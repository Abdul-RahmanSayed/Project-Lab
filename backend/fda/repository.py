"""New report projections reuse the existing selection CTE, not a new search policy."""

from contextlib import contextmanager
import sqlite3

from query import open_database, selection


@contextmanager
def connection(database, token):
    token.check()
    db = open_database(database)
    db.set_progress_handler(lambda: int(token.cancelled()), 1000)
    try:
        token.check()
        yield db
        token.check()
    except sqlite3.OperationalError:
        token.check()
        raise
    finally:
        db.close()


def summary(row):
    value = row["event_date"]
    return {"reportId": row["report_id"], "eventDate": f"{value[:4]}-{value[4:6]}-{value[6:8]}",
            "year": row["year"], "ageYears": row["age_years"], "gender": row["gender"]}


def rows(db, filters, limit, after=None, report_id=None):
    if filters["productFilter"] is None:
        cte = ""
        # Use the existing unique-ID index: otherwise SQLite sorts the entire year set on every page.
        source = "reports r INDEXED BY sqlite_autoindex_reports_1"
        params = {"start": filters["startYear"], "end": filters["endYear"]}
        membership = "r.year BETWEEN :start AND :end"
    else:
        source = "reports r"
        cte, params = selection(db, filters)
        membership = "r.rid IN (SELECT rid FROM selected)"
    if report_id is not None:
        membership += " AND r.report_id = :report_id COLLATE BINARY"
        params["report_id"] = report_id
    if after is not None:
        membership += " AND r.report_id > :after COLLATE BINARY"
        params["after"] = after
    params["size"] = limit
    return db.execute(cte + "SELECT r.* FROM " + source + " WHERE " + membership
                      + " ORDER BY r.report_id COLLATE BINARY ASC LIMIT :size", params).fetchall()


def detail(db, row, filters, token):
    token.check()
    products = []
    for item in db.execute("""SELECT p.*, d.display_label, d.disclosure FROM report_products p
            LEFT JOIN term_dictionary d ON d.field = 'product' AND d.canonical = p.canonical
            WHERE p.rid = ? ORDER BY p.ordinal""", (row["rid"],)):
        product = filters["productFilter"]
        products.append({"ordinal": item["ordinal"], "rawName": item["raw_name"], "role": item["role"],
                         "canonicalTerm": item["canonical"], "displayLabel": item["display_label"],
                         "disclosure": item["disclosure"], "matchesProductFilter": None if product is None
                         else item["role"] == "SUSPECT" and product.casefold() in item["search_text"]})
        token.check()
    terms = {}
    for name, table in (("suspectProductsCanonical", "report_suspect_products"),
                        ("reactionsCanonical", "report_reactions"), ("outcomesCanonical", "report_outcomes")):
        terms[name] = [item[0] for item in db.execute(
            f"SELECT canonical FROM {table} WHERE rid = ? ORDER BY canonical COLLATE BINARY", (row["rid"],))]
    return {**summary(row), "products": products, **terms,
            "provenance": {"sourcePage": row["source_page"], "sourceIndex": row["source_index"]}}
