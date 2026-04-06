"""
Model discovery tool for finding trending models from HuggingFace.

This module provides functionality to discover trending models from specified
labs/organizations based on configuration criteria.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import yaml

from ..clients.factory import get_hf_client
from ..clients.base import ModelInfo, HFClientBase


logger = logging.getLogger(__name__)


def discover_trending_models(
    labs: Optional[List[str]] = None,
    config: Optional[Dict[str, Any]] = None,
    hf_client: Optional[HFClientBase] = None,
) -> List[Dict[str, Any]]:
    """
    Discover trending models from specified labs/organizations.

    This function searches HuggingFace for models from specified organizations,
    filtering and sorting according to configuration criteria.

    Args:
        labs: List of organization names to search (e.g., ["Qwen", "meta-llama"]).
              If None, loads from config.yaml (project root)
        config: Configuration dictionary with discovery settings.
                If None, loads from config.yaml (project root)
        hf_client: HuggingFace client instance. If None, creates one using factory.

    Returns:
        List of dictionaries containing model information:
            - id: Model identifier
            - author: Organization/author name
            - downloads: Download count
            - likes: Like count
            - tags: List of tags
            - pipeline_tag: Primary task type
            - created_at: Creation timestamp
            - last_modified: Last update timestamp
            - library_name: ML library used
            - metadata: Additional metadata

    Raises:
        ValueError: If configuration is invalid
        RuntimeError: If model discovery fails

    Example:
        >>> models = discover_trending_models(
        ...     labs=["Qwen", "meta-llama"],
        ...     config={"models_per_lab": 10, "sort_by": "downloads"}
        ... )
        >>> print(f"Found {len(models)} models")
    """
    try:
        # Load config from file if not provided
        if config is None or labs is None:
            config_path = Path(__file__).parent.parent.parent.parent / "config.yaml"
            with open(config_path, "r") as f:
                yaml_config = yaml.safe_load(f)

            if labs is None:
                labs = yaml_config.get("labs", [])
            if config is None:
                config = yaml_config.get("discovery", {})

        if not labs:
            raise ValueError("No labs specified and none found in configuration")

        # Get HuggingFace client
        if hf_client is None:
            hf_client = get_hf_client()

        # Extract discovery settings
        models_per_lab = config.get("models_per_lab", 20)
        sort_by = config.get("sort_by", "downloads")
        filter_tags = config.get("filter_tags", [])
        exclude_tags = config.get("exclude_tags", [])
        min_downloads = config.get("min_downloads", 0)
        date_filter_months = config.get("date_filter_months", None)

        logger.info(
            f"Discovering models from {len(labs)} labs: {', '.join(labs)}"
        )
        logger.info(
            f"Settings: {models_per_lab} models/lab, sort by {sort_by}, "
            f"min downloads: {min_downloads}, date filter: {date_filter_months} months"
        )

        all_models = []

        # Discover models for each lab
        for lab in labs:
            try:
                logger.debug(f"Fetching models for {lab}...")

                # Build filter parameters
                kwargs = {}
                if filter_tags:
                    kwargs["tags"] = filter_tags

                # Fetch models from this lab
                lab_models = hf_client.list_models(
                    author=lab,
                    limit=models_per_lab * 2,  # Fetch extra to account for filtering
                    sort=sort_by,
                    **kwargs
                )

                # Apply additional filtering
                filtered_models = []
                for model in lab_models:
                    # Check minimum downloads
                    if model.downloads < min_downloads:
                        continue

                    # Check tags if specified
                    if filter_tags:
                        if not any(tag in model.tags for tag in filter_tags):
                            continue

                    # Check exclude_tags
                    if exclude_tags:
                        if any(tag in model.tags for tag in exclude_tags):
                            continue

                    # Check date filter (last N months)
                    if date_filter_months and model.created_at:
                        from datetime import datetime, timezone
                        from dateutil.relativedelta import relativedelta

                        cutoff_date = datetime.now(timezone.utc) - relativedelta(months=date_filter_months)
                        if model.created_at < cutoff_date:
                            continue

                    filtered_models.append(model)

                    # Stop if we have enough models
                    if len(filtered_models) >= models_per_lab:
                        break

                logger.info(f"Found {len(filtered_models)} models for {lab}")

                # Convert to dictionaries with metadata
                for model in filtered_models:
                    model_dict = model.to_dict()
                    model_dict["metadata"] = {
                        "discovered_from_lab": lab,
                        "discovery_sort": sort_by,
                    }
                    all_models.append(model_dict)

            except Exception as e:
                logger.warning(f"Failed to fetch models for {lab}: {e}")
                continue

        logger.info(f"Discovered {len(all_models)} total models from {len(labs)} labs")

        return all_models

    except FileNotFoundError as e:
        raise ValueError(f"Configuration file not found: {e}")
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML configuration: {e}")
    except Exception as e:
        logger.error(f"Model discovery failed: {e}")
        raise RuntimeError(f"Failed to discover models: {e}")


def filter_models_by_criteria(
    models: List[Dict[str, Any]],
    min_downloads: Optional[int] = None,
    min_likes: Optional[int] = None,
    required_tags: Optional[List[str]] = None,
    exclude_tags: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Filter models by additional criteria.

    Utility function to apply post-discovery filtering on model lists.

    Args:
        models: List of model dictionaries
        min_downloads: Minimum download count (None to skip)
        min_likes: Minimum like count (None to skip)
        required_tags: Tags that must be present (any match)
        exclude_tags: Tags that must not be present

    Returns:
        Filtered list of model dictionaries

    Example:
        >>> filtered = filter_models_by_criteria(
        ...     models,
        ...     min_downloads=1000,
        ...     required_tags=["text-generation"]
        ... )
    """
    filtered = []

    for model in models:
        # Check minimum downloads
        if min_downloads is not None and model.get("downloads", 0) < min_downloads:
            continue

        # Check minimum likes
        if min_likes is not None and model.get("likes", 0) < min_likes:
            continue

        # Check required tags
        if required_tags:
            model_tags = model.get("tags", [])
            if not any(tag in model_tags for tag in required_tags):
                continue

        # Check excluded tags
        if exclude_tags:
            model_tags = model.get("tags", [])
            if any(tag in model_tags for tag in exclude_tags):
                continue

        filtered.append(model)

    return filtered
