from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from enum import Enum

class NodeType(str, Enum):
    FILE = "FILE"
    CLASS = "CLASS"
    FUNCTION = "FUNCTION"
    METHOD = "METHOD"
    IMPORT = "IMPORT"
    VARIABLE = "VARIABLE"

class RelationshipType(str, Enum):
    CONTAINS = "CONTAINS"
    IMPORTS = "IMPORTS"
    CALLS = "CALLS"
    DEFINES = "DEFINES"
    INSTANTIATES = "INSTANTIATES"

class CodeNode(BaseModel):
    id: str  # e.g., file_path for FILE, file_path:class_name for CLASS
    node_type: NodeType
    name: str
    start_line: int
    end_line: int
    metadata: Dict[str, Any] = {}

class CodeRelationship(BaseModel):
    source_id: str
    target_id: str
    type: RelationshipType
    metadata: Dict[str, Any] = {}
