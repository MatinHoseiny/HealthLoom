"""
HealthLoom Conversation Manager Node
Manages AI chatbot conversations with health context
"""

import logging
import json
from typing import Dict, Any, List

import google.generativeai as genai

from config import settings
from agent.state import AgentState
from agent.prompts import PromptTemplates

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)


async def conversation_manager_node(state: AgentState) -> AgentState:
    """
    Conversation Manager Node - Handles AI chatbot with health context
    
    Capabilities:
    - Context-aware conversations using user's health data
    - Memory of previous interactions
    - Personalized health insights
    - Empathetic responses
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with current_response and context_used
    """
    logger.info("💬 Conversation Manager: Processing chat message")
    
    updates = {
        "current_node": "conversation_manager",
        "processing_steps": ["Conversation Manager: Generating response"],
        "errors": [],
        "next_node": "END"
    }
    
    user_message = state.get("user_message", "")
    
    if not user_message:
        error_msg = "No user message provided"
        logger.error(error_msg)
        updates["errors"].append(error_msg)
        return updates
    
    try:
        # Generate AI response with health context
        updates["processing_steps"].append("Conversation Manager: Loading health context")
        
        response_data = await generate_contextual_response(
            user_message=user_message,
            user_profile=state.get("user_profile", {}),
            recent_tests=state.get("recent_test_results", []),
            current_medications=state.get("current_medications", []),
            chat_history=state.get("chat_history", [])
        )
        
        # Update state
        updates["current_response"] = response_data.get("response", "")
        updates["context_used"] = response_data.get("context_used", {})
        
        # Add to chat history
        updates["chat_history"] = list(state.get("chat_history", []))
        updates["chat_history"].append({
            "role": "user",
            "content": user_message
        })
        updates["chat_history"].append({
            "role": "assistant",
            "content": updates["current_response"]
        })
        
        # Store suggestions for UI
        curr_ai_analysis = dict(state.get("ai_analysis", {}))
        curr_ai_analysis["suggestions"] = response_data.get("suggestions", [])
        updates["ai_analysis"] = curr_ai_analysis
        
        # Check if medical attention needed
        priority = response_data.get("priority_level", "low")
        if priority in ["high", "critical"]:
            logger.warning(f"⚠️  High priority health concern detected: {priority}")
            updates["processing_steps"].append(f"Conversation Manager: High priority ({priority})")
        
        logger.info("✅ Conversation Manager: Response generated")
        
        # Decide next node based on input type
        if state.get("input_type") == "health_question":
            updates["next_node"] = "recommendation_engine"
        
    except Exception as e:
        error_msg = f"Conversation generation failed: {str(e)}"
        logger.error(error_msg)
        updates["errors"].append(error_msg)
        updates["current_response"] = "I apologize, but I encountered an error processing your message. Please try again."
    
    return updates


async def generate_contextual_response(
    user_message: str,
    user_profile: Dict[str, Any],
    recent_tests: List[Dict[str, Any]],
    current_medications: List[Dict[str, Any]],
    chat_history: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    Generate AI response with full health context
    
    Args:
        user_message: User's message
        user_profile: User profile data
        recent_tests: Recent test results
        current_medications: Current medications
        chat_history: Previous chat messages
        
    Returns:
        Dict containing response and metadata
    """
    logger.info(f"🔍 Generating contextual response for: {user_message[:50]}...")
    
    try:
        # Initialize Gemini model
        model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                "temperature": settings.gemini_temperature,
                "max_output_tokens": settings.gemini_max_tokens,
            }
        )
        
        # Generate prompt with full context
        prompt = PromptTemplates.health_chat_prompt(
            user_message=user_message,
            user_profile=user_profile,
            recent_tests=recent_tests,
            current_medications=current_medications,
            chat_history=chat_history
        )
        
        # Call Gemini API
        logger.info("Calling Gemini API for conversational response...")
        response = model.generate_content(prompt)
        
        # Parse response
        response_text = response.text
        logger.info(f"Received response from Gemini ({len(response_text)} chars)")
        
        # Extract JSON
        from agent.nodes.document_processor import _extract_json
        json_text = _extract_json(response_text)
        
        try:
            response_data = json.loads(json_text)
        except Exception as json_err:
            logger.warning(f"JSON Parse failed, attempting regex salvage: {json_err}")
            import re
            # Salvage the most important part: the response string
            res_match = re.search(r'"response"\s*:\s*"(.*?)"\s*(?:,|})', json_text, re.DOTALL)
            if res_match:
                # Clean up any literal newlines that broke the JSON parser
                fallback_msg = res_match.group(1).replace('\n', ' ').replace('\r', ' ')
                response_data = {
                    "response": fallback_msg,
                    "suggestions": [],
                    "key_points": [],
                    "priority_level": "moderate"
                }
                logger.info("Successfully salvaged chat response via regex.")
            else:
                logger.error(f"Failed to salvage JSON. Raw text: {json_text}")
                raise json_err
                
        
        logger.info("✅ Successfully generated contextual response")
        return response_data
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return {
            "response": "I apologize, but I'm having trouble accessing your health data right now. Please try again or rephrase your question.",
            "context_used": {},
            "suggestions": [
                "Can you tell me about my recent test results?",
                "What should I know about my medications?",
                "Do I have any abnormal test results?"
            ],
            "priority_level": "low"
        }


async def stream_gemini_response(
    user_message: str,
    user_profile: Dict[str, Any],
    recent_tests: List[Dict[str, Any]],
    current_medications: List[Dict[str, Any]],
    chat_history: List[Dict[str, str]]
):
    """
    Stream Gemini response for real-time chat experience
    
    This is a generator function for Server-Sent Events (SSE)
    
    Args:
        Same as generate_contextual_response
        
    Yields:
        str: Chunks of response text
    """
    logger.info("🌊 Starting streaming response...")
    
    try:
        # Initialize Gemini model
        model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                "temperature": settings.gemini_temperature,
                "max_output_tokens": settings.gemini_max_tokens,
            }
        )
        
        # Generate prompt
        prompt = PromptTemplates.health_chat_prompt(
            user_message=user_message,
            user_profile=user_profile,
            recent_tests=recent_tests,
            current_medications=current_medications,
            chat_history=chat_history
        )
        
        # Stream response
        response = model.generate_content(prompt, stream=True)
        
        for chunk in response:
            if chunk.text:
                yield chunk.text
        
        logger.info("✅ Streaming complete")
        
    except Exception as e:
        logger.error(f"Error in streaming response: {e}")
        yield f"Error: {str(e)}"
