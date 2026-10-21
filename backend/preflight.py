"""Offline, bounded-memory checks of every retained report and the largest page."""

import argparse
import heapq
from pathlib import Path
import time

from common import environment, peak_memory, write_json
from query import open_database
from runtime import encode

from .config import Settings
from .fda import models, repository
from .fda.parameters import identifier, make_cursor
from .fda.service import Service
from .jobs import Cancellation


def inspect_release(settings, output):
    started = time.perf_counter()
    service = Service(settings)
    token = Cancellation(time.monotonic() + 3600)
    db = open_database(service.database)
    largest, max_detail, max_id, max_cursor, total = [], 0, 0, 0, 0
    filters = {**service.default_filters, "productFilter": "\U0001f600" * 256}
    try:
        for row in db.execute("SELECT * FROM reports ORDER BY report_id COLLATE BINARY"):
            identifier(row["report_id"])
            max_id = max(max_id, len(row["report_id"].encode("utf-8")))
            max_cursor = max(max_cursor, len(make_cursor(service.release_id, filters, 100, row["report_id"])))
            service.check_provenance(row)
            summary = models.Summary.model_validate(repository.summary(row)).model_dump(mode="json")
            size = len(encode(summary))
            heapq.heappush(largest, (size, row["report_id"], summary))
            if len(largest) > 100:
                heapq.heappop(largest)
            report = repository.detail(db, row, filters, token)
            payload = service.encoded(models.DetailResponse, service.envelope("detail", {**service.context(filters), "report": report}))
            max_detail = max(max_detail, len(payload))
            total += 1
            if total % 10000 == 0:
                print(f"Preflight: {total:,} reports checked", flush=True)
        items = sorted((item[2] for item in largest), key=lambda item: item["reportId"])
        cursor = "A" * 2048
        page = {**service.context(filters), "sort": "reportId:asc", "limit": 100,
                "returnedCount": len(items), "items": items, "hasMore": True, "nextCursor": cursor}
        page_bytes = len(service.encoded(models.ReportsResponse, service.envelope("page", page)))
        if total != service.metadata["uniqueReportCount"] or max_cursor > 2048:
            raise ValueError("Report count or cursor bound failed preflight.")
    finally:
        db.close()
    report = {"releaseId": service.release_id, "reportsChecked": total, "maximumIdUtf8Bytes": max_id,
              "maximumDetailBytesWithWorstFilter": max_detail, "largest100SummaryPageBytesWithWorstFilter": page_bytes,
              "maximumActualCursorCharacters": max_cursor, "metadataBytes": len(service.metadata_payload),
              "defaultBytes": len(service.default_payload), "responseLimitBytes": settings.max_response_bytes,
              "seconds": time.perf_counter() - started, "memory": peak_memory(), "environment": environment(),
              "scope": "Every retained detail and summary; 100 largest summaries together; maximum permitted filter and full cursor allowance. No raw fields invented."}
    write_json(output, report)
    print(report, flush=True)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-directory", type=Path, required=True)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    inspect_release(Settings(args.release_directory.resolve(), args.release_id), args.output)
