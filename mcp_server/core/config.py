from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
from pathlib import Path

# Determine the base directory of the project (l:/mcp-server/sentient-brain)
# This assumes config.py is in l:/mcp-server/sentient-brain/mcp_server/core/
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env file from the mcp_server directory
# The .env file should be located at l:/mcp-server/sentient-brain/mcp_server/.env
env_path = BASE_DIR / "mcp_server" / ".env"
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sentient Brain MCP Server"
    API_V1_STR: str = "/api/v1"

    # Database settings
    # Example for SQLite: "sqlite:///./mcp_server_data/mcp_database.db"
    # The path is relative to the project root (l:/mcp-server/sentient-brain)
    # So, the DB file will be at l:/mcp-server/sentient-brain/mcp_server_data/mcp_database.db
    DATABASE_URL: str = f"sqlite:///{BASE_DIR.joinpath('mcp_server_data', 'mcp_database.db')}"

    # Gemini API Key
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")

    class Config:
        case_sensitive = True

settings = Settings()

# Note for user: Create a .env file in l:/mcp-server/sentient-brain/mcp_server/
# with the following content:
# GEMINI_API_KEY=your_actual_gemini_api_key
