import os
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from typing import Optional, List

from .services.ingestion_service import IngestionService
from .services.code_graph_service import CodeGraphService
from .services.file_watcher import FileWatcherService
from .services.groq_agentic_service import get_groq_service, SearchSettings
from .services.weaviate_inspector import get_weaviate_inspector
from .db.neo4j_driver import get_neo4j_driver, close_neo4j_driver, get_neo4j_session
from .db.weaviate_client import get_weaviate_client
from .models.document_models import DocumentSource, DocumentType, IngestionStatus

# Dependency to get the ingestion service
def get_ingestion_service():
    return IngestionService()
    # On startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    print("Initializing application...", flush=True)
    try:
        # Initialize Weaviate
        ingestion_service = get_ingestion_service()
        ingestion_service.initialize_schema(recreate=True)
        print("Schema initialization complete.", flush=True)

        # Initialize Neo4j and services that depend on it
        get_neo4j_driver() # Establishes and verifies the connection
        app.state.code_graph_service = CodeGraphService()

        # Initialize and start the file watcher
        watch_paths = os.getenv("WATCH_PATHS", "src").split(',')
        app.state.file_watcher = FileWatcherService(
            paths_to_watch=watch_paths,
            code_graph_service=app.state.code_graph_service
        )
        app.state.file_watcher.start()
        print("CodeGraphService initialized.", flush=True)

    except Exception as e:
        print(f"An error occurred during startup: {e}", flush=True)
    
    yield
    
    # On shutdown
    if hasattr(app.state, 'file_watcher') and app.state.file_watcher:
        app.state.file_watcher.stop()
    close_neo4j_driver()
    print("Application shutdown.", flush=True)

app = FastAPI(title="Sentient Brain Python Server", lifespan=lifespan)

# -----------------------------
# Health & Context Endpoints
# -----------------------------

from neo4j import Result  # type: ignore
from weaviate.collections import Collection  # type: ignore


def _get_neo4j_counts() -> dict:
    """Returns node and relationship counts from Neo4j."""
    try:
        with get_neo4j_session() as session:
            node_count: Result = session.run("MATCH (n) RETURN count(n) AS c")
            rel_count: Result = session.run("MATCH ()-[r]->() RETURN count(r) AS c")
            return {
                "nodes": node_count.single().get("c", 0),
                "relationships": rel_count.single().get("c", 0),
            }
    except Exception as exc:
        return {"error": str(exc)}


def _get_weaviate_counts() -> dict:
    """Returns object counts for key collections in Weaviate."""
    try:
        client = get_weaviate_client()
        counts = {}
        for cls in ["CodeChunk", "DocumentChunk", "DocumentSource"]:
            try:
                coll = client.collections.get(cls)
                # Use fetch_objects with limit=0 to get count
                result = coll.query.fetch_objects(limit=10000)  # Get actual objects
                counts[cls] = len(result.objects) if hasattr(result, 'objects') else 0
            except Exception as e:
                print(f"[HEALTH] Error counting {cls}: {e}", flush=True)
                counts[cls] = "error"
        return counts
    except Exception as exc:
        return {"error": str(exc)}


@app.get("/health", tags=["Health"])
def health():
    """Returns basic liveness plus DB counts."""
    return {
        "status": "ok",
        "neo4j": _get_neo4j_counts(),
        "weaviate": _get_weaviate_counts(),
    }


@app.get("/context", tags=["Context"])
def get_context(file: str):
    """Return code graph slice & code chunks for the given file path."""
    result = {"file": file, "nodes": [], "relationships": [], "chunks": []}
    # 1. Graph slice
    try:
        with get_neo4j_session() as session:
            records = session.run(
                """
                MATCH (f {id: $file})-[:CONTAINS*0..2]->(n)
                OPTIONAL MATCH (n)-[r]->(m)
                RETURN n,r,m
                """,
                file=file,
            )
            for rec in records:
                if rec["n"]:
                    result["nodes"].append(rec["n"]._properties)
                if rec["r"]:
                    rel_props = rec["r"]._properties
                    rel_props.update({"type": rec["r"].type})
                    result["relationships"].append(rel_props)
                if rec["m"]:
                    result["nodes"].append(rec["m"]._properties)
    except Exception as exc:
        result["graph_error"] = str(exc)

    # 2. Code chunks from Weaviate
    try:
        client = get_weaviate_client()
        code_chunk_coll = client.collections.get("CodeChunk")
        # Simplified: Get all chunks, filter client-side for now
        objs = code_chunk_coll.query.fetch_objects(limit=1000)
        for ob in objs.objects:  # type: ignore
            if ob.properties.get("file_path") == file:
                result["chunks"].append(ob.properties)
    except Exception as exc:
        result["weaviate_error"] = str(exc)

    return result

# -------------------------------------------------

@app.get("/", tags=["Health Check"])
def read_root():
    """Check if the server is running."""
    return {"status": "ok", "message": "Sentient Brain Python Server is alive!"}

@app.post("/test-ingestion/", tags=["Testing"])
def test_ingestion(service: IngestionService = Depends(get_ingestion_service)):
    """A temporary endpoint to test the full ingestion pipeline."""
    print("--- Running Test Ingestion ---")
    # 1. Create a sample document source
    test_source = DocumentSource(
        title="Gemini API Documentation",
        document_type=DocumentType.DOCUMENTATION,
        uri="https://ai.google.dev/gemini-api/docs/embeddings",
        status=IngestionStatus.PENDING
    )

    # 2. Ingest the source
    source_uuid = service.ingest_document_source(test_source)
    print(f"Ingested source document, got UUID: {source_uuid}")

    # 3. Define sample chunks
    chunks = [
        "Gemini is a family of generative AI models that lets developers generate content and solve problems.",
        "These models are designed and trained to handle both text and images as input.",
        "The Gemini API also provides embedding models, which are specialized for use cases such as semantic search and text classification."
    ]

    # 4. Ingest the chunks
    service.ingest_document_chunks(source_uuid, chunks)

    return {"status": "success", "message": f"Ingested 3 chunks for source {source_uuid}"}

