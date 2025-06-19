from fastapi import FastAPI

app = FastAPI(
    title="Sentient Brain - MCP Server",
    description="An MCP server providing multi-layered memory for AI builders.",
    version="0.1.0",
)

@app.get("/")
async def root():
    return {"message": "Welcome to the Sentient Brain MCP Server!"}

# Placeholder for API routers
# from .api import code_indexer_router, guides_router, tasks_router, dependencies_router
# app.include_router(code_indexer_router.router, prefix="/api/v1/code", tags=["Code Indexing"])
# app.include_router(guides_router.router, prefix="/api/v1/guides", tags=["Guides & Implementation"])
# app.include_router(tasks_router.router, prefix="/api/v1/tasks", tags=["Task Management"])
# app.include_router(dependencies_router.router, prefix="/api/v1/dependencies", tags=["Dependency Docs"])

if __name__ == "__main__":
    import uvicorn
    # This is for development purposes only.
    # For production, use a proper ASGI server like Uvicorn run as a separate process.
    uvicorn.run(app, host="0.0.0.0", port=8008)
