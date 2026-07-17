from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from wsl_dev_doctor.checks import collect_checks
from wsl_dev_doctor.interactive import select_tools
from wsl_dev_doctor.inventory import collect_inventory
from wsl_dev_doctor.presets import load_presets, save_preset
from wsl_dev_doctor.report import build_report, render_json, render_markdown
from wsl_dev_doctor.updater import build_update_plan, execute_update_plan, render_plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wsl-doctor",
        description="Safe WSL/Linux developer-environment diagnostics and controlled updater.",
    )
    _add_scan_arguments(parser)
    subparsers = parser.add_subparsers(dest="subcommand")

    update = subparsers.add_parser("update", help="Plan or apply updates for detected tools.")
    update.add_argument(
        "--tool", action="append", default=[], help="Registered tool ID to include."
    )
    update.add_argument("--preset", help="Built-in or custom preset to include.")
    update.add_argument(
        "--interactive",
        action="store_true",
        help="Select detected updateable tools in a terminal UI.",
    )
    update.add_argument(
        "--dry-run",
        action="store_true",
        help="Explicitly print the plan without making changes (the default).",
    )
    update.add_argument("--apply", action="store_true", help="Execute the selected update plan.")
    update.add_argument(
        "--yes", action="store_true", help="Confirm non-interactive execution with --apply."
    )
    update.add_argument("--include-system-packages", action="store_true")
    update.add_argument("--include-global-js-packages", action="store_true")
    update.add_argument("--include-homebrew", action="store_true")
    update.add_argument("--format", choices=("markdown", "json"), default="markdown")
    update.add_argument("--output", default="-", help="Output path, or '-' for stdout.")

    preset = subparsers.add_parser("preset", help="List, show, or save update presets.")
    preset_subparsers = preset.add_subparsers(dest="preset_command", required=True)
    preset_subparsers.add_parser("list", help="List available presets.")
    show = preset_subparsers.add_parser("show", help="Show tools in a preset.")
    show.add_argument("name")
    save = preset_subparsers.add_parser("save", help="Save a custom preset of registered tools.")
    save.add_argument("name")
    save.add_argument("--tool", action="append", required=True)
    return parser


def _add_scan_arguments(parser: argparse.ArgumentParser) -> None:
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


def _write(content: str, output: str) -> None:
    if output == "-":
        print(content, end="")
        return
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"Report written to {path}")


def _scan(args: argparse.Namespace) -> int:
    report = build_report(collect_checks(), collect_inventory())
    _write(render_json(report) if args.format == "json" else render_markdown(report), args.output)
    if args.fail_on == "warn" and (report.summary["warn"] or report.summary["fail"]):
        return 1
    return int(args.fail_on == "fail" and bool(report.summary["fail"]))


def _update(args: argparse.Namespace) -> int:
    if args.dry_run and args.apply:
        raise ValueError("--dry-run and --apply cannot be used together.")
    inventory = collect_inventory()
    selected = list(args.tool)
    presets = load_presets()
    if args.preset:
        if args.preset not in presets:
            raise ValueError(f"Unknown preset: {args.preset}")
        selected.extend(presets[args.preset])
    if args.interactive:
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            raise ValueError("--interactive requires a TTY terminal.")
        selected.extend(select_tools(inventory))
    if not selected:
        selected = [tool.id for tool in inventory if tool.update_supported]
    plan = build_update_plan(
        inventory,
        selected,
        include_system=args.include_system_packages,
        include_global_js=args.include_global_js_packages,
        include_homebrew=args.include_homebrew,
    )
    results = plan
    if args.apply:
        if not args.yes:
            raise ValueError("--apply requires --yes after reviewing a dry-run plan.")
        if args.interactive:
            print(render_plan(plan), end="")
            if input("Apply this update plan? [y/N] ").strip().lower() not in {"y", "yes"}:
                print("Update cancelled.")
                return 0
        results = execute_update_plan(plan)
    if args.format == "json":
        content = json.dumps([item.to_dict() for item in results], indent=2) + "\n"
    else:
        content = render_plan(results)
    _write(content, args.output)
    return int(any(item.status == "failed" for item in results))


def _preset(args: argparse.Namespace) -> int:
    if args.preset_command == "save":
        print(f"Preset saved to {save_preset(args.name, args.tool)}")
        return 0
    presets = load_presets()
    if args.preset_command == "list":
        for name in sorted(presets):
            print(name)
        return 0
    if args.name not in presets:
        raise ValueError(f"Unknown preset: {args.name}")
    print("\n".join(presets[args.name]))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.subcommand == "update":
            return _update(args)
        if args.subcommand == "preset":
            return _preset(args)
        return _scan(args)
    except ValueError as error:
        parser.error(str(error))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
