from __future__ import annotations

from wsl_dev_doctor.inventory import collect_inventory


def test_inventory_reports_present_and_not_present_without_health_status() -> None:
    def which(command: str) -> str | None:
        return "/usr/bin/pnpm" if command == "pnpm" else None

    def run(command: tuple[str, ...]) -> tuple[int, str, str]:
        assert command == ("pnpm", "--version")
        return 0, "9.0.0\n", ""

    inventory = collect_inventory(which=which, run=run)
    by_id = {tool.id: tool for tool in inventory}

    assert by_id["pnpm"].status == "present"
    assert by_id["pnpm"].version == "9.0.0"
    assert by_id["terraform"].status == "not_present"
    assert by_id["terraform"].path is None
    assert len(inventory) >= 50


def test_inventory_keeps_present_tool_when_version_fails() -> None:
    inventory = collect_inventory(
        which=lambda command: "/usr/bin/terraform" if command == "terraform" else None,
        run=lambda command: (1, "", "unsupported"),
    )
    terraform = next(tool for tool in inventory if tool.id == "terraform")
    assert terraform.status == "present"
    assert terraform.version is None
