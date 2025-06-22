"""TypeScript/JavaScript code parser implementation using Tree-sitter.

Converts TypeScript and JavaScript source files into CodeNode / CodeRelationship 
lists compatible with the rest of the indexing pipeline.
"""
from __future__ import annotations

import logging
from typing import List, Tuple, Dict, Optional

import tree_sitter_javascript as ts_javascript
import tree_sitter_typescript as ts_typescript
from tree_sitter import Language, Parser, Tree, Node

from .base import ICodeParser
from ..models.graph_models import CodeNode, CodeRelationship, NodeType, RelationshipType

logger = logging.getLogger(__name__)


class _TypeScriptGraphVisitor:
    """Tree-sitter visitor that builds graph representation for TypeScript/JavaScript code."""

    def __init__(self, file_path: str, source_code: str, language: str):
        self.file_path = file_path
        self.source_code = source_code.encode('utf-8')
        self.language = language
        self.nodes: Dict[str, CodeNode] = {}
        self.relationships: List[CodeRelationship] = []
        self.scope_stack: List[str] = []

        # Root file node
        file_node_id = self.file_path
        source_lines = source_code.splitlines()
        self.nodes[file_node_id] = CodeNode(
            id=file_node_id,
            node_type=NodeType.FILE,
            name=file_path.split("/")[-1],
            start_line=1,
            end_line=len(source_lines),
        )
        self.scope_stack.append(file_node_id)

    def _get_text(self, node: Node) -> str:
        """Extract text content from a tree-sitter node."""
        return self.source_code[node.start_byte:node.end_byte].decode('utf-8')

    def _get_identifier_name(self, node: Node) -> Optional[str]:
        """Extract identifier name from various node types."""
        if node.type == 'identifier':
            return self._get_text(node)
        
        # Handle property_identifier
        if node.type == 'property_identifier':
            return self._get_text(node)
            
        # For function expressions and other complex nodes
        for child in node.children:
            if child.type == 'identifier':
                return self._get_text(child)
                
        return None

    def _process_function_node(self, node: Node, is_method: bool = False) -> None:
        """Process function declaration, function expression, method definition, etc."""
        # Try to get function name
        func_name = None
        for child in node.children:
            if child.type == 'identifier' or child.type == 'property_identifier':
                func_name = self._get_text(child)
                break
        
        if not func_name:
            # Anonymous function or arrow function
            func_name = f"anonymous_{node.start_point[0]}"

        parent_id = self.scope_stack[-1]
        parent_node = self.nodes.get(parent_id)
        
        # Determine if this is a method based on context
        actual_is_method = is_method or (parent_node and parent_node.node_type == NodeType.CLASS)
        node_type = NodeType.METHOD if actual_is_method else NodeType.FUNCTION

        function_node_id = (
            f"{parent_id}:{func_name}" if actual_is_method else f"{self.file_path}:{func_name}"
        )
        
        self.nodes[function_node_id] = CodeNode(
            id=function_node_id,
            node_type=node_type,
            name=func_name,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
        )
        
        self.relationships.append(
            CodeRelationship(
                source_id=parent_id,
                target_id=function_node_id,
                type=RelationshipType.CONTAINS,
            )
        )

        self.scope_stack.append(function_node_id)
        self._visit_children(node)
        self.scope_stack.pop()

    def _process_class_node(self, node: Node) -> None:
        """Process class declaration."""
        class_name = None
        for child in node.children:
            if child.type == 'identifier':
                class_name = self._get_text(child)
                break
        
        if not class_name:
            class_name = f"anonymous_class_{node.start_point[0]}"

        class_node_id = f"{self.file_path}:{class_name}"
        parent_id = self.scope_stack[-1]

        self.nodes[class_node_id] = CodeNode(
            id=class_node_id,
            node_type=NodeType.CLASS,
            name=class_name,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
        )
        
        self.relationships.append(
            CodeRelationship(
                source_id=parent_id,
                target_id=class_node_id,
                type=RelationshipType.CONTAINS,
            )
        )

        self.scope_stack.append(class_node_id)
        self._visit_children(node)
        self.scope_stack.pop()

    def _process_import_node(self, node: Node) -> None:
        """Process import statements."""
        import_text = self._get_text(node)
        
        # Extract module name from different import patterns
        module_name = "unknown"
        
        # Try to find import_clause and source
        for child in node.children:
            if child.type == 'string':
                # Remove quotes from string literal
                module_name = self._get_text(child).strip('"').strip("'")
                break

        import_node_id = f"import:{module_name}"
        
        self.nodes[import_node_id] = CodeNode(
            id=import_node_id,
            node_type=NodeType.IMPORT,
            name=module_name,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
        )
        
        self.relationships.append(
            CodeRelationship(
                source_id=self.file_path,
                target_id=import_node_id,
                type=RelationshipType.IMPORTS,
            )
        )

    def _visit_children(self, node: Node) -> None:
        """Recursively visit all children of a node."""
        for child in node.children:
            self._visit_node(child)

    def _visit_node(self, node: Node) -> None:
        """Visit a single node and process it based on its type."""
        
        # Function-related nodes
        if node.type in ['function_declaration', 'function_expression', 'arrow_function']:
            self._process_function_node(node)
            
        # Method definitions in classes
        elif node.type in ['method_definition', 'function_signature']:
            self._process_function_node(node, is_method=True)
            
        # Class declarations
        elif node.type == 'class_declaration':
            self._process_class_node(node)
            
        # Import statements
        elif node.type in ['import_statement', 'import_declaration']:
            self._process_import_node(node)
            
        else:
            # Continue visiting children for other node types
            self._visit_children(node)

    def visit(self, tree: Tree) -> None:
        """Start visiting from the root node."""
        self._visit_node(tree.root_node)


class TypeScriptParser(ICodeParser):
    """Parser plugin for TypeScript and JavaScript source files."""

    _SUPPORTED_EXTS = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
    
    def __init__(self):
        # Initialize languages
        self.js_language = Language(ts_javascript.language())
        self.ts_language = Language(ts_typescript.language_typescript())
        
        # Create parsers
        self.js_parser = Parser(self.js_language)
        self.ts_parser = Parser(self.ts_language)

    def supports_extension(self, ext: str) -> bool:
        """Return True if this parser can handle the given file extension."""
        return ext.lower() in self._SUPPORTED_EXTS

    def _get_parser_and_language(self, file_path: str) -> Tuple[Parser, str]:
        """Get the appropriate parser and language name based on file extension."""
        ext = file_path.lower().split('.')[-1]
        if ext in ['ts', 'tsx']:
            return self.ts_parser, 'typescript'
        else:
            return self.js_parser, 'javascript'

    def parse(
        self, file_path: str, source_code: str
    ) -> Tuple[List[CodeNode], List[CodeRelationship]]:
        """Parse TypeScript/JavaScript source code into graph nodes and relationships."""
        try:
            parser, language = self._get_parser_and_language(file_path)
            
            # Parse the source code
            source_bytes = source_code.encode('utf-8')
            tree = parser.parse(source_bytes)
            
            # Build the graph
            visitor = _TypeScriptGraphVisitor(file_path, source_code, language)
            visitor.visit(tree)
            
            logger.info(f"TypeScript/JS parser processed {file_path}: "
                       f"{len(visitor.nodes)} nodes, {len(visitor.relationships)} relationships")
            
            return list(visitor.nodes.values()), visitor.relationships
            
        except Exception as e:
            logger.error(f"TypeScriptParser: error parsing {file_path}: {e}")
            return [], [] 