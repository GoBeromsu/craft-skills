from pathlib import Path
from typing import Final, Protocol


class _PluginContext(Protocol):
    def register_skill(
        self,
        name: str,
        path: Path,
        description: str = "",
    ) -> None: ...


_SKILLS_DIR: Final = Path(__file__).parent / "skills"


def register(ctx: _PluginContext) -> None:
    for skill_file in sorted(_SKILLS_DIR.glob("*/SKILL.md")):
        ctx.register_skill(skill_file.parent.name, skill_file)
