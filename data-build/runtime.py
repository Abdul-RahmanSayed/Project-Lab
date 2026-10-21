"""Read a checked release; reuse only its exact prepared default selection."""

import hashlib
import json
from pathlib import Path

from common import sha256_file
from prepare import validate_release
from query import explore, open_database


def encode(value):
    return json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode("utf-8")


class OverviewRuntime:
    def __init__(self, release_directory):
        self._root = Path(release_directory).resolve()
        release = validate_release(self._root)

        def checked_json(name):
            payload = (self._root / name).read_bytes()
            expected = release["files"][name]
            if len(payload) != expected["bytes"] or hashlib.sha256(payload).hexdigest() != expected["sha256"]:
                raise ValueError("Release changed while loading: " + name)
            return json.loads(payload)

        self._metadata = checked_json("metadata.json")
        saved = checked_json("saved-overview.json")
        if sha256_file(Path(__file__).with_name("query.py")) != self._metadata["queryHash"]:
            raise ValueError("Query code differs from the release; prepare a new checked release.")
        self._default_filters = dict(saved["overview"]["appliedFilters"])
        self._default_payload = self._response(saved["overview"], "prepared-default", saved["label"])

    @property
    def release_id(self):
        return self._metadata["releaseId"]

    @property
    def default_filters(self):
        return dict(self._default_filters)

    def describe(self):
        return {"releaseId": self.release_id, "datasetId": self._metadata["datasetId"],
                "policyVersion": self._metadata["policyVersion"], "schemaHash": self._metadata["schemaHash"],
                "queryHash": self._metadata["queryHash"], "preparedEntryCount": 1,
                "preparedPayloadBytes": len(self._default_payload), "filteredResponseCache": False,
                "evictions": 0, "evictionApplicable": False,
                "runtimeConcurrencyLimit": None, "inflightCoalescing": False}

    def _response(self, overview, source, label):
        return encode({"label": label, "isLive": False, "source": source,
                       "releaseId": self.release_id,
                       "snapshotAcquiredAt": self._metadata["acquisitionCompletedAt"], "overview": overview})

    def _validated_filters(self, filters):
        if not isinstance(filters, dict) or set(filters) != {"startYear", "endYear", "productFilter"}:
            raise ValueError("Expected startYear, endYear, and productFilter only.")
        filters = dict(filters)
        start, end, product = filters["startYear"], filters["endYear"], filters["productFilter"]
        if type(start) is not int or type(end) is not int or not (
                self._default_filters["startYear"] <= start <= end <= self._default_filters["endYear"]):
            raise ValueError("Year range is outside the snapshot or reversed.")
        if product is not None and (not isinstance(product, str) or not product.strip()):
            raise ValueError("Product search must be nonblank text or None.")
        return filters

    def read(self, filters):
        filters = self._validated_filters(filters)
        if filters == self._default_filters:
            # Immutable bytes can be shared without cross-request mutations or JSON re-encoding.
            return self._default_payload
        connection = open_database(self._root / "fda.sqlite3")
        try:
            return self._response(explore(connection, filters), "sqlite", "Queried overview / data snapshot")
        finally:
            connection.close()
