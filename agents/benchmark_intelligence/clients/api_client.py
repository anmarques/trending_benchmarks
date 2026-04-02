"""
HuggingFace API client implementation using huggingface_hub library.

This implementation uses the official HuggingFace Hub Python library
to interact with the HuggingFace API directly.
"""

import os
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from huggingface_hub import HfApi, ModelCard
from huggingface_hub.utils import (
    RepositoryNotFoundError,
    HfHubHTTPError,
    BadRequestError,
)

from .base import HFClientBase, ModelInfo


logger = logging.getLogger(__name__)


class HFAPIClient(HFClientBase):
    """
    HuggingFace client using the huggingface_hub API.

    This implementation uses the official HuggingFace Hub library to provide
    direct API access to HuggingFace models and metadata.

    Attributes:
        api: The HfApi instance used for API calls
        token: Optional HuggingFace API token for authentication
        max_retries: Maximum number of retries for rate-limited requests
        retry_delay: Initial delay between retries (seconds)
    """

    def __init__(
        self,
        token: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize the HuggingFace API client.

        Args:
            token: HuggingFace API token. If None, will try to read from HF_TOKEN env var
            max_retries: Maximum number of retries for rate-limited requests
            retry_delay: Initial delay between retries (seconds), uses exponential backoff

        Raises:
            ValueError: If no token is provided and HF_TOKEN env var is not set
        """
        self.token = token or os.getenv("HF_TOKEN")
        if not self.token:
            logger.warning(
                "No HuggingFace token provided. API access will be limited. "
                "Set HF_TOKEN environment variable or pass token to constructor."
            )

        self.api = HfApi(token=self.token)
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def _handle_rate_limit(self, attempt: int) -> None:
        """
        Handle rate limiting with exponential backoff.

        Args:
            attempt: Current attempt number (0-indexed)
        """
        delay = self.retry_delay * (2 ** attempt)
        logger.warning(f"Rate limited. Retrying in {delay:.1f} seconds...")
        time.sleep(delay)

    def _execute_with_retry(self, func, *args, **kwargs):
        """
        Execute a function with retry logic for rate limiting.

        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            The function's return value

        Raises:
            The last exception if all retries are exhausted
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except HfHubHTTPError as e:
                last_exception = e
                # Check if it's a rate limit error (429)
                if e.response.status_code == 429:
                    if attempt < self.max_retries - 1:
                        self._handle_rate_limit(attempt)
                        continue
                # For other HTTP errors, raise immediately
                raise
            except Exception as e:
                # For non-HTTP errors, raise immediately
                raise

        # If we exhausted all retries, raise the last exception
        raise last_exception

    def _convert_to_model_info(self, model) -> ModelInfo:
        """
        Convert HuggingFace ModelInfo object to our ModelInfo dataclass.

        Args:
            model: HuggingFace ModelInfo object

        Returns:
            Our ModelInfo dataclass instance
        """
        return ModelInfo(
            id=model.id,
            author=model.author or model.id.split("/")[0] if "/" in model.id else "unknown",
            downloads=getattr(model, "downloads", 0) or 0,
            likes=getattr(model, "likes", 0) or 0,
            created_at=getattr(model, "created_at", None),
            last_modified=getattr(model, "last_modified", None),
            tags=model.tags or [],
            pipeline_tag=getattr(model, "pipeline_tag", None),
            private=getattr(model, "private", False),
            gated=getattr(model, "gated", False) or False,
            library_name=getattr(model, "library_name", None),
        )

    def list_models(
        self,
        author: Optional[str] = None,
        limit: int = 100,
        sort: str = "downloads",
        **kwargs
    ) -> List[ModelInfo]:
        """
        List models from HuggingFace Hub.

        Args:
            author: Filter by model author/organization (e.g., "meta-llama")
            limit: Maximum number of models to return
            sort: Sort order - one of: "downloads", "likes", "trending", "created", "modified"
            **kwargs: Additional filtering parameters:
                - task: Filter by task (e.g., "text-generation")
                - library: Filter by library (e.g., "transformers")
                - tags: Filter by tags (list of strings)
                - search: Search query string
                - gated: Filter gated models (bool)

        Returns:
            List of ModelInfo objects

        Raises:
            ValueError: If parameters are invalid
            ConnectionError: If unable to connect to HuggingFace
            RuntimeError: If the request fails
        """
        try:
            # Map our sort parameter to HuggingFace API sort parameter
            sort_mapping = {
                "downloads": "downloads",
                "likes": "likes",
                "trending": "trending",
                "created": "createdAt",
                "modified": "lastModified",
            }

            if sort not in sort_mapping:
                raise ValueError(
                    f"Invalid sort parameter: {sort}. "
                    f"Must be one of: {', '.join(sort_mapping.keys())}"
                )

            # Build filter parameters (don't include author in filter)
            filter_params = {}
            if "task" in kwargs:
                filter_params["task"] = kwargs["task"]
            if "library" in kwargs:
                filter_params["library"] = kwargs["library"]
            if "tags" in kwargs and kwargs["tags"]:  # Only add if non-empty
                filter_params["tags"] = kwargs["tags"]
            if "gated" in kwargs:
                filter_params["gated"] = kwargs["gated"]

            search_query = kwargs.get("search")

            # Execute API call with retry logic
            models = self._execute_with_retry(
                self.api.list_models,
                filter=filter_params if filter_params else None,
                author=author,
                search=search_query,
                sort=sort_mapping[sort],
                limit=limit,
            )

            # Convert to our ModelInfo objects
            result = [self._convert_to_model_info(model) for model in models]

            logger.info(f"Retrieved {len(result)} models from HuggingFace Hub")
            return result

        except BadRequestError as e:
            raise ValueError(f"Invalid request parameters: {e}")
        except HfHubHTTPError as e:
            if e.response.status_code >= 500:
                raise ConnectionError(f"HuggingFace API server error: {e}")
            raise RuntimeError(f"HuggingFace API request failed: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to list models: {e}")

    def get_model_card(self, model_id: str) -> str:
        """
        Retrieve the README/model card content for a model.

        Args:
            model_id: The model identifier (e.g., "meta-llama/Llama-2-7b")

        Returns:
            The model card content as a markdown string

        Raises:
            ValueError: If model_id is invalid
            FileNotFoundError: If model or model card doesn't exist
            RuntimeError: If the request fails
        """
        if not model_id or not isinstance(model_id, str):
            raise ValueError("model_id must be a non-empty string")

        try:
            # Load the model card
            card = self._execute_with_retry(
                ModelCard.load,
                model_id,
                token=self.token,
            )

            # Return the text content
            content = card.content if card.content else ""

            logger.info(f"Retrieved model card for {model_id} ({len(content)} chars)")
            return content

        except RepositoryNotFoundError:
            raise FileNotFoundError(f"Model not found: {model_id}")
        except HfHubHTTPError as e:
            if e.response.status_code == 404:
                raise FileNotFoundError(f"Model card not found for: {model_id}")
            raise RuntimeError(f"Failed to retrieve model card: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve model card for {model_id}: {e}")

    def get_model_metadata(self, model_id: str) -> Dict[str, Any]:
        """
        Retrieve comprehensive metadata for a model.

        Args:
            model_id: The model identifier (e.g., "meta-llama/Llama-2-7b")

        Returns:
            Dictionary containing model metadata including:
                - id, author, downloads, likes
                - tags, pipeline_tag, library_name
                - created_at, last_modified
                - card_data: Model card metadata
                - siblings: List of files in the repository

        Raises:
            ValueError: If model_id is invalid
            FileNotFoundError: If model doesn't exist
            RuntimeError: If the request fails
        """
        if not model_id or not isinstance(model_id, str):
            raise ValueError("model_id must be a non-empty string")

        try:
            # Get model info from API
            model_info = self._execute_with_retry(
                self.api.model_info,
                model_id,
                token=self.token,
            )

            # Build metadata dictionary
            metadata = {
                "id": model_info.id,
                "author": model_info.author or model_id.split("/")[0] if "/" in model_id else "unknown",
                "downloads": getattr(model_info, "downloads", 0) or 0,
                "likes": getattr(model_info, "likes", 0) or 0,
                "created_at": model_info.created_at.isoformat() if model_info.created_at else None,
                "last_modified": model_info.last_modified.isoformat() if model_info.last_modified else None,
                "tags": model_info.tags or [],
                "pipeline_tag": getattr(model_info, "pipeline_tag", None),
                "library_name": getattr(model_info, "library_name", None),
                "private": getattr(model_info, "private", False),
                "gated": getattr(model_info, "gated", False) or False,
                "disabled": getattr(model_info, "disabled", False),
            }

            # Add card data if available
            if hasattr(model_info, "card_data") and model_info.card_data:
                metadata["card_data"] = model_info.card_data

            # Add siblings (files) information
            if hasattr(model_info, "siblings") and model_info.siblings:
                metadata["siblings"] = [
                    {
                        "rfilename": s.rfilename,
                        "size": getattr(s, "size", None),
                    }
                    for s in model_info.siblings
                ]

            # Add config if available
            if hasattr(model_info, "config") and model_info.config:
                metadata["config"] = model_info.config

            logger.info(f"Retrieved metadata for {model_id}")
            return metadata

        except RepositoryNotFoundError:
            raise FileNotFoundError(f"Model not found: {model_id}")
        except HfHubHTTPError as e:
            if e.response.status_code == 404:
                raise FileNotFoundError(f"Model not found: {model_id}")
            raise RuntimeError(f"Failed to retrieve model metadata: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve metadata for {model_id}: {e}")
