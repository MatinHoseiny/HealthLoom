"""
HealthLoom Recommendation Engine Node
Generates personalized health recommendations based on test results
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


async def recommendation_engine_node(state: AgentState) -> AgentState:
    """
    Recommendation Engine Node - Generates actionable health recommendations
    
    Capabilities:
    - Prioritized action items
    - Limitation-aware suggestions
    - Context-specific advice
    - Retest timelines
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with recommendations
    """
    logger.info("💡 Recommendation Engine: Generating personalized recommendations")
    
    updates = {
        "current_node": "recommendation_engine",
        "processing_steps": ["Recommendation Engine: Analyzing health data"],
        "errors": [],
        "recommendations": [],
        "next_node": "END"
    }
    
    try:
        # Get relevant data
        test_results = state.get("recent_test_results", [])
        extracted_tests = state.get("extracted_tests", [])
        medications = state.get("current_medications", [])
        user_profile = state.get("user_profile", {})
        
        # Combine all test results
        all_tests = test_results + extracted_tests
        
        if not all_tests:
            logger.info("No test results available for recommendations")
            updates["processing_steps"].append("Recommendation Engine: No test data available")
            return updates
        
        # Generate recommendations
        updates["processing_steps"].append("Recommendation Engine: Creating action plan")
        
        recommendations= await generate_recommendations(
            test_results=all_tests,
            medications=medications,
            user_profile=user_profile
        )
        
        updates["recommendations"] = recommendations.get("recommendations", [])
        
        # Add to AI analysis
        curr_ai_analysis = state.get("ai_analysis", {})
        curr_ai_analysis["overall_health_summary"] = recommendations.get("overall_health_summary", "")
        curr_ai_analysis["positive_findings"] = recommendations.get("positive_findings", [])
        curr_ai_analysis["areas_for_improvement"] = recommendations.get("areas_for_improvement", [])
        updates["ai_analysis"] = curr_ai_analysis
        
        # Update response to include recommendations
        rec_count = len(updates["recommendations"])
        logger.info(f"✅ Recommendation Engine: Generated {rec_count} recommendations")
        updates["processing_steps"].append(f"Recommendation Engine: Created {rec_count} action items")
        
    except Exception as e:
        error_msg = f"Recommendation generation failed: {str(e)}"
        logger.error(error_msg)
        updates["errors"].append(error_msg)
    
    return updates


async def generate_recommendations(
    test_results: List[Dict[str, Any]],
    medications: List[Dict[str, Any]],
    user_profile: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate personalized health recommendations using Gemini
    
    Args:
        test_results: All test results (recent + newly uploaded)
        medications: Current medications
        user_profile: User profile with limitations
        
    Returns:
        Dict containing recommendations and health summary
    """
    logger.info(f"🔍 Generating recommendations from {len(test_results)} test results")
    
    try:
        # Initialize Gemini model
        model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                "temperature": 0.5,  # Balanced for creative but accurate recommendations
                "max_output_tokens": 6144,
            }
        )
        
        # Generate prompt
        prompt = PromptTemplates.recommendation_engine_prompt(
            test_results=test_results,
            medications=medications,
            user_profile=user_profile
        )
        
        # Call Gemini API
        logger.info("Calling Gemini API for recommendations...")
        response = model.generate_content(prompt)
        
        # Parse response
        response_text = response.text
        logger.info(f"Received response from Gemini ({len(response_text)} chars)")
        
        # Extract JSON
        from agent.nodes.document_processor import extract_json_from_response
        json_text = extract_json_from_response(response_text)
        recommendations_data = json.loads(json_text)
        
        logger.info("✅ Successfully generated recommendations")
        return recommendations_data
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        return {
            "recommendations": [
                {
                    "title": "Review Your Results",
                    "priority": "medium",
                    "category": "General",
                    "action_items": [
                        "Review your test results with your healthcare provider",
                        "Keep track of any symptoms or changes",
                        "Schedule a follow-up appointment"
                    ],
                    "explanation": f"Unable to generate specific recommendations due to an error: {str(e)}",
                    "retest_timeline": "As advised by your doctor",
                    "limitation_adjusted": False,
                    "adjustments_made": None
                }
            ],
            "overall_health_summary": "Please consult your healthcare provider to review your results.",
            "positive_findings": [],
            "areas_for_improvement": ["Consult with healthcare provider"]
        }


def format_recommendations_for_display(recommendations: List[Dict[str, Any]]) -> str:
    """
    Format recommendations into user-friendly text
    
    Args:
        recommendations: List of recommendation dictionaries
        
    Returns:
        Formatted string for display
    """
    if not recommendations:
        return "No specific recommendations at this time. Keep up the good work!"
    
    output_parts = []
    output_parts.append("# 📋 Your Personalized Health Action Plan\n")
    
    # Sort by priority
    priority_order = {"high": 1, "medium": 2, "low": 3}
    sorted_recs = sorted(
        recommendations,
        key=lambda x: priority_order.get(x.get("priority", "medium"), 2)
    )
    
    for i, rec in enumerate(sorted_recs, 1):
        priority = rec.get("priority", "medium").upper()
        emoji = "🔴" if priority == "HIGH" else "🟡" if priority == "MEDIUM" else "🟢"
        
        output_parts.append(f"## {i}. {emoji} {rec.get('title', 'Recommendation')}")
        output_parts.append(f"**Priority**: {priority} | **Category**: {rec.get('category', 'General')}\n")
        
        # Explanation
        output_parts.append(f"**Why This Matters**:")
        output_parts.append(f"{rec.get('explanation', '')}\n")
        
        # Action items
        output_parts.append(f"**Action Steps**:")
        for action in rec.get("action_items", []):
            output_parts.append(f"- {action}")
        
        # Retest timeline
        if rec.get("retest_timeline"):
            output_parts.append(f"\n**Retest In**: {rec.get('retest_timeline')}")
        
        # Limitations adjustment note
        if rec.get("limitation_adjusted"):
            output_parts.append(f"\n✨ *Adjusted for your limitations: {rec.get('adjustments_made')}*")
        
        output_parts.append("\n---\n")
    
    return "\n".join(output_parts)
