# MCP-Crawl4AI-RAG: Deep Analysis & Implementation Patterns

## 1. Core Finding: AST-Based Graph Construction

The most significant finding from the `mcp-crawl4ai-rag` repository is the `Neo4jCodeAnalyzer` class within `parse_repo_into_neo4j.py`. It provides a robust, high-speed, non-LLM method for creating a detailed code knowledge graph directly from a Git repository. This will be the foundational pattern for our `code_graph_service.py`.

## 2. Implementation Blueprint for `CodeGraphService`

Our service will replicate the core logic of `Neo4jCodeAnalyzer`:

### A. Main Workflow (`analyze_repo` method)

1.  **Clone Repository**: Use `subprocess.run` to execute `git clone` into a temporary directory.
2.  **File Traversal**: Use `pathlib.Path.rglob('*.py')` to iterate through all Python files in the cloned repo.
3.  **AST Parsing**: For each file:
    *   Read the file content.
    *   Use `ast.parse()` to generate an Abstract Syntax Tree.
    *   Instantiate and run a custom `ast.NodeVisitor` class on the tree.
4.  **Database Insertion**: The `NodeVisitor` will be responsible for creating nodes and relationships in Neo4j as it traverses the tree.

### B. The `ast.NodeVisitor` Implementation

This is the heart of the parser. We will create a class that inherits from `ast.NodeVisitor` and implements the following visitor methods:

*   `visit_ClassDef(self, node)`: Creates a `(:Class {name, file_path})` node.
*   `visit_FunctionDef(self, node)`: Creates a `(:Function {name, file_path, signature})` node. If inside a class, it's a `(:Method)` and a `HAS_METHOD` relationship is created.
*   `visit_Import(self, node)` and `visit_ImportFrom(self, node)`: Create `(:Module)` nodes and `IMPORTS` relationships.
*   `visit_Call(self, node)`: This is crucial for understanding code flow. It identifies function/method calls and creates `CALLS` relationships between the calling function/method and the callee.

### C. Neo4j Schema and Cypher Queries

We will adopt the same simple but powerful schema:

*   **Nodes**: `Repository`, `File`, `Class`, `Method`, `Function`, `Module`.
*   **Relationships**: `CONTAINS`, `DEFINES`, `IMPORTS`, `CALLS`, `HAS_METHOD`.

We will adapt the Cypher queries directly from the script, using `MERGE` to prevent duplicate nodes and relationships. For example:

```cypher
// Create a class and its relationship to the file
MERGE (f:File {path: $file_path})
MERGE (c:Class {name: $class_name, file_path: $file_path})
MERGE (f)-[:DEFINES]->(c)
```

## 3. Patterns for Advanced RAG (Retrieval Service)

The other scripts (`ai_hallucination_detector.py`, `knowledge_graph_validator.py`) provide the blueprint for the *consumer* of our code graph.

*   **Hallucination Detection**: Our `RetrievalService` will implement a `validate_code` method. Given a piece of generated code, it will parse it and query the Neo4j graph to verify that all called functions, classes, and methods actually exist. This grounds the agent's output in reality.
*   **Contextual Querying**: The `query_knowledge_graph.py` script shows how to construct queries to explore the graph. Our gRPC retrieval endpoints will support queries like:
    *   "Find the definition of method `X` in class `Y`."
    *   "Show all functions that call method `Z`."
    *   "List all classes defined in file `A.py`."

## 4. Conclusion

The `mcp-crawl4ai-rag` project provides a complete, end-to-end implementation pattern. By adopting its AST-based parsing logic and its graph-based validation techniques, we can build a powerful and accurate codebase memory layer for `sentient-brain`.

This concludes the deep analysis. The next step is to create the unified architectural blueprint.