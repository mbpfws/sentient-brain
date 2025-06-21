# Sentient-Brain: Unified Synthesis & Architecture

## 1. Executive Mandate

This document supersedes all previous analysis files. It represents the final, consolidated architectural plan for the `sentient-brain` Python MCP server. Our exclusive focus is the development of a standalone, Docker-based Python application within the `sentient-brain-py-server` directory. The immediate priority is to implement **Layer 1: The Codebase Knowledge Memory**, leveraging a hybrid Graph and Vector RAG architecture.

## 2. Core Architectural Pillars (Synthesized)

Our architecture is a direct synthesis of the most effective patterns from the three reference projects:

*   **Agentic Engine (`Archon`):** We will adopt the use of a Pydantic-based graph structure for defining and executing complex, type-safe agentic workflows. This provides a robust framework for our RAG pipelines.
*   **High-Performance Communication (`a2a-python`):** We will implement a `gRPC`-based interface for all server-client communication, ensuring a high-performance, strongly-typed, and scalable API.
*   **Code-to-Graph Pipeline (`mcp-crawl4ai-rag`):** We will replicate the proven pattern of using Python's `ast` module to parse source code into an Abstract Syntax Tree and then transforming this tree into a rich, queryable knowledge graph within Neo4j. This is the cornerstone of our Codebase Memory layer.

## 3. Final Technology Stack (Layer 1)

-   **Web Framework**: FastAPI
-   **Agentic Engine**: LangGraph (selected for its maturity and explicit state management)
-   **Communication**: gRPC (`grpcio`, `grpcio-tools`, `protobuf`)
-   **Graph Database**: Neo4j (`neo4j` driver)
-   **Vector Database**: Weaviate (`weaviate-client`)
-   **LLM Abstraction**: LiteLLM
-   **Embedding Generation**: Sentence-Transformers (interfacing with Ollama)
-   **Data Validation**: Pydantic
-   **Web/File Ingestion**: Playwright, BeautifulSoup, Unstructured
-   **Observability**: OpenTelemetry, Structlog
-   **CLI & Utilities**: Typer, Rich, python-dotenv, Tenacity

## 4. System Architecture (Layer 1: Codebase Focus)

```mermaid
graph TD
    subgraph User / Client
        A[Developer IDE]
    end

    subgraph Sentient-Brain Server (FastAPI + gRPC)
        B(gRPC Gateway) -- routes --> C{Service Router}
        C --> D[Code Graph Service]
        C --> E[Retrieval Service]

        subgraph Core Logic
            D -- uses --> F(AST Parser)
            F -- generates --> G(Neo4j Cypher Queries)
            D -- writes to --> H[Neo4j Database]
            E -- reads from --> H
            E -- reads from --> I[Weaviate Database]
        end
    end

    subgraph Data Stores
        H
        I
    end

    A -- gRPC Call --> B
```

## 5. Implementation Roadmap

1.  **Finalize Dependencies**: Create the definitive `requirements.txt` based on the stack defined above.
2.  **Seek User Approval**: Present this architecture and the final dependency list to the user for explicit sign-off.
3.  **Environment Build**: Rebuild the Docker environment with the approved `requirements.txt`. Ensure all services (FastAPI, Neo4j, Weaviate, Ollama) start correctly.
4.  **Service Scaffolding**: Create the initial Python files for `code_graph_service.py`, `retrieval_service.py`, and the database connection managers.
5.  **Implement AST-to-Graph Pipeline**: Build the core functionality within the `Code Graph Service` to:
    a.  Accept a Git repository URL.
    b.  Parse all Python files using the `ast` module.
    c.  Translate the AST into nodes (Classes, Functions, Imports) and relationships (Calls, Inheritance).
    d.  Write the resulting graph structure to Neo4j.
6.  **Implement Retrieval Endpoints**: Expose initial gRPC endpoints to query the Neo4j graph for code constructs.

This concludes the planning phase. I will now generate the final `requirements.txt` and await your approval to proceed.