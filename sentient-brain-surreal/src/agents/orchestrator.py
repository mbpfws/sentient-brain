"""
Ultra Orchestrator Agent - Central Intelligence and Workflow Coordinator.

This agent serves as the central intelligence hub, interfacing with user prompts
to regulate all tasks and workflows, implementing user intent disambiguation,
project context maintenance, and agent delegation.
"""
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

from ..models.agent_models import AgentMessage, AgentResponse, AgentConfig, AgentType
from ..models.workflow_models import UserIntent, WorkflowState, AgentWorkflowType, UserIntentType
from ..models.knowledge_models import ProjectContext
from ..services.groq_service import GroqLLMService
from ..services.surreal_service import SurrealDBService

logger = logging.getLogger(__name__)


class UltraOrchestratorAgent:
    """
    The Ultra Orchestrator Agent serves as the central coordination hub
    for the multi-agent system, managing workflows and agent delegation.
    """
    
    def __init__(self, config: AgentConfig, db_service: SurrealDBService, llm_service: GroqLLMService):
        self.config = config
        self.db_service = db_service
        self.llm_service = llm_service
        self.agent_type = AgentType.ULTRA_ORCHESTRATOR
        self.active_workflows: Dict[str, WorkflowState] = {}
        
    async def process_user_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Main entry point for processing user queries and orchestrating responses.
        
        Args:
            query: Raw user query
            context: Additional context information
            
        Returns:
            AgentResponse with orchestrated results
        """
        try:
            # Step 1: Intent Disambiguation
            intent = await self._disambiguate_intent(query, context or {})
            
            # Step 2: Project Context Analysis
            project_context = await self._analyze_project_context(intent)
            
            # Step 3: Workflow Planning
            workflow = await self._plan_workflow(intent, project_context)
            
            # Step 4: Agent Delegation
            result = await self._execute_workflow(workflow)
            
            return AgentResponse(
                agent_id=self.config.agent_id,
                success=True,
                content=result,
                metadata={
                    "intent_type": intent.intent_type,
                    "workflow_id": workflow.id,
                    "agents_involved": workflow.involved_agents
                }
            )
            
        except Exception as e:
            logger.error(f"Error in orchestrator processing: {e}")
            return AgentResponse(
                agent_id=self.config.agent_id,
                success=False,
                error_message=str(e),
                content={"error": "Failed to process query"}
            )
    
    async def _disambiguate_intent(self, query: str, context: Dict[str, Any]) -> UserIntent:
        """
        Analyze user query to determine intent and extract relevant parameters.
        
        Uses advanced LLM reasoning to understand user needs and classify intent type.
        """
        disambiguation_prompt = f"""
        Analyze the following user query and classify the intent. Consider the context provided.
        
        User Query: "{query}"
        Context: {context}
        
        Classify into one of these intent types:
        - new_project: Starting a new software project
        - existing_project: Working with existing codebase
        - debug_request: Debugging or troubleshooting code
        - refactor_request: Code refactoring or optimization
        - documentation_request: Documentation generation or analysis
        - analysis_request: Code analysis or review
        - general_query: General development questions
        
        Also extract:
        1. Technical level (novice/intermediate/expert)
        2. Preferred mode (guided/autonomous)
        3. Key entities and parameters
        4. Required clarifications (if any)
        
        Return as JSON with fields: intent_type, confidence, technical_level, preferred_mode, entities, parameters, clarifications
        """
        
        response = await self.llm_service.generate_response(disambiguation_prompt, context)
        
        # Parse LLM response and create UserIntent object
        # Note: In production, add proper JSON parsing and validation
        intent_data = self._parse_intent_response(response)
        
        intent = UserIntent(
            raw_query=query,
            intent_type=UserIntentType(intent_data.get("intent_type", "general_query")),
            confidence=intent_data.get("confidence", 0.8),
            entities=intent_data.get("entities", {}),
            parameters=intent_data.get("parameters", {}),
            context=context,
            user_technical_level=intent_data.get("technical_level", "intermediate"),
            preferred_mode=intent_data.get("preferred_mode", "guided"),
            required_clarifications=intent_data.get("clarifications", []),
            processed_by=self.config.agent_id
        )
        
        # Store intent in database
        await self.db_service.create_record("intents", intent.dict())
        
        return intent
    
    async def _analyze_project_context(self, intent: UserIntent) -> Optional[ProjectContext]:
        """
        Analyze and retrieve/create project context based on user intent.
        """
        if intent.intent_type == UserIntentType.NEW_PROJECT:
            # Create new project context
            project_context = ProjectContext(
                name=intent.parameters.get("project_name", "New Project"),
                description=intent.parameters.get("description", ""),
                root_path=intent.parameters.get("root_path", "."),
                languages=intent.parameters.get("languages", []),
                frameworks=intent.parameters.get("frameworks", [])
            )
            await self.db_service.create_record("projects", project_context.dict())
            return project_context
        
        elif intent.intent_type == UserIntentType.EXISTING_PROJECT:
            # Retrieve existing project context
            project_id = intent.parameters.get("project_id")
            if project_id:
                project_data = await self.db_service.get_record("projects", project_id)
                if project_data:
                    return ProjectContext(**project_data)
        
        return None
    
    async def _plan_workflow(self, intent: UserIntent, project_context: Optional[ProjectContext]) -> WorkflowState:
        """
        Plan and create workflow based on intent and project context.
        """
        workflow_type = self._determine_workflow_type(intent)
        
        workflow = WorkflowState(
            workflow_type=workflow_type,
            initial_input={
                "intent": intent.dict(),
                "project_context": project_context.dict() if project_context else {}
            },
            context={
                "user_technical_level": intent.user_technical_level,
                "preferred_mode": intent.preferred_mode
            }
        )
        
        # Determine which agents to involve
        workflow.involved_agents = self._select_agents_for_workflow(workflow_type, intent)
        
        # Store workflow in database and memory
        await self.db_service.create_record("workflows", workflow.dict())
        self.active_workflows[workflow.id] = workflow
        
        return workflow
    
    async def _execute_workflow(self, workflow: WorkflowState) -> Dict[str, Any]:
        """
        Execute the planned workflow by coordinating with appropriate agents.
        """
        workflow.status = "running"
        workflow.started_at = datetime.utcnow()
        
        try:
            # Execute based on workflow type
            if workflow.workflow_type == AgentWorkflowType.ARCHITECTURE_DESIGN:
                result = await self._execute_architecture_workflow(workflow)
            elif workflow.workflow_type == AgentWorkflowType.CODE_ANALYSIS:
                result = await self._execute_analysis_workflow(workflow)
            elif workflow.workflow_type == AgentWorkflowType.DEBUG_REFACTOR:
                result = await self._execute_debug_workflow(workflow)
            else:
                result = await self._execute_general_workflow(workflow)
            
            workflow.status = "completed"
            workflow.completed_at = datetime.utcnow()
            workflow.final_output = result
            
        except Exception as e:
            workflow.status = "failed"
            workflow.errors.append({
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "node": workflow.current_node
            })
            raise
        
        finally:
            await self.db_service.update_record("workflows", workflow.id, workflow.dict())
        
        return result
    
    def _determine_workflow_type(self, intent: UserIntent) -> AgentWorkflowType:
        """Determine appropriate workflow type based on user intent."""
        intent_to_workflow = {
            UserIntentType.NEW_PROJECT: AgentWorkflowType.ARCHITECTURE_DESIGN,
            UserIntentType.EXISTING_PROJECT: AgentWorkflowType.CODE_ANALYSIS,
            UserIntentType.DEBUG_REQUEST: AgentWorkflowType.DEBUG_REFACTOR,
            UserIntentType.REFACTOR_REQUEST: AgentWorkflowType.DEBUG_REFACTOR,
            UserIntentType.DOCUMENTATION_REQUEST: AgentWorkflowType.DOCUMENTATION,
            UserIntentType.ANALYSIS_REQUEST: AgentWorkflowType.CODE_ANALYSIS,
        }
        return intent_to_workflow.get(intent.intent_type, AgentWorkflowType.ORCHESTRATION)
    
    def _select_agents_for_workflow(self, workflow_type: AgentWorkflowType, intent: UserIntent) -> List[str]:
        """Select appropriate agents for the workflow type."""
        agent_map = {
            AgentWorkflowType.ARCHITECTURE_DESIGN: ["architect", "task_memory"],
            AgentWorkflowType.CODE_ANALYSIS: ["codebase_knowledge_memory", "document_memory"],
            AgentWorkflowType.DEBUG_REFACTOR: ["debug_refactor", "codebase_knowledge_memory"],
            AgentWorkflowType.DOCUMENTATION: ["document_memory", "codebase_knowledge_memory"],
            AgentWorkflowType.TASK_PLANNING: ["task_memory", "architect"],
        }
        return agent_map.get(workflow_type, ["architect"])
    
    async def _execute_architecture_workflow(self, workflow: WorkflowState) -> Dict[str, Any]:
        """Execute architecture design workflow."""
        # This would delegate to the Architect Agent
        return {
            "workflow_type": "architecture_design",
            "status": "completed",
            "deliverables": ["high_level_plan", "tech_stack_recommendation", "project_structure"]
        }
    
    async def _execute_analysis_workflow(self, workflow: WorkflowState) -> Dict[str, Any]:
        """Execute code analysis workflow."""
        # This would delegate to Knowledge Memory agents
        return {
            "workflow_type": "code_analysis",
            "status": "completed",
            "deliverables": ["analysis_report", "dependency_graph", "quality_metrics"]
        }
    
    async def _execute_debug_workflow(self, workflow: WorkflowState) -> Dict[str, Any]:
        """Execute debug/refactor workflow."""
        # This would delegate to Debug/Refactor Agent
        return {
            "workflow_type": "debug_refactor",
            "status": "completed",
            "deliverables": ["issue_analysis", "refactor_suggestions", "improvement_plan"]
        }
    
    async def _execute_general_workflow(self, workflow: WorkflowState) -> Dict[str, Any]:
        """Execute general workflow."""
        return {
            "workflow_type": "general",
            "status": "completed",
            "deliverables": ["response", "recommendations"]
        }
    
    def _parse_intent_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured intent data."""
        # Simple parser - in production, use proper JSON parsing with validation
        try:
            import json
            return json.loads(response)
        except:
            # Fallback parsing
            return {
                "intent_type": "general_query",
                "confidence": 0.5,
                "technical_level": "intermediate",
                "preferred_mode": "guided",
                "entities": {},
                "parameters": {},
                "clarifications": []
            } 