"""
HealthLoom Health Analyzer
AI-powered health analysis and insights generation
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import google.generativeai as genai
from config import settings

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)


async def generate_overall_health_summary(
    user_data: Dict[str, Any],
    test_results: List[Dict[str, Any]],
    medications: List[Dict[str, Any]]
) -> str:
    """
    Generate an AI-powered overall health summary based on all user data.
    
    Args:
        user_data: User profile (age, gender, conditions, limitations)
        test_results: List of test results
        medications: List of active medications
        
    Returns:
        A comprehensive health summary text
    """
    try:
        # Prepare context
        user_context = f"""
Patient Profile:
- Age: {user_data.get('age', 'Unknown')}
- Gender: {user_data.get('gender', 'Unknown')}
- Known Conditions: {', '.join(user_data.get('conditions_json', [])) or 'None reported'}
- Limitations: {', '.join(user_data.get('limitations_json', [])) or 'None reported'}

Recent Test Results ({len(test_results)} tests):
"""
        
        # Add test results summary
        for test in test_results[:20]:  # Limit to 20 most recent
            status = "⚠️ ABNORMAL" if test.get('is_abnormal') else "✓ Normal"
            user_context += f"- {test.get('test_name')}: {test.get('value')} {test.get('unit', '')} ({test.get('category', 'General')}) - {status}\n"
        
        # Add medications
        if medications:
            user_context += f"\nActive Medications ({len(medications)}):\n"
            for med in medications:
                user_context += f"- {med.get('brand_name')} ({med.get('active_molecule', 'Unknown')}): {med.get('dosage', 'N/A')}\n"
        else:
            user_context += "\nActive Medications: None\n"
        
        # Create prompt
        prompt = f"""You are a medical AI assistant analyzing a patient's overall health condition.

{user_context}

Based on this information, provide a concise, friendly, and informative overall health summary (2-3 sentences).

Guidelines:
1. Start with an overall assessment (e.g., "You appear to be in good health overall" or "There are some areas that need attention")
2. Highlight the most important findings (abnormal results, concerning trends)
3. Be reassuring but honest
4. Use simple, non-technical language
5. Do NOT provide specific medical advice or treatment recommendations
6. Keep it brief and easy to understand at a glance

