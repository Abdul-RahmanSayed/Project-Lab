"""Build a content-identified read-only SQLite/metadata/saved-overview release atomically."""

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import time

from common import (content_hash, core_files, environment, load_core, peak_memory,
                    sha256_file, source_identity, write_json)
from schema import SCHEMA, SCHEMA_HASH, SCHEMA_VERSION


def add_report(connection, policy, report, rid, source_page, source_index):
    connection.execute("INSERT INTO reports VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (
        rid, report["report_number"], report["date_started"], int(report["date_started"][:4]),
        policy.ageInYears(report["consumer"]), policy.getGender(report["consumer"]) or "Unknown",
        source_page, source_index))
    dictionary = set()
    products = []
    for ordinal, product in enumerate(report["products"]):
        raw = product["name_brand"]
        canonical = policy.normalizeTerm(raw, "product") or None
        products.append((rid, ordinal, product["role"], raw, raw.casefold(), canonical))
        if canonical:
            label = policy.getProductLabel(canonical)
            dictionary.add(("product", canonical, label,
                            label if canonical == "EXEMPTION 4" else None))
    connection.executemany("INSERT INTO report_products VALUES (?, ?, ?, ?, ?, ?)", products)
    for field, table in (("reaction", "report_reactions"), ("outcome", "report_outcomes")):
        terms = policy.normalizeTerms(report[field + "s"], field)
        connection.executemany(f"INSERT INTO {table} VALUES (?, ?)", [(rid, term) for term in terms])
        dictionary.update((field, term, term, None) for term in terms)
    connection.executemany("INSERT OR IGNORE INTO term_dictionary VALUES (?, ?, ?, ?)", sorted(dictionary))
    suspects = policy.normalizeTerms(policy.getSuspectProducts(report), "product")
    connection.executemany("INSERT INTO report_suspect_products VALUES (?, ?)", [(rid, name) for name in suspects])


def verify_pin(source_repo, lock):
    if source_identity(source_repo) != lock["source"]:
        raise ValueError("FDA source does not match the pinned source lock.")
    core = load_core()
    installed_root = Path(core.__file__).parent
    expected = {name: digest for name, digest in lock["source"]["files"].items() if name.startswith("fda_core/")}
    installed = {"fda_core/" + path.name: sha256_file(path) for path in sorted(installed_root.glob("*.py"))}
    if installed != expected or core.__version__ != lock["coreVersion"]:
        raise ValueError("Installed FDA core differs from the source lock; install the pinned wheel.")
    if "fda-core-sha256:" + content_hash(expected) != lock["policyVersion"]:
        raise ValueError("Invalid policy identity in source lock.")
    return core


def validate_release(root):
    root = Path(root).resolve()
    release = json.loads((root / "release.json").read_text(encoding="utf-8"))
    if release["schemaVersion"] != SCHEMA_VERSION or release["schemaHash"] != SCHEMA_HASH:
        raise ValueError("Unsupported release schema.")
    if set(release["files"]) != {"fda.sqlite3", "metadata.json", "page-inventory.json", "saved-overview.json"}:
        raise ValueError("Release artifact inventory is incomplete or unsupported.")
    for name, item in release["files"].items():
        path = (root / name).resolve()
        if path.parent != root or sha256_file(path) != item["sha256"] or path.stat().st_size != item["bytes"]:
            raise ValueError(f"Release artifact failed integrity validation: {name}")
    metadata = json.loads((root / "metadata.json").read_text(encoding="utf-8"))
    overview = json.loads((root / "saved-overview.json").read_text(encoding="utf-8"))
    if (metadata["releaseId"] != release["releaseId"] or overview["releaseId"] != release["releaseId"]
            or metadata["datasetId"] != release["datasetId"] or metadata["policyVersion"] != release["policyVersion"]
            or overview["overview"]["datasetId"] != metadata["datasetId"]
            or overview["overview"]["policyVersion"] != metadata["policyVersion"]
            or overview["overview"]["appliedFilters"] != {
                "startYear": int(metadata["coverageStart"][:4]), "endYear": int(metadata["coverageEnd"][:4]),
                "productFilter": None} or overview["isLive"] is not False
            or overview["label"] != "Saved overview / data snapshot"):
        raise ValueError("Release, saved overview, or applied selection identities differ.")
    from query import open_database, read_metadata
    connection = open_database(root / "fda.sqlite3")
    try:
        if read_metadata(connection) != metadata:
            raise ValueError("SQLite and companion metadata differ.")
    finally:
        connection.close()
    return release


