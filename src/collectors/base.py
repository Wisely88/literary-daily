from __future__ import annotations

from typing import Protocol

from ..models import Candidate


class Collector(Protocol):
    name: str

    def collect(self, limit: int) -> list[Candidate]: ...
