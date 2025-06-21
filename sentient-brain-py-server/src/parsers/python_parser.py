"""Python code parser implementation using `ast`.

Converts Python source files into CodeNode / CodeRelationship lists compatible
with the rest of the indexing pipeline.
"""
from __future__ import annotations

import ast
from typing import List, Tuple, Dict

from .base import ICodeParser
from ..models.graph_models import CodeNode, CodeRelationship, NodeType, RelationshipType


class _PythonCodeGraphVisitor(ast.NodeVisitor):
    """AST visitor that builds graph representation for Python code."""

    def __init__(self, file_path: str, source_code: str):
        self.file_path = file_path
        self.source_code = source_code
        self.nodes: Dict[str, CodeNode] = {}
        self.relationships: List[CodeRelationship] = []
        self.scope_stack: List[str] = []

        # Root file node
        file_node_id = self.file_path
        self.nodes[file_node_id] = CodeNode(
            id=file_node_id,
            node_type=NodeType.FILE,
            name=file_path.split("/")[-1],
            start_line=1,
            end_line=len(source_code.splitlines()),
        )
        self.scope_stack.append(file_node_id)

    # ------------------------------------------------------------------
    # AST visitors
    # ------------------------------------------------------------------
    def visit_ClassDef(self, node: ast.ClassDef):  # type: ignore[override]
        class_node_id = f"{self.file_path}:{node.name}"
        parent_id = self.scope_stack[-1]

        self.nodes[class_node_id] = CodeNode(
            id=class_node_id,
            node_type=NodeType.CLASS,
            name=node.name,
            start_line=node.lineno,
            end_line=getattr(node, "end_lineno", node.lineno),
        )
        self.relationships.append(
            CodeRelationship(
                source_id=parent_id,
                target_id=class_node_id,
                type=RelationshipType.CONTAINS,
            )
        )

        self.scope_stack.append(class_node_id)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef):  # type: ignore[override]
        parent_id = self.scope_stack[-1]
        parent_node = self.nodes.get(parent_id)
        is_method = parent_node and parent_node.node_type == NodeType.CLASS
        node_type = NodeType.METHOD if is_method else NodeType.FUNCTION

        function_node_id = (
            f"{parent_id}:{node.name}" if is_method else f"{self.file_path}:{node.name}"
        )
        self.nodes[function_node_id] = CodeNode(
            id=function_node_id,
            node_type=node_type,
            name=node.name,
            start_line=node.lineno,
            end_line=getattr(node, "end_lineno", node.lineno),
        )
        self.relationships.append(
            CodeRelationship(
                source_id=parent_id,
                target_id=function_node_id,
                type=RelationshipType.CONTAINS,
            )
        )

        self.scope_stack.append(function_node_id)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_Import(self, node: ast.Import):  # type: ignore[override]
        for alias in node.names:
            import_node_id = f"import:{alias.name}"
            self.nodes[import_node_id] = CodeNode(
                id=import_node_id,
                node_type=NodeType.IMPORT,
                name=alias.name,
                start_line=node.lineno,
                end_line=node.lineno,
            )
            self.relationships.append(
                CodeRelationship(
                    source_id=self.file_path,
                    target_id=import_node_id,
                    type=RelationshipType.IMPORTS,
                )
            )

    def visit_ImportFrom(self, node: ast.ImportFrom):  # type: ignore[override]
        module_name = node.module or "."
        for alias in node.names:
            import_node_id = f"import:{module_name}.{alias.name}"
            self.nodes[import_node_id] = CodeNode(
                id=import_node_id,
                node_type=NodeType.IMPORT,
                name=f"{module_name}.{alias.name}",
                start_line=node.lineno,
                end_line=node.lineno,
            )
            self.relationships.append(
                CodeRelationship(
                    source_id=self.file_path,
                    target_id=import_node_id,
                    type=RelationshipType.IMPORTS,
                )
            )


class PythonParser(ICodeParser):
    """Parser plugin for Python source files."""

    _SUPPORTED_EXTS = {".py"}

    def supports_extension(self, ext: str) -> bool:  # noqa: D401
        return ext.lower() in self._SUPPORTED_EXTS

    def parse(
        self, file_path: str, source_code: str
    ) -> Tuple[List[CodeNode], List[CodeRelationship]]:
        try:
            tree = ast.parse(source_code)
            visitor = _PythonCodeGraphVisitor(file_path, source_code)
            visitor.visit(tree)
            return list(visitor.nodes.values()), visitor.relationships
        except SyntaxError as e:
            print(f"PythonParser: syntax error in {file_path}: {e}")
            return [], []
