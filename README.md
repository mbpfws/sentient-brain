# Sentient Brain - MCP Server

This project is an MCP (Model Context Protocol) server designed to function as a multi-layered memory for AI builders and agents.

## Project Goal

To provide a persistent, structured, and relational memory that AI agents (especially those integrated into IDEs like Cursor and Windsurf) can interact with through tool calls. This enables them to retrieve information and perform tasks more effectively across different stages of a development project.

## Memory Layers

1.  **Code Indexing Memory**: Maintains an indexed representation of the local codebase.
2.  **Guides and Implementation Memory**: Stores and structures knowledge from external sources.
3.  **Task Breakdown Memory**: Manages project plans and tasks.
4.  **Dependency Documentation Memory**: Keeps a record of project dependencies and their usage.

## Core Technologies

*   **Backend Framework**: FastAPI
*   **Database (Relational)**: SQLite (initially, using SQLAlchemy ORM)
*   **Database (Vector)**: ChromaDB (for semantic search, to be integrated later)
*   **LLM Integration**: Google Gemini
*   **Development Language**: Python

## Setup

1.  Create a virtual environment: `python -m venv venv` (in `l:\mcp-server\sentient-brain`)
2.  Activate it:
    *   Windows: `.\venv\Scripts\activate`
    *   macOS/Linux: `source venv/bin/activate`
3.  Install dependencies: `pip install -r requirements.txt`
4.  Set up environment variables: Create a `.env` file in the `l:\mcp-server\sentient-brain\mcp_server` directory. You can copy `l:\mcp-server\sentient-brain\mcp_server\.env.example` to `l:\mcp-server\sentient-brain\mcp_server\.env` and fill in your details.
5.  Initialize/Upgrade database: `alembic upgrade head` (after Alembic is configured, from `l:\mcp-server\sentient-brain`)
6.  Run the server: `uvicorn mcp_server.main:app --reload --port 8008` (from the `l:\mcp-server\sentient-brain` directory)
