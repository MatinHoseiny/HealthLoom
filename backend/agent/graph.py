"""
HealthLoom LangGraph Workflow
Main agent orchestration using LangGraph
"""

import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END

# LangFuse is optional
try:
    from langfuse.decorators import observe, langfuse_context
    LANGFUSE_AVAILABLE = True
except Exception:
    # Create dummy decorators if langfuse not available
    def observe(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else decorator(args[0])
    
    class DummyLangfuseContext:
        def update_current_trace(self, **kwargs):
            pass
    
    langfuse_context = DummyLangfuseContext()
    LANGFUSE_AVAILABLE = False

from config import settings
from agent.state import AgentState, create_initial_state, state_to_dict
from agent.nodes.router import router_node, route_decision
from agent.nodes.document_processor import document_processor_node
from agent.nodes.medication_analyzer import medication_analyzer_node
from agent.nodes.conversation_manager import conversation_manager_node
from agent.nodes.recommendation_engine import recommendation_engine_node

logger = logging.getLogger(__name__)


# ==============================================
# LANGGRAPH WORKFLOW DEFINITION
# ==============================================

def create_healthloom_graph() -> StateGraph:
    """
    Create the HealthLoom LangGraph workflow
    
    Workflow:
        START → router → [document_processor | medication_analyzer | conversation_manager]
                      → recommendation_engine (optional) → END
    
    Returns:
        StateGraph: Compiled LangGraph workflow
    """
    logger.info("🏗️  Building HealthLoom LangGraph workflow...")
    
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("router", router_node)
    workflow.add_node("document_processor", document_processor_node)
    workflow.add_node("medication_analyzer", medication_analyzer_node)
    workflow.add_node("conversation_manager", conversation_manager_node)
    workflow.add_node("recommendation_engine", recommendation_engine_node)
    
    # Set entry point
    workflow.set_entry_point("router")
    
    # Add conditional edges from router
    workflow.add_conditional_edges(
        "router",
        route_decision,
        {
            "document_processor": "document_processor",
            "medication_analyzer": "medication_analyzer",
            "conversation_manager": "conversation_manager",
            "END": END
        }
    )
    
    # Add edges from specialized nodes
    workflow.add_conditional_edges(
        "document_processor",
        lambda state: state.get("next_node", "END"),
        {
            "recommendation_engine": "recommendation_engine",
            "END": END
        }
    )
    
    workflow.add_conditional_edges(
        "medication_analyzer",
        lambda state: state.get("next_node", "END"),
        {
            "END": END
        }
    )
    
    workflow.add_conditional_edges(
        "conversation_manager",
        lambda state: state.get("next_node", "END"),
        {
            "recommendation_engine": "recommendation_engine",
            "END": END
        }
    )
    
    workflow.add_conditional_edges(
        "recommendation_engine",
        lambda state: state.get("next_node", "END"),
        {
            "END": END
        }
    )
    
    # Compile graph
    app = workflow.compile()
    
    logger.info("✅ HealthLoom LangGraph workflow created successfully")
    return app


# Global workflow instance
healthloom_workflow = create_healthloom_graph()


# ==============================================
# WORKFLOW EXECUTION WITH LANGFUSE TRACING
# ==============================================

@observe(name="HealthLoom Agent")
async def run_healthloom_agent(
    user_id: str,
    input_type: str,
    user_message: str = None,
    uploaded_file_path: str = None,
    uploaded_file_type: str = None,
    user_profile: Dict[str, Any] = None,
    user_preferences: Dict[str, Any] = None,
    recent_tests: list = None,
    current_medications: list = None
) -> Dict[str, Any]:
    """
    Run the HealthLoom agent workflow with LangFuse tracing
    
    Args:
        user_id: UUID of the user
        input_type: Type of input ('document_upload', 'medication_query', 'chat', 'health_question')
        user_message: Optional user message
        uploaded_file_path: Optional uploaded file path
        uploaded_file_type: Optional file MIME type
        user_profile: User profile data
        user_preferences: User preferences from questionnaire
        recent_tests: Recent test results
        current_medications: Current medications
        
    Returns:
        Dict containing agent response and metadata
    """
    from uuid import UUID
    
    logger.info(f"🚀 Starting HealthLoom agent for user {user_id}, type: {input_type}")
    
    # Track in LangFuse if enabled
    if settings.langfuse_enabled:
        langfuse_context.update_current_trace(
            user_id=str(user_id),
            metadata={
                "input_type": input_type,
                "has_file": uploaded_file_path is not None
            }
        )
    
    try:
        # Create initial state
        initial_state = create_initial_state(
            user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
            input_type=input_type,
            user_message=user_message,
            uploaded_file_path=uploaded_file_path,
            uploaded_file_type=uploaded_file_type
        )
        
        # Add context data
        if user_profile:
            initial_state["user_profile"] = user_profile
            initial_state["user_limitations"] = user_profile.get("limitations_json", [])
            initial_state["user_conditions"] = user_profile.get("conditions_json", [])
        
        if user_preferences:
            initial_state["user_preferences"] = user_preferences
        
        if recent_tests:
            initial_state["recent_test_results"] = recent_tests
        
        if current_medications:
            initial_state["current_medications"] = current_medications
        
        # Run workflow
        logger.info("🔄 Executing LangGraph workflow...")
        final_state = await healthloom_workflow.ainvoke(initial_state)
        
        # Extract results
        result = {
            "success": len(final_state.get("errors", [])) == 0,
            "response": final_state.get("current_response", ""),
            "extracted_tests": final_state.get("extracted_tests", []),
            "medication_conflicts": final_state.get("medication_conflicts", []),
            "recommendations": final_state.get("recommendations", []),
            "ai_analysis": final_state.get("ai_analysis", {}),
            "context_used": final_state.get("context_used", {}),
            "processing_steps": final_state.get("processing_steps", []),
            "errors": final_state.get("errors", []),
            "state": state_to_dict(final_state)
        }
        
        logger.info(f"✅ HealthLoom agent completed successfully")
        
        # Log to LangFuse
        if settings.langfuse_enabled:
            langfuse_context.update_current_trace(
                output=result,
                metadata={
                    "tests_extracted": len(result["extracted_tests"]),
                    "recommendations_generated": len(result["recommendations"]),
                    "has_errors": not result["success"]
                }
            )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ HealthLoom agent failed: {e}")
        
        error_result = {
            "success": False,
            "response": "I apologize, but I encountered an error processing your request. Please try again.",
            "extracted_tests": [],
            "medication_conflicts": [],
            "recommendations": [],
            "ai_analysis": {},
            "context_used": {},
            "processing_steps": [],
            "errors": [str(e)],
            "state": {}
        }
        
        # Log error to LangFuse
        if settings.langfuse_enabled:
            langfuse_context.update_current_trace(
                output=error_result,
                level="ERROR",
                metadata={"error": str(e)}
            )
        
        return error_result


# ==============================================
# WORKFLOW VISUALIZATION
# ==============================================

def visualize_workflow():
    """
    Print workflow structure for debugging
    """
    print("=" * 60)
    print("HealthLoom LangGraph Workflow Structure")
    print("=" * 60)
    print("\nNodes:")
    print("  1. router - Routes requests to specialized nodes")
    print("  2. document_processor - Analyzes medical documents")
    print("  3. medication_analyzer - Checks medication conflicts")
    print("  4. conversation_manager - Handles chat conversations")
    print("  5. recommendation_engine - Generates health recommendations")
    print("\nWorkflow:")
    print("  START → router →")
    print("    ├─ document_upload → document_processor → recommendation_engine → END")
    print("    ├─ medication_query → medication_analyzer → END")
    print("    ├─ chat → conversation_manager → END")
    print("    └─ health_question → conversation_manager → recommendation_engine → END")
    print("=" * 60)


if __name__ == "__main__":
    # Visualize workflow when run directly
    visualize_workflow()
