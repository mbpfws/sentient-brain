"""
Workflow-related data models for the Sentient Brain Multi-Agent System.

Defines structures for orchestrating complex multi-agent workflows,
project phases, and user intent processing using LangGraph patterns.
"""
from enum import Enum
from typing import List, Dict, Any, Optional, Union, Literal
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import uuid4


class ProjectPhase(str, Enum):
    """Project development phases."""
    DISCOVERY = "discovery"
    REQUIREMENTS = "requirements"
    ARCHITECTURE = "architecture"
    DEVELOPMENT = "development"
    TESTING = "testing"
    OPTIMIZATION = "optimization"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"


class UserIntentType(str, Enum):
    """Types of user intents that can be processed."""
    NEW_PROJECT = "new_project"
    EXISTING_PROJECT = "existing_project"
    DEBUG_REQUEST = "debug_request"
    REFACTOR_REQUEST = "refactor_request"
    DOCUMENTATION_REQUEST = "documentation_request"
    OPTIMIZATION_REQUEST = "optimization_request"
    ANALYSIS_REQUEST = "analysis_request"
    GENERAL_QUERY = "general_query"


class WorkflowStatus(str, Enum):
    """Status of a workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentWorkflowType(str, Enum):
    """Types of agent workflows."""
    ORCHESTRATION = "orchestration"
    ARCHITECTURE_DESIGN = "architecture_design"
    CODE_ANALYSIS = "code_analysis"
    DEBUG_REFACTOR = "debug_refactor"
    TASK_PLANNING = "task_planning"
    DOCUMENTATION = "documentation"
    CLIENT_INTERACTION = "client_interaction"


class UserIntent(BaseModel):
    """Processed user intent with disambiguation."""
    id: str = Field(default_factory=lambda: f"intent:{uuid4()}")
    raw_query: str
    intent_type: UserIntentType
    confidence: float = Field(ge=0.0, le=1.0)
    
    # Processed intent data
    entities: Dict[str, Any] = Field(default_factory=dict)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    
    # User proficiency assessment
    user_technical_level: str = "intermediate"  # novice, intermediate, expert
    preferred_mode: str = "guided"  # guided, autonomous
    
    # Intent resolution
    next_actions: List[str] = Field(default_factory=list)
    required_clarifications: List[str] = Field(default_factory=list)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_by: Optional[str] = None


class WorkflowState(BaseModel):
    """State management for LangGraph workflows."""
    id: str = Field(default_factory=lambda: f"workflow:{uuid4()}")
    workflow_type: AgentWorkflowType
    status: WorkflowStatus = WorkflowStatus.PENDING
    
    # Input and context
    initial_input: Dict[str, Any] = Field(default_factory=dict)
    current_state: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    
    # Execution tracking
    current_node: Optional[str] = None
    completed_nodes: List[str] = Field(default_factory=list)
    failed_nodes: List[str] = Field(default_factory=list)
    
    # Agent assignments
    primary_agent: Optional[str] = None
    involved_agents: List[str] = Field(default_factory=list)
    
    # Results and outputs
    intermediate_results: Dict[str, Any] = Field(default_factory=dict)
    final_output: Optional[Dict[str, Any]] = None
    
    # Error handling
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class WorkflowNode(BaseModel):
    """Individual node in a workflow graph."""
    id: str = Field(default_factory=lambda: f"node:{uuid4()}")
    name: str
    node_type: str  # agent, tool, decision, parallel, etc.
    
    # Node configuration
    agent_type: Optional[str] = None
    function_name: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Dependencies and flow
    dependencies: List[str] = Field(default_factory=list)
    next_nodes: List[str] = Field(default_factory=list)
    conditional_edges: Dict[str, str] = Field(default_factory=dict)
    
    # Execution state
    status: WorkflowStatus = WorkflowStatus.PENDING
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    
    # Error handling
    error_message: Optional[str] = None
    retry_count: int = 0
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class AgentCollaboration(BaseModel):
    """Model for agent-to-agent collaboration."""
    id: str = Field(default_factory=lambda: f"collab:{uuid4()}")
    requesting_agent: str
    target_agent: str
    collaboration_type: str  # consultation, delegation, peer_review, etc.
    
    # Request details
    request_context: Dict[str, Any] = Field(default_factory=dict)
    expected_deliverable: str
    priority: str = "medium"  # low, medium, high, urgent
    
    # Response
    response_data: Optional[Dict[str, Any]] = None
    status: str = "requested"  # requested, accepted, in_progress, completed, rejected
    
    # Timing
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class MemoryLayer(BaseModel):
    """Memory layer abstraction for agent persistence."""
    id: str = Field(default_factory=lambda: f"memory:{uuid4()}")
    layer_type: str  # codebase, documentation, tasks, project
    agent_id: str
    
    # Memory content
    short_term_memory: Dict[str, Any] = Field(default_factory=dict)
    long_term_memory: Dict[str, Any] = Field(default_factory=dict)
    
    # Context and retrieval
    active_context: List[str] = Field(default_factory=list)
    recent_queries: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Performance metrics
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    relevance_threshold: float = 0.3
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectMetrics(BaseModel):
    """Metrics for project development progress."""
    id: str = Field(default_factory=lambda: f"metrics:{uuid4()}")
    project_id: str
    
    # Development metrics
    total_tasks: int = 0
    completed_tasks: int = 0
    blocked_tasks: int = 0
    
    # Code metrics
    lines_of_code: int = 0
    functions_count: int = 0
    classes_count: int = 0
    complexity_score: Optional[float] = None
    
    # Quality metrics
    test_coverage: Optional[float] = None
    code_quality_score: Optional[float] = None
    technical_debt_score: Optional[float] = None
    
    # Agent activity
    active_agents: List[str] = Field(default_factory=list)
    agent_utilization: Dict[str, float] = Field(default_factory=dict)
    
    # Timeline
    estimated_completion: Optional[datetime] = None
    actual_completion: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DecisionPoint(BaseModel):
    """Decision points in workflows requiring human or agent input."""
    id: str = Field(default_factory=lambda: f"decision:{uuid4()}")
    workflow_id: str
    node_id: str
    
    # Decision details
    decision_type: str  # approval, choice, configuration, etc.
    question: str
    options: List[Dict[str, Any]] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    
    # Decision maker
    assigned_to: str  # agent_id or "human"
    priority: str = "medium"
    
    # Resolution
    decision_made: Optional[Dict[str, Any]] = None
    decided_by: Optional[str] = None
    decided_at: Optional[datetime] = None
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    deadline: Optional[datetime] = None


class WorkflowTemplate(BaseModel):
    """Reusable workflow templates."""
    id: str = Field(default_factory=lambda: f"template:{uuid4()}")
    name: str
    description: str
    workflow_type: AgentWorkflowType
    
    # Template structure
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Configuration
    parameters: Dict[str, Any] = Field(default_factory=dict)
    required_agents: List[str] = Field(default_factory=list)
    estimated_duration: Optional[int] = None  # in minutes
    
    # Usage tracking
    usage_count: int = 0
    success_rate: float = 0.0
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None


class ExecutionResult(BaseModel):
    """Result of workflow or agent execution."""
    id: str = Field(default_factory=lambda: f"result:{uuid4()}")
    workflow_id: Optional[str] = None
    agent_id: Optional[str] = None
    
    # Result data
    success: bool
    output: Dict[str, Any] = Field(default_factory=dict)
    artifacts: List[str] = Field(default_factory=list)  # File paths or IDs
    
    # Performance metrics
    execution_time_ms: float = 0.0
    tokens_used: Optional[int] = None
    api_calls_made: int = 0
    
    # Error information
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    
    # Context
    input_context: Dict[str, Any] = Field(default_factory=dict)
    environment: Dict[str, str] = Field(default_factory=dict)
    
    created_at: datetime = Field(default_factory=datetime.utcnow) 