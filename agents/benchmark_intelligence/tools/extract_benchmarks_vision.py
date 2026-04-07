"""
Vision AI-powered benchmark extraction from PDFs and images.

Uses Claude's vision capabilities to extract benchmark tables from
PDF documents, charts, and figures.
"""

import logging
import base64
import io
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from ._claude_client import call_claude, is_anthropic_available

logger = logging.getLogger(__name__)


def _extract_section_structure(pdf) -> List[Dict[str, Any]]:
    """
    Extract section titles and page ranges from PDF.

    Uses heuristics to detect section headings:
    - Lines starting with numbers (e.g., "5. Evaluation", "3.2 Results")
    - Title case lines with limited length
    - Common section patterns

    Args:
        pdf: Open pdfplumber PDF object

    Returns:
        List of sections with title, start_page, end_page:
            [{"title": "5. Evaluation", "start_page": 10, "end_page": 15}, ...]
    """
    sections = []

    for page_num, page in enumerate(pdf.pages, 1):
        page_text = page.extract_text()
        if not page_text:
            continue

        # Split into lines and look for section headings
        lines = page_text.split('\n')
        for line in lines:
            line_stripped = line.strip()

            # Skip empty or very long lines (unlikely to be headings)
            if not line_stripped or len(line_stripped) > 100:
                continue

            # Heuristic 1: Lines starting with section numbers (e.g., "5. Evaluation")
            # Pattern: digit(s), optional dot/space, title case text
            import re
            if re.match(r'^\d+(\.\d+)*[\.\s]+[A-Z]', line_stripped):
                sections.append({
                    "title": line_stripped,
                    "start_page": page_num,
                    "end_page": page_num  # Will be updated when next section found
                })

            # Heuristic 2: Common section keywords in title case
            # (helps catch unnumbered sections like "Results" or "Evaluation")
            elif re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)*$', line_stripped):
                keywords = ['evaluation', 'results', 'experiments', 'benchmarks',
                           'performance', 'analysis', 'conclusion', 'appendix']
                if any(kw in line_stripped.lower() for kw in keywords):
                    sections.append({
                        "title": line_stripped,
                        "start_page": page_num,
                        "end_page": page_num
                    })

    # Update end_page for each section (spans until next section starts)
    for i in range(len(sections) - 1):
        sections[i]["end_page"] = sections[i + 1]["start_page"] - 1

    # Last section extends to end of document
    if sections:
        sections[-1]["end_page"] = len(pdf.pages)

    return sections


