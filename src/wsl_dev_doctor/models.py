from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

Status = Literal["pass", "warn", "fail", "info"]


@dataclass(frozen=True)
class Check:
    id: str
    category: str
    status: Status
    summary: str
    remediation: str | None = None
    details: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class Report:
    generated_at: str
    checks: list[Check]
    summary: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at,
            "summary": self.summary,
            "checks": [check.to_dict() for check in self.checks],
        }
