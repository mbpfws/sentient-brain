from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Assuming config.py is in ..core.config
# Adjust import path if your structure is different or if running as a script directly
# For package structure, it should be: from ..core.config import settings
try:
    from ..core.config import settings
except ImportError:
    # Fallback for cases where this might be run in a context where package imports don't work as expected
    # This might happen during initial alembic setup if PYTHONPATH is not correctly configured
    import sys
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent))
    from mcp_server.core.config import settings


# Ensure the directory for the SQLite database exists
# The database file will be in l:/mcp-server/sentient-brain/mcp_server_data/
db_path_str = settings.DATABASE_URL.replace("sqlite:///", "")

# Handle both absolute and relative paths that might come from DATABASE_URL
if Path(db_path_str).is_absolute():
    db_file = Path(db_path_str)
else:
    # If relative, assume it's relative to BASE_DIR (l:/mcp-server/sentient-brain)
    db_file = settings.BASE_DIR / db_path_str

db_dir = db_file.parent

if not db_dir.exists():
    db_dir.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    str(settings.DATABASE_URL), # Ensure DATABASE_URL is a string
    connect_args={"check_same_thread": False} # Needed for SQLite with FastAPI
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
