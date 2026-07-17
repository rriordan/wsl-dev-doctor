from __future__ import annotations

import subprocess
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass

from wsl_dev_doctor.inventory import ToolInventory
from wsl_dev_doctor.registry import tool_by_id

Run = Callable[[tuple[str, ...]], tuple[int, str, str]]


@dataclass(frozen=True)
class UpdatePlan:
    tool_id: str
    command: tuple[str, ...]
    status: str
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _eligible(
    scope: str | None, include_system: bool, include_global_js: bool, include_homebrew: bool
) -> bool:
    return (
        scope == "dedicated"
        or (scope == "system" and include_system)
        or (scope == "global_js" and include_global_js)
        or (scope == "homebrew" and include_homebrew)
    )


def build_update_plan(
    inventory: Iterable[ToolInventory],
    selected_ids: Iterable[str],
    *,
    include_system: bool = False,
    include_global_js: bool = False,
    include_homebrew: bool = False,
) -> list[UpdatePlan]:
    by_id = {tool.id: tool for tool in inventory}
    plans: list[UpdatePlan] = []
    for tool_id in dict.fromkeys(selected_ids):
        spec = tool_by_id(tool_id)
        discovered = by_id.get(tool_id)
        if spec is None:
            plans.append(UpdatePlan(tool_id, (), "skipped", "Unknown registered tool."))
        elif discovered is None or discovered.status != "present":
            plans.append(UpdatePlan(tool_id, (), "skipped", "Tool is not present."))
        elif spec.update_command is None:
            plans.append(UpdatePlan(tool_id, (), "skipped", "No supported updater."))
        elif not _eligible(spec.update_scope, include_system, include_global_js, include_homebrew):
            plans.append(
                UpdatePlan(
                    tool_id,
                    spec.update_command,
                    "gated",
                    f"Requires explicit opt-in for {spec.update_scope} updates.",
                )
            )
        else:
            plans.append(
                UpdatePlan(tool_id, spec.update_command, "planned", "Safe dedicated updater.")
            )
    return plans


def execute_update_plan(plans: Iterable[UpdatePlan], run: Run | None = None) -> list[UpdatePlan]:
    active_run = run or _run
    results: list[UpdatePlan] = []
    for plan in plans:
        if plan.status != "planned":
            results.append(plan)
            continue
        code, stdout, stderr = active_run(plan.command)
        detail = (stdout or stderr).strip()[:300]
        results.append(
            UpdatePlan(
                plan.tool_id,
                plan.command,
                "updated" if code == 0 else "failed",
                detail or f"Exit {code}.",
            )
        )
    return results


def _run(command: tuple[str, ...]) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            command, capture_output=True, text=True, check=False, timeout=300
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as error:
        return 1, "", str(error)
    return completed.returncode, completed.stdout, completed.stderr


def render_plan(plans: Iterable[UpdatePlan]) -> str:
    lines = ["# WSL Dev Doctor update plan", ""]
    for plan in plans:
        command = " ".join(plan.command) if plan.command else "—"
        lines.append(f"- **{plan.tool_id}**: `{plan.status}` — `{command}` — {plan.reason}")
    return "\n".join(lines) + "\n"
