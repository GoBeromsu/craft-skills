from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).parents[1] / "scripts" / "init.py"
SPEC = importlib.util.spec_from_file_location("init_dispatcher_test", SCRIPT)
assert SPEC and SPEC.loader
init = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = init
SPEC.loader.exec_module(init)


class InitDispatcherTests(unittest.TestCase):
    def test_bare_and_explicit_map_delegate_identical_arguments(self) -> None:
        calls: list[tuple[str, list[str]]] = []

        class Map:
            @staticmethod
            def main(argv: list[str]) -> int:
                calls.append(("map", argv))
                return 17

        with patch.object(init, "_load_operation", return_value=Map):
            bare = init.main(["repository", "--snapshot", "state.json"])
            explicit = init.main(["map", "repository", "--snapshot", "state.json"])

        self.assertEqual(17, bare)
        self.assertEqual(17, explicit)
        self.assertEqual(
            [
                ("map", ["repository", "--snapshot", "state.json"]),
                ("map", ["repository", "--snapshot", "state.json"]),
            ],
            calls,
        )

    def test_audit_and_prune_route_only_when_explicit(self) -> None:
        calls: list[tuple[str, list[str]]] = []

        class Operation:
            def __init__(self, name: str) -> None:
                self.name = name

            def main(self, argv: list[str]) -> int:
                calls.append((self.name, argv))
                return 0

        def load(operation: str) -> Operation:
            return Operation(operation)

        with patch.object(init, "_load_operation", side_effect=load):
            init.main(["audit", "repository"])
            init.main(["prune", "repository"])

        self.assertEqual([("audit", ["repository"]), ("prune", ["repository"])], calls)

    def test_legacy_operation_flags_fail_before_a_target_runs(self) -> None:
        with patch.object(init, "_load_operation") as load:
            with self.assertRaisesRegex(SystemExit, "^2$"):
                init.main(["audit", "--create-new", "repository"])

        load.assert_not_called()


if __name__ == "__main__":
    unittest.main()