def prepare(source_repo, output_root, lock_path):
    started = time.perf_counter()
    source_repo, output_root = Path(source_repo).resolve(), Path(output_root).resolve()
    if output_root.is_relative_to(source_repo):
        raise ValueError("Release output must be outside the FDA source checkout.")
    lock = json.loads(Path(lock_path).read_text(encoding="utf-8"))
    core = verify_pin(source_repo, lock)
    data = source_repo / "data"
    if sha256_file(data / "manifest.json") != lock["snapshot"]["manifestSha256"]:
        raise ValueError("Completion manifest differs from the pinned snapshot.")
    manifest = core.loadManifest(data)
    build_environment = {key: environment()[key] for key in ("python", "sqlite")}
    builder_files = {name: sha256_file(Path(__file__).with_name(name))
                     for name in ("prepare.py", "query.py", "common.py", "schema.py")}
    build_identity = {
        "datasetId": "fda-sha256:" + lock["snapshot"]["snapshotSha256"],
        "policyVersion": lock["policyVersion"], "schemaVersion": SCHEMA_VERSION, "schemaHash": SCHEMA_HASH,
        "sourceLockHash": content_hash(lock), "preparerHash": sha256_file(__file__),
        "queryHash": sha256_file(Path(__file__).with_name("query.py")), "builderFiles": builder_files,
        "buildEnvironment": build_environment}
    release_id = "fda-release-sha256:" + content_hash(build_identity)
    output_root.mkdir(parents=True, exist_ok=True)
    final = output_root / content_hash(build_identity)
    inventory = []
    count = 0
    with tempfile.TemporaryDirectory(prefix=".building-", dir=output_root) as directory:
        candidate = Path(directory).resolve()
        if candidate.parent != output_root:
            raise ValueError("Candidate directory escaped the output root.")
        database = candidate / "fda.sqlite3"
        connection = sqlite3.connect(database)
        try:
            connection.executescript(SCHEMA)
            connection.execute("PRAGMA cache_size = -8192")
            connection.execute("BEGIN")

            def page_reader(path, label):
                payload, page = core.readJsonBytes(path, label)
                inventory.append({"path": path.relative_to(data).as_posix(),
                                  "sha256": hashlib.sha256(payload).hexdigest(),
                                  "bytes": len(payload),
                                  "reports": len(page["results"]) if isinstance(page, dict)
                                  and isinstance(page.get("results"), list) else 0})
                return page

            for file_name, reports in core.iterValidatedPages(data, pageReader=page_reader):
                for index, report in enumerate(reports, 1):
                    count += 1
                    add_report(connection, core, report, count, file_name, index)
            snapshot_hash = content_hash({"manifestSha256": lock["snapshot"]["manifestSha256"], "pages": inventory})
            unique = connection.execute("SELECT COUNT(DISTINCT report_id) FROM reports").fetchone()[0]
            if (snapshot_hash != lock["snapshot"]["snapshotSha256"] or count != lock["snapshot"]["reportCount"]
                    or unique != lock["snapshot"]["uniqueReportCount"] or len(inventory) != lock["snapshot"]["pageCount"]):
                raise ValueError("Snapshot content, counts, or uniqueness differs from the pin.")
            # Covering year lookup avoids repeatedly fetching the wide provenance rows.
            connection.execute("CREATE INDEX reports_year ON reports(year, rid, age_years, gender)")
            connection.execute("CREATE INDEX suspect_search ON report_products(search_text, rid, canonical) WHERE role = 'SUSPECT'")
            connection.execute("""INSERT INTO annual_stats SELECT year, COUNT(*), COUNT(age_years), SUM(age_years),
                COUNT(CASE WHEN gender = 'Female' THEN age_years END),
                SUM(CASE WHEN gender = 'Female' THEN age_years END),
                COUNT(CASE WHEN gender = 'Male' THEN age_years END),
                SUM(CASE WHEN gender = 'Male' THEN age_years END) FROM reports GROUP BY year""")
            connection.execute("""INSERT INTO annual_histogram SELECT year, CAST(age_years AS INTEGER), COUNT(*)
                FROM reports WHERE age_years IS NOT NULL GROUP BY year, CAST(age_years AS INTEGER)""")
            connection.execute("INSERT INTO annual_gender SELECT year, gender, COUNT(*) FROM reports GROUP BY year, gender")
            for field, table in (("product", "report_suspect_products"), ("outcome", "report_outcomes"),
                                 ("reaction", "report_reactions")):
                connection.execute(f"""INSERT INTO annual_terms SELECT ?, r.year, p.canonical, COUNT(*) FROM {table} p
                    JOIN reports r ON r.rid = p.rid GROUP BY r.year, p.canonical""", (field,))
            metadata = {
                **build_identity, "releaseId": release_id, "source": lock["source"], "coreVersion": core.__version__,
                **lock["snapshot"], "reportCount": count, "uniqueReportCount": unique,
                "windowPartitionPolicy": "The final 2025 download window includes January 1, 2026; report years use actual event dates.",
                "downloadWindows": [{"start": w["startDate"], "end": w["endDate"]} for w in manifest["windows"]],
                "notes": ["2026 covers January 1 only, stored in the final 2025 download window.",
                          "Report counts use actual event years; download-window splits do not redefine years.",
                          "Adverse-event reports do not establish causation, incidence, or product safety."]}
            for key, value in sorted(metadata.items()):
                connection.execute("INSERT INTO snapshot_metadata VALUES (?, ?)",
                                   (key, json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False)))
            connection.execute("ANALYZE")
            connection.commit()
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("SQLite integrity check failed.")
            if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise ValueError("SQLite foreign-key check failed.")
            tables = ("reports", "report_products", "report_suspect_products", "report_reactions",
                      "report_outcomes", "term_dictionary", "annual_stats", "annual_histogram", "annual_gender", "annual_terms")
            table_counts = {table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in tables}
        finally:
            connection.close()
        if sha256_file(data / "manifest.json") != lock["snapshot"]["manifestSha256"]:
            raise ValueError("Manifest changed during preparation.")
        for page in inventory:
            if sha256_file(data / page["path"]) != page["sha256"]:
                raise ValueError("Raw snapshot changed during preparation.")
        verify_pin(source_repo, lock)
        if any(sha256_file(Path(__file__).with_name(name)) != digest for name, digest in builder_files.items()):
            raise ValueError("Preparation/query code changed during the build.")
        from query import explore, open_database
        readonly = open_database(database)
        try:
            overview = explore(readonly, {"startYear": int(metadata["coverageStart"][:4]),
                                         "endYear": int(metadata["coverageEnd"][:4]), "productFilter": None})
        finally:
            readonly.close()
        write_json(candidate / "metadata.json", metadata)
        write_json(candidate / "page-inventory.json", inventory)
        write_json(candidate / "saved-overview.json", {
            "label": "Saved overview / data snapshot", "isLive": False, "releaseId": release_id,
            "snapshotAcquiredAt": metadata["acquisitionCompletedAt"], "overview": overview})
        names = ("fda.sqlite3", "metadata.json", "page-inventory.json", "saved-overview.json")
        release = {"releaseId": release_id, "datasetId": metadata["datasetId"], "policyVersion": metadata["policyVersion"],
                   "schemaVersion": SCHEMA_VERSION, "schemaHash": SCHEMA_HASH,
                   "files": {name: {"sha256": sha256_file(candidate / name), "bytes": (candidate / name).stat().st_size}
                             for name in names}}
        write_json(candidate / "release.json", release)
        validate_release(candidate)
        if final.exists():
            if validate_release(final) != release:
                raise ValueError("An existing release has the same identity but different content.")
        else:
            candidate.rename(final)
    result = {"releaseDirectory": str(final), "release": release, "metadata": metadata,
              "pageInventory": inventory, "tableCounts": table_counts,
              "preparationSeconds": time.perf_counter() - started,
              "databaseBytes": (final / "fda.sqlite3").stat().st_size,
              "databaseSha256": release["files"]["fda.sqlite3"]["sha256"],
              "memory": peak_memory(), "environment": environment()}
    write_json(output_root / "preparation.json", result)
    print(json.dumps({key: result[key] for key in ("releaseDirectory", "tableCounts", "preparationSeconds",
                                                  "databaseBytes", "memory")}, indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--lock", type=Path, default=Path(__file__).with_name("fda_source.lock.json"))
    args = parser.parse_args()
    prepare(args.source_repo, args.output_root, args.lock)
