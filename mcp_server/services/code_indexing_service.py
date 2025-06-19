import os
import hashlib
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

from sqlalchemy.orm import Session
from ..database.models import code_indexing_models, project_models
from ..models import code_indexing_schemas, project_schemas
from ..core.config import settings
import google.generativeai as genai

genai.configure(api_key=settings.GEMINI_API_KEY)

# Placeholder for Gemini client setup
# if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
#     genai.configure(api_key=settings.GEMINI_API_KEY)
#     gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest') # Or your preferred model
# else:
#     gemini_model = None
#     print("Warning: GEMINI_API_KEY not configured. AI description generation will be disabled.")

def get_file_hash(file_path: Path) -> str:
    """Calculates SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError:
        return ""

async def generate_ai_description(file_path: Path) -> str:
    """Generates a concise, one-sentence description for a code file using the Gemini API."""
    try:
        # Limit file size to avoid excessive API costs and long processing times
        if file_path.stat().st_size > 1_000_000: # 1MB limit
            return "File is too large to be summarized."

        content = file_path.read_text(encoding='utf-8', errors='ignore')
        if not content.strip():
            return "File is empty."

        model = genai.GenerativeModel('gemini-pro')
        prompt = (
            f"Analyze the following code from the file '{file_path.name}' and provide a single, concise sentence describing its primary purpose or function. "
            f"Focus on the high-level role of the code. For example: 'This file defines the main FastAPI application and its routes.' or 'This module contains SQLAlchemy models for user data.'"
            f"\n\n---\n\n{content[:30000]}" # Limit content sent to API
        )

        response = await asyncio.to_thread(model.generate_content, prompt)
        
        return response.text.strip()
    except Exception as e:
        # Log the error in a real application
        print(f"Error generating AI description for {file_path.name}: {e}")
        return f"Error generating description: {e}"

async def index_codebase(db: Session, project_alias: str, root_path: str) -> Dict:
    """Scans a directory, calculates hashes, and stores file info in the DB."""
    # Step 1: Find or create the project
    project = db.query(project_models.Project).filter(project_models.Project.alias == project_alias).first()
    source_path = Path(root_path)

    if not source_path.is_dir():
        raise ValueError(f"Provided path {root_path} is not a directory or does not exist.")

    if not project:
        project = project_models.Project(alias=project_alias, root_path=str(source_path.resolve()))
        db.add(project)
        db.commit()
        db.refresh(project)

        # Use a local import to prevent circular dependency
        from .file_watcher_service import file_watcher_service
        # Immediately start watching the new project without needing a server restart
        file_watcher_service.watch_project(project)
    elif str(source_path.resolve()) != project.root_path:
        raise ValueError(f"Project alias '{project_alias}' exists but is mapped to a different root path: {project.root_path}")

    indexed_files = 0
    updated_files = 0
    new_files = 0
    errors = []

    for item in source_path.rglob('*'): # rglob for recursive scan
        if item.is_file():
            try:
                file_path_abs_str = str(item.resolve())
                file_hash = get_file_hash(item)

                # Check if file already exists with the same project_id and path
                db_file = db.query(code_indexing_models.CodeFile)\
                    .filter(code_indexing_models.CodeFile.project_id == project.id)\
                    .filter(code_indexing_models.CodeFile.file_path == file_path_abs_str)\
                    .first()

                if db_file:
                    # File exists, check if it needs update
                    size_bytes = item.stat().st_size
                    last_modified_at_fs = datetime.fromtimestamp(item.stat().st_mtime)
                    if db_file.file_hash != file_hash or \
                       db_file.size_bytes != size_bytes:
                        
                        db_file.file_hash = file_hash
                        db_file.size_bytes = size_bytes
                        db_file.last_modified_at_fs = last_modified_at_fs
                        db_file.description = await generate_ai_description(item)
                        db.add(db_file)
                        updated_files += 1
                else:
                    # New file
                    ai_description = await generate_ai_description(item)
                    new_file_entry = code_indexing_models.CodeFile(
                        file_path=file_path_abs_str,
                        file_name=item.name,
                        parent_directory=str(item.parent.resolve()),
                        project_id=project.id, # Use the new project ID
                        file_hash=file_hash,
                        size_bytes=item.stat().st_size,
                        last_modified_at_fs=datetime.fromtimestamp(item.stat().st_mtime),
                        description=ai_description
                    )
                    db.add(new_file_entry)
                    new_files += 1
                
                indexed_files += 1
            except Exception as e:
                errors.append({'file': str(item), 'error': str(e)})
    
    db.commit()
    return {
        "message": f"Indexing complete for project '{project_alias}' at {root_path}",
        "total_files_processed": indexed_files,
        "new_files_added": new_files,
        "files_updated": updated_files,
        "errors": errors
    }

def get_code_files(db: Session, skip: int = 0, limit: int = 100, project_alias: Optional[str] = None) -> List[code_indexing_models.CodeFile]:
    query = db.query(code_indexing_models.CodeFile)
    if project_alias:
        query = query.join(project_models.Project).filter(project_models.Project.alias == project_alias)
    return query.offset(skip).limit(limit).all()

def get_code_file(db: Session, file_id: int) -> Optional[code_indexing_models.CodeFile]:
    return db.query(code_indexing_models.CodeFile).filter(code_indexing_models.CodeFile.id == file_id).first()

def delete_code_file(db: Session, file_id: int) -> bool:
    db_file = get_code_file(db, file_id)
    if db_file:
        db.delete(db_file)
        db.commit()
        return True
    return False

def update_file_description(db: Session, file_id: int, description: str) -> Optional[code_indexing_models.CodeFile]:
    db_file = get_code_file(db, file_id)
    if db_file:
        db_file.description = description
        # db_file.updated_at_db = datetime.utcnow() # Handled by onupdate in model
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        return db_file
    return None

# --- Project Service Functions ---

def create_project(db: Session, project: project_schemas.ProjectCreate) -> project_models.Project:
    db_project = project_models.Project(alias=project.alias, root_path=project.root_path, description=project.description)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


# --- Watcher Service Helpers ---

async def update_or_create_code_file_by_path(db: Session, project_alias: str, file_path_str: str):
    """
    Updates an existing code file entry or creates a new one for a given path.
    This is intended to be called by the file watcher.
    """
    file_path = Path(file_path_str)
    if not file_path.is_file():
        # Maybe it was deleted between the event and this function call
        return

    project = get_project_by_alias(db, alias=project_alias)
    if not project:
        print(f"[Error] Project '{project_alias}' not found for watched file update: {file_path_str}")
        return

    file_path_abs_str = str(file_path.resolve())
    file_hash = get_file_hash(file_path)

    db_file = db.query(code_indexing_models.CodeFile)\
        .filter(code_indexing_models.CodeFile.project_id == project.id)\
        .filter(code_indexing_models.CodeFile.file_path == file_path_abs_str)\
        .first()

    if db_file:
        # File exists, update it
        db_file.file_hash = file_hash
        db_file.size_bytes = file_path.stat().st_size
        db_file.last_modified_at_fs = datetime.fromtimestamp(file_path.stat().st_mtime)
        db_file.description = await generate_ai_description(file_path)
        db.add(db_file)
        print(f"[Indexer] Updated file: {file_path_str}")
    else:
        # New file
        ai_description = await generate_ai_description(file_path)
        new_file_entry = code_indexing_models.CodeFile(
            file_path=file_path_abs_str,
            file_name=file_path.name,
            parent_directory=str(file_path.parent.resolve()),
            project_id=project.id,
            file_hash=file_hash,
            size_bytes=file_path.stat().st_size,
            last_modified_at_fs=datetime.fromtimestamp(file_path.stat().st_mtime),
            description=ai_description
        )
        db.add(new_file_entry)
        print(f"[Indexer] Created file: {file_path_str}")

    db.commit()


def delete_code_file_by_path(db: Session, project_alias: str, file_path_str: str):
    """
    Deletes a code file entry from the database using its path.
    """
    project = get_project_by_alias(db, alias=project_alias)
    if not project:
        print(f"[Error] Project '{project_alias}' not found for watched file deletion: {file_path_str}")
        return

    file_path_abs_str = str(Path(file_path_str).resolve())

    db_file = db.query(code_indexing_models.CodeFile)\
        .filter(code_indexing_models.CodeFile.project_id == project.id)\
        .filter(code_indexing_models.CodeFile.file_path == file_path_abs_str)\
        .first()
    
    if db_file:
        db.delete(db_file)
        db.commit()
        print(f"[Indexer] Deleted file: {file_path_str}")


def get_project(db: Session, project_id: int) -> Optional[project_models.Project]:
    return db.query(project_models.Project).filter(project_models.Project.id == project_id).first()

def get_project_by_alias(db: Session, alias: str) -> Optional[project_models.Project]:
    return db.query(project_models.Project).filter(project_models.Project.alias == alias).first()

def get_projects(db: Session, skip: int = 0, limit: int = 100) -> List[project_models.Project]:
    return db.query(project_models.Project).offset(skip).limit(limit).all()

def delete_project(db: Session, project_id: int) -> bool:
    db_project = get_project(db, project_id)
    if db_project:
        db.delete(db_project)
        db.commit()
        return True
    return False
