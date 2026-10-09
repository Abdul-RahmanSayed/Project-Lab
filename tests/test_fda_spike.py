"""Focused query regressions against the unmodified FDA Python policy."""

import argparse
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest


LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB / "data-build"))
sys.dont_write_bytecode = True

from common import load_policy, sha256_file
from schema import SCHEMA_HASH, SCHEMA_VERSION
from prepare import SCHEMA, add_report
from query import explore, open_database, rankings, selected_ids
from verify import assert_equal, oracle_result


def report(identifier, products, age=None, unit="year(s)", gender=None, year=2024):
    return {"report_number": identifier, "date_started": f"{year}0101",
            "products": [{"name_brand": name, "role": role} for name, role in products],
            "consumer": {"age": age, "age_unit": unit, "gender": gender},
            "outcomes": ["Hospitalisation", "HOSPITALIZATION"],
            "reactions": ["Hallucinations", "HALLUCINATION", "Nausea"]}


class QueryParityTests(unittest.TestCase):
    policy = None

    def setUp(self):
        self.reports = [
            report("R1", [("Stra\u00dfe 50%_mix", "SUSPECT"), ("STRA\u00dfE 50%_mix", "SUSPECT"),
                          ("Unmatched companion", "SUSPECT")], .5, gender="Female"),
            report("R2", [("Stra\u00dfe", "CONCOMITANT"), ("Vitamin D3", "SUSPECT"),
                          ("VITAMIN D", "SUSPECT"), ("Vitamin D3 5000 IU", "SUSPECT")],
                   125, gender="Male", year=2025),
            report("R3", [("A+B Nutrition", "SUSPECT"), ("A+B Nutrition", "SUSPECT")], 12, "month(s)"),
            report("R4", [("Only concomitant", "CONCOMITANT")], True, gender="other"),
            report("R5", [("125.5", "SUSPECT")], 125.01, gender="Female"),
            report("R6", [("EXEMPTION 4", "SUSPECT")], 0, "day(s)", year=2026),
            report("R7", [("Strength 1/2 MG", "SUSPECT"), ("Strength 1.2 MG", "SUSPECT")],
                   "NaN", gender="Male"),
        ]
        self.connection = sqlite3.connect(":memory:")
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)
        for rid, item in enumerate(self.reports, 1):
            self.policy.checkReport(item, "20020101", "20260101", "fixture")
            add_report(self.connection, self.policy, item, rid, "fixture.json", rid)
        metadata = {"schemaVersion": SCHEMA_VERSION, "schemaHash": SCHEMA_HASH,
                    "coverageStart": "20020101", "coverageEnd": "20260101",
                    "datasetId": "fixture", "policyVersion": "fixture", "notes": []}
        self.connection.executemany("INSERT INTO snapshot_metadata VALUES (?, ?)",
                                    [(key, json.dumps(value)) for key, value in metadata.items()])
        self.connection.commit()
        self.connection.execute("""INSERT INTO annual_stats SELECT year, COUNT(*), COUNT(age_years), SUM(age_years),
            COUNT(CASE WHEN gender = 'Female' THEN age_years END), SUM(CASE WHEN gender = 'Female' THEN age_years END),
            COUNT(CASE WHEN gender = 'Male' THEN age_years END), SUM(CASE WHEN gender = 'Male' THEN age_years END)
            FROM reports GROUP BY year""")
        self.connection.execute("INSERT INTO annual_histogram SELECT year, CAST(age_years AS INTEGER), COUNT(*) FROM reports WHERE age_years IS NOT NULL GROUP BY year, CAST(age_years AS INTEGER)")
        self.connection.execute("INSERT INTO annual_gender SELECT year, gender, COUNT(*) FROM reports GROUP BY year, gender")
        for field, table in (("product", "report_suspect_products"), ("outcome", "report_outcomes"), ("reaction", "report_reactions")):
            self.connection.execute(f"INSERT INTO annual_terms SELECT ?, r.year, p.canonical, COUNT(*) FROM {table} p JOIN reports r ON r.rid = p.rid GROUP BY r.year, p.canonical", (field,))
        self.connection.commit()

    def tearDown(self):
        self.connection.close()

    def compare(self, product=None, start=2002, end=2026):
        filters = {"startYear": start, "endYear": end, "productFilter": product}
        expected = oracle_result(self.policy, self.reports, filters)
        actual = explore(self.connection, filters)
        assert_equal(actual, expected["overview"])
        assert_equal(selected_ids(self.connection, filters), expected["selectedIds"])
        assert_equal(rankings(self.connection, filters, sys.maxsize), expected["allRankings"])
        return actual

    def test_unicode_casefold_and_matching_products_only(self):
        actual = self.compare("STRASSE")
        self.assertEqual(actual["selectedCount"], 1)
        self.assertEqual(actual["rankings"]["products"], [["STRASSE 50% MIX", 1]])

    def test_literal_wildcards_and_punctuation(self):
        for product in ("%", "_", "A+B", "1/2", "125.5", "' OR 1=1 --"):
            with self.subTest(product=product):
                self.compare(product)
        self.assertEqual(self.compare("%")['selectedCount'], 1)

    def test_aliases_after_raw_selection(self):
        actual = self.compare("Vitamin D3")
        self.assertEqual(actual["rankings"]["products"], [["VITAMIN D", 1], ["VITAMIN D 5000 IU", 1]])
        self.assertEqual(self.compare("VITAMIN D")["selectedCount"], 1)

    def test_age_boundaries_units_missing_and_unknown_gender(self):
        actual = self.compare()
        self.assertEqual(actual["selectedCount"], 7)
        self.assertEqual(actual["validAgeCount"], 4)
        self.assertEqual(actual["ageHistogram"][0], [0, 2])
        self.assertEqual(actual["ageHistogram"][1], [1, 1])
        self.assertEqual(actual["ageHistogram"][125], [125, 1])
        self.assertEqual(actual["genderCounts"], [["Female", 2], ["Male", 2], ["Unknown", 3]])

    def test_year_range_and_empty_selection(self):
        self.compare(start=2024, end=2024)
        actual = self.compare("No match")
        self.assertEqual(actual["selectedCount"], 0)
        self.assertEqual(actual["ageMeans"], {"total": None, "female": None, "male": None})
        self.assertEqual(len(actual["ageHistogram"]), 126)
        self.assertEqual(len(actual["yearCounts"]), 25)

    def test_distinct_terms_report_overlap_and_disclosure(self):
        actual = self.compare()
        self.assertEqual(actual["rankings"]["outcomes"], [["HOSPITALIZATION", 7]])
        self.assertEqual(sum(count for _, count in actual["rankings"]["products"]), 9)
        label = self.connection.execute(
            "SELECT display_label FROM term_dictionary WHERE field = 'product' AND canonical = 'EXEMPTION 4'"
        ).fetchone()[0]
        self.assertIn("may include multiple products", label)

    def test_invalid_ranges_and_blank_search(self):
        for filters in ({"startYear": 2025, "endYear": 2024, "productFilter": None},
                        {"startYear": 2001, "endYear": 2024, "productFilter": None},
                        {"startYear": True, "endYear": 2024, "productFilter": None},
                        {"startYear": 2024, "endYear": 2024, "productFilter": " "}):
            with self.assertRaises(ValueError):
                explore(self.connection, filters)

    def test_read_only_rejects_writes_and_keeps_database_hash(self):
        root = LAB / "generated" / "tests"
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as directory:
            path = Path(directory) / "test.sqlite3"
            target = sqlite3.connect(path)
            self.connection.backup(target)
            target.close()
            before = sha256_file(path)
            readonly = open_database(path)
            try:
                with self.assertRaises(sqlite3.OperationalError):
                    readonly.execute("DELETE FROM reports")
            finally:
                readonly.close()
            self.assertEqual(sha256_file(path), before)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-repo", required=True, type=Path)
    args, remaining = parser.parse_known_args()
    QueryParityTests.policy = load_policy(args.source_repo)
    unittest.main(argv=[sys.argv[0], *remaining])
