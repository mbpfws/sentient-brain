"""
Agent-related data models for the Sentient Brain Multi-Agent System.

Defines the structure and behavior of different agent types, their configurations,
messages, and responses within the system.
"""
from enum import Enum
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import uuid4


class AgentType(str, Enum):
    """Types of agents in the multi-agent system."""
    ULTRA_ORCHESTRATOR = "ultra_orchestrator"
    ARCHITECT = "architect"
    CODEBASE_KNOWLEDGE_MEMORY = "codebase_knowledge_memory"
    DEBUG_REFACTOR = "debug_refactor"
    PLAN_TASKS_MEMORY = "plan_tasks_memory"
    DOCUMENTS_MEMORY = "documents_memory"
    CLIENT_SIDE_AI = "client_side_ai"


class AgentState(str, Enum):
    """Current state of an agent."""
    INACTIVE = "inactive"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"


class AgentConfig(BaseModel):
    """Configuration for an agent instance."""
    agent_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_type: AgentType
    name: str
    description: str
    state: AgentState = AgentState.INACTIVE
    
    # Agent-specific configurations
    model_config: Dict[str, Any] = Field(default_factory=dict)
    system_prompt: Optional[str] = None
    max_iterations: int = 10
    timeout_seconds: int = 300
    
    # Memory and context settings
    memory_enabled: bool = True
    context_window_size: int = 4000
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AgentMessage(BaseModel):
    """Message structure for inter-agent communication."""
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    sender_agent_id: str
    receiver_agent_id: Optional[str] = None  # None for broadcast
    
    message_type: str = "text"  # text, action, data, error, etc.
    content: Union[str, Dict[str, Any]]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    priority: int = 1  # 1=low, 5=high
    requires_response: bool = False
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentResponse(BaseModel):
    """Response structure from an agent."""
    response_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_id: str
    request_message_id: Optional[str] = None
    
    status: str = "success"  # success, error, partial, pending
    content: Union[str, Dict[str, Any]]
    
    # Action taken by the agent
    action_taken: Optional[str] = None
    next_actions: List[str] = Field(default_factory=list)
    
    # Performance metrics
    processing_time_ms: Optional[int] = None
    tokens_used: Optional[int] = None
    
    # Error information
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentCapability(BaseModel):
    """Describes a capability that an agent possesses."""
    capability_name: str
    description: str
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    requires_external_api: bool = False
    
    
class AgentWorkflowStep(BaseModel):
    """Represents a step in an agent's workflow."""
    step_id: str = Field(default_factory=lambda: str(uuid4()))
    step_name: str
    description: str
    
    input_requirements: List[str] = Field(default_factory=list)
    output_produces: List[str] = Field(default_factory=list)
    
    execution_order: int = 1
    is_conditional: bool = False
    condition_logic: Optional[str] = None
    
    estimated_duration_seconds: Optional[int] = None


class AgentPerformanceMetrics(BaseModel):
    """Performance tracking for agent activities."""
    agent_id: str
    metric_type: str  # response_time, success_rate, error_count, etc.
    metric_value: float
    measurement_unit: str
    
    time_period_start: datetime
    time_period_end: datetime
    
    context: Dict[str, Any] = Field(default_factory=dict)
    recorded_at: datetime = Field(default_factory=datetime.utcnow) 