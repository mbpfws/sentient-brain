import os
import ast
import uuid
from typing import List, Tuple, Dict, Any

from ..models.graph_models import CodeNode, CodeRelationship, NodeType, RelationshipType
from ..db.neo4j_driver import get_neo4j_session
from ..db.weaviate_client import get_weaviate_client
from ..embedding.embedder import get_embedder
from ..parsers.registry import get_parser_registry
from .metadata_extractor import get_metadata_extractor

class CodeGraphVisitor(ast.NodeVisitor):
    """An AST visitor that builds a graph of nodes and relationships."""

    MIN_BLOCK_LINES = 5  # Minimum lines for a block to be considered significant

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
        self.block_counter = 0

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

    def _is_significant_block(self, node) -> bool:
        start_line = node.lineno
        end_line = getattr(node, 'end_lineno', start_line)
        return (end_line - start_line + 1) >= self.MIN_BLOCK_LINES

    def _create_block_node(self, node, block_type: str):
        if not self._is_significant_block(node):
            self.generic_visit(node) # Still need to visit children
            return

        parent_id = self.scope_stack[-1]
        self.block_counter += 1
        block_node_id = f"{parent_id}:block_{self.block_counter}_{block_type}_{node.lineno}"

        self.nodes[block_node_id] = CodeNode(
            id=block_node_id,
            node_type=NodeType.BLOCK,
            name=f"{block_type.capitalize()} Block",
            start_line=node.lineno,
            end_line=getattr(node, 'end_lineno', node.lineno),
        )
        self.relationships.append(
            CodeRelationship(
                source_id=parent_id,
                target_id=block_node_id,
                type=RelationshipType.CONTAINS,
            )
        )
        # We don't push block to scope_stack, but we visit children from here
        self.scope_stack.append(block_node_id)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_If(self, node: ast.If):
        self._create_block_node(node, 'if')

    def visit_For(self, node: ast.For):
        self._create_block_node(node, 'for_loop')

    def visit_While(self, node: ast.While):
        self._create_block_node(node, 'while_loop')

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
    """Service to parse source code, build a knowledge graph, and sync to Weaviate."""

    def __init__(self):
        self.weaviate_client = get_weaviate_client()
        self.embedder = get_embedder()
        self.metadata_extractor = get_metadata_extractor()
        print("CodeGraphService initialized with Weaviate, Embedder, and MetadataExtractor.")

    def parse_code_to_graph(
        self, file_path: str, source_code: str
    ) -> Tuple[List[CodeNode], List[CodeRelationship]]:
        """Parses Python source code into a list of nodes and relationships."""
        # Decide which parser to use based on file extension
        ext = os.path.splitext(file_path)[1]
        parser = get_parser_registry().get_parser_for_ext(ext)
        if not parser:
            print(f"No parser registered for extension {ext}, skipping {file_path}")
            return [], []
        return parser.parse(file_path, source_code)

    def persist_graph(self, nodes: List[CodeNode], relationships: List[CodeRelationship], file_metadata: Dict[str, Any]):
        """Persists the graph nodes and relationships to Neo4j."""
        with get_neo4j_session() as session:
            for node in nodes:
                # Neo4j does not allow nested maps as property values, so exclude metadata
                base_props = node.model_dump(exclude={"id", "node_type", "metadata"})

                # Find the FILE node and add the extracted metadata
                if node.node_type == NodeType.FILE:
                    base_props.update(file_metadata)

                session.run(
                    """MERGE (n {id: $id})
                       SET n += $props, n.node_type = $node_type""",
                    id=node.id,
                    props=base_props,
                    node_type=node.node_type.value,
                )
            for rel in relationships:
                if rel.metadata:
                    props_clause = "SET r += $props"
                else:
                    props_clause = ""
                cypher = (
                    """MATCH (a {id: $source_id}), (b {id: $target_id})
                       MERGE (a)-[r:%s {type: $type}]->(b)
                       %s""" % (rel.type.value, props_clause)
                )
                session.run(
                    cypher,
                    source_id=rel.source_id,
                    target_id=rel.target_id,
                    type=rel.type.value,
                    props=rel.metadata if rel.metadata else {},
                )
        print(f"Persisted {len(nodes)} nodes and {len(relationships)} relationships.")

    def sync_code_chunks_to_weaviate(self, file_path: str, source_code: str, nodes: List[CodeNode]):
        """Extracts code content, generates embeddings, and upserts to Weaviate."""
        code_chunk_collection = self.weaviate_client.collections.get("CodeChunk")
        source_lines = source_code.splitlines()

        nodes_to_embed = [
            n for n in nodes 
            if n.node_type in [NodeType.CLASS, NodeType.FUNCTION, NodeType.METHOD, NodeType.BLOCK]
        ]

        if not nodes_to_embed:
            return

        # Prepare content for batch embedding
        contents_to_embed = []
        for node in nodes_to_embed:
            # Ensure start and end lines are within bounds
            start = max(0, node.start_line - 1)
            end = min(len(source_lines), node.end_line)
            content = "\n".join(source_lines[start:end])
            contents_to_embed.append(content)

        # Get embeddings
        vectors = self.embedder.embed(contents_to_embed)

        # Insert each code chunk individually with proper UUID format
        for i, node in enumerate(nodes_to_embed):
            # Generate a proper UUID4 for Weaviate
            chunk_uuid = str(uuid.uuid4())
            
            data_object = {
                "source_id": node.id,  # Store original Neo4j ID for linking
                "file_path": file_path,
                "node_type": node.node_type.value,
                "name": node.name,
                "start_line": node.start_line,
                "end_line": node.end_line,
                "content": contents_to_embed[i],
            }
            
            try:
                code_chunk_collection.data.insert(
                    properties=data_object,
                    vector=vectors[i],
                    uuid=chunk_uuid  # Use proper UUID format
                )
                print(f"[WEAVIATE] Inserted chunk {node.name} with UUID: {chunk_uuid}", flush=True)
            except Exception as e:
                print(f"[WEAVIATE] Error inserting chunk {node.name}: {e}", flush=True)
        
        print(f"Synced {len(nodes_to_embed)} code chunks to Weaviate for file {file_path}.")

    def process_file(self, file_path: str, source_code: str, commit_hash: str = None, commit_author: str = None):
        """Parses a file, enriches with metadata, persists graph, and syncs chunks."""
        # 1. Extract metadata first
        metadata = self.metadata_extractor.extract_metadata(file_path)
        print(f"Extracted metadata for {file_path}: {metadata}", flush=True)

        # 2. Parse code into structural graph
        nodes, relationships = self.parse_code_to_graph(file_path, source_code)
        if not nodes and not relationships:
            return

        # 3. Persist to Neo4j and Weaviate, now with metadata
        self.persist_graph(nodes, relationships, metadata)
        self.sync_code_chunks_to_weaviate(file_path, source_code, nodes)

        # 4. If commit info is present, link the file to the commit
        if commit_hash:
            self.link_file_to_commit(file_path, commit_hash, commit_author)

        # Summary log
        class_count = sum(1 for n in nodes if n.node_type == NodeType.CLASS)
        func_count = sum(1 for n in nodes if n.node_type in [NodeType.FUNCTION, NodeType.METHOD])
        print(f"Indexed {class_count} classes, {func_count} functions from {file_path} with domain '{metadata['domain']}'.")

    def link_file_to_commit(self, file_path: str, commit_hash: str, commit_author: str = None):
        """Create a :Commit node and link it to the modified :File node."""
        with get_neo4j_session() as session:
            session.run(
                """MERGE (c:Commit {hash: $hash})
                   ON CREATE SET c.author = $author, c.timestamp = timestamp()
                   WITH c
                   MATCH (f:File {id: $file_id})
                   MERGE (c)-[:MODIFIED]->(f)""",
                hash=commit_hash,
                author=commit_author,
                file_id=file_path
            )
            print(f"Linked {file_path} to commit {commit_hash}", flush=True)

    # ---------------------
    # Back-population util
    # ---------------------

    def backpopulate_missing_chunks(self):
        """Scan Neo4j for code nodes missing in Weaviate and insert them."""
        print("[BACKPOP] Starting back-population check…", flush=True)
        client = get_weaviate_client()
        chunk_coll = client.collections.get("CodeChunk")

        # 1. Fetch all existing source_ids from Weaviate
        existing_source_ids: set[str] = set()
        try:
            objs = chunk_coll.query.fetch_objects(limit=100000)  # all
            for ob in objs.objects:  # type: ignore
                existing_source_ids.add(ob.properties.get("source_id"))
        except Exception as exc:
            print(f"[BACKPOP] Error fetching existing chunks: {exc}", flush=True)

        # 2. Query Neo4j for candidate nodes
        with get_neo4j_session() as session:
            records = session.run(
                """
                MATCH (n)
                WHERE n.node_type IN ['CLASS','FUNCTION','METHOD']
                RETURN n.id   AS id,
                       n.name AS name,
                       n.node_type AS node_type,
                       n.start_line AS start_line,
                       n.end_line   AS end_line,
                       n.file_path  AS file_path
                """
            )
            missing = []
            for rec in records:
                sid = rec["id"]
                if sid not in existing_source_ids:
                    missing.append(rec)

            print(f"[BACKPOP] {len(missing)} missing chunks to backfill.", flush=True)

            for rec in missing:
                file_path = rec["file_path"]
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.read().splitlines()
                    start = max(0, (rec["start_line"] or 1)-1)
                    end = min(len(lines), rec["end_line"] or start+1)
                    content = "\n".join(lines[start:end])
                    vector = self.embedder.embed([content])[0]
                    chunk_uuid = str(uuid.uuid4())
                    chunk_coll.data.insert(
                        properties={
                            "source_id": sid,
                            "file_path": file_path,
                            "node_type": rec["node_type"],
                            "name": rec["name"],
                            "start_line": rec["start_line"],
                            "end_line": rec["end_line"],
                            "content": content,
                        },
                        vector=vector,
                        uuid=chunk_uuid,
                    )
                    print(f"[BACKPOP] Inserted missing chunk {sid} → {chunk_uuid}", flush=True)
                except Exception as exc:
                    print(f"[BACKPOP] Failed to backfill {sid}: {exc}", flush=True)
        print("[BACKPOP] Completed.", flush=True)
