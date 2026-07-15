from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone

from wsl_dev_doctor.models import Check, Report

_STATUS_ICON = {"pass": "✅", "warn": "⚠️", "fail": "❌", "info": "ℹ️"}


def build_report(checks: list[Check], generated_at: str | None = None) -> Report:
    counts = Counter(check.status for check in checks)
    summary = {status: counts[status] for status in ("pass", "warn", "fail", "info")}
    timestamp = generated_at or datetime.now(timezone.utc).isoformat(timespec="seconds")
    return Report(generated_at=timestamp, checks=checks, summary=summary)


def render_json(report: Report) -> str:
    return json.dumps(report.to_dict(), indent=2, sort_keys=True) + "\n"


def render_markdown(report: Report) -> str:
    lines = [
        "# WSL Dev Environment Doctor Report",
        "",
        f"Generated: `{report.generated_at}`",
        "",
        "## Summary",
        "",
        f"- ✅ Pass: {report.summary['pass']}",
        f"- ⚠️ Warnings: {report.summary['warn']}",
        f"- ❌ Failures: {report.summary['fail']}",
        f"- ℹ️ Informational: {report.summary['info']}",
        "",
        "## Checks",
        "",
        "| Status | Category | Check | Result |",
        "| --- | --- | --- | --- |",
    ]
    for check in report.checks:
        lines.append(
            f"| {_STATUS_ICON[check.status]} {check.status.upper()} | {check.category} "
            f"| `{check.id}` | {check.summary} |"
        )

    remediations = [
        check for check in report.checks if check.remediation and check.status in {"fail", "warn"}
    ]
    if remediations:
        lines.extend(["", "## Prioritized remediation", ""])
        for index, check in enumerate(remediations, start=1):
            lines.append(f"{index}. **{check.id}** — {check.remediation}")

    lines.extend(
        [
            "",
            "## Privacy note",
            "",
            "This report is read-only. Environment-variable values, shell history, credentials, "
            "and configuration files are not collected.",
            "",
        ]
    )
    return "\n".join(lines)
