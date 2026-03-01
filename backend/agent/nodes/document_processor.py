"""
HealthLoom Document Processor Node
Processes medical documents using Gemini multimodal capabilities
"""

import logging
import json
import re
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

import google.generativeai as genai
from PIL import Image

from config import settings
from agent.state import AgentState
from agent.prompts import PromptTemplates

logger = logging.getLogger(__name__)

# Configure Gemini
genai.configure(api_key=settings.gemini_api_key)


async def document_processor_node(state: AgentState) -> AgentState:
    """
    Document Processor Node - Analyzes medical documents using Gemini

    Capabilities:
    - OCR text extraction from images and PDFs
    - Graph and chart analysis
    - Medical image interpretation
    - Test result categorization
    - Semantic normalization

    Args:
        state: Current agent state with uploaded_file_path

    Returns:
        Updated state with extracted_tests and ai_analysis
    """
    logger.info("📄 Document Processor: Starting document analysis")

    updates = {
        "current_node": "document_processor",
        "processing_steps": ["Document Processor: Loading document"],
        "errors": [],
        "extracted_tests": [],
        "ai_analysis": {},
        "next_node": "END"
    }

    file_path = state.get("uploaded_file_path")
    file_type = state.get("uploaded_file_type", "unknown")

    if not file_path:
        error_msg = "No file path provided for document processing"
        logger.error(error_msg)
        updates["errors"].append(error_msg)
        return updates

    try:
        updates["processing_steps"].append(f"Document Processor: Analyzing {file_type}")

        analysis_results = await analyze_medical_document(file_path, file_type)

        # Extract test results
        extracted_tests = analysis_results.get("extracted_tests", [])
        updates["extracted_tests"] = extracted_tests

        # Store full AI analysis
        updates["ai_analysis"] = {
            "overall_analysis": analysis_results.get("overall_analysis", ""),
            "patient_info": analysis_results.get("patient_info", {}),
            "recommendations": analysis_results.get("recommendations", []),
            "processing_timestamp": datetime.now().isoformat()
        }

        logger.info(f"✅ Document Processor: Extracted {len(extracted_tests)} test results")
        updates["processing_steps"].append(f"Document Processor: Extracted {len(extracted_tests)} tests")

        # Route to recommendations if abnormal results found
        abnormal_count = sum(1 for test in extracted_tests if test.get("is_abnormal"))
        if abnormal_count > 0:
            logger.info(f"⚠️  Found {abnormal_count} abnormal results, routing to recommendation engine")
            updates["next_node"] = "recommendation_engine"

    except Exception as e:
        error_msg = f"Document processing failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        updates["errors"].append(error_msg)

    return updates