def _filter_benchmark_sections(sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter sections to those likely containing benchmark data.

    Args:
        sections: List of section dictionaries from _extract_section_structure()

    Returns:
        Filtered list of benchmark-relevant sections
    """
    # Keywords indicating benchmark/evaluation content
    relevant_keywords = [
        'evaluation', 'result', 'benchmark', 'experiment',
        'performance', 'comparison', 'analysis', 'testing',
        'assessment', 'metric', 'score', 'accuracy', 'appendix'
    ]

    filtered = []
    for section in sections:
        title_lower = section['title'].lower()
        if any(keyword in title_lower for keyword in relevant_keywords):
            filtered.append(section)
            logger.debug(f"Selected section: {section['title']} (pages {section['start_page']}-{section['end_page']})")

    return filtered


def extract_benchmarks_from_pdf(
    pdf_content: bytes,
    source_name: Optional[str] = None,
    max_tokens: int = 16384,
    chunk_size: int = 8,
) -> Dict[str, Any]:
    """
    Extract benchmarks from PDF using two-pass section filtering + chunked AI extraction.

    Strategy:
    1. Extract section structure from PDF (titles + page ranges)
    2. Filter to benchmark-relevant sections (Evaluation, Results, etc.)
    3. Split filtered pages into chunks (default: 8 pages per chunk)
    4. Extract benchmarks from each chunk separately
    5. Merge results from all chunks

    This approach ensures robustness for benchmark-heavy papers by:
    - Reducing input tokens 50-80% via section filtering
    - Processing in smaller chunks to avoid JSON truncation
    - Handling papers with 100+ benchmarks reliably

    Args:
        pdf_content: PDF file content as bytes
        source_name: Name/identifier of the source document
        max_tokens: Maximum tokens in response per chunk
        chunk_size: Pages per chunk (default: 8)

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

        # Extract text from PDF using pdfplumber with section filtering
        import io
        try:
            import pdfplumber
        except ImportError:
            raise RuntimeError("pdfplumber not installed. Install with: pip install pdfplumber")

        # Initialize metadata tracking variables
        sections = []
        relevant_sections = []
        relevant_pages = []
        total_pages = 0

        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            total_pages = len(pdf.pages)
            logger.debug(f"PDF has {total_pages} pages")

            # Pass 1: Extract section structure
            sections = _extract_section_structure(pdf)
            logger.info(f"Detected {len(sections)} sections in PDF")

            # Pass 2: Filter to benchmark-relevant sections
            relevant_sections = _filter_benchmark_sections(sections)

            if not relevant_sections:
                logger.warning("No benchmark-relevant sections found, extracting full PDF")
                # Fallback: extract all pages if no sections detected
                relevant_pages = list(range(1, total_pages + 1))
            else:
                # Extract page numbers from relevant sections
                relevant_pages_set = set()
                for section in relevant_sections:
                    for page_num in range(section['start_page'], section['end_page'] + 1):
                        relevant_pages_set.add(page_num)
                relevant_pages = sorted(relevant_pages_set)

                logger.info(
                    f"Filtered to {len(relevant_sections)} relevant sections "
                    f"({len(relevant_pages)}/{total_pages} pages)"
                )

            # Split relevant pages into chunks for robust processing
            page_chunks = []
            for i in range(0, len(relevant_pages), chunk_size):
                chunk = relevant_pages[i:i + chunk_size]
                page_chunks.append(chunk)

            logger.info(
                f"Split {len(relevant_pages)} pages into {len(page_chunks)} chunks "
                f"(chunk_size={chunk_size})"
            )

        # Check if Claude API is available
        if not is_anthropic_available():
            raise RuntimeError(
                "Anthropic API not available. Set ANTHROPIC_API_KEY environment "
                "variable or install anthropic package (pip install anthropic)"
            )

        # Extract benchmarks from each chunk
        all_benchmarks = []
        chunks_processed = 0
        chunks_failed = 0

        with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
            for chunk_idx, chunk_pages in enumerate(page_chunks, 1):
                try:
                    # Extract text from this chunk
                    chunk_text = ""
                    for page_num in chunk_pages:
                        page = pdf.pages[page_num - 1]  # pdfplumber uses 0-based indexing
                        page_text = page.extract_text()
                        if page_text:
                            chunk_text += f"\n\n=== Page {page_num} ===\n\n{page_text}"

                    if not chunk_text or len(chunk_text) < 100:
                        logger.warning(f"Chunk {chunk_idx}/{len(page_chunks)}: No text extracted, skipping")
                        chunks_failed += 1
                        continue

                    logger.info(
                        f"Chunk {chunk_idx}/{len(page_chunks)}: Extracted {len(chunk_text)} chars "
                        f"from pages {chunk_pages[0]}-{chunk_pages[-1]}"
                    )

                    # Build extraction prompt for this chunk
                    prompt = _build_text_extraction_prompt(chunk_text)

                    # Use standard text extraction
                    from ._claude_client import call_claude_json

                    logger.debug(f"Chunk {chunk_idx}/{len(page_chunks)}: Calling Claude")

                    chunk_result = call_claude_json(
                        prompt=prompt,
                        max_tokens=max_tokens
                    )

                    # Merge benchmarks from this chunk
                    chunk_benchmarks = chunk_result.get("benchmarks", [])
                    all_benchmarks.extend(chunk_benchmarks)
                    chunks_processed += 1

                    logger.info(
                        f"Chunk {chunk_idx}/{len(page_chunks)}: Extracted {len(chunk_benchmarks)} benchmarks"
                    )

                except Exception as e:
                    logger.error(f"Chunk {chunk_idx}/{len(page_chunks)} failed: {e}")
                    chunks_failed += 1
                    # Continue processing other chunks

        if not all_benchmarks and chunks_processed == 0:
            logger.warning("No benchmarks extracted from any chunk")
            return _empty_result(source_name, "no_benchmarks_extracted")

        # Build consolidated result
        result = {"benchmarks": all_benchmarks}
        logger.info(
            f"Chunked extraction complete: {len(all_benchmarks)} benchmarks from "
            f"{chunks_processed}/{len(page_chunks)} chunks ({chunks_failed} failed)"
        )

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
        result["metadata"]["extraction_method"] = "claude_vision_api_with_section_filtering_and_chunking"
        result["metadata"]["total_pages"] = total_pages
        result["metadata"]["pages_processed"] = len(relevant_pages)
        result["metadata"]["sections_found"] = len(sections)
        result["metadata"]["sections_used"] = len(relevant_sections)
        result["metadata"]["chunks_total"] = len(page_chunks)
        result["metadata"]["chunks_processed"] = chunks_processed
        result["metadata"]["chunks_failed"] = chunks_failed
        result["metadata"]["chunk_size"] = chunk_size

        logger.info(
            f"Extracted {len(result['benchmarks'])} benchmarks from PDF using chunked section-filtered AI extraction "
            f"({len(relevant_pages)}/{total_pages} pages, {chunks_processed}/{len(page_chunks)} chunks)"
        )

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
