from importlib import import_module
from typing import Callable

from tool_definitions import AVAILABLE_TOOLS


def _load_tool_functions() -> dict[str, Callable]:
    functions = {}
    for definition in AVAILABLE_TOOLS:
        tool_name = definition["function"]["name"]
        module = import_module(tool_name)
        function = getattr(module, tool_name, None)
        if not callable(function):
            raise RuntimeError(
                f"Tool '{tool_name}' must be implemented as "
                f"'{tool_name}.{tool_name}'."
            )
        functions[tool_name] = function
    return functions


TOOL_FUNCTIONS = _load_tool_functions()
