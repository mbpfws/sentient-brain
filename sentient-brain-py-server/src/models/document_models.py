from pydantic import BaseModel, Field
from uuid import uuid4
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    MARKDOWN = "MARKDOWN"
    SOURCE_CODE = "SOURCE_CODE"
    NOTE = "NOTE"
    WEB_PAGE = "WEB_PAGE"
    DOCUMENTATION = "DOCUMENTATION"

class IngestionStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class DocumentSource(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier")
    title: Optional[str] = None
    uri: Optional[str] = None
    document_type: DocumentType
    tech_stack: List[str] = []
    last_crawled_at: datetime = Field(default_factory=datetime.utcnow)
    status: IngestionStatus = IngestionStatus.PENDING
    metadata: Dict[str, Any] = {}

class DocumentChunk(BaseModel):
    id: str # Unique ID for the chunk, e.g., source_id:chunk_index
    source_id: str = Field(..., description="ID of the DocumentSource this chunk belongs to")
    content: str
    order: int
    headings: List[str] = []
    metadata_tags: List[str] = []
    embedding_provider: Optional[str] = None
