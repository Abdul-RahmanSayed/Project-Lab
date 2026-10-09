"""Independent pre-extraction policy/CLI parity and atomic release regressions."""

import argparse
from contextlib import redirect_stdout
from datetime import datetime
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
sys.dont_write_bytecode = True

import fda_core as core
from common import content_hash, load_policy, sha256_file, write_json
from prepare import prepare, validate_release
from package_core import package
from legacy import ensure_legacy
from query import open_database


def report(identifier="R1", date="20240101", age="40"):
    return {"report_number": identifier, "date_started": date,
            "products": [{"role": "SUSPECT", "name_brand": "Stra\u00dfe 1/2 MG"}],
            "consumer": {"age": age, "age_unit": "year(s)", "gender": "Female"},
            "outcomes": ["Hospitalisation", "HOSPITALIZATION"], "reactions": ["Nausea"]}


def fixture(root, reports):
    data = root / "data"
    data.mkdir(parents=True, exist_ok=True)
    page = data / "page.json"
    write_json(page, {"results": reports})
    count = len(reports)
    manifest = {"schemaVersion": 1, "complete": True, "startDate": "20020101", "endDate": "20260101",
                "startedAt": "2026-09-04T18:24:34.942Z", "completedAt": "2026-09-04T18:29:41.824Z",
                "pageLimit": 100, "windowCount": 1, "pageCount": 1, "savedCount": count,
                "total": count, "uniqueCount": count,
                "windows": [{"startDate": "20020101", "endDate": "20260101", "savedCount": count,
                             "total": count, "pageCount": 1, "files": ["page.json"]}]}
    write_json(data / "manifest.json", manifest)
    inventory = [{"path": "page.json", "sha256": sha256_file(page), "bytes": page.stat().st_size, "reports": count}]
    manifest_hash = sha256_file(data / "manifest.json")
    lock = json.loads((LAB / "data-build" / "fda_source.lock.json").read_text(encoding="utf-8"))
    lock["snapshot"] = {"manifestSha256": manifest_hash,
                        "snapshotSha256": content_hash({"manifestSha256": manifest_hash, "pages": inventory}),
                        "reportCount": count, "uniqueReportCount": count, "pageCount": 1,
                        "coverageStart": "20020101", "coverageEnd": "20260101",
                        "acquisitionStartedAt": manifest["startedAt"], "acquisitionCompletedAt": manifest["completedAt"]}
    write_json(root / "lock.json", lock)
    return data, lock, manifest