async def analyze_medical_document(file_path: str, file_type: str) -> Dict[str, Any]:
    """
    Analyze medical document using Gemini multimodal API

    Args:
        file_path: Path to the uploaded file
        file_type: MIME type of the file

    Returns:
        Dict containing extracted tests and analysis
    """
    logger.info(f"🔍 Analyzing document: {file_path}")

    try:
        # Initialize Gemini model
        # Use a compact prompt that naturally produces JSON, then parse it.
        model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config={
                "temperature": 0.1,  # Low temperature for accurate extraction
                "max_output_tokens": 8192,
            }
        )

        # Generate the analysis prompt
        prompt = PromptTemplates.document_analysis_prompt(file_type)

        # Prepare file content for Gemini
        file_content = None

        if "image" in file_type:
            image = Image.open(file_path)
            file_content = image
            logger.info(f"Loaded image: {image.size}")

        elif "pdf" in file_type:
            # Convert PDF to images page-by-page for maximum extraction coverage
            try:
                from pdf2image import convert_from_path
                images = convert_from_path(file_path, dpi=150)
                if images:
                    file_content = images
                    logger.info(f"Converted PDF to {len(images)} images")
            except Exception as e:
                logger.warning(f"PDF-to-image failed, falling back to upload: {e}")
                try:
                    uploaded_file = genai.upload_file(file_path)
                    file_content = uploaded_file
                    logger.info(f"Uploaded PDF: {uploaded_file.name}")
                except Exception as e2:
                    logger.error(f"Both PDF methods failed: {e2}")

        # Call Gemini API
        logger.info("Calling Gemini API for document analysis...")

        if file_content is None:
            # Plain-text fallback
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text_content = f.read()
            response = model.generate_content([prompt, text_content])
            raw_responses = [response.text]

        elif isinstance(file_content, list):
            # Process one page at a time.
            raw_responses = []
            for i, page_img in enumerate(file_content):
                logger.info(f"Analyzing page {i+1}/{len(file_content)}...")
                page_response = model.generate_content([prompt, page_img])
                raw_responses.append(page_response.text)
        else:
            # Single file/image
            response = model.generate_content([prompt, file_content])
            raw_responses = [response.text]

        logger.info(f"Received {len(raw_responses)} response(s) from Gemini")

        # Parse and aggregate results
        analysis_results = {
            "patient_info": {},
            "extracted_tests": [],
            "overall_analysis": ""
        }

        for idx, response_text in enumerate(raw_responses):
            logger.info(f"Response {idx+1} length: {len(response_text)} chars")

            try:
                json_text = _extract_json(response_text)
                page_results = json.loads(json_text)
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"JSON parse failed for response {idx+1}: {e}")
                logger.warning(f"Raw start: {response_text[:300]}")
                page_results = {}

            # Merge patient info (take first non-empty one)
            if page_results.get("patient_info") and not analysis_results["patient_info"].get("name"):
                analysis_results["patient_info"] = page_results["patient_info"]

            # Merge overall analysis
            if page_results.get("overall_analysis") and not analysis_results["overall_analysis"]:
                analysis_results["overall_analysis"] = page_results.get("overall_analysis", "")

            # Collect tests from this page
            tests = page_results.get("extracted_tests", [])
            logger.info(f"Response {idx+1}: {len(tests)} tests extracted")
            analysis_results["extracted_tests"].extend(tests)

        # Normalize and deduplicate extracted tests
        analysis_results["extracted_tests"] = _normalize_and_deduplicate(
            analysis_results["extracted_tests"]
        )

        total = len(analysis_results["extracted_tests"])
        logger.info(f"✅ Total unique tests extracted: {total}")
        return analysis_results

    except Exception as e:
        logger.error(f"Error analyzing document: {e}", exc_info=True)
        return {
            "extracted_tests": [],
            "overall_analysis": f"Error analyzing document: {str(e)}",
            "patient_info": {}
        }


def _extract_json(text: str) -> str:
    """
    Extract JSON from Gemini response text.
    Handles markdown code blocks, bare JSON, and truncated responses.
    """
    # Strip markdown code fences if present
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        text = text[start:end].strip() if end != -1 else text[start:].strip()
    elif "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        text = text[start:end].strip() if end != -1 else text[start:].strip()

    # Find outermost JSON object start
    start = text.find("{")
    if start == -1:
        return text

    # Walk through to find matching close brace
    brace_count = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            brace_count += 1
        elif text[i] == "}":
            brace_count -= 1
            if brace_count == 0:
                # Complete valid JSON found
                return text[start:i + 1]

    # JSON is truncated — try to salvage complete test objects via regex
    partial = text[start:]
    return _salvage_truncated_json(partial)


def _salvage_truncated_json(partial: str) -> str:
    """
    Salvage complete test entries from a truncated JSON response.
    Matches complete JSON objects within the extracted_tests array.
    """
    # Match the patient_info block if present
    patient_info = {}
    pi_match = re.search(r'"patient_info"\s*:\s*(\{[^}]*\})', partial, re.DOTALL)
    if pi_match:
        try:
            patient_info = json.loads(pi_match.group(1))
        except Exception:
            pass

    # Match all complete test objects — they start with "test_name" field.
    # Use a bracket-counting approach to find complete objects regardless of newlines.
    complete_tests = []
    search_from = 0
    while True:
        # Find the next test_name key in the string
        pos = partial.find('"test_name"', search_from)
        if pos == -1:
            break
        # Walk backwards to find the opening brace of this object
        obj_start = partial.rfind("{", 0, pos)
        if obj_start == -1:
            search_from = pos + 1
            continue
        # Walk forward with brace counting to find the closing brace
        brace_count = 0
        obj_end = -1
        for i in range(obj_start, len(partial)):
            if partial[i] == "{":
                brace_count += 1
            elif partial[i] == "}":
                brace_count -= 1
                if brace_count == 0:
                    obj_end = i
                    break
        if obj_end == -1:
            # Object is incomplete (truncated), stop here
            break
        try:
            obj = json.loads(partial[obj_start:obj_end + 1])
            if obj.get("test_name"):
                complete_tests.append(obj)
        except Exception:
            pass
        search_from = obj_end + 1

    if complete_tests:
        logger.info(f"Salvaged {len(complete_tests)} complete tests from truncated JSON")
        repaired = {
            "patient_info": patient_info,
            "extracted_tests": complete_tests,
            "overall_analysis": "Partial analysis (response truncated by API)"
        }
        return json.dumps(repaired)

    # Return the partial text and let caller handle the error
    logger.warning("Could not salvage any test objects from truncated JSON")
    return partial




