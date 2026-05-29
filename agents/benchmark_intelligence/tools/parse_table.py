"""
Deterministic benchmark extraction from HTML and Markdown tables.

Parses structured tables from model cards and documentation to extract
benchmark results without AI inference. Fast, reliable, and cost-free.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# Known benchmark names for table validation
KNOWN_BENCHMARKS = {
    'mmlu', 'gsm8k', 'gsm-8k', 'humaneval', 'mbpp', 'math', 'arc', 'arc-c', 'arc-challenge',
    'hellaswag', 'winogrande', 'triviaqa', 'squad', 'boolq', 'drop', 'quac', 'race',
    'bbh', 'big-bench', 'gpqa', 'ifeval', 'api-bank', 'bfcl', 'nexus', 'mgsm', 'agieval',
    'commonsenseqa', 'piqa', 'siqa', 'openbookqa', 'truthfulqa', 'alpacaeval', 'mt-bench',
    'librispeech', 'docvqa', 'chartqa', 'infovqa', 'multipl-e', 'livebench', 'livecodebench',
    'arena-hard', 'alignbench', 'paws', 'zeroscrolls', 'infinitebench', 'quality'
}


def parse_benchmark_name_context(name: str) -> Tuple[str, Dict[str, Any]]:
    """
    Parse benchmark name and extract context (shot count, subset, version).

    Args:
        name: Raw benchmark name from table (e.g., "MMLU (5-shot)", "ARC-Challenge")

    Returns:
        Tuple of (clean_name, context_dict)

    Example:
        >>> parse_benchmark_name_context("MMLU (5-shot)")
        ('MMLU', {'shot_count': 5, 'subset': None, 'version': None, 'special_conditions': None})
        >>> parse_benchmark_name_context("MMLU-Pro (CoT)")
        ('MMLU-Pro', {'shot_count': None, 'subset': None, 'version': None, 'special_conditions': 'chain-of-thought'})
    """
    if not name:
        return "", {}

    # Initialize context
    context = {
        'shot_count': None,
        'subset': None,
        'version': None,
        'special_conditions': None
    }

    # Extract parenthetical content
    # Pattern: "Name (content)" or "Name(content)"
    paren_match = re.search(r'(.*?)\s*\((.*?)\)\s*$', name)

    if paren_match:
        clean_name = paren_match.group(1).strip()
        paren_content = paren_match.group(2).strip()

        # Parse parenthetical content
        # Shot count: "5-shot", "0-shot", "8 shot"
        shot_match = re.search(r'(\d+)[-\s]?shot', paren_content, re.IGNORECASE)
        if shot_match:
            context['shot_count'] = int(shot_match.group(1))

        # CoT / Chain-of-thought
        if re.search(r'\bCoT\b', paren_content, re.IGNORECASE):
            context['special_conditions'] = 'chain-of-thought'

        # With/without conditions
        if 'w sub' in paren_content.lower() or 'with sub' in paren_content.lower():
            context['special_conditions'] = 'with subtitles'
        elif 'w/o sub' in paren_content.lower() or 'without sub' in paren_content.lower():
            context['special_conditions'] = 'without subtitles'
        elif 'w/ CI' in paren_content or 'with CI' in paren_content:
            context['special_conditions'] = 'with CI'
        elif 'w/o CI' in paren_content or 'without CI' in paren_content:
            context['special_conditions'] = 'without CI'

    else:
        clean_name = name.strip()

    # Extract subset from name itself (not in parentheses)
    # Examples: "ARC-Challenge", "ARC-c", "test-clean"
    if re.search(r'[-_]challenge', clean_name, re.IGNORECASE):
        context['subset'] = 'challenge'
    elif re.search(r'[-_]easy', clean_name, re.IGNORECASE):
        context['subset'] = 'easy'
    elif re.search(r'test[-_]clean', clean_name, re.IGNORECASE):
        context['subset'] = 'test-clean'
    elif re.search(r'test[-_]other', clean_name, re.IGNORECASE):
        context['subset'] = 'test-other'

    # Extract version
    # Patterns: "v2", "V4", "1.1"
    version_match = re.search(r'\b[vV](\d+(?:\.\d+)?)\b', clean_name)
    if version_match:
        context['version'] = version_match.group(1)

    return clean_name, context


def detect_html_table(content: str) -> bool:
    """
    Detect if content contains HTML tables.

    Args:
        content: Document content

    Returns:
        True if HTML table tags found, False otherwise
    """
    return bool(re.search(r'<table[^>]*>.*?</table>', content, re.DOTALL | re.IGNORECASE))


def parse_html_table(html_content: str, model_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Parse HTML tables to extract benchmark results.

    Handles various table formats commonly found in model cards:
    - Benchmark name in first column
    - Scores in subsequent columns (may have multiple model columns)
    - Shot count, metric columns may be present
    - Category/rowspan grouping

    Args:
        html_content: HTML content containing <table> tags
        model_id: Optional model identifier for attribution

    Returns:
        List of benchmark dictionaries with standard schema

    Example:
        >>> html = '''
        ... <table>
        ...   <tr><td>Benchmark</td><td>Score</td></tr>
        ...   <tr><td>MMLU (5-shot)</td><td>82.5</td></tr>
        ... </table>
        ... '''
        >>> benchmarks = parse_html_table(html)
        >>> len(benchmarks)
        1
    """
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('table')

    if not tables:
        logger.warning("No HTML tables found in content")
        return []

    all_benchmarks = []

    for table_idx, table in enumerate(tables):
        rows = table.find_all('tr')

        if len(rows) < 2:
            continue  # Skip tables with only header or empty

        # Parse header row to identify columns
        header_row = rows[0]
        headers = [cell.get_text(strip=True) for cell in header_row.find_all(['th', 'td'])]

        # Identify column types
        benchmark_col = None
        score_cols = []
        shot_col = None
        metric_col = None
        category_col = None

        for idx, header in enumerate(headers):
            header_lower = header.lower()

            if 'benchmark' in header_lower or header_lower in ['task', 'dataset']:
                benchmark_col = idx
            elif 'category' in header_lower or header_lower == 'type':
                category_col = idx
            elif any(keyword in header_lower for keyword in ['shot', '# shot', 'n-shot']):
                shot_col = idx
            elif any(keyword in header_lower for keyword in ['metric', 'measure']):
                metric_col = idx
            elif header_lower and not any(word in header_lower for word in ['training', 'params', 'context', 'input', 'output', 'date']):
                # Columns that look like model names (but exclude metadata columns)
                # Skip if header looks like metadata (Training Data, Params, etc.)
                if not re.search(r'\b(data|training|parameters|modality|modalities|context\s+length)\b', header_lower):
                    score_cols.append(idx)

        if benchmark_col is None:
            # Try to identify benchmark column by content in first few rows
            # Look for rows with numeric scores
            sample_rows = rows[1:min(5, len(rows))]
            potential_benchmark_col = None

            for col_idx in range(len(headers)):
                # Check if this column has text that looks like benchmark names
                sample_values = []
                for row in sample_rows:
                    cells = row.find_all(['td', 'th'])
                    if col_idx < len(cells):
                        sample_values.append(cells[col_idx].get_text(strip=True))

                # If column has mostly text (not numbers), might be benchmark column
                numeric_count = sum(1 for v in sample_values if re.match(r'^[\d.]+%?$', v))
                if numeric_count < len(sample_values) / 2:  # Less than 50% numeric
                    potential_benchmark_col = col_idx
                    break

            if potential_benchmark_col is not None:
                benchmark_col = potential_benchmark_col
                score_cols = [i for i in range(len(headers)) if i != benchmark_col and i != category_col]
            else:
                # Skip this table - can't identify structure
                logger.debug(f"Skipping table {table_idx+1}: Cannot identify benchmark column")
                continue

        logger.debug(f"Table {table_idx+1}: benchmark_col={benchmark_col}, score_cols={score_cols}")

        # Validate this looks like a benchmark table
        # Check if at least one row contains a known benchmark name
        has_known_benchmark = False
        for row in rows[1:min(10, len(rows))]:  # Check first 10 data rows
            cells = row.find_all(['td', 'th'])
            if benchmark_col < len(cells):
                cell_text = cells[benchmark_col].get_text(strip=True).lower()
                # Remove common suffixes for matching
                cell_text = re.sub(r'\s*\([^)]*\)', '', cell_text)  # Remove (5-shot) etc
                cell_text = cell_text.replace('-', '').replace('_', '').replace(' ', '')

                if cell_text in KNOWN_BENCHMARKS or any(kb in cell_text for kb in KNOWN_BENCHMARKS):
                    has_known_benchmark = True
                    break

        if not has_known_benchmark:
            logger.debug(f"Skipping table {table_idx+1}: No known benchmarks found")
            continue

        # Parse data rows
        for row_idx, row in enumerate(rows[1:], 1):
            cells = row.find_all(['td', 'th'])

            if not cells or len(cells) < 2:
                continue

            # Handle rowspan: if cell count doesn't match header count,
            # try to find benchmark name in first non-numeric cell
            raw_name = None
            effective_benchmark_col = benchmark_col

            if len(cells) != len(headers):
                # Cell count mismatch - likely due to rowspan
                # Find first cell that contains text (not just numbers)
                for idx, cell in enumerate(cells):
                    text = cell.get_text(strip=True)
                    # Skip if it's just a number or empty
                    if text and not re.match(r'^[\d.,-]+$', text):
                        raw_name = text
                        effective_benchmark_col = idx
                        break
            else:
                # Normal case: use specified benchmark column
                if benchmark_col < len(cells):
                    raw_name = cells[benchmark_col].get_text(strip=True)

            if not raw_name:
                continue
            if not raw_name or raw_name.lower() in ['category', 'type', '']:
                continue  # Skip category rows or empty

            # Parse name and context
            benchmark_name, context = parse_benchmark_name_context(raw_name)

            # Extract shot count from dedicated column if available
            # Adjust for rowspan offset
            if shot_col is not None:
                adjusted_shot_col = shot_col if len(cells) == len(headers) else shot_col - (benchmark_col - effective_benchmark_col)
                if 0 <= adjusted_shot_col < len(cells):
                    shot_text = cells[adjusted_shot_col].get_text(strip=True)
                    shot_match = re.search(r'(\d+)', shot_text)
                    if shot_match:
                        context['shot_count'] = int(shot_match.group(1))

            # Extract metric from dedicated column if available
            metric = None
            if metric_col is not None:
                adjusted_metric_col = metric_col if len(cells) == len(headers) else metric_col - (benchmark_col - effective_benchmark_col)
                if 0 <= adjusted_metric_col < len(cells):
                    metric = cells[adjusted_metric_col].get_text(strip=True)

            # Extract scores from score columns
            # Track if we found at least one valid score (to filter out metadata rows)
            has_valid_score = False

            for col_idx in score_cols:
                # Adjust for rowspan
                adjusted_col = col_idx if len(cells) == len(headers) else col_idx - (benchmark_col - effective_benchmark_col)

                if adjusted_col < 0 or adjusted_col >= len(cells):
                    continue

                score_text = cells[adjusted_col].get_text(strip=True)

                # Parse score
                score = _parse_score(score_text)

                # Skip if no valid score (might be metadata row)
                if score is None:
                    continue

                has_valid_score = True

                # Determine model name from header
                model_name = headers[col_idx] if col_idx < len(headers) else None

                # Create benchmark entry
                benchmark = {
                    'name': benchmark_name,
                    'score': score,
                    'metric': metric or _infer_metric(benchmark_name),
                    'context': context.copy(),
                    'model_name': model_name,
                    'source_location': f'Table {table_idx + 1}, Row {row_idx}'
                }

                all_benchmarks.append(benchmark)

            # Log if no valid scores found for this row
            if not has_valid_score:
                logger.debug(f"Skipping row {row_idx} in table {table_idx+1}: '{raw_name}' - no valid scores")

        logger.info(f"Extracted {len(all_benchmarks)} benchmarks from table {table_idx + 1}")

    return all_benchmarks


