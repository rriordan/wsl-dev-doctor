from __future__ import annotations

from pathlib import Path

from wsl_dev_doctor.checks import CheckRunner, _subprocess_run, collect_checks


def test_collect_checks_flags_missing_wsl_and_docker() -> None:
    responses = {
        ("docker", "version", "--format", "{{.Server.Version}}"): (
            1,
            "",
            "Cannot connect to the Docker daemon",
        ),
        ("ss", "-ltnH"): (0, "LISTEN 0 4096 0.0.0.0:3000 0.0.0.0:*\n", ""),
    }

    def run(command: tuple[str, ...]) -> tuple[int, str, str]:
        return responses.get(command, (127, "", "not found"))

    checks = collect_checks(
        CheckRunner(run=run, exists=lambda path: path == Path("/usr/bin/python3")),
        environ={"PATH": "/usr/bin:/missing", "API_TOKEN": "secret"},
        proc_version="Linux host kernel",
        which=lambda command: "/usr/bin/python3" if command == "python3" else None,
        disk_usage=lambda path: (100, 80, 20),
    )

    by_id = {check.id: check for check in checks}
    assert by_id["platform.wsl"].status == "warn"
    assert by_id["docker"].status == "warn"
    assert by_id["environment"].details["sensitive_name_count"] == 1
    assert by_id["environment"].details["variable_names"] == ["API_TOKEN", "PATH"]
    assert by_id["ports"].details["tcp_listeners"] == ["0.0.0.0:3000"]


def test_collect_checks_recognizes_wsl_and_tools() -> None:
    def run(command: tuple[str, ...]) -> tuple[int, str, str]:
        if command == ("docker", "version", "--format", "{{.Server.Version}}"):
            return 0, "27.0.0\n", ""
        if command == ("nvidia-smi", "--query-gpu=name", "--format=csv,noheader"):
            return 0, "NVIDIA RTX\n", ""
        if command == ("ss", "-ltnH"):
            return 0, "", ""
        return 127, "", "not found"

    checks = collect_checks(
        CheckRunner(run=run, exists=lambda path: True),
        environ={"PATH": "/usr/bin:/opt/tools"},
        proc_version="Linux version 6.6.36.6-microsoft-standard-WSL2",
        which=lambda command: f"/usr/bin/{command}",
        disk_usage=lambda path: (100, 10, 90),
    )

    by_id = {check.id: check for check in checks}
    assert by_id["platform.wsl"].status == "pass"
    assert by_id["docker"].status == "pass"
    assert by_id["gpu"].details["gpus"] == ["NVIDIA RTX"]
    assert by_id["path"].status == "pass"


def test_check_runner_truncates_command_error() -> None:
    result = CheckRunner(
        run=lambda command: (1, "", "x" * 500),
        exists=lambda path: path.exists(),
    ).command(("nope",))
    assert result.error is not None
    assert len(result.error) == 300


def test_subprocess_runner_handles_missing_command() -> None:
    returncode, stdout, stderr = _subprocess_run(("wsl-doctor-command-that-does-not-exist",))

    assert returncode == 127
    assert stdout == ""
    assert stderr == "Command not found: wsl-doctor-command-that-does-not-exist"
