"""Exact URL parsing and unsigned public-data pagination bookmarks."""

import base64
import json
import re
from urllib.parse import parse_qsl

from common import content_hash

from backend.errors import ApiError


def invalid(message="The request contains an invalid parameter."):
    return ApiError(422, "INVALID_PARAMETER", message)


def parameters(request, allowed):
    raw = request.scope["query_string"]
    try:
        text = raw.decode("ascii")
        if re.search(r"%(?![0-9a-fA-F]{2})", text):
            raise ValueError("Invalid percent encoding")
        pairs = parse_qsl(text, keep_blank_values=True, encoding="utf-8", errors="strict", max_num_fields=16)
    except (ValueError, UnicodeError):
        raise invalid() from None
    if any(key not in allowed for key, _ in pairs) or len({key for key, _ in pairs}) != len(pairs):
        raise invalid("Unknown or repeated parameters are not supported.")
    return dict(pairs)


def checked_release(params, active):
    value = params.get("releaseId", active)
    if not re.fullmatch(r"fda-release-sha256:[0-9a-f]{64}", value):
        raise invalid("Invalid release identifier.")
    if value != active:
        raise ApiError(409, "RELEASE_MISMATCH", "The snapshot changed; restart with its current metadata.")


def filters(params, defaults):
    result = {}
    for name in ("startYear", "endYear"):
        value = params.get(name, str(defaults[name]))
        if not re.fullmatch(r"[0-9]{4}", value):
            raise invalid("Years must have four ASCII digits.")
        result[name] = int(value)
    if not defaults["startYear"] <= result["startYear"] <= result["endYear"] <= defaults["endYear"]:
        raise invalid("The year range is reversed or outside the saved snapshot.")
    product = params.get("productFilter")
    if product is not None and (not product.strip() or len(product) > 256 or len(product.encode("utf-8")) > 1024):
        raise invalid("Product search must be nonblank and within the documented size limit.")
    return {**result, "productFilter": product}


def identifier(value):
    if not isinstance(value, str) or not value or len(value.encode("utf-8")) > 512:
        raise invalid("A report identifier is required and must fit the documented size limit.")
    return value


def page_limit(params):
    value = params.get("limit", "25")
    if not re.fullmatch(r"[0-9]{1,3}", value) or not 1 <= int(value) <= 100:
        raise invalid("Page size must be between 1 and 100.")
    if params.get("sort", "reportId:asc") != "reportId:asc":
        raise invalid("Only reportId:asc sorting is supported.")
    return int(value)


def make_cursor(release, selection, limit, after):
    payload = {"v": 1, "release": release, "selection": content_hash(selection),
               "limit": limit, "sort": "reportId:asc", "after": after}
    return _encode_cursor(payload)


def _encode_cursor(payload):
    return base64.urlsafe_b64encode(json.dumps(payload, sort_keys=True, ensure_ascii=True,
                                             separators=(",", ":"), allow_nan=False).encode()).rstrip(b"=").decode()


def _unique(pairs):
    if len({key for key, _ in pairs}) != len(pairs):
        raise ValueError("Repeated fields")
    return dict(pairs)


def read_cursor(value, release, selection, limit):
    if value is None:
        return None
    try:
        if len(value) > 2048 or not re.fullmatch(r"[A-Za-z0-9_-]+", value):
            raise ValueError("Invalid token")
        raw = base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique)
        if (not isinstance(payload, dict) or set(payload) != {"v", "release", "selection", "limit", "sort", "after"}
                or type(payload["v"]) is not int or payload["v"] != 1 or type(payload["limit"]) is not int
                or not all(isinstance(payload[key], str) for key in ("release", "selection", "sort", "after"))):
            raise ValueError("Invalid payload")
        identifier(payload["after"])
        if _encode_cursor(payload) != value:
            raise ValueError("Noncanonical token")
    except (ValueError, UnicodeError, TypeError, KeyError, ApiError):
        raise ApiError(400, "INVALID_CURSOR", "The next-page bookmark is malformed.") from None
    if payload["release"] != release:
        raise ApiError(409, "RELEASE_MISMATCH", "The bookmark belongs to a different snapshot.")
    if payload["selection"] != content_hash(selection) or payload["limit"] != limit or payload["sort"] != "reportId:asc":
        raise ApiError(409, "CURSOR_CONTEXT_MISMATCH", "Filters or page settings changed; restart at page one.")
    return payload["after"]
