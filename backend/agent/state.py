"""
HealthLoom Agent State Management
Defines the state structure for LangGraph agent workflow
"""

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from datetime import datetime
from uuid import UUID
import operator


class AgentState(TypedDict):
    """
    State structure for HealthLoom LangGraph agent
    
    This state is passed between all agent nodes and maintains
    the conversation context, user data, and processing results.
    """
    
    # User Context
    user_id: UUID
    user_profile: Dict[str, Any]
    
    # Current Request
    input_type: str  # 'document_upload', 'medication_query', 'chat', 'health_question'
    user_message: Optional[str]
    uploaded_file_path: Optional[str]
    uploaded_file_type: Optional[str]
    
    # Health Data Context
    recent_test_results: List[Dict[str, Any]]
    current_medications: List[Dict[str, Any]]
    user_limitations: List[str]
    user_conditions: List[str]
    
    # Processing Results
    extracted_tests: Annotated[List[Dict[str, Any]], operator.add]
    medication_conflicts: List[Dict[str, Any]]
    ai_analysis: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    
    # Conversation
    chat_history: List[Dict[str, str]]
    current_response: str
    context_used: Dict[str, Any]
    
    # Agent Metadata
    current_node: str
    next_node: Optional[str]
    processing_steps: Annotated[List[str], operator.add]
    errors: Annotated[List[str], operator.add]
    
    # Session
    session_id: Optional[UUID]
    timestamp: datetime


def create_initial_state(
    user_id: UUID,
    input_type: str,
    user_message: Optional[str] = None,
    uploaded_file_path: Optional[str] = None,
    uploaded_file_type: Optional[str] = None
) -> AgentState:
    """
    Create initial state for agent workflow
    
    Args:
        user_id: UUID of the user
        input_type: Type of input ('document_upload', 'medication_query', 'chat', 'health_question')
        user_message: Optional user message for chat
        uploaded_file_path: Optional path to uploaded file
        uploaded_file_type: Optional file type
        
    Returns:
        AgentState: Initial state dictionary
    """
    return AgentState(
        # User Context
        user_id=user_id,
        user_profile={},
        
        # Current Request
        input_type=input_type,
        user_message=user_message,
        uploaded_file_path=uploaded_file_path,
        uploaded_file_type=uploaded_file_type,
        
        # Health Data Context
        recent_test_results=[],
        current_medications=[],
        user_limitations=[],
        user_conditions=[],
        
        # Processing Results
        extracted_tests=[],
        medication_conflicts=[],
        ai_analysis={},
        recommendations=[],
        
        # Conversation
        chat_history=[],
        current_response="",
        context_used={},
        
        # Agent Metadata
        current_node="router",
        next_node=None,
        processing_steps=[],
        errors=[],
        
        # Session
        session_id=None,
        timestamp=datetime.now()
    )


def state_to_dict(state: AgentState) -> Dict[str, Any]:
    """
    Convert AgentState to serializable dictionary
    For storing in database
    """
    return {
        "user_id": str(state["user_id"]),
        "user_profile": state["user_profile"],
        "input_type": state["input_type"],
        "user_message": state["user_message"],
        "recent_test_results": state["recent_test_results"],
        "current_medications": state["current_medications"],
        "extracted_tests": state["extracted_tests"],
        "medication_conflicts": state["medication_conflicts"],
        "ai_analysis": state["ai_analysis"],
        "recommendations": state["recommendations"],
        "chat_history": state["chat_history"],
        "current_response": state["current_response"],
        "context_used": state["context_used"],
        "processing_steps": state["processing_steps"],
        "session_id": str(state["session_id"]) if state["session_id"] else None,
        "timestamp": state["timestamp"].isoformat()
    }


def dict_to_state(data: Dict[str, Any]) -> AgentState:
    """
    Convert dictionary back to AgentState
    For loading from database
    """
    from uuid import UUID
    from datetime import datetime
    
    return AgentState(
        user_id=UUID(data["user_id"]),
        user_profile=data.get("user_profile", {}),
        input_type=data["input_type"],
        user_message=data.get("user_message"),
        uploaded_file_path=data.get("uploaded_file_path"),
        uploaded_file_type=data.get("uploaded_file_type"),
        recent_test_results=data.get("recent_test_results", []),
        current_medications=data.get("current_medications", []),
        user_limitations=data.get("user_limitations", []),
        user_conditions=data.get("user_conditions", []),
        extracted_tests=data.get("extracted_tests", []),
        medication_conflicts=data.get("medication_conflicts", []),
        ai_analysis=data.get("ai_analysis", {}),
        recommendations=data.get("recommendations", []),
        chat_history=data.get("chat_history", []),
        current_response=data.get("current_response", ""),
        context_used=data.get("context_used", {}),
        current_node=data.get("current_node", "router"),
        next_node=data.get("next_node"),
        processing_steps=data.get("processing_steps", []),
        errors=data.get("errors", []),
        session_id=UUID(data["session_id"]) if data.get("session_id") else None,
        timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now()
    )
