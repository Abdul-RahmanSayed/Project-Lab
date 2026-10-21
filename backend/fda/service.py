"""Checked release lifecycle and the one immutable default response."""

import hashlib
import json
from pathlib import PurePosixPath
import sqlite3

from pydantic import ValidationError
from query import explore, open_database, read_metadata
from runtime import OverviewRuntime, encode

from backend.errors import ApiError
from . import models, repository
from .parameters import identifier, make_cursor


def calendar(value):
    return f"{value[:4]}-{value[4:6]}-{value[6:8]}"


class Service:
    def __init__(self, settings):
        self.settings = settings
        self.ready = False
        self.reader = OverviewRuntime(settings.release_directory)
        if self.reader.release_id != settings.expected_release_id:
            raise ValueError("Configured and checked release identities differ.")
        self.release_id = self.reader.release_id
        self.database = settings.release_directory / "fda.sqlite3"
        db = open_database(self.database)
        try:
            self.metadata = read_metadata(db)
            # Projection checks are cheap; exhaustive size validation is the offline preflight.
            db.execute("SELECT r.report_id, r.event_date, r.year, r.age_years, r.gender, r.source_page, r.source_index FROM reports r LIMIT 0")
            db.execute("SELECT raw_name, role, ordinal, canonical, search_text FROM report_products LIMIT 0")
            overrides = [dict(row) for row in db.execute("""SELECT canonical, display_label AS displayLabel,
                disclosure FROM term_dictionary WHERE field = 'product'
                AND (display_label != canonical OR disclosure IS NOT NULL) ORDER BY canonical COLLATE BINARY""")]
        finally:
            db.close()
        inventory = json.loads((settings.release_directory / "page-inventory.json").read_bytes())
        self.pages = {item["path"]: item["reports"] for item in inventory}
        self.default_filters = self.reader.default_filters
        self.default_payload = self.reader.read(self.default_filters)
        if len(self.default_payload) > settings.max_response_bytes:
            raise ValueError("Prepared response exceeds the configured byte limit.")
        saved = models.ExploreResponse.model_validate_json(self.default_payload)
        if (saved.source != "prepared-default" or saved.label != "Saved overview / data snapshot"
                or saved.overview.appliedFilters.model_dump() != self.default_filters
                or saved.overview.datasetId != self.metadata["datasetId"]
                or saved.overview.policyVersion != self.metadata["policyVersion"]
                or saved.snapshotAcquiredAt != self.metadata["acquisitionCompletedAt"]):
            raise ValueError("Prepared public response identity differs.")
        self.default_etag = '"' + hashlib.sha256(self.default_payload).hexdigest() + '"'
        info = self.metadata
        public = {**self.context(), "coreVersion": info["coreVersion"], "schemaVersion": info["schemaVersion"],
                  "interpretationNotes": ["Counts describe FDA adverse-event reports, not unique people, causation, incidence, relative risk, or product-safety conclusions."],
                  "schemaHash": info["schemaHash"], "queryHash": info["queryHash"],
                  "sourceRevision": info["source"]["revision"], "revisionKind": info["source"]["revisionKind"],
                  "reportCount": info["reportCount"], "uniqueReportCount": info["uniqueReportCount"],
                  "pageCount": info["pageCount"], "coverageStart": calendar(info["coverageStart"]),
                  "coverageEnd": calendar(info["coverageEnd"]), "defaultFilters": self.default_filters,
                  "supportedFilters": ["startYear", "endYear", "productFilter"],
                  "supportedSorts": ["reportId:asc"], "limits": {"productCharacters": 256,
                      "productUtf8Bytes": 1024, "cursorCharacters": 2048, "reportIdUtf8Bytes": 512,
                      "defaultPage": 25, "maximumPage": 100, "responseBytes": settings.max_response_bytes},
                  "termDisplayOverrides": overrides}
        self.metadata_payload = self.encoded(models.MetadataResponse, self.envelope("metadata", public, "prepared-metadata"))
        self.ready = True

    def context(self, filters=None):
        result = {"datasetId": self.metadata["datasetId"], "policyVersion": self.metadata["policyVersion"],
                  "coverageNotes": self.metadata["notes"]}
        if filters is not None:
            result["appliedFilters"] = filters
        return result

    def envelope(self, name, value, source="sqlite"):
        return {"label": "Queried overview / data snapshot" if name == "overview" else "Saved data snapshot",
                "isLive": False, "source": source, "releaseId": self.release_id,
                "snapshotAcquiredAt": self.metadata["acquisitionCompletedAt"], name: value}

    def encoded(self, model, value):
        payload = encode(model.model_validate(value).model_dump(mode="json"))
        if len(payload) > self.settings.max_response_bytes:
            raise ApiError(503, "RESPONSE_TOO_LARGE", "The response exceeds the checked size limit.")
        return payload

    def check_provenance(self, row):
        path = PurePosixPath(row["source_page"])
        if (path.is_absolute() or ".." in path.parts or "\\" in str(path)
                or row["source_page"] not in self.pages
                or not 1 <= row["source_index"] <= self.pages[row["source_page"]]):
            raise ValueError("Invalid report provenance.")

    def execute(self, kind, filters, token, *, limit=25, after=None, report_id=None):
        try:
            with repository.connection(self.database, token) as db:
                if kind == "overview":
                    payload = self.encoded(models.ExploreResponse, self.envelope("overview", explore(db, filters)))
                elif kind == "page":
                    found = repository.rows(db, filters, limit + 1, after)
                    items = [repository.summary(row) for row in found[:limit]]
                    more = len(found) > limit
                    cursor = make_cursor(self.release_id, filters, limit, items[-1]["reportId"]) if more else None
                    value = {**self.context(filters), "sort": "reportId:asc", "limit": limit,
                             "returnedCount": len(items), "items": items, "hasMore": more, "nextCursor": cursor}
                    payload = self.encoded(models.ReportsResponse, self.envelope("page", value))
                else:
                    found = repository.rows(db, filters, 1, report_id=report_id)
                    if not found:
                        raise ApiError(404, "REPORT_NOT_FOUND", "No matching report was found.")
                    self.check_provenance(found[0])
                    value = {**self.context(filters), "report": repository.detail(db, found[0], filters, token)}
                    payload = self.encoded(models.DetailResponse, self.envelope("detail", value))
                token.check()
                return payload
        except (sqlite3.DatabaseError, ValidationError, ValueError, OSError):
            self.ready = False
            raise
