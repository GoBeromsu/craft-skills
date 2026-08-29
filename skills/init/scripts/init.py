"""Public dispatcher for the init lifecycle commands."""

from __future__ import annotations

import argparse
import importlib
import sys
from collections.abc import Sequence
from types import ModuleType


OPERATIONS = ("map", "audit", "prune")
LEGACY_FLAGS = ("--create-new", "--max-depth", "--map", "--audit", "--prune", "--operation")


def _parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog="init.py",
        usage="%(prog)s [map|audit|prune] [arguments ...]",
        description="Run an init lifecycle operation; omitting it selects map.",
    )


def _load_operation(operation: str) -> ModuleType:
    module_name = f"lifecycle_{operation}"
    if __package__:
        return importlib.import_module(f"{__package__}.{module_name}")
    return importlib.import_module(module_name)


def _reject_legacy_flags(arguments: Sequence[str], parser: argparse.ArgumentParser) -> None:
    for argument in arguments:
        if argument in LEGACY_FLAGS or any(argument.startswith(f"{flag}=") for flag in LEGACY_FLAGS):
            parser.error(f"{argument.split('=', 1)[0]} is not a dispatcher option")


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch argv to a lifecycle command without changing its arguments."""
    arguments = sys.argv[1:] if argv is None else argv
    parser = _parser()

    if arguments and arguments[0] in ("-h", "--help"):
        parser.parse_args(arguments)

    _reject_legacy_flags(arguments, parser)
    operation = "map"
    delegated_arguments = arguments
    if arguments and arguments[0] in OPERATIONS:
        operation = arguments[0]
        delegated_arguments = arguments[1:]

    result = _load_operation(operation).main(delegated_arguments)
    return 0 if result is None else result


if __name__ == "__main__":
    raise SystemExit(main())