@app.post("/backpopulate", tags=["Admin"])
def trigger_backpopulate():
    """Manually trigger back-population of missing Weaviate chunks."""
    try:
        app.state.code_graph_service.backpopulate_missing_chunks()
        return {"status": "success", "message": "Back-population completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/groq/analyze-code", tags=["Groq Agentic"])
def analyze_code_with_groq(
    code_snippet: str,
    question: str,
    exclude_domains: Optional[List[str]] = None,
    include_domains: Optional[List[str]] = None
):
    """Analyze code using Groq's compound-beta with real-time web search."""
    try:
        groq_service = get_groq_service()
        search_settings = None
        if exclude_domains or include_domains:
            search_settings = SearchSettings(
                exclude_domains=exclude_domains,
                include_domains=include_domains
            )
        
        response = groq_service.analyze_code_with_search(
            code_snippet=code_snippet,
            question=question,
            search_settings=search_settings
        )
        
        return {
            "status": "success",
            "analysis": response.content,
            "tools_used": response.executed_tools,
            "model": response.model_used,
            "usage": response.usage_stats
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/groq/debug-code", tags=["Groq Agentic"])
def debug_code_with_groq(
    code_snippet: str,
    error_message: Optional[str] = None
):
    """Debug code using Groq's compound-beta-mini with code execution."""
    try:
        groq_service = get_groq_service()
        response = groq_service.debug_with_execution(
            code_snippet=code_snippet,
            error_message=error_message
        )
        
        return {
            "status": "success",
            "debug_analysis": response.content,
            "tools_used": response.executed_tools,
            "model": response.model_used,
            "usage": response.usage_stats
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/groq/research", tags=["Groq Agentic"])
def research_technology_with_groq(
    technology: str,
    question: str,
    exclude_domains: Optional[List[str]] = None,
    include_domains: Optional[List[str]] = None
):
    """Research technology using Groq's compound-beta with web search."""
    try:
        groq_service = get_groq_service()
        search_settings = None
        if exclude_domains or include_domains:
            search_settings = SearchSettings(
                exclude_domains=exclude_domains,
                include_domains=include_domains
            )
        
        response = groq_service.research_technology(
            technology=technology,
            specific_question=question,
            search_settings=search_settings
        )
        
        return {
            "status": "success",
            "research": response.content,
            "tools_used": response.executed_tools,
            "model": response.model_used,
            "usage": response.usage_stats
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/groq/generate-code", tags=["Groq Agentic"])
def generate_code_with_groq(
    requirements: str,
    language: str = "python"
):
    """Generate and validate code using Groq's compound-beta."""
    try:
        groq_service = get_groq_service()
        response = groq_service.generate_code_with_validation(
            requirements=requirements,
            language=language
        )
        
        return {
            "status": "success",
            "generated_code": response.content,
            "tools_used": response.executed_tools,
            "model": response.model_used,
            "usage": response.usage_stats
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/groq/reason", tags=["Groq Agentic"])
def advanced_reasoning_with_groq(
    query: str,
    context: Optional[str] = None
):
    """Advanced reasoning using Groq's Llama 4 Scout model."""
    try:
        groq_service = get_groq_service()
        response = groq_service.enhanced_reasoning(
            complex_query=query,
            context=context
        )
        
        return {
            "status": "success",
            "reasoning": response.content,
            "model": response.model_used,
            "usage": response.usage_stats
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/weaviate/overview", tags=["Weaviate Inspector"])
def get_weaviate_overview():
    """Get comprehensive overview of Weaviate database contents."""
    inspector = get_weaviate_inspector()
    return inspector.get_database_overview()

@app.get("/weaviate/collection/{collection_name}", tags=["Weaviate Inspector"])
def get_collection_details(collection_name: str):
    """Get detailed information about a specific Weaviate collection."""
    inspector = get_weaviate_inspector()
    return inspector.get_collection_details(collection_name)

@app.get("/weaviate/search", tags=["Weaviate Inspector"])
def search_weaviate_content(
    query: str,
    collection: str = "CodeChunk",
    limit: int = 10
):
    """Search Weaviate database by content similarity."""
    inspector = get_weaviate_inspector()
    return inspector.search_by_content(query, collection, limit)

@app.get("/weaviate/filter", tags=["Weaviate Inspector"])
def filter_weaviate_objects(
    collection: str,
    property_name: str,
    property_value: str,
    limit: int = 50
):
    """Filter Weaviate objects by property values."""
    inspector = get_weaviate_inspector()
    return inspector.filter_objects(collection, property_name, property_value, limit)

@app.get("/weaviate/file/{file_path:path}", tags=["Weaviate Inspector"])
def get_code_chunks_for_file(file_path: str):
    """Get all code chunks for a specific file path."""
    inspector = get_weaviate_inspector()
    return inspector.get_code_chunks_by_file(file_path)

@app.get("/weaviate/statistics", tags=["Weaviate Inspector"])
def get_weaviate_statistics():
    """Get comprehensive statistics about all Weaviate collections."""
    inspector = get_weaviate_inspector()
    return inspector.get_collection_statistics()

@app.get("/weaviate/export/{collection_name}", tags=["Weaviate Inspector"])
def export_collection_data(collection_name: str):
    """Export all data from a Weaviate collection in JSON format."""
    inspector = get_weaviate_inspector()
    return inspector.export_collection_data(collection_name)
