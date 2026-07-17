from __future__ import annotations

from pathlib import Path

import pytest

from wsl_dev_doctor.presets import load_presets, save_preset


def test_builtin_presets_are_available() -> None:
    assert "ai-dev" in load_presets(Path("/tmp/does-not-exist"))


def test_custom_preset_round_trip(tmp_path: Path) -> None:
    target = tmp_path / "presets.toml"
    save_preset("my-stack", ["claude", "codex", "uv"], target)
    assert load_presets(target)["my-stack"] == ("claude", "codex", "uv")


def test_custom_preset_rejects_unknown_tool(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown registered tools"):
        save_preset("bad", ["does-not-exist"], tmp_path / "presets.toml")
