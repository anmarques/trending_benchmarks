"""
Abstract base class for HuggingFace clients.

Defines the interface that all HuggingFace client implementations must follow.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional


@dataclass
class ModelInfo:
    """
    Information about a HuggingFace model.

    Attributes:
        id: The model's unique identifier (e.g., "meta-llama/Llama-2-7b")
        author: The model's author/organization
        downloads: Number of downloads
        likes: Number of likes/stars
        created_at: When the model was created
        last_modified: When the model was last updated
        tags: List of tags associated with the model
        pipeline_tag: The primary task/pipeline (e.g., "text-generation")
        private: Whether the model is private
        gated: Whether the model requires access approval
        library_name: The ML library used (e.g., "transformers", "diffusers")
    """
    id: str
    author: str
    downloads: int
    likes: int
    created_at: Optional[datetime]
    last_modified: Optional[datetime]
    tags: List[str]
    pipeline_tag: Optional[str]
    private: bool
    gated: bool
    library_name: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert ModelInfo to dictionary representation."""
        return {
            "id": self.id,
            "author": self.author,
            "downloads": self.downloads,
            "likes": self.likes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_modified": self.last_modified.isoformat() if self.last_modified else None,
            "tags": self.tags,
            "pipeline_tag": self.pipeline_tag,
            "private": self.private,
            "gated": self.gated,
            "library_name": self.library_name,
        }


class HFClientBase(ABC):
    """
    Abstract base class for HuggingFace client implementations.

    This interface defines the core operations needed for interacting with
    HuggingFace models and their metadata. Implementations can use different
    backends (API, MCP, etc.) while maintaining a consistent interface.
    """

    @abstractmethod
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
            **kwargs: Additional filtering parameters (e.g., task, library, tags)

        Returns:
            List of ModelInfo objects

        Raises:
            ValueError: If parameters are invalid
            ConnectionError: If unable to connect to HuggingFace
            RuntimeError: If the request fails
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
                - model card metadata
                - config information (if available)

        Raises:
            ValueError: If model_id is invalid
            FileNotFoundError: If model doesn't exist
            RuntimeError: If the request fails
        """
        pass

    def validate_connection(self) -> bool:
        """
        Validate that the client can connect to HuggingFace.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to list a single model as a connectivity test
            self.list_models(limit=1)
            return True
        except Exception:
            return False