class Slice2Tests(unittest.TestCase):
    legacy = None
    cli = None

    def setUp(self):
        directory = LAB / "generated" / "slice2" / "tests"
        directory.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=directory)
        self.root = Path(self.temp.name).resolve()
        if self.root.parent != directory.resolve():
            raise ValueError("Unexpected temporary test directory.")

    def tearDown(self):
        self.temp.cleanup()

    def test_core_import_needs_no_analysis_libraries(self):
        result = subprocess.check_output([sys.executable, "-B", "-c",
            "import sys,fda_core; assert not any(n in sys.modules for n in ('pandas','numpy','matplotlib'))"], text=True)
        self.assertEqual(result, "")

    def test_numeric_aliases_and_clinical_neighbors_match_legacy(self):
        names = ["Formula 1.5 MG", "Formula 15 MG", "Formula 1/2 MG", "Formula 12 MG", "Formula 1\u00bd MG",
                 "VITAMIN D3", "Vitamin D3 5000 IU", "Vitamin D3 1000 IU", "D3", "NATURE MADE D3 2000IU",
                 "JIFF CREAMY PEANUTBUTTER", "JIF CREAMY PEANUT BUTTER", "EXEMPTION 4",
                 "Stra\u00dfe 50%_mix", "A+B Nutrition", "Hospitalisation", "Hallucinations", "STROKE", "HAEMORRHAGIC STROKE"]
        for field in ("product", "reaction", "outcome"):
            for name in names:
                with self.subTest(field=field, name=name):
                    self.assertEqual(core.normalizeTerm(name, field), self.legacy.normalizeTerm(name, field))
            self.assertEqual(core.normalizeTerms(names + names, field), self.legacy.normalizeTerms(names + names, field))
        self.assertNotEqual(core.normalizeTerm("Formula 1.5 MG", "product"), core.normalizeTerm("Formula 15 MG", "product"))
        self.assertNotEqual(core.normalizeTerm("Formula 1/2 MG", "product"), core.normalizeTerm("Formula 12 MG", "product"))
        self.assertNotEqual(core.normalizeTerm("STROKE", "reaction"), core.normalizeTerm("HAEMORRHAGIC STROKE", "reaction"))

    def test_all_age_units_boundaries_and_invalid_values_match_legacy(self):
        values = [None, True, False, 0, .5, 125, 125.000001, -1, "NaN", "inf", "bad", "1e10000", 10 ** 1000]
        for unit in [*core.ageFactors, " YEAR(S) ", "unknown", None]:
            for age in values:
                with self.subTest(unit=unit, age=str(age)[:24]):
                    consumer = {"age": age, "age_unit": unit}
                    self.assertEqual(core.ageInYears(consumer), self.legacy.ageInYears(consumer))
        for gender in (None, "female", " MALE ", "Unknown", 3):
            self.assertEqual(core.getGender({"gender": gender}), self.legacy.getGender({"gender": gender}))

    def test_current_cli_argument_contract_matches_legacy(self):
        for values in ([], ["2022"], ["2024", "2024"], ["2026", "CARROTS", "2024"],
                       ["--product", "125.5"], ["--group-by", "gender"], ["2024", "--group-by", "product"]):
            self.assertEqual(self.cli.parseArgs(values), self.legacy.parseArgs(values))
        for values in (["2001"], ["--product"], ["--group-by", "invalid"], [" "]):
            errors = []
            for module in (self.cli, self.legacy):
                try:
                    module.parseArgs(values)
                except Exception as error:
                    errors.append((type(error).__name__, str(error)))
            self.assertEqual(len(errors), 2)
            self.assertEqual(errors[0], errors[1])

    def test_january_first_2026_keeps_actual_year_in_final_2025_window(self):
        reports = [report("Y2025", "20251231"), report("Y2026", "20260101")]
        data, _, manifest = fixture(self.root, reports)
        manifest["windowCount"] = 2
        manifest["windows"] = [
            {"startDate": "20020101", "endDate": "20241231", "savedCount": 0, "total": 0, "pageCount": 0, "files": []},
            {"startDate": "20250101", "endDate": "20260101", "savedCount": 2, "total": 2, "pageCount": 1, "files": ["page.json"]}]
        write_json(data / "manifest.json", manifest)
        self.assertEqual(core.loadReports(data), self.legacy.loadReports(data))
        selected = core.selectReports(core.loadReports(data), {"startYear": 2026, "endYear": 2026, "productFilter": None})
        self.assertEqual([item["report"]["report_number"] for item in selected], ["Y2026"])

    def test_cli_summary_grouping_and_png_match_legacy(self):
        data, _, _ = fixture(self.root, [report(), report("R2", "20260101", None)])
        for index, values in enumerate(([], ["--group-by", "year"], ["--group-by", "gender"], ["--group-by", "product"], ["--product", "No match"])):
            outputs, pngs = [], []
            for name, module in (("legacy", self.legacy), ("current", self.cli)):
                charts = self.root / f"{name}-{index}"
                output = io.StringIO()
                with redirect_stdout(output):
                    module.main(values, root=data, chartRoot=charts, executionTime=datetime(2026, 10, 9, 12))
                outputs.append(output.getvalue().replace(str(charts), "CHARTS"))
                pngs.append(sha256_file(next(charts.glob("*.png"))))
            self.assertEqual(outputs[0], outputs[1])
            self.assertEqual(pngs[0], pngs[1])

    def test_package_rebuild_requires_pinned_wheel(self):
        source = Path(self.cli.__file__).parent
        pin = LAB / "data-build" / "fda_source.lock.json"
        lock = json.loads(pin.read_text(encoding="utf-8"))
        output = self.root / "package"

        def changed_wheel(*args, **kwargs):
            (output / lock["wheel"]["name"]).write_bytes(b"not the pinned wheel")

        with patch("package_core.source_identity", return_value=lock["source"]), \
                patch("package_core.core_files", return_value=lock["source"]["files"]), \
                patch("package_core.subprocess.run", side_effect=changed_wheel):
            with self.assertRaisesRegex(ValueError, "pinned package lock"):
                package(source, output, snapshot_lock=pin)
        self.assertFalse((output / "fda_source.lock.json").exists())

    def test_atomic_reproducible_release_and_saved_overview(self):
        source = self.root / "source"
        _, lock, _ = fixture(source, [report(), report("R2", "20260101", None)])
        with patch("prepare.source_identity", return_value=lock["source"]):
            first = prepare(source, self.root / "first", source / "lock.json")
            second = prepare(source, self.root / "second", source / "lock.json")
        self.assertEqual(first["release"], second["release"])
        root = Path(first["releaseDirectory"])
        saved = json.loads((root / "saved-overview.json").read_text())
        self.assertEqual(saved["label"], "Saved overview / data snapshot")
        self.assertIs(saved["isLive"], False)
        self.assertEqual(saved["overview"]["selectedCount"], 2)
        self.assertEqual(dict(saved["overview"]["yearCounts"])[2026], 1)
        manifest_path = root / "release.json"
        manifest = json.loads(manifest_path.read_text())
        bad_manifest = json.loads(manifest_path.read_text())
        bad_manifest["files"].pop("fda.sqlite3")
        write_json(manifest_path, bad_manifest)
        with self.assertRaisesRegex(ValueError, "inventory"):
            validate_release(root)
        write_json(manifest_path, manifest)
        (root / "saved-overview.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "integrity"):
            validate_release(root)

    def test_incomplete_duplicate_and_modified_pages_fail_without_release(self):
        for label in ("incomplete", "duplicate", "modified"):
            with self.subTest(case=label):
                root = self.root / label
                reports = [report(), report("R1" if label == "duplicate" else "R2")]
                source = root / "source"
                data, lock, manifest = fixture(source, reports)
                if label == "incomplete":
                    manifest["complete"] = False
                    write_json(data / "manifest.json", manifest)
                    lock["snapshot"]["manifestSha256"] = sha256_file(data / "manifest.json")
                    write_json(source / "lock.json", lock)
                elif label == "modified":
                    reports[0]["products"][0]["name_brand"] = "Changed raw name"
                    write_json(data / "page.json", {"results": reports})
                with patch("prepare.source_identity", return_value=lock["source"]):
                    pattern = "complete" if label == "incomplete" else "Duplicate" if label == "duplicate" else "differs from"
                    with self.assertRaisesRegex((core.DataError, ValueError), pattern):
                        prepare(source, root / "output", source / "lock.json")
                output = root / "output"
                self.assertFalse(output.exists() and any(output.iterdir()))

    def test_validation_errors_match_legacy(self):
        for name in ("boolean_schema", "path_escape", "invalid_date", "missing_consumer", "invalid_terms", "invalid_utf8", "cr_newlines"):
            with self.subTest(case=name):
                root = self.root / name
                data, _, manifest = fixture(root, [report()])
                if name == "boolean_schema":
                    manifest["schemaVersion"] = True
                    write_json(data / "manifest.json", manifest)
                elif name == "path_escape":
                    manifest["windows"][0]["files"] = ["../escape.json"]
                    write_json(data / "manifest.json", manifest)
                elif name == "invalid_utf8":
                    (data / "page.json").write_bytes(b"\xff\xfe")
                elif name == "cr_newlines":
                    (data / "page.json").write_bytes(b'{\r"results": [\rbroken\r]}')
                else:
                    item = report()
                    if name == "invalid_date":
                        item["date_started"] = "20240230"
                    elif name == "missing_consumer":
                        item.pop("consumer")
                    else:
                        item["reactions"] = [3]
                    write_json(data / "page.json", {"results": [item]})
                errors = []
                for module in (core, self.legacy):
                    try:
                        module.loadReports(data)
                    except Exception as error:
                        errors.append((type(error).__name__, str(error)))
                self.assertEqual(len(errors), 2)
                self.assertEqual(errors[0], errors[1])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-repo", required=True, type=Path)
    args, remaining = parser.parse_known_args()
    Slice2Tests.cli = load_policy(args.source_repo)
    Slice2Tests.legacy = load_policy(ensure_legacy(args.source_repo))
    unittest.main(argv=[sys.argv[0], *remaining])
