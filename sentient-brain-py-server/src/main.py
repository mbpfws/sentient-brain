from fastapi import FastAPI

app = FastAPI(title="Sentient Brain Python Server")

@app.get("/", tags=["Health Check"])
def read_root():
    """Check if the server is running."""
    return {"status": "ok", "message": "Sentient Brain Python Server is alive!"}
