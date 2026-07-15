from typing import Protocol


class _PluginContext(Protocol):
    ...


def register(_ctx: _PluginContext) -> None:
    return None
