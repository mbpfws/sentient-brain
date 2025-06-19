from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any, Dict

from ..database import database as db_utils
from ..services import code_indexing_service
from ..models import code_indexing_schemas, project_schemas

router = APIRouter()

# --- Project Endpoints ---

@router.post("/projects/", response_model=project_schemas.ProjectSchema, status_code=status.HTTP_201_CREATED, tags=["Projects"])
def create_project(project: project_schemas.ProjectCreate, db: Session = Depends(db_utils.get_db)):
    """
    Create a new project to be indexed.
    """
    db_project = code_indexing_service.get_project_by_alias(db, alias=project.alias)
    if db_project:
        raise HTTPException(status_code=400, detail=f"Project alias '{project.alias}' already registered.")
    return code_indexing_service.create_project(db=db, project=project)

@router.get("/projects/", response_model=List[project_schemas.ProjectSchema], tags=["Projects"])
def list_projects(skip: int = 0, limit: int = 100, db: Session = Depends(db_utils.get_db)):
    """
    List all registered projects.
    """
    return code_indexing_service.get_projects(db, skip=skip, limit=limit)

@router.get("/projects/{project_id}", response_model=project_schemas.ProjectSchema, tags=["Projects"])
def get_project_details(project_id: int, db: Session = Depends(db_utils.get_db)):
    """
    Get details for a specific project by its ID.
    """
    db_project = code_indexing_service.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return db_project

@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Projects"])
def delete_project(project_id: int, db: Session = Depends(db_utils.get_db)):
    """
    Delete a project and all its associated indexed files (cascade delete).
    """
    success = code_indexing_service.delete_project(db, project_id=project_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or could not be deleted")
    return

# --- Indexing and File Management Endpoints ---

class IndexRequest(project_schemas.ProjectCreate):
    pass

@router.post("/index", status_code=status.HTTP_202_ACCEPTED, tags=["Code Indexing"])
async def trigger_codebase_indexing(
    request: IndexRequest, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(db_utils.get_db)
) -> Dict:
    """
    Triggers a background task to scan and index the specified project directory.
    Finds a project by its alias or creates a new one if it doesn't exist.
    """
    # The service function will run in the background. 
    # Initial validation errors will not be returned to the client, but will be logged.
    # This is a trade-off for non-blocking behavior.
    background_tasks.add_task(
        code_indexing_service.index_codebase, 
        db=db, 
        project_alias=request.alias, 
        root_path=request.root_path
    )
    return {"message": f"Codebase indexing started in the background for project '{request.alias}'."}

@router.get("/files", response_model=List[code_indexing_schemas.CodeFileSchema], tags=["Code Indexing"])
def list_indexed_files(
    skip: int = 0, 
    limit: int = 100, 
    project_alias: str = None, 
    db: Session = Depends(db_utils.get_db)
) -> Any:
    """
    Retrieve a list of indexed code files, optionally filtering by project alias.
    """
    files = code_indexing_service.get_code_files(db, skip=skip, limit=limit, project_alias=project_alias)
    return files

@router.get("/files/{file_id}", response_model=code_indexing_schemas.CodeFileSchema, tags=["Code Indexing"])
def get_indexed_file_details(file_id: int, db: Session = Depends(db_utils.get_db)) -> Any:
    """
    Retrieve details for a specific indexed file by its database ID.
    """
    db_file = code_indexing_service.get_code_file(db, file_id=file_id)
    if db_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return db_file

@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Code Indexing"])
def delete_indexed_file(file_id: int, db: Session = Depends(db_utils.get_db)):
    """
    Delete an indexed file entry from the database by its ID.
    """
    success = code_indexing_service.delete_code_file(db, file_id=file_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found or could not be deleted")
    return

@router.put("/files/{file_id}/description", response_model=code_indexing_schemas.CodeFileSchema, tags=["Code Indexing"])
def update_file_description_endpoint(
    file_id: int, 
    description_update: code_indexing_schemas.CodeFileUpdate,
    db: Session = Depends(db_utils.get_db)
):
    """
    Update the description of an indexed file.
    """
    if description_update.description is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Description field is required.")
    updated_file = code_indexing_service.update_file_description(
        db=db, 
        file_id=file_id, 
        description=description_update.description
    )
    if updated_file is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return updated_file
