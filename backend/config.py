"""Trusted local settings, never selected by an HTTP caller."""

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    release_directory: Path
    expected_release_id: str
    sql_jobs: int = 5
    request_seconds: float = 30
    max_response_bytes: int = 1024 * 1024
    allowed_origins: tuple[str, ...] = ()

    def __post_init__(self):
        if not 1 <= self.sql_jobs <= 5 or self.request_seconds <= 0 or self.max_response_bytes <= 0:
            raise ValueError("Invalid resource settings.")

    @classmethod
    def from_environment(cls):
        return cls(Path(os.environ["FDA_RELEASE_DIRECTORY"]), os.environ["FDA_RELEASE_ID"],
                   allowed_origins=tuple(filter(None, os.environ.get("FDA_ALLOWED_ORIGINS", "").split(","))))
