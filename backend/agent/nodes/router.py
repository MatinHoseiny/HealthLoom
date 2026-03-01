"""
HealthLoom Router Node
Intelligently routes requests to appropriate agent nodes
"""

import logging
from typing import Dict, Any
from agent.state import AgentState

logger = logging.getLogger(__name__)


async def router_node(state: AgentState) -> AgentState:
    """
    Router node - determines which specialized node should handle the request
    
    Routes based on input_type:
    - 'document_upload' → document_processor
    - 'medication_query' → medication_analyzer
    - 'chat' → conversation_manager
    - 'health_question' → conversation_manager → recommendation_engine
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with next_node set
    """
    logger.info(f"🔀 Router: Processing input type '{state['input_type']}'")
    
    input_type = state["input_type"]
    
    updates = {
        "current_node": "router",
        "processing_steps": ["Router: Analyzing request type"],
        "errors": [],
    }
    
    # Route based on input type
    if input_type == "document_upload":
        updates["next_node"] = "document_processor"
        updates["processing_steps"].append("Router: Routing to document processor")
        logger.info("→ Routing to: document_processor")
        
    elif input_type == "medication_query":
        updates["next_node"] = "medication_analyzer"
        updates["processing_steps"].append("Router: Routing to medication analyzer")
        logger.info("→ Routing to: medication_analyzer")
        
    elif input_type == "chat":
        updates["next_node"] = "conversation_manager"
        updates["processing_steps"].append("Router: Routing to conversation manager")
        logger.info("→ Routing to: conversation_manager")
        
    elif input_type == "health_question":
        updates["next_node"] = "conversation_manager"
        updates["processing_steps"].append("Router: Routing to conversation manager for health question")
        logger.info("→ Routing to: conversation_manager (then recommendation_engine)")
        
    else:
        logger.warning(f"Unknown input type '{input_type}', defaulting to conversation_manager")
        updates["next_node"] = "conversation_manager"
        updates["processing_steps"].append(f"Router: Unknown type '{input_type}', using conversation manager")
    
    return updates


def route_decision(state: AgentState) -> str:
    """
    Decision function for LangGraph conditional routing
    
    Args:
        state: Current agent state
        
    Returns:
        str: Name of the next node to execute
    """
    next_node = state.get("next_node")
    
    if not next_node:
        logger.error("No next_node set in state, defaulting to END")
        return "END"
    
    return next_node