def _normalize_and_deduplicate(tests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normalize test fields and remove duplicates.

    Dedup key: (test_name_lower, value, test_date)
    """
    seen = set()
    unique_tests = []

    for test in tests:
        # Ensure required fields exist
        test_name = str(test.get("test_name") or "").strip()
        if not test_name or test_name.lower() in ("unknown", ""):
            continue

        # Skip demographic entries that slipped through (safety net)
        demographic_keywords = {"name", "age", "gender", "dob", "date of birth", "patient"}
        if test_name.lower() in demographic_keywords:
            logger.warning(f"Skipping demographic entry masquerading as test: {test_name}")
            continue

        value = str(test.get("value") or "").strip()
        test_date = str(test.get("test_date") or "").strip()

        # Deduplication key
        dedup_key = (test_name.lower(), value.lower(), test_date)
        if dedup_key in seen:
            continue
        seen.add(dedup_key)

        # Normalize is_abnormal to strict boolean
        raw_abnormal = test.get("is_abnormal", False)
        if isinstance(raw_abnormal, str):
            is_abnormal = raw_abnormal.lower() in ("true", "1", "yes")
        else:
            is_abnormal = bool(raw_abnormal)

        # Trust the model's is_abnormal judgment.

        unique_tests.append({
            "test_name": test_name,
            "test_type_normalized": test.get("test_type_normalized") or test_name,
            "value": value,
            "unit": str(test.get("unit") or "").strip(),
            "reference_range": str(test.get("reference_range") or "").strip(),
            "test_date": test_date or None,
            "category": str(test.get("category") or "Other").strip(),
            "is_abnormal": is_abnormal,
            "interpretation": str(test.get("interpretation") or "").strip(),
            "confidence_score": float(test.get("confidence_score") or 0.95),
        })

    return unique_tests


def _compute_is_abnormal(value_str: str, reference_range: str) -> bool:
    """
    Fallback: check if a numeric value is outside a numeric reference range.
    Returns False if the range or value cannot be parsed.
    """
    try:
        # Extract numeric part from value
        value_match = re.search(r"[-+]?\d*\.?\d+", value_str)
        if not value_match:
            return False
        value = float(value_match.group())

        # Handle "X-Y" range format
        range_match = re.search(r"([-+]?\d*\.?\d+)\s*[-–]\s*([-+]?\d*\.?\d+)", reference_range)
        if range_match:
            low = float(range_match.group(1))
            high = float(range_match.group(2))
            return value < low or value > high

        # Handle "< X" or "> X" formats
        lt_match = re.search(r"<\s*([-+]?\d*\.?\d+)", reference_range)
        gt_match = re.search(r">\s*([-+]?\d*\.?\d+)", reference_range)
        if lt_match:
            return value >= float(lt_match.group(1))
        if gt_match:
            return value <= float(gt_match.group(1))

    except Exception:
        pass

    return False


def categorize_test(test_name: str) -> str:
    """
    Fallback categorization.
    """
    keywords = {
        "Blood Chemistry": ["glucose", "sodium", "potassium", "chloride", "co2", "bun", "creatinine", "calcium"],
        "Lipid Profile": ["cholesterol", "hdl", "ldl", "triglyceride", "lipid"],
        "Liver Function": ["alt", "ast", "alp", "bilirubin", "albumin", "ggt", "liver"],
        "Kidney Function": ["creatinine", "bun", "egfr", "urea", "kidney"],
        "Thyroid": ["tsh", "t3", "t4", "thyroid", "free t"],
        "Vitamins & Minerals": ["vitamin", "vit", "b12", "folate", "folic", "iron", "ferritin", "zinc", "magnesium"],
        "Hormones": ["testosterone", "estrogen", "cortisol", "prolactin", "fsh", "lh", "insulin", "hba1c"],
        "Complete Blood Count": ["wbc", "rbc", "hemoglobin", "hematocrit", "platelet", "cbc", "neutrophil", "lymphocyte", "monocyte", "eosinophil", "basophil"],
        "Inflammation & Immunology": ["crp", "esr", "ferritin", "il-", "interleukin", "ige"],
        "Infectious Disease": ["hbsag", "hepatitis", "hiv", "hcv", "syphilis", "covid"],
    }

    test_lower = test_name.lower()
    for category, words in keywords.items():
        if any(word in test_lower for word in words):
            return category

    return "Other"
