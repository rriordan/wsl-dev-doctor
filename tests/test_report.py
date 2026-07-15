from __future__ import annotations

import json

from wsl_dev_doctor.models import Check
from wsl_dev_doctor.report import build_report, render_json, render_markdown


def test_report_renders_remediation_and_machine_readable_data() -> None:
    report = build_report(
        [
            Check(
                id="docker",
                category="Containers",
                status="warn",
                summary="Docker daemon is unavailable.",
                remediation="Start Docker Desktop and enable WSL integration.",
            ),
            Check(
                id="python",
                category="Toolchain",
                status="pass",
                summary="python3 found.",
            ),
        ],
        generated_at="2026-07-15T00:00:00+00:00",
    )

    markdown = render_markdown(report)
    data = json.loads(render_json(report))

    assert "## Prioritized remediation" in markdown
    assert "Start Docker Desktop" in markdown
    assert data["summary"] == {"pass": 1, "warn": 1, "fail": 0, "info": 0}
    assert data["checks"][0]["id"] == "docker"
