from __future__ import annotations

from wsl_dev_doctor.inventory import ToolInventory
from wsl_dev_doctor.updater import build_update_plan, execute_update_plan


def _tool(tool_id: str, status: str = "present") -> ToolInventory:
    return ToolInventory(
        id=tool_id,
        command=tool_id,
        category="Test",
        status=status,
        path=f"/bin/{tool_id}" if status == "present" else None,
        version="1.0" if status == "present" else None,
        update_supported=True,
        update_scope="dedicated",
    )


def test_update_plan_gates_global_js_and_skips_missing_tools() -> None:
    plans = build_update_plan(
        [_tool("uv"), _tool("pnpm"), _tool("claude", "not_present")], ["uv", "pnpm", "claude"]
    )
    assert [plan.status for plan in plans] == ["planned", "gated", "skipped"]
    assert plans[0].command == ("uv", "self", "update")


def test_update_plan_allows_explicit_global_js_opt_in() -> None:
    plan = build_update_plan([_tool("pnpm")], ["pnpm"], include_global_js=True)[0]
    assert plan.status == "planned"
    assert plan.command == ("pnpm", "update", "--global")


def test_update_plan_gates_and_allows_system_package_updates() -> None:
    gated = build_update_plan([_tool("apt")], ["apt"])[0]
    allowed = build_update_plan([_tool("apt")], ["apt"], include_system=True)[0]

    assert gated.status == "gated"
    assert allowed.status == "planned"
    assert allowed.command == ("sudo", "apt-get", "upgrade", "--yes")


def test_execute_plan_reports_each_result() -> None:
    plan = build_update_plan([_tool("uv")], ["uv"])
    results = execute_update_plan(plan, run=lambda command: (0, "updated\n", ""))
    assert results[0].status == "updated"
    assert results[0].reason == "updated"
