from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# Shared properties
class ProjectBase(BaseModel):
    alias: str = Field(..., description="Unique alias for the project (e.g., 'my_project_frontend')")
    root_path: str = Field(..., description="Absolute root path of the project directory")
    description: Optional[str] = None

# Properties to receive on item creation
class ProjectCreate(ProjectBase):
    pass

# Properties to receive on item update
class ProjectUpdate(BaseModel):
    alias: Optional[str] = None
    root_path: Optional[str] = None
    description: Optional[str] = None

# Properties shared by models stored in DB
class ProjectInDBBase(ProjectBase):
    id: int
    created_at_db: datetime
    updated_at_db: datetime

    class Config:
        from_attributes = True

# Properties to return to client
class ProjectSchema(ProjectInDBBase):
    pass

# Properties stored in DB
class ProjectInDB(ProjectInDBBase):
    pass