def parse_markdown_table(markdown_content: str, model_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Parse Markdown tables to extract benchmark results.

    Markdown table format:
    ```
    | Benchmark | Score |
    |-----------|-------|
    | MMLU      | 82.5  |
    ```

    Args:
        markdown_content: Markdown content containing tables
        model_id: Optional model identifier

    Returns:
        List of benchmark dictionaries
    """
    if not markdown_content:
        return []

    # Find all markdown tables
    # Pattern: Lines starting with |, followed by separator line, followed by data rows
    table_pattern = r'(\|.+\|[\r\n]+\|[-:\s|]+\|[\r\n]+(?:\|.+\|[\r\n]*)+)'
    tables = re.findall(table_pattern, markdown_content)

    if not tables:
        logger.warning("No Markdown tables found in content")
        return []

    all_benchmarks = []

    for table_idx, table_text in enumerate(tables):
        lines = [line.strip() for line in table_text.split('\n') if line.strip()]

        if len(lines) < 3:
            continue  # Need header + separator + at least one data row

        # Parse header
        header_line = lines[0]
        headers = [cell.strip() for cell in header_line.split('|')[1:-1]]  # Skip first/last empty

        # Skip separator line (lines[1])

        # Parse data rows
        data_rows = lines[2:]

        # Identify column types (same logic as HTML)
        benchmark_col = 0  # Assume first column is benchmark
        score_cols = list(range(1, len(headers)))

        for row_idx, row_line in enumerate(data_rows, 1):
            cells = [cell.strip() for cell in row_line.split('|')[1:-1]]

            if not cells or len(cells) < 2:
                continue

            raw_name = cells[0]
            if not raw_name:
                continue

            # Parse name and context
            benchmark_name, context = parse_benchmark_name_context(raw_name)

            # Extract scores
            for col_idx in score_cols:
                if col_idx >= len(cells):
                    continue

                score_text = cells[col_idx]
                score = _parse_score(score_text)

                model_name = headers[col_idx] if col_idx < len(headers) else None

                benchmark = {
                    'name': benchmark_name,
                    'score': score,
                    'metric': _infer_metric(benchmark_name),
                    'context': context.copy(),
                    'model_name': model_name,
                    'source_location': f'Markdown Table {table_idx + 1}, Row {row_idx}'
                }

                all_benchmarks.append(benchmark)

    logger.info(f"Extracted {len(all_benchmarks)} benchmarks from {len(tables)} Markdown tables")
    return all_benchmarks


def _parse_score(score_text: str) -> Optional[float]:
    """
    Parse score from text.

    Handles:
    - Percentages: "82.5%", "82.5 %" → 82.5
    - Decimals: "82.5", "0.825" → 82.5
    - Missing: "--", "N/A", "-" → None

    Args:
        score_text: Text containing score

    Returns:
        Parsed score as float, or None if missing
    """
    if not score_text:
        return None

    score_text = score_text.strip()

    # Check for missing values
    if score_text in ['--', 'N/A', '-', 'TBD', '']:
        return None

    # Remove percentage sign
    score_text = score_text.replace('%', '').strip()

    # Try to parse as float
    try:
        score = float(score_text)

        # Convert 0-1 range to percentage if it looks like a proportion
        # (Common in some benchmarks)
        if 0 < score < 1:
            score = score * 100

        return score
    except ValueError:
        logger.warning(f"Could not parse score: '{score_text}'")
        return None


def _infer_metric(benchmark_name: str) -> Optional[str]:
    """
    Infer metric type from benchmark name.

    Args:
        benchmark_name: Benchmark name

    Returns:
        Inferred metric string (e.g., "accuracy", "pass@1", "wer")
    """
    name_lower = benchmark_name.lower()

    # Code benchmarks
    if any(keyword in name_lower for keyword in ['humaneval', 'mbpp', 'codecontests', 'apps']):
        return 'pass@1'

    # Audio benchmarks
    if any(keyword in name_lower for keyword in ['librispeech', 'commonvoice', 'fleurs']):
        return 'wer'

    # Document/OCR benchmarks
    if any(keyword in name_lower for keyword in ['docvqa', 'infovqa', 'ocr']):
        return 'anls'

    # Most other benchmarks use accuracy
    return 'accuracy'
