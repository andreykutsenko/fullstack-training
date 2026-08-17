from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Status(str, Enum):
    OK = "OK"
    BROKEN = "BROKEN"
    SKIPPED = "SKIPPED"


class LinkKind(str, Enum):
    LOCAL = "local"
    EXTERNAL = "external"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class Link:
    source_file: Path
    line: int
    url: str


@dataclass(frozen=True)
class CheckOutcome:
    status: Status
    http_code: int | None = None
    note: str = ""


@dataclass(frozen=True)
class LinkResult:
    link: Link
    status: Status
    http_code: int | None = None
    note: str = ""

    @property
    def is_broken(self) -> bool:
        return self.status is Status.BROKEN

    @property
    def is_counted(self) -> bool:
        return self.status is not Status.SKIPPED
