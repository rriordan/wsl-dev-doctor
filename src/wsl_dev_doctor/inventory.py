from __future__ import annotations

import shutil
import subprocess
from collections.abc import Callable
from dataclasses import asdict, dataclass

from wsl_dev_doctor.registry import TOOLS, ToolSpec

Which = Callable[[str], str | None]
Run = Callable[[tuple[str, ...]], tuple[int, str, str]]


@dataclass(frozen=True)
class ToolInventory:
    id: str
    command: str
    category: str
    status: str
    path: str | None
    version: str | None
    update_supported: bool
    update_scope: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _run(command: tuple[str, ...]) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=4)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 1, "", ""
    return completed.returncode, completed.stdout, completed.stderr


def _version(spec: ToolSpec, run: Run) -> str | None:
    code, stdout, stderr = run((spec.command, *spec.version_args))
    if code != 0:
        return None
    output = (stdout or stderr).strip().splitlines()
    return output[0][:200] if output else None


def collect_inventory(which: Which = shutil.which, run: Run = _run) -> list[ToolInventory]:
    inventory: list[ToolInventory] = []
    for spec in TOOLS:
        path = which(spec.command)
        inventory.append(
            ToolInventory(
                id=spec.id,
                command=spec.command,
                category=spec.category,
                status="present" if path else "not_present",
                path=path,
                version=_version(spec, run) if path else None,
                update_supported=spec.update_command is not None,
                update_scope=spec.update_scope,
            )
        )
    return inventory
