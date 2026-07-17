from __future__ import annotations

from wsl_dev_doctor.cli import build_parser


def test_update_dry_run_is_explicit_and_non_mutating() -> None:
    args = build_parser().parse_args(["update", "--dry-run", "--tool", "uv"])
    assert args.apply is False
    assert args.dry_run is True
    assert args.tool == ["uv"]


def test_update_apply_requires_separate_confirmation_flag() -> None:
    args = build_parser().parse_args(["update", "--apply", "--yes", "--tool", "uv"])
    assert args.apply is True
    assert args.yes is True


def test_scan_defaults_remain_compatible() -> None:
    args = build_parser().parse_args([])
    assert args.subcommand is None
    assert args.format == "markdown"
