"""
Groq Agentic Service - Advanced AI capabilities with web search and code execution.

This service provides:
1. Real-time web search via Tavily
2. Code execution via E2B (Python)
3. Advanced reasoning with Llama 4 Scout
4. Fallback capabilities for complex queries
"""
import os
import json
from typing import List, Dict, Any, Optional
from groq import Groq
from dataclasses import dataclass
from enum import Enum

class GroqModel(Enum):
    """Available Groq models for different use cases."""
    COMPOUND_BETA = "compound-beta"  # Multi-tool calls per request
    COMPOUND_BETA_MINI = "compound-beta-mini"  # Single tool call per request (3x faster)
    LLAMA_4_SCOUT = "meta-llama/llama-4-scout-17b-16e-instruct"  # Latest reasoning model
    LLAMA_33_70B = "llama-3.3-70b-versatile"  # High-performance general model

@dataclass
class SearchSettings:
    """Configuration for web search behavior."""
    exclude_domains: Optional[List[str]] = None
    include_domains: Optional[List[str]] = None

@dataclass
class GroqResponse:
    """Structured response from Groq agentic service."""
    content: str
    executed_tools: Optional[List[Dict[str, Any]]] = None
    model_used: str = ""
    usage_stats: Optional[Dict[str, Any]] = None

class GroqAgenticService:
    """Service for advanced AI capabilities using Groq's agentic tooling."""
    
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        if not os.getenv("GROQ_API_KEY"):
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        print("[GROQ] Agentic service initialized with compound-beta models", flush=True)
    
    def analyze_code_with_search(
        self, 
        code_snippet: str, 
        question: str,
        search_settings: Optional[SearchSettings] = None
    ) -> GroqResponse:
        """
        Analyze code with real-time web search for documentation/examples.
        Uses compound-beta for multi-tool capability.
        """
        prompt = f"""
        Analyze this code snippet and answer the question using both your knowledge 
        and current web search for the latest documentation/best practices:

        Code:
        ```python
        {code_snippet}
        ```

        Question: {question}

        Please provide:
        1. Code analysis
        2. Current best practices (search for latest info)
        3. Potential improvements
        4. Security considerations
        """
        
        return self._make_request(
            prompt=prompt,
            model=GroqModel.COMPOUND_BETA,
            search_settings=search_settings,
            system_message="You are an expert code analyst with access to real-time documentation."
        )
    
    def debug_with_execution(
        self, 
        code_snippet: str, 
        error_message: Optional[str] = None
    ) -> GroqResponse:
        """
        Debug code by executing it and analyzing results.
        Uses compound-beta-mini for faster single-tool execution.
        """
        prompt = f"""
        Debug this Python code snippet:

        Code:
        ```python
        {code_snippet}
        ```
        """
        
        if error_message:
            prompt += f"\n\nError encountered: {error_message}"
        
        prompt += """
        
        Please:
        1. Execute the code to see what happens
        2. Identify any issues
        3. Provide a corrected version if needed
        4. Explain the debugging process
        """
        
        return self._make_request(
            prompt=prompt,
            model=GroqModel.COMPOUND_BETA_MINI,
            system_message="You are a debugging expert. Execute code to understand issues."
        )
    
    def research_technology(
        self, 
        technology: str, 
        specific_question: str,
        search_settings: Optional[SearchSettings] = None
    ) -> GroqResponse:
        """
        Research current technology trends and documentation.
        Uses compound-beta for comprehensive web search.
        """
        prompt = f"""
        Research the latest information about {technology} and answer this specific question:
        
        Question: {specific_question}
        
        Please provide:
        1. Current state of the technology (search for latest updates)
        2. Recent developments or changes
        3. Best practices and recommendations
        4. Code examples if applicable
        5. Links to authoritative sources
        """
        
        return self._make_request(
            prompt=prompt,
            model=GroqModel.COMPOUND_BETA,
            search_settings=search_settings,
            system_message="You are a technology researcher with access to real-time information."
        )
    
    def generate_code_with_validation(
        self, 
        requirements: str,
        language: str = "python"
    ) -> GroqResponse:
        """
        Generate code and validate it through execution.
        Uses compound-beta for generation + validation.
        """
        prompt = f"""
        Generate {language} code that meets these requirements:
        
        {requirements}
        
        Please:
        1. Write the code
        2. Execute it to verify it works
        3. Provide usage examples
        4. Include error handling
        5. Add documentation comments
        """
        
        return self._make_request(
            prompt=prompt,
            model=GroqModel.COMPOUND_BETA,
            system_message=f"You are an expert {language} developer. Generate and validate code."
        )
    
    def enhanced_reasoning(
        self, 
        complex_query: str,
        context: Optional[str] = None
    ) -> GroqResponse:
        """
        Use Llama 4 Scout for advanced reasoning on complex problems.
        """
        prompt = complex_query
        if context:
            prompt = f"Context: {context}\n\nQuery: {complex_query}"
        
        return self._make_request(
            prompt=prompt,
            model=GroqModel.LLAMA_4_SCOUT,
            system_message="You are an advanced reasoning AI. Think step by step through complex problems."
        )
    
    def _make_request(
        self,
        prompt: str,
        model: GroqModel,
        search_settings: Optional[SearchSettings] = None,
        system_message: str = "You are a helpful AI assistant."
    ) -> GroqResponse:
        """Make a request to Groq API with proper error handling."""
        try:
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
            
            # Prepare request parameters
            request_params = {
                "model": model.value,
                "messages": messages,
                "temperature": 0.1,  # Lower temperature for more consistent results
                "max_tokens": 4000
            }
            
            # Add search settings if provided and model supports it
            if search_settings and model in [GroqModel.COMPOUND_BETA, GroqModel.COMPOUND_BETA_MINI]:
                search_config = {}
                if search_settings.exclude_domains:
                    search_config["exclude_domains"] = search_settings.exclude_domains
                if search_settings.include_domains:
                    search_config["include_domains"] = search_settings.include_domains
                
                if search_config:
                    request_params["search_settings"] = search_config
            
            # Make the API call
            response = self.client.chat.completions.create(**request_params)
            
            # Extract response data
            choice = response.choices[0]
            content = choice.message.content
            executed_tools = getattr(choice.message, 'executed_tools', None)
            
            # Extract usage stats if available
            usage_stats = None
            if hasattr(response, 'usage'):
                usage_stats = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            
            print(f"[GROQ] Request completed with model: {model.value}", flush=True)
            if executed_tools:
                print(f"[GROQ] Tools executed: {len(executed_tools)}", flush=True)
            
            return GroqResponse(
                content=content,
                executed_tools=executed_tools,
                model_used=model.value,
                usage_stats=usage_stats
            )
            
        except Exception as e:
            print(f"[GROQ] Error in request: {e}", flush=True)
            # Return fallback response
            return GroqResponse(
                content=f"Error occurred with Groq API: {str(e)}. Please check your API key and try again.",
                model_used=model.value
            )

# Factory function for easy access
def get_groq_service() -> GroqAgenticService:
    """Get a configured Groq agentic service instance."""
    return GroqAgenticService() 