"""
HealthLoom Medication Analyzer Node
Analyzes medications for conflicts and interactions using Gemini
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


async def medication_analyzer_node(state: AgentState) -> AgentState:
    """
    Medication Analyzer Node - Analyzes medications for conflicts
    
    Capabilities:
    - Drug-to-active-ingredient mapping
    - Duplicate medication detection
    - Drug-drug interaction analysis
    - Food-drug interaction warnings
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with medication_conflicts
    """
    logger.info("💊 Medication Analyzer: Starting medication analysis")
    
    updates = {
        "current_node": "medication_analyzer",
        "processing_steps": ["Medication Analyzer: Checking for conflicts"],
        "errors": [],
        "medication_conflicts": [],
        "next_node": "END"
    }
    
    # Get medication info from user message or state
    new_medication = state.get("user_message", "")
    current_medications = state.get("current_medications", [])
    
    if not new_medication:
        error_msg = "No medication information provided"
        logger.error(error_msg)
        updates["errors"].append(error_msg)
        return updates
    
    try:
        # Analyze medication
        updates["processing_steps"].append(f"Medication Analyzer: Analyzing '{new_medication}'")
        
        analysis_results = await analyze_medication(new_medication, current_medications)
        
        # Store conflict data
        updates["medication_conflicts"] = [analysis_results]
        
        # Generate response
        updates["current_response"] = format_medication_response(analysis_results)
        
        # Check severity
        has_critical = any(
            interaction.get("severity") in ["high", "critical"]
            for interaction in analysis_results.get("drug_interactions", [])
        )
        
        if has_critical:
            logger.warning("⚠️  CRITICAL drug interaction detected!")
            updates["processing_steps"].append("Medication Analyzer: CRITICAL interaction found")
        
        if analysis_results.get("is_duplicate"):
            logger.warning(f"⚠️  Duplicate medication detected: {analysis_results.get('duplicate_of')}")
            updates["processing_steps"].append("Medication Analyzer: Duplicate detected")
        
        logger.info("✅ Medication Analyzer: Analysis complete")
        
    except Exception as e:
        error_msg = f"Medication analysis failed: {str(e)}"
        logger.error(error_msg)
        updates["errors"].append(error_msg)
    
    return updates


async def analyze_medication(
    new_medication: str,
    current_medications: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Analyze medication using Gemini AI
    
    Args:
        new_medication: Name of new medication to analyze
        current_medications: List of current medications
        
    Returns:
        Dict containing analysis results
    """
    logger.info(f"🔍 Analyzing medication: {new_medication}")
    
    try:
        # Initialize Gemini model
        model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                "temperature": 0.3,  # Lower temperature for factual medical info
                "max_output_tokens": 4096,
                "response_mime_type": "application/json",
            }
        )
        
        # Generate prompt
        prompt = PromptTemplates.medication_analysis_prompt(
            new_medication,
            current_medications
        )
        
        # Call Gemini API
        logger.info("Calling Gemini API for medication analysis...")
        response = model.generate_content(prompt)
        
        # Parse response
        response_text = response.text
        logger.info(f"Received response from Gemini ({len(response_text)} chars)")
        
        # Extract JSON
        from agent.nodes.document_processor import _extract_json
        json_text = _extract_json(response_text)
        analysis_results = json.loads(json_text)
        
        logger.info("✅ Successfully parsed medication analysis")
        return analysis_results
        
    except Exception as e:
        logger.error(f"Error analyzing medication: {e}")
        return {
            "active_molecule": "Unknown",
            "is_duplicate": False,
            "duplicate_of": [],
            "drug_interactions": [],
            "food_interactions": [],
            "warnings": [f"Error analyzing medication: {str(e)}"],
            "overall_safety_assessment": "Unable to analyze - consult pharmacist",
            "conflict_summary": "Analysis failed"
        }


def format_medication_response(analysis: Dict[str, Any]) -> str:
    """
    Format medication analysis into user-friendly response
    
    Args:
        analysis: Analysis results from Gemini
        
    Returns:
        Formatted response string
    """
    response_parts = []
    
    # Header
    response_parts.append(f"**Medication Analysis Complete**\n")
    response_parts.append(f"Active Ingredient: {analysis.get('active_molecule', 'Unknown')}\n")
    
    # Duplicate check
    if analysis.get("is_duplicate"):
        response_parts.append("\n⚠️  **DUPLICATE DETECTED**")
        duplicates = analysis.get("duplicate_of", [])
        response_parts.append(f"This medication contains the same active ingredient as: {', '.join(duplicates)}")
        response_parts.append("**Recommendation**: Do not take both medications. Consult your doctor.\n")
    
    # Drug interactions
    drug_interactions = analysis.get("drug_interactions", [])
    if drug_interactions:
        response_parts.append("\n**Drug Interactions**:")
        for interaction in drug_interactions:
            severity = interaction.get("severity", "unknown").upper()
            med = interaction.get("interacting_medication", "")
            mech = interaction.get("mechanism", "")
            rec = interaction.get("recommendation", "")
            
            emoji = "🔴" if severity in ["HIGH", "CRITICAL"] else "🟡" if severity == "MEDIUM" else "🟢"
            response_parts.append(f"{emoji} **{severity}**: {med}")
            response_parts.append(f"   {mech}")
            response_parts.append(f"   → {rec}")
    
    # Food interactions
    food_interactions = analysis.get("food_interactions", [])
    if food_interactions:
        response_parts.append("\n**Food Interactions**:")
        for interaction in food_interactions:
            food = interaction.get("food_item", "")
            itype = interaction.get("interaction_type", "")
            reason = interaction.get("reason", "")
            rec = interaction.get("recommendation", "")
            
            emoji = "🚫" if itype == "avoid" else "✅"
            response_parts.append(f"{emoji} **{food}**: {reason}")
            response_parts.append(f"   → {rec}")
    
    # Warnings
    warnings = analysis.get("warnings", [])
    if warnings:
        response_parts.append("\n**Important Warnings**:")
        for warning in warnings:
            response_parts.append(f"⚠️  {warning}")
    
    # Overall assessment
    response_parts.append(f"\n**Overall Safety**: {analysis.get('overall_safety_assessment', 'Unknown')}")
    response_parts.append(f"\n{analysis.get('conflict_summary', '')}")
    
    response_parts.append("\n\n💡 **Remember**: Always consult your doctor or pharmacist before starting new medications.")
    
    return "\n".join(response_parts)


# Future: When medication API is integrated
async def query_medication_api(medication_name: str) -> Dict[str, Any]:
    """
    Query external medication database API (to be implemented)
    
    Args:
        medication_name: Name of medication to query
        
    Returns:
        Medication information from API
    """
    # TODO: Implement medication API integration
    
    logger.info("Medication API not yet configured - using Gemini knowledge base")
    return {
        "source": "gemini_knowledge",
        "api_available": False
    }
