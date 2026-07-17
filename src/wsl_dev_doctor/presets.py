from __future__ import annotations

import os
from pathlib import Path

from wsl_dev_doctor.registry import BUILTIN_PRESETS, tool_by_id

try:
    import tomllib  # type: ignore[import-not-found]
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10 only
    import tomli as tomllib  # type: ignore[import-not-found]


def config_path() -> Path:
    root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / "wsl-dev-doctor" / "presets.toml"


def load_presets(path: Path | None = None) -> dict[str, tuple[str, ...]]:
    presets = dict(BUILTIN_PRESETS)
    source = path or config_path()
    if not source.exists():
        return presets
    data = tomllib.loads(source.read_text(encoding="utf-8"))
    for name, value in data.get("presets", {}).items():
        tools = value.get("tools") if isinstance(value, dict) else None
        if isinstance(tools, list) and all(
            isinstance(tool, str) and tool_by_id(tool) for tool in tools
        ):
            presets[name] = tuple(tools)
    return presets


def save_preset(name: str, tools: list[str], path: Path | None = None) -> Path:
    if not name.replace("-", "").replace("_", "").isalnum() or not name:
        raise ValueError(
            "Preset names must contain only letters, numbers, hyphens, and underscores."
        )
    unknown = [tool for tool in tools if tool_by_id(tool) is None]
    if unknown:
        raise ValueError(f"Unknown registered tools: {', '.join(unknown)}")
    target = path or config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    previous = tomllib.loads(target.read_text(encoding="utf-8")) if target.exists() else {}
    presets = previous.setdefault("presets", {})
    presets[name] = {"tools": tools}
    rows = ["# Custom WSL Dev Doctor update presets", ""]
    for preset_name in sorted(presets):
        rendered = ", ".join(f'"{tool}"' for tool in presets[preset_name]["tools"])
        rows.extend([f"[presets.{preset_name}]", f"tools = [{rendered}]", ""])
    target.write_text("\n".join(rows), encoding="utf-8")
    return target
