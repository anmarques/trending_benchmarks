"""
Stage utilities for modular 6-stage pipeline.

Provides JSON schema definitions and helper functions for saving/loading
standardized stage outputs.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict


logger = logging.getLogger(__name__)


# JSON Schema Constants for all 6 stages (T018)

@dataclass
class StageOutput:
    """Base class for standardized stage output schema."""
    stage: str
    timestamp: str
    input_count: int
    output_count: int
    data: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


# Stage-specific schema definitions

STAGE_SCHEMAS = {
    "filter_models": {
        "description": "Stage 1: Model discovery and filtering",
        "required_fields": ["stage", "timestamp", "input_count", "output_count", "data", "errors"],
        "data_schema": {
            "model_id": str,
            "lab": str,
            "release_date": str,
            "downloads": int,
            "likes": int,
        }
    },
    "find_documents": {
        "description": "Stage 2: Document URL discovery per model",
        "required_fields": ["stage", "timestamp", "input_count", "output_count", "data", "errors"],
        "data_schema": {
            "model_id": str,
            "documents": list,  # List of {type, url, found, error}
        }
    },
    "parse_documents": {
        "description": "Stage 3: Benchmark extraction from documents",
        "required_fields": ["stage", "timestamp", "input_count", "output_count", "data", "errors"],
        "data_schema": {
            "model_id": str,
            "source_type": str,
            "source_url": str,
            "benchmarks": list,  # List of {name, variant, method}
        }
    },
    "consolidate_names": {
        "description": "Stage 4: Benchmark name consolidation",
        "required_fields": ["stage", "timestamp", "input_count", "output_count", "data", "errors"],
        "data_schema": {
            "canonical_name": str,
            "variants": list,
            "similarity_scores": list,
            "web_search_used": bool,
        }
    },
    "categorize_benchmarks": {
        "description": "Stage 5: Benchmark categorization and taxonomy",
        "required_fields": ["stage", "timestamp", "input_count", "output_count", "data", "errors"],
        "data_schema": {
            "canonical_name": str,
            "categories": list,
            "taxonomy_version": str,
            "newly_created_category": bool,
        }
    },
    "generate_report": {
        "description": "Stage 6: Report generation metadata",
        "required_fields": ["stage", "timestamp", "snapshot_id", "report_path", "sections_generated", "errors"],
        "data_schema": {
            "snapshot_id": int,
            "report_path": str,
            "sections_generated": int,
        }
    }
}


def get_outputs_dir() -> Path:
    """
    Get the outputs directory path.

    Returns:
        Path to outputs directory (agents/benchmark_intelligence/outputs/)
    """
    # Get directory relative to this file
    current_file = Path(__file__).parent
    outputs_dir = current_file / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    return outputs_dir


def find_latest_stage_output(stage_name: str) -> Optional[str]:
    """
    Find the most recent JSON output file from a given stage.

    Args:
        stage_name: Name of the stage (e.g., "filter_models", "find_documents")

    Returns:
        Path to most recent JSON file for this stage, or None if not found

    Example:
        >>> path = find_latest_stage_output("filter_models")
        >>> # Returns: "outputs/filter_models_20260406_120000.json"
    """
    outputs_dir = get_outputs_dir()
    pattern = f"{stage_name}_*.json"

    # Find all matching files
    matching_files = list(outputs_dir.glob(pattern))

    if not matching_files:
        logger.warning(f"No output files found for stage '{stage_name}' in {outputs_dir}")
        return None

    # Sort by modification time (most recent first)
    latest_file = max(matching_files, key=lambda p: p.stat().st_mtime)

    logger.info(f"Found latest output for {stage_name}: {latest_file.name}")
    return str(latest_file)


def load_stage_json(filepath: str) -> Dict[str, Any]:
    """
    Load and validate JSON from stage output file.

    Args:
        filepath: Path to JSON file

    Returns:
        Parsed JSON data as dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
        ValueError: If schema validation fails

    Example:
        >>> data = load_stage_json("outputs/filter_models_20260406.json")
        >>> print(data["stage"], data["output_count"])
    """
    path = Path(filepath)

    if not path.exists():
        raise FileNotFoundError(f"Stage output file not found: {filepath}")

    with open(path, 'r') as f:
        data = json.load(f)

    # Validate required fields
    if "stage" not in data:
        raise ValueError(f"Missing required field 'stage' in {filepath}")

    stage_name = data["stage"]
    if stage_name in STAGE_SCHEMAS:
        schema = STAGE_SCHEMAS[stage_name]
        required_fields = schema["required_fields"]

        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(
                f"Missing required fields for stage '{stage_name}': {missing_fields}"
            )

    logger.info(f"Loaded and validated stage output: {path.name}")
    return data


def save_stage_json(
    data: List[Dict[str, Any]],
    stage_name: str,
    input_count: int = 0,
    errors: Optional[List[Dict[str, Any]]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save stage output with standardized schema and naming.

    Creates JSON file with standard format:
    {
      "stage": "stage_name",
      "timestamp": "2026-04-06T12:00:00",
      "input_count": 100,
      "output_count": 150,
      "data": [...],
      "errors": [...],
      "metadata": {...}  (optional)
    }

    Filename format: {stage_name}_{timestamp}.json

    Args:
        data: List of output data items
        stage_name: Name of the stage
        input_count: Number of input items processed
        errors: List of error dictionaries (optional)
        metadata: Additional metadata (optional, e.g., error_summary)

    Returns:
        Path to saved JSON file

    Example:
        >>> models = [{"id": "meta-llama/Llama-3.1", ...}, ...]
        >>> path = save_stage_json(models, "filter_models", input_count=1000)
        >>> # Saves to: outputs/filter_models_20260406_120000.json
    """
    outputs_dir = get_outputs_dir()

    # Generate timestamp for filename
    timestamp = datetime.utcnow()
    timestamp_str = timestamp.isoformat()
    filename_timestamp = timestamp.strftime("%Y%m%d_%H%M%S")

    # Create standardized output structure
    output = {
        "stage": stage_name,
        "timestamp": timestamp_str,
        "input_count": input_count,
        "output_count": len(data),
        "data": data,
        "errors": errors or []
    }

    # Add metadata if provided
    if metadata:
        output["metadata"] = metadata

    # Generate filename
    filename = f"{stage_name}_{filename_timestamp}.json"
    filepath = outputs_dir / filename

    # Save to file
    with open(filepath, 'w') as f:
        json.dump(output, f, indent=2, default=str)

    logger.info(
        f"Saved stage output: {filename} "
        f"(input: {input_count}, output: {len(data)}, errors: {len(errors or [])})"
    )

    return str(filepath)


