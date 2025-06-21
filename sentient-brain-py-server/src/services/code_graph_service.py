import ast
from typing import List, Tuple, Dict, Any

from ..models.graph_models import CodeNode, CodeRelationship, NodeType, RelationshipType
from ..core.db.neo4j_driver import get_neo4j_session

class CodeGraphVisitor(ast.NodeVisitor):
    """An AST visitor that builds a graph of nodes and relationships."""

    def __init__(self, file_path: str, source_code: str):
        self.file_path = file_path
        self.source_code = source_code
        self.nodes: Dict[str, CodeNode] = {}
        self.relationships: List[CodeRelationship] = []
        self.scope_stack: List[str] = []

        # Create the root FILE node
        file_node_id = self.file_path
        self.nodes[file_node_id] = CodeNode(
            id=file_node_id,
            node_type=NodeType.FILE,
            name=self.file_path.split('/')[-1],
            start_line=1,
            end_line=len(self.source_code.splitlines()),
        )
        self.scope_stack.append(file_node_id)

    def visit_ClassDef(self, node: ast.ClassDef):
        class_node_id = f"{self.file_path}:{node.name}"
        parent_id = self.scope_stack[-1]

        self.nodes[class_node_id] = CodeNode(
            id=class_node_id,
            node_type=NodeType.CLASS,
            name=node.name,
            start_line=node.lineno,
            end_line=node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
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

    def visit_FunctionDef(self, node: ast.FunctionDef):
        parent_id = self.scope_stack[-1]
        parent_node = self.nodes.get(parent_id)

        is_method = parent_node and parent_node.node_type == NodeType.CLASS
        node_type = NodeType.METHOD if is_method else NodeType.FUNCTION
        
        function_node_id = f"{parent_id}:{node.name}" if is_method else f"{self.file_path}:{node.name}"

        self.nodes[function_node_id] = CodeNode(
            id=function_node_id,
            node_type=node_type,
            name=node.name,
            start_line=node.lineno,
            end_line=node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
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

    def visit_Import(self, node: ast.Import):
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
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
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
        self.generic_visit(node)

class CodeGraphService:
    """Service to parse source code and build a knowledge graph."""

    def parse_code_to_graph(
        self, file_path: str, source_code: str
    ) -> Tuple[List[CodeNode], List[CodeRelationship]]:
        """Parses Python source code into a list of nodes and relationships."""
        try:
            tree = ast.parse(source_code)
            visitor = CodeGraphVisitor(file_path, source_code)
            visitor.visit(tree)
            return list(visitor.nodes.values()), visitor.relationships
        except SyntaxError as e:
            print(f"Error parsing {file_path}: {e}")
            return [], []

    def persist_graph(self, nodes: List[CodeNode], relationships: List[CodeRelationship]):
        """Persists the graph nodes and relationships to Neo4j."""
        with get_neo4j_session() as session:
            for node in nodes:
                session.run(
                    """MERGE (n {id: $id}) 
                       SET n += $props, n.node_type = $node_type""",
                    id=node.id,
                    props=node.dict(exclude={'id', 'node_type'}),
                    node_type=node.node_type.value
                )
            for rel in relationships:
                session.run(
                    """MATCH (a {id: $source_id}), (b {id: $target_id})
                       MERGE (a)-[r:%s {type: $type}]->(b)
                       SET r += $props""" % rel.type.value,
                    source_id=rel.source_id,
                    target_id=rel.target_id,
                    type=rel.type.value,
                    props=rel.metadata
                )
        print(f"Persisted {len(nodes)} nodes and {len(relationships)} relationships.")

    def process_file(self, file_path: str, source_code: str):
        """A convenience method to parse a file and persist its graph."""
        nodes, relationships = self.parse_code_to_graph(file_path, source_code)
        if nodes or relationships:
            self.persist_graph(nodes, relationships)
