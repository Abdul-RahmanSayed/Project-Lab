"""Prepared-default dispatch, unchanged filtered results, and release guards."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


LAB = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LAB / "data-build"))
sys.path.insert(0, str(LAB / "tests"))
sys.dont_write_bytecode = True

from common import load_policy, sha256_file
from legacy import ensure_legacy
from prepare import prepare
from runtime import OverviewRuntime
from test_fda_spike import report
from test_slice2 import fixture
from verify import assert_equal, oracle_result


class RuntimeTests(unittest.TestCase):
    policy = None

    def setUp(self):
        directory = LAB / "generated" / "performance" / "tests"
        directory.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=directory)
        self.root = Path(self.temp.name).resolve()
        if self.root.parent != directory.resolve():
            raise ValueError("Unexpected temporary test directory.")
        self.reports = [
            report("R1", [("Stra\u00dfe 50%_mix", "SUSPECT"), ("Other", "SUSPECT")], .5, gender="Female"),
            report("R2", [("VITAMIN D3", "SUSPECT"), ("VITAMIN D", "SUSPECT")], 125, gender="Male", year=2025),
            report("R3", [("A+B", "SUSPECT"), ("A+B", "SUSPECT")], 12, "month(s)"),
            report("R4", [("Stra\u00dfe", "CONCOMITANT")], True),
            report("R5", [("EXEMPTION 4", "SUSPECT")], 0, "day(s)", year=2026),
        ]
        source = self.root / "source"
        _, lock, _ = fixture(source, self.reports)
        with redirect_stdout(io.StringIO()), patch("prepare.source_identity", return_value=lock["source"]):
            result = prepare(source, self.root / "release", source / "lock.json")
        self.release = Path(result["releaseDirectory"])
        self.runtime = OverviewRuntime(self.release)

    def tearDown(self):
        self.temp.cleanup()

    def check(self, filters):
        response = json.loads(self.runtime.read(filters))
        expected = oracle_result(self.policy, self.reports, filters)["overview"]
        assert_equal(response["overview"], expected)
        self.assertIs(response["isLive"], False)
        self.assertEqual(response["releaseId"], self.runtime.release_id)
        return response

    def test_default_is_shared_immutable_bytes_without_sql(self):
        filters = self.runtime.default_filters
        with patch("runtime.open_database", side_effect=AssertionError("Default must not open SQLite")):
            first = self.runtime.read(filters)
            self.assertIsInstance(first, bytes)
            self.assertIs(first, self.runtime.read(dict(filters)))
        result = self.check(filters)
        self.assertEqual(result["source"], "prepared-default")
        self.assertEqual(result["label"], "Saved overview / data snapshot")
        result["overview"]["selectedCount"] = -1
        filters["startYear"] = 2024
        self.assertEqual(self.check(self.runtime.default_filters)["overview"]["selectedCount"], 5)

    def test_changed_years_always_use_sql(self):
        for start, end in ((2024, 2024), (2024, 2026), (2026, 2026), (2002, 2003)):
            result = self.check({"startYear": start, "endYear": end, "productFilter": None})
            self.assertEqual(result["source"], "sqlite")

    def test_raw_search_aliases_literal_punctuation_and_empty_match_oracle(self):
        for product in ("STRASSE", "%", "_", "A+B", "VITAMIN D3", "not a product", "' OR 1=1 --"):
            with self.subTest(product=product):
                result = self.check({"startYear": 2002, "endYear": 2026, "productFilter": product})
                self.assertEqual(result["source"], "sqlite")

    def test_invalid_filters_cannot_take_default_shortcut(self):
        for changes in ({"startYear": 2002.0}, {"endYear": True}, {"startYear": 2027},
                        {"productFilter": " "}, {"productFilter": 0}, {"extra": None}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.runtime.read({**self.runtime.default_filters, **changes})
        with self.assertRaises(ValueError):
            self.runtime.read({})

    def test_concurrent_requests_match_and_do_not_change_database(self):
        before = sha256_file(self.release / "fda.sqlite3")
        filters = [self.runtime.default_filters,
                   {"startYear": 2024, "endYear": 2024, "productFilter": None},
                   {"startYear": 2002, "endYear": 2026, "productFilter": "%"}]
        with ThreadPoolExecutor(max_workers=5) as pool:
            responses = list(pool.map(self.runtime.read, filters * 10))
        for index, payload in enumerate(responses):
            expected = oracle_result(self.policy, self.reports, filters[index % 3])["overview"]
            assert_equal(json.loads(payload)["overview"], expected)
        self.assertEqual(sha256_file(self.release / "fda.sqlite3"), before)
        self.assertFalse(self.runtime.describe()["filteredResponseCache"])
        self.assertEqual(self.runtime.describe()["preparedEntryCount"], 1)

    def test_corrupt_saved_overview_fails_closed(self):
        (self.release / "saved-overview.json").write_bytes(b"{}")
        with self.assertRaisesRegex(ValueError, "integrity"):
            OverviewRuntime(self.release)

    def test_changed_query_code_requires_new_release(self):
        with patch("runtime.sha256_file", return_value="different"):
            with self.assertRaisesRegex(ValueError, "Query code differs"):
                OverviewRuntime(self.release)

    def test_runtime_does_not_import_analysis_or_policy_packages(self):
        code = ("import sys;sys.path.insert(0," + repr(str(LAB / "data-build")) + ");"
                "from runtime import OverviewRuntime;r=OverviewRuntime(" + repr(str(self.release)) + ");"
                "r.read(r.default_filters);"
                "assert not any(n in sys.modules for n in ('numpy','pandas','matplotlib','fda_core'))")
        subprocess.run([sys.executable, "-B", "-c", code], check=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-repo", required=True, type=Path)
    args, remaining = parser.parse_known_args()
    RuntimeTests.policy = load_policy(ensure_legacy(args.source_repo))
    unittest.main(argv=[sys.argv[0], *remaining])