Generate the summary:"""

        # Call Gemini
        model = genai.GenerativeModel(settings.gemini_model)
        response = model.generate_content(prompt)
        
        summary = response.text.strip()
        logger.info(f"Generated health summary: {summary[:100]}...")
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating health summary: {e}")
        return "Unable to generate health summary at this time. Please consult with your healthcare provider for a comprehensive health assessment."


async def analyze_abnormal_result(
    test_result: Dict[str, Any],
    user_context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Analyze a single abnormal test result and provide interpretation, risks, and recommendations.
    
    Args:
        test_result: Single test result data
        user_context: User profile context
        
    Returns:
        {
            "test_name": str,
            "value": str,
            "unit": str,
            "is_high": bool,
            "is_low": bool,
            "interpretation": str,
            "risks": List[str],
            "recommendations": List[str]
        }
    """
    try:
        test_name = test_result.get('test_name')
        value = test_result.get('value')
        unit = test_result.get('unit', '')
        reference_range = test_result.get('reference_range', 'Unknown')
        
        # Create prompt
        prompt = f"""Analyze this abnormal test result for a patient:

Test: {test_name}
Value: {value} {unit}
Reference Range: {reference_range}
Patient Age: {user_context.get('age', 'Unknown')}
Patient Gender: {user_context.get('gender', 'Unknown')}

IMPORTANT: Provide DETAILED and INFORMATIVE medical analysis. Be educational and specific.

Provide a JSON response with the following structure:
{{
  "is_high": true/false,
  "is_low": true/false,
  "interpretation": "Clear, detailed explanation of what this abnormal value means and why it's concerning (2-3 sentences)",
  "possible_causes": ["Specific cause 1", "Specific cause 2", "Specific cause 3"],
  "risks": ["Specific health risk/complication 1", "Specific health risk/complication 2", "Specific health risk/complication 3"],
  "recommendations": ["Specific lifestyle recommendation 1", "Specific dietary recommendation 2", "Specific action 3", "Consult your healthcare provider for proper diagnosis and personalized treatment plan"]
}}

Guidelines:
- In "interpretation": Provide a clear, informative explanation of what this value indicates
- In "possible_causes": List 3-4 SPECIFIC medical conditions or factors that commonly cause this abnormality
- In "risks": List 3-4 SPECIFIC health complications or diseases this abnormality may lead to if left untreated
- In "recommendations": Provide 2-3 ACTIONABLE lifestyle/dietary changes, then ALWAYS end with consulting a healthcare provider
- BE SPECIFIC - use actual medical terminology explained in simple terms
- BE EDUCATIONAL - the patient wants to understand their health
- DON'T BE VAGUE - avoid phrases like "various conditions" or "potential issues"
- ALWAYS emphasize consulting a doctor for proper medical care

JSON response:"""

        # Call Gemini
        model = genai.GenerativeModel(settings.gemini_model)
        response = model.generate_content(prompt)
        
        # Parse JSON response
        import json
        response_text = response.text.strip()
        
        # Extract JSON from markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        analysis = json.loads(response_text)
        
        # Build complete response
        result = {
            "test_name": test_name,
            "value": value,
            "unit": unit,
            "is_high": analysis.get("is_high", False),
            "is_low": analysis.get("is_low", False),
            "interpretation": analysis.get("interpretation", "This value is outside the normal range."),
            "possible_causes": analysis.get("possible_causes", [])[:4],  # Limit to 4
            "risks": analysis.get("risks", [])[:4],  # Limit to 4
            "recommendations": analysis.get("recommendations", [])[:4]  # Limit to 4
        }
        
        logger.info(f"Analyzed abnormal result for {test_name}")
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing abnormal result: {e}")
        return {
            "test_name": test_result.get('test_name'),
            "value": test_result.get('value'),
            "unit": test_result.get('unit', ''),
            "is_high": False,
            "is_low": False,
            "interpretation": "This value is outside the normal range. Please consult your healthcare provider.",
            "risks": ["Potential health impact - consult your doctor"],
            "recommendations": ["Schedule a follow-up with your healthcare provider"]
        }


async def get_detailed_advice(
    test_name: str,
    test_value: str,
    user_context: Dict[str, Any]
) -> str:
    """
    Get detailed AI advice for a specific health issue.
    
    Args:
        test_name: Name of the test
        test_value: Test value
        user_context: User profile and context
        
    Returns:
        Detailed advice text
    """
    try:
        prompt = f"""Provide detailed health advice for a patient with an abnormal test result.

Test: {test_name}
Value: {test_value}
Patient Age: {user_context.get('age', 'Unknown')}
Patient Gender: {user_context.get('gender', 'Unknown')}
Known Conditions: {', '.join(user_context.get('conditions_json', [])) or 'None'}

Provide comprehensive advice covering:
1. What this result means in simple terms
2. Lifestyle modifications that may help
3. Dietary recommendations
4. Exercise suggestions
5. When to see a doctor
6. Questions to ask your healthcare provider

Important:
- Use clear, simple language
- Be supportive and encouraging
- Do NOT prescribe medication or specific medical treatments
- Emphasize the importance of professional medical consultation
- Keep total response under 300 words

Your advice:"""

        # Call Gemini
        model = genai.GenerativeModel(settings.gemini_model)
        response = model.generate_content(prompt)
        
        advice = response.text.strip()
        logger.info(f"Generated detailed advice for {test_name}")
        
        return advice
        
    except Exception as e:
        logger.error(f"Error generating advice: {e}")
        return "Unable to generate advice at this time. Please consult with your healthcare provider for personalized recommendations."
