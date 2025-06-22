"""Abstract interface for language-specific code parsers.

Each parser must return a list of `CodeNode` objects and `CodeRelationship`
objects that the rest of the system (Neo4j persistence, Weaviate sync) can
consume irrespective of language.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Tuple

from ..models.graph_models import CodeNode, CodeRelationship


class ICodeParser(ABC):
    """Abstract base class for code parsers."""

    @abstractmethod
    def supports_extension(self, ext: str) -> bool:
        """Return True if this parser can handle the given file extension."""

    @abstractmethod
    def parse(self, file_path: str, source_code: str) -> Tuple[List[CodeNode], List[CodeRelationship]]:
        """Parse source code into graph nodes and relationships."""
        
