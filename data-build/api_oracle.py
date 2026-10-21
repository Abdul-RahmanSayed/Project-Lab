"""Fresh original-Python reference for HTTP selections and retained report details."""

import argparse
from pathlib import Path
import random

from common import load_policy, source_identity, write_json
from legacy import ensure_legacy
from verify import cases, oracle_result


def run(source, output):
    before = source_identity(source)
    policy = load_policy(ensure_legacy(source))
    reports = policy.loadReports(source / "data")
    by_id = {report["report_number"]: report for report in reports}
    selections = cases()
    randomizer = random.Random(20261020)
    for index in range(12):
        report = randomizer.choice(reports)
        names = policy.getSuspectProducts(report)
        name = randomizer.choice(names) if names else "no-match-7c46ba"
        fragment = name[:min(len(name), randomizer.randint(3, 12))]
        start = randomizer.randint(2002, 2025)
        selections.append((f"sample_{index}", {"startYear": start, "endYear": randomizer.randint(start, 2026),
                                               "productFilter": fragment}))
    selections += [("literal_plus", {"startYear": 2002, "endYear": 2026, "productFilter": "+"}),
                   ("unicode_casefold", {"startYear": 2002, "endYear": 2026, "productFilter": "Stra\u00dfe"})]
    results = {}
    for name, filters in selections:
        result = oracle_result(policy, reports, filters)
        ids = result["selectedIds"]
        details = {}
        for rid in sorted({ids[index] for index in (0, len(ids) // 2, len(ids) - 1)}) if ids else []:
            report = by_id[rid]
            products = []
            for ordinal, product in enumerate(report["products"]):
                term = policy.normalizeTerm(product["name_brand"], "product") or None
                label = policy.getProductLabel(term) if term else None
                query = filters["productFilter"]
                products.append({"ordinal": ordinal, "rawName": product["name_brand"], "role": product["role"],
                    "canonicalTerm": term, "displayLabel": label, "disclosure": label if term == "EXEMPTION 4" else None,
                    "matchesProductFilter": None if query is None else product["role"] == "SUSPECT"
                    and query.casefold() in product["name_brand"].casefold()})
            date = report["date_started"]
            details[rid] = {"reportId": rid, "eventDate": f"{date[:4]}-{date[4:6]}-{date[6:8]}", "year": int(date[:4]),
                "ageYears": policy.ageInYears(report["consumer"]), "gender": policy.getGender(report["consumer"]) or "Unknown",
                "products": products, "suspectProductsCanonical": sorted(policy.normalizeTerms(policy.getSuspectProducts(report), "product")),
                "reactionsCanonical": sorted(policy.normalizeTerms(report["reactions"], "reaction")),
                "outcomesCanonical": sorted(policy.normalizeTerms(report["outcomes"], "outcome"))}
        results[name] = {"filters": filters, "overview": result["overview"], "selectedIds": ids, "details": details}
        print(f"Original-Python HTTP reference {name}: {len(ids):,} reports", flush=True)
    if source_identity(source) != before:
        raise AssertionError("FDA source changed while producing the HTTP reference.")
    write_json(output, {"source": before, "cases": results})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.source_repo.resolve(), args.output)
