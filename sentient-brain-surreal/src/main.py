"""Minimal FastAPI app wired to SurrealDB.

This mirrors the robustness of the previous sentient-brain-py-server entrypoint but
uses the new SurrealClient wrapper for DB access.
"""

from fastapi import FastAPI
from dotenv import load_dotenv

from db.surreal_client import get_surreal_client

load_dotenv()

app = FastAPI(title="Sentient-Brain Surreal Server", version="0.1.0")


@app.on_event("startup")
async def on_startup() -> None:
    # Ensure SurrealDB connection is alive
    client = get_surreal_client()
    await client.query("INFO FOR DB;")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    from db.surreal_client import _SURREAL_CLIENT  # type: ignore

    if _SURREAL_CLIENT:
        import asyncio
        asyncio.create_task(_SURREAL_CLIENT.close())


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok", "db": "surreal"}
