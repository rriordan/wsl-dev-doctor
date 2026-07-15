from __future__ import annotations

import os
import platform
import re
import shutil
import subprocess
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from wsl_dev_doctor.models import Check, Status

Command = tuple[str, ...]
CommandResult = tuple[int, str, str]
RunCommand = Callable[[Command], CommandResult]
Which = Callable[[str], str | None]
DiskUsage = Callable[[str], tuple[int, int, int]]

_TOOL_COMMANDS = ("python3", "uv", "node", "npm", "git", "docker", "bun")
_SECRET_NAME = re.compile(r"(?:key|token|secret|password|credential|auth)", re.IGNORECASE)


@dataclass(frozen=True)
class CommandOutcome:
    returncode: int
    stdout: str
    error: str | None


@dataclass(frozen=True)
class CheckRunner:
    run: RunCommand
    exists: Callable[[Path], bool]

    def command(self, command: Command) -> CommandOutcome:
        returncode, stdout, stderr = self.run(command)
        error = stderr.strip() or None
        if error is not None:
            error = error[:300]
        return CommandOutcome(returncode, stdout.strip(), error)


def _subprocess_run(command: Command) -> CommandResult:
    completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=5)
    return completed.returncode, completed.stdout, completed.stderr


def _check_wsl(proc_version: str) -> Check:
    is_wsl = "microsoft" in proc_version.lower() or "wsl" in proc_version.lower()
    if is_wsl:
        release = platform.release()
        return Check(
            id="platform.wsl",
            category="Platform",
            status="pass",
            summary="WSL environment detected.",
            details={"kernel_release": release},
        )
    return Check(
        id="platform.wsl",
        category="Platform",
        status="warn",
        summary="WSL was not detected; Linux diagnostics will still run.",
        remediation="Run this inside a WSL distribution to validate WSL-specific integration.",
    )


def _check_tools(which: Which) -> Check:
    found = {tool: which(tool) for tool in _TOOL_COMMANDS}
    missing_required = [tool for tool in ("python3", "git") if found[tool] is None]
    missing_optional = [
        tool for tool in ("uv", "node", "npm", "docker", "bun") if found[tool] is None
    ]
    if missing_required:
        return Check(
            id="toolchain",
            category="Toolchain",
            status="fail",
            summary=f"Required tools missing: {', '.join(missing_required)}.",
            remediation=(
                "Install the missing required tools with your distribution package manager."
            ),
            details={"found": found, "missing_optional": missing_optional},
        )
    status: Status = "warn" if missing_optional else "pass"
    summary = "Required development tools are available."
    if missing_optional:
        summary += f" Optional tools absent: {', '.join(missing_optional)}."
    return Check(
        id="toolchain",
        category="Toolchain",
        status=status,
        summary=summary,
        remediation=(
            "Install optional tools only if they match your workflow." if missing_optional else None
        ),
        details={"found": found, "missing_optional": missing_optional},
    )


def _check_path(environ: Mapping[str, str], exists: Callable[[Path], bool]) -> Check:
    entries = [entry for entry in environ.get("PATH", "").split(os.pathsep) if entry]
    missing = [entry for entry in entries if not exists(Path(entry))]
    status: Status = "warn" if missing else "pass"
    return Check(
        id="path",
        category="Environment",
        status=status,
        summary=(
            f"PATH contains {len(missing)} nonexistent entr{'y' if len(missing) == 1 else 'ies'}."
            if missing
            else "PATH entries exist."
        ),
        remediation=(
            "Remove or correct stale PATH entries in your shell configuration." if missing else None
        ),
        details={"entry_count": len(entries), "missing_entries": missing},
    )


def _check_environment(environ: Mapping[str, str]) -> Check:
    names = sorted(environ)
    sensitive = [name for name in names if _SECRET_NAME.search(name)]
    return Check(
        id="environment",
        category="Environment",
        status="info",
        summary="Environment variable names inventoried; values were not read or reported.",
        details={"variable_names": names, "sensitive_name_count": len(sensitive)},
    )


def _check_disk(disk_usage: DiskUsage) -> Check:
    total, used, free = disk_usage("/")
    percent_used = round((used / total) * 100) if total else 0
    status: Status = "warn" if percent_used >= 85 else "pass"
    return Check(
        id="disk",
        category="Storage",
        status=status,
        summary=f"Root filesystem is {percent_used}% used.",
        remediation=(
            "Free disk space before builds, container pulls, or model downloads fail."
            if status == "warn"
            else None
        ),
        details={
            "total_bytes": total,
            "used_bytes": used,
            "free_bytes": free,
            "percent_used": percent_used,
        },
    )


def _check_docker(runner: CheckRunner) -> Check:
    outcome = runner.command(("docker", "version", "--format", "{{.Server.Version}}"))
    if outcome.returncode == 0 and outcome.stdout:
        return Check(
            id="docker",
            category="Containers",
            status="pass",
            summary=f"Docker daemon available (server {outcome.stdout}).",
        )
    return Check(
        id="docker",
        category="Containers",
        status="warn",
        summary="Docker daemon is unavailable.",
        remediation=(
            "Start Docker Desktop and enable WSL integration, or install/start Docker Engine "
            "in this distribution."
        ),
        details={"error": outcome.error},
    )


def _check_ports(runner: CheckRunner) -> Check:
    outcome = runner.command(("ss", "-ltnH"))
    if outcome.returncode != 0:
        return Check(
            id="ports",
            category="Network",
            status="info",
            summary="Could not inventory listening TCP ports.",
            details={"error": outcome.error},
        )
    listeners = [line.split()[3] for line in outcome.stdout.splitlines() if len(line.split()) >= 4]
    return Check(
        id="ports",
        category="Network",
        status="info",
        summary=f"Found {len(listeners)} listening TCP port(s).",
        details={"tcp_listeners": listeners[:50], "truncated": len(listeners) > 50},
    )


def _check_gpu(runner: CheckRunner) -> Check:
    outcome = runner.command(("nvidia-smi", "--query-gpu=name", "--format=csv,noheader"))
    if outcome.returncode == 0 and outcome.stdout:
        gpus = [line.strip() for line in outcome.stdout.splitlines() if line.strip()]
        return Check(
            id="gpu",
            category="GPU",
            status="pass",
            summary=f"NVIDIA GPU visible: {', '.join(gpus)}.",
            details={"gpus": gpus},
        )
    return Check(
        id="gpu",
        category="GPU",
        status="info",
        summary="No NVIDIA GPU was visible through nvidia-smi.",
        remediation=(
            "If GPU compute is expected, install a current Windows NVIDIA driver with WSL "
            "support and restart WSL."
        ),
        details={"error": outcome.error},
    )


def collect_checks(
    runner: CheckRunner | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    proc_version: str | None = None,
    which: Which = shutil.which,
    disk_usage: DiskUsage = shutil.disk_usage,
) -> list[Check]:
    active_runner = runner or CheckRunner(run=_subprocess_run, exists=Path.exists)
    active_environ = environ if environ is not None else os.environ
    active_proc_version = proc_version
    if active_proc_version is None:
        try:
            active_proc_version = Path("/proc/version").read_text(encoding="utf-8")
        except OSError:
            active_proc_version = platform.platform()
    return [
        _check_wsl(active_proc_version),
        _check_tools(which),
        _check_path(active_environ, active_runner.exists),
        _check_environment(active_environ),
        _check_disk(disk_usage),
        _check_docker(active_runner),
        _check_ports(active_runner),
        _check_gpu(active_runner),
    ]
