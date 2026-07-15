from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from wsl_dev_doctor.checks import collect_checks
from wsl_dev_doctor.report import build_report, render_json, render_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wsl-doctor",
        description="Run safe, read-only diagnostics for a WSL/Linux development environment.",
    )
    parser.add_argument(
        "--format", choices=("markdown", "json"), default="markdown", help="Report format."
    )
    parser.add_argument(
        "--output", default="wsl-doctor-report.md", help="Output file path, or '-' for stdout."
    )
    parser.add_argument(
        "--fail-on",
        choices=("never", "warn", "fail"),
        default="never",
        help="Return status 1 when warning/failure thresholds are met.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_report(collect_checks())
    content = render_json(report) if args.format == "json" else render_markdown(report)
    if args.output == "-":
        print(content, end="")
    else:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        print(f"Report written to {output}")

    if args.fail_on == "warn" and (report.summary["warn"] or report.summary["fail"]):
        return 1
    if args.fail_on == "fail" and report.summary["fail"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
