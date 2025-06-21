from fastapi import FastAPI
from contextlib import asynccontextmanager
from .services.ingestion_service import IngestionService
from .services.code_graph_service import CodeGraphService
from .db.neo4j_driver import get_neo4j_driver, close_neo4j_driver

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    print("Initializing application...", flush=True)
    try:
        # Initialize Weaviate
        ingestion_service = IngestionService()
        ingestion_service.initialize_schema(recreate=True)
        print("Schema initialization complete.", flush=True)

        # Initialize Neo4j and services that depend on it
        get_neo4j_driver() # Establishes and verifies the connection
        app.state.code_graph_service = CodeGraphService()
        print("CodeGraphService initialized.", flush=True)

    except Exception as e:
        print(f"An error occurred during startup: {e}", flush=True)
        # Depending on the severity, you might want to exit the application
    
    yield
    
    # On shutdown
    close_neo4j_driver()
    print("Application shutdown.", flush=True)

app = FastAPI(title="Sentient Brain Python Server", lifespan=lifespan)

@app.get("/", tags=["Health Check"])
def read_root():
    """Check if the server is running."""
    return {"status": "ok", "message": "Sentient Brain Python Server is alive!"}
