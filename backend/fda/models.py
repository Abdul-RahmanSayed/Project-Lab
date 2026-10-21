"""Executable public response schemas, also used to validate prepared bytes."""

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator


Count = Annotated[int, Field(ge=0, strict=True)]
Age = Annotated[FiniteFloat, Field(ge=0, le=125)]
ReleaseId = Annotated[str, Field(pattern=r"^fda-release-sha256:[0-9a-f]{64}$")]
Gender = Literal["Female", "Male", "Unknown"]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Filters(Model):
    startYear: int
    endYear: int
    productFilter: str | None


class MetadataQuery(Model):
    releaseId: ReleaseId | None = None


class SelectionQuery(MetadataQuery):
    startYear: Annotated[str, Field(pattern=r"^[0-9]{4}$")] | None = None
    endYear: Annotated[str, Field(pattern=r"^[0-9]{4}$")] | None = None
    productFilter: Annotated[str, Field(min_length=1, max_length=256)] | None = None


class ReportsQuery(SelectionQuery):
    limit: Annotated[int, Field(ge=1, le=100)] = 25
    sort: Literal["reportId:asc"] = "reportId:asc"
    cursor: Annotated[str, Field(min_length=1, max_length=2048)] | None = None


class DetailQuery(SelectionQuery):
    reportId: Annotated[str, Field(min_length=1, max_length=512)]


class Snapshot(Model):
    datasetId: str
    policyVersion: str
    coverageNotes: list[str]


class Selection(Snapshot):
    appliedFilters: Filters


class Means(Model):
    total: Age | None
    female: Age | None
    male: Age | None


class Rankings(Model):
    products: list[tuple[str, Count]]
    outcomes: list[tuple[str, Count]]
    reactions: list[tuple[str, Count]]


class Overview(Selection):
    selectedCount: Count
    validAgeCount: Count
    missingAgeCount: Count
    ageMeans: Means
    yearCounts: list[tuple[int, Count]]
    ageHistogram: list[tuple[int, Count]]
    genderCounts: list[tuple[Gender, Count]]
    rankings: Rankings

    @model_validator(mode="after")
    def coherent(self):
        if self.selectedCount != self.validAgeCount + self.missingAgeCount:
            raise ValueError("Inconsistent age counts.")
        years = list(range(self.appliedFilters.startYear, self.appliedFilters.endYear + 1))
        for pairs, labels, total in ((self.yearCounts, years, self.selectedCount),
                                    (self.ageHistogram, list(range(126)), self.validAgeCount),
                                    (self.genderCounts, ["Female", "Male", "Unknown"], self.selectedCount)):
            if [key for key, _ in pairs] != labels or sum(count for _, count in pairs) != total:
                raise ValueError("Inconsistent ordered counts.")
        for pairs in (self.rankings.products, self.rankings.outcomes, self.rankings.reactions):
            if (len(pairs) > 25 or len({key for key, _ in pairs}) != len(pairs)
                    or pairs != sorted(pairs, key=lambda pair: (-pair[1], pair[0]))
                    or any(count > self.selectedCount for _, count in pairs)):
                raise ValueError("Inconsistent ranking.")
        return self


class Envelope(Model):
    label: str
    isLive: Literal[False]
    releaseId: ReleaseId
    snapshotAcquiredAt: str


class ExploreResponse(Envelope):
    source: Literal["prepared-default", "sqlite"]
    overview: Overview


class Summary(Model):
    reportId: str
    eventDate: date
    year: int
    ageYears: Age | None
    gender: Gender


class Page(Selection):
    sort: Literal["reportId:asc"]
    limit: Annotated[int, Field(ge=1, le=100)]
    returnedCount: Count
    items: list[Summary]
    hasMore: bool
    nextCursor: Annotated[str, Field(max_length=2048)] | None

    @model_validator(mode="after")
    def coherent(self):
        ids = [row.reportId for row in self.items]
        if (len(ids) != self.returnedCount or len(ids) > self.limit or ids != sorted(set(ids))
                or self.hasMore != (self.nextCursor is not None)):
            raise ValueError("Inconsistent page.")
        return self


class ReportsResponse(Envelope):
    source: Literal["sqlite"]
    page: Page


class Product(Model):
    ordinal: Count
    rawName: str
    role: str
    canonicalTerm: str | None
    displayLabel: str | None
    disclosure: str | None
    matchesProductFilter: bool | None


class Provenance(Model):
    sourcePage: str
    sourceIndex: Annotated[int, Field(ge=1)]


class Report(Summary):
    products: list[Product]
    suspectProductsCanonical: list[str]
    reactionsCanonical: list[str]
    outcomesCanonical: list[str]
    provenance: Provenance


class Detail(Selection):
    report: Report


class DetailResponse(Envelope):
    source: Literal["sqlite"]
    detail: Detail


class Metadata(Snapshot):
    interpretationNotes: list[str]
    coreVersion: str
    schemaVersion: int
    schemaHash: str
    queryHash: str
    sourceRevision: str
    revisionKind: str
    reportCount: Count
    uniqueReportCount: Count
    pageCount: Count
    coverageStart: date
    coverageEnd: date
    defaultFilters: Filters
    supportedFilters: list[str]
    supportedSorts: list[str]
    limits: dict[str, int]
    termDisplayOverrides: list[dict[str, str | None]]


class MetadataResponse(Envelope):
    source: Literal["prepared-metadata"]
    metadata: Metadata


class ErrorBody(Model):
    code: str
    message: str
    details: list[dict[str, str]]
    retryable: bool


class ErrorResponse(Model):
    error: ErrorBody
    requestId: str
