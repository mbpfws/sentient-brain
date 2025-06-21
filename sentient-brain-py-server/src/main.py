import os
from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager

from .services.ingestion_service import IngestionService
from .services.code_graph_service import CodeGraphService
from .services.file_watcher import FileWatcherService
from .db.neo4j_driver import get_neo4j_driver, close_neo4j_driver
from .models.document_models import DocumentSource, DocumentType, IngestionStatus

# Dependency to get the ingestion service
def get_ingestion_service():
    return IngestionService()

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
