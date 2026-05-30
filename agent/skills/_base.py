"""Skill dataclass — composable unit of tools + prompt guidance."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Skill:
    name: str
    tools: tuple[str, ...]
    prompt_section: str  # markdown injected into system prompt

    def __repr__(self) -> str:
        return f"Skill({self.name!r})"
