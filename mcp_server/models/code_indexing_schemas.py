from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Shared properties
class CodeFileBase(BaseModel):
    file_path: str = Field(..., description="Full absolute path to the file")
    file_name: str
    parent_directory: str = Field(..., description="Full absolute path of the parent directory")
    project_root: str = Field(..., description="Root directory of the indexed project")
    file_hash: str = Field(..., description="SHA-256 hash of the file content")
    size_bytes: int
    last_modified_at_fs: datetime = Field(..., description="Last modification timestamp from the file system")
    description: Optional[str] = None

# Properties to receive on item creation
class CodeFileCreate(CodeFileBase):
    pass

# Properties to receive on item update (all optional)
class CodeFileUpdate(BaseModel):
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    parent_directory: Optional[str] = None
    project_root: Optional[str] = None
    file_hash: Optional[str] = None
    size_bytes: Optional[int] = None
    last_modified_at_fs: Optional[datetime] = None
    description: Optional[str] = None

# Properties shared by models stored in DB
class CodeFileInDBBase(CodeFileBase):
    id: int
    created_at_db: datetime
    updated_at_db: datetime

    class Config:
        from_attributes = True # Replace orm_mode = True for Pydantic v2

# Properties to return to client
class CodeFileSchema(CodeFileInDBBase):
    pass

# Properties stored in DB
class CodeFileInDB(CodeFileInDBBase):
    pass