def validate_stage_output(data: Dict[str, Any], stage_name: str) -> bool:
    """
    Validate stage output against schema.

    Args:
        data: Stage output data
        stage_name: Expected stage name

    Returns:
        True if valid, False otherwise
    """
    if stage_name not in STAGE_SCHEMAS:
        logger.warning(f"No schema defined for stage '{stage_name}'")
        return True  # No schema to validate against

    schema = STAGE_SCHEMAS[stage_name]
    required_fields = schema["required_fields"]

    # Check all required fields present
    missing = [field for field in required_fields if field not in data]
    if missing:
        logger.error(f"Validation failed for {stage_name}: missing fields {missing}")
        return False

    # Check stage name matches
    if data.get("stage") != stage_name:
        logger.error(
            f"Stage name mismatch: expected '{stage_name}', got '{data.get('stage')}'"
        )
        return False

    logger.info(f"Validation passed for stage '{stage_name}'")
    return True


def create_error_entry(
    error_type: str,
    count: int,
    samples: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create standardized error entry for stage outputs.

    Args:
        error_type: Type/category of error
        count: Number of occurrences
        samples: Optional list of sample error messages

    Returns:
        Error entry dictionary
    """
    return {
        "error_type": error_type,
        "count": count,
        "samples": samples or []
    }
