"""Simple registry that holds available language parsers.

Plugins can register themselves by being imported; for now we manually add
PythonParser. This keeps responsibilities isolated and makes it easy to add
new languages later.
"""
from __future__ import annotations

from typing import List

from .base import ICodeParser
from .python_parser import PythonParser


class ParserRegistry:
    """Holds instantiated parser plugins and selects one by extension."""

    def __init__(self) -> None:
        self._parsers: List[ICodeParser] = [PythonParser()]

    def get_parser_for_ext(self, ext: str) -> ICodeParser | None:  # noqa: D401
        for parser in self._parsers:
            if parser.supports_extension(ext):
                return parser
        return None

    # Convenience singleton

_registry: ParserRegistry | None = None

def get_parser_registry() -> ParserRegistry:  # noqa: D401
    global _registry
    if _registry is None:
        _registry = ParserRegistry()
    return _registry
