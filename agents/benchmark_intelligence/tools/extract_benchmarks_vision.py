"""
Vision AI-powered benchmark extraction from PDFs and images.

Uses Claude's vision capabilities to extract benchmark tables from
PDF documents, charts, and figures.
"""

import logging
import base64
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from ._claude_client import call_claude, is_anthropic_available

logger = logging.getLogger(__name__)


def extract_benchmarks_from_pdf(
    pdf_content: bytes,
    source_name: Optional[str] = None,
    max_tokens: int = 16384,
) -> Dict[str, Any]:
    """
    Extract benchmarks from PDF using text extraction + AI.

    Strategy:
    1. Extract text from PDF using pdfplumber
    2. Send text to Claude for benchmark extraction (much smaller than full PDF)
    3. Parse structured response

    Args:
        pdf_content: PDF file content as bytes
        source_name: Name/identifier of the source document
        max_tokens: Maximum tokens in response

    Returns:
        Dictionary containing extracted benchmark data:
            - benchmarks: List of benchmark entries with scores and context
            - metadata: Extraction metadata (source, date, count, etc.)

    Raises:
        ValueError: If pdf_content is empty or invalid
        RuntimeError: If extraction fails

    Example:
        >>> with open("paper.pdf", "rb") as f:
        ...     pdf_bytes = f.read()
        >>> result = extract_benchmarks_from_pdf(pdf_bytes, source_name="Llama-3.1 Paper")
        >>> print(f"Found {result['metadata']['total_benchmarks']} benchmarks")
    """
    try:
        if not pdf_content or not isinstance(pdf_content, bytes):
            raise ValueError("pdf_content must be non-empty bytes")

        if len(pdf_content) < 100:
            logger.warning("PDF content is very small, may not be valid")
            return _empty_result(source_name, "pdf_too_small")

        logger.info(f"Extracting benchmarks from PDF ({len(pdf_content)} bytes)")

        # Extract text from PDF using pdfplumber (avoids 200K token limit)
        import io
        try:
            import pdfplumber
        except ImportError:
            raise RuntimeError("pdfplumber not installed. Install with: pip install pdfplumber")

        pdf_text = ""
        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            logger.debug(f"PDF has {len(pdf.pages)} pages")
            # Extract text from all pages
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    pdf_text += f"\n\n=== Page {page_num} ===\n\n{page_text}"

        if not pdf_text or len(pdf_text) < 100:
            logger.warning("Could not extract text from PDF or text is empty")
            return _empty_result(source_name, "no_text_extracted")

        logger.info(f"Extracted {len(pdf_text)} chars of text from PDF")

        # Check if Claude API is available
        if not is_anthropic_available():
            raise RuntimeError(
                "Anthropic API not available. Set ANTHROPIC_API_KEY environment "
                "variable or install anthropic package (pip install anthropic)"
            )

        # Build extraction prompt with PDF text
        prompt = _build_text_extraction_prompt(pdf_text)

        # Use standard text extraction (no vision needed for extracted text)
        from ._claude_client import call_claude_json

        logger.debug(f"Calling Claude with extracted PDF text ({len(pdf_text)} chars)")

        response_text = call_claude_json(
            prompt=prompt,
            max_tokens=max_tokens
        )

        # Response is already parsed JSON from call_claude_json
        result = response_text
        logger.debug(f"Claude API call successful")

        # result is already a dict from call_claude_json
        # Validate and enhance result
        if not isinstance(result, dict):
            logger.warning("Response is not a dict, creating empty result")
            result = {"benchmarks": []}

        if "benchmarks" not in result:
            logger.warning("No benchmarks key in response, creating empty result")
            result = {"benchmarks": []}

        # Ensure metadata exists
        if "metadata" not in result:
            result["metadata"] = {}

        result["metadata"]["document_source"] = source_name or "unknown"
        result["metadata"]["extraction_date"] = datetime.utcnow().isoformat()
        result["metadata"]["total_benchmarks"] = len(result.get("benchmarks", []))
        result["metadata"]["source_type"] = "pdf_vision"
        result["metadata"]["extraction_method"] = "claude_vision_api"

        logger.info(f"Extracted {len(result['benchmarks'])} benchmarks from PDF using vision AI")

        return result

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"PDF vision extraction failed: {e}")
        raise RuntimeError(f"Failed to extract benchmarks from PDF: {e}")


def _build_text_extraction_prompt(pdf_text: str) -> str:
    """
    Build the prompt for text-based extraction from PDF.

    Args:
        pdf_text: Extracted text from PDF

    Returns:
        Prompt string with embedded PDF text
    """
    # Build prompt without f-string to avoid format errors
    prompt_template = """Extract all benchmark evaluation results from this research paper text.

The text below is extracted from a PDF research paper. Find all benchmark evaluation results.

{pdf_text}

---

Instructions:
Extract all benchmark names, scores, and evaluation contexts from the text above.

Focus on finding benchmark names, scores, and contexts from tables and text.

For each benchmark, extract:
{{
  "name": "benchmark name",
  "score": numeric_value,
  "metric": "accuracy|pass@1|exact_match|etc",
  "context": {{
    "shot_count": number or null,
    "subset": "specific variant if any",
    "special_conditions": "CoT|PoT|base|instruct|etc"
  }},
  "source_location": "Table X or Page Y"
}}

Return JSON:
{{
  "benchmarks": [ ...array of benchmarks... ],
  "metadata": {{
    "total_benchmarks": number,
    "extraction_confidence": "high|medium|low"
  }}
}}

Important:
- Extract ALL benchmarks found
- Include shot count if mentioned (5-shot, 0-shot, etc.)
- Include variant info (CoT, base, instruct, etc.)
- If unsure about score, omit it
- Return only JSON"""

    return prompt_template.format(pdf_text=pdf_text)


def _detect_environment() -> str:
    """Detect Claude environment (ambient or standard)."""
    import os

    ambient_indicators = [
        os.getenv("AMBIENT_SESSION_ID"),
        os.getenv("AMBIENT_WORKSPACE_ID"),
        os.getenv("CLAUDECODE") == "1",
    ]
    if any(ambient_indicators):
        return "ambient"
    return "standard"


def _empty_result(source_name: Optional[str], reason: str) -> Dict[str, Any]:
    """Create empty result with error reason."""
    return {
        "benchmarks": [],
        "metadata": {
            "document_source": source_name or "unknown",
            "extraction_date": datetime.utcnow().isoformat(),
            "total_benchmarks": 0,
            "source_type": "pdf_vision",
            "error": reason
        }
    }
