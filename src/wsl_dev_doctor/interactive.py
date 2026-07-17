from __future__ import annotations

import curses
from collections.abc import Sequence

from wsl_dev_doctor.inventory import ToolInventory


def select_tools(inventory: Sequence[ToolInventory]) -> list[str]:
    eligible = [tool for tool in inventory if tool.status == "present" and tool.update_supported]
    if not eligible:
        return []
    return curses.wrapper(_selector, eligible)


def _selector(screen: curses.window, tools: Sequence[ToolInventory]) -> list[str]:
    cursor = 0
    selected = {tool.id for tool in tools if tool.update_scope == "dedicated"}
    while True:
        screen.erase()
        screen.addstr(0, 0, "WSL Dev Doctor — select detected tools to update")
        screen.addstr(
            1, 0, "Up/Down navigate  Space toggle  a select all  Enter continue  q cancel"
        )
        for index, tool in enumerate(tools):
            marker = "[x]" if tool.id in selected else "[ ]"
            prefix = "> " if index == cursor else "  "
            screen.addstr(index + 3, 0, f"{prefix}{marker} {tool.command} ({tool.update_scope})")
        key = screen.getch()
        if key in (ord("q"), 27):
            return []
        if key in (curses.KEY_UP, ord("k")):
            cursor = (cursor - 1) % len(tools)
        elif key in (curses.KEY_DOWN, ord("j")):
            cursor = (cursor + 1) % len(tools)
        elif key == ord(" "):
            tool_id = tools[cursor].id
            selected.symmetric_difference_update({tool_id})
        elif key == ord("a"):
            selected = {tool.id for tool in tools}
        elif key in (10, 13, curses.KEY_ENTER):
            return [tool.id for tool in tools if tool.id in selected]
