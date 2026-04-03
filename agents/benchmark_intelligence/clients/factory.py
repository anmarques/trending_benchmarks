"""
Factory for creating HuggingFace client instances.

Provides a centralized way to get the appropriate HuggingFace client,
with automatic fallback from MCP to API if needed.
"""

import os
import logging
from typing import Optional

from .base import HFClientBase
from .api_client import HFAPIClient
from .mcp_client import HFMCPClient


logger = logging.getLogger(__name__)


class HFClientFactory:
    """
    Factory class for creating HuggingFace client instances.

    This factory implements a fallback strategy:
    1. Try MCP client if available and enabled
    2. Fall back to API client if MCP is unavailable or disabled
    3. Raise error if API client cannot be configured
    """

    @staticmethod
    def create(
        prefer_mcp: bool = True,
        fallback_api: bool = True,
        token: Optional[str] = None,
        **kwargs
    ) -> HFClientBase:
        """
        Create a HuggingFace client instance.

        Args:
            prefer_mcp: Whether to try MCP first (default: True)
            fallback_api: Whether to fall back to API if MCP unavailable (default: True)
            token: Optional HuggingFace token (if None, reads from HF_TOKEN env var)
            **kwargs: Additional configuration options passed to the client

        Returns:
            A HFClientBase instance (either HFMCPClient or HFAPIClient)

        Raises:
            RuntimeError: If no valid client can be created

        Examples:
            >>> # Default behavior: try MCP, fallback to API
            >>> client = HFClientFactory.create()

            >>> # Force API client
            >>> client = HFClientFactory.create(prefer_mcp=False)

            >>> # MCP only, no fallback
            >>> client = HFClientFactory.create(fallback_api=False)

            >>> # With explicit token
            >>> client = HFClientFactory.create(token="hf_...")
        """
        # Try MCP first if preferred
        if prefer_mcp:
            logger.debug("Attempting to create MCP client...")
            if HFMCPClient.is_available():
                try:
                    client = HFMCPClient(**kwargs)
                    if client.validate_connection():
                        logger.info("Successfully created HuggingFace MCP client")
                        return client
                    else:
                        logger.warning("MCP client created but connection validation failed")
                except Exception as e:
                    logger.warning(f"Failed to create MCP client: {e}")
            else:
                logger.debug("MCP is not available")

            # If MCP failed and no fallback allowed, raise error
            if not fallback_api:
                raise RuntimeError(
                    "MCP client is not available and API fallback is disabled. "
                    "Enable fallback_api=True or ensure MCP is properly configured."
                )

        # Fall back to API client
        logger.debug("Creating HuggingFace API client...")

        # Get token from parameter or environment
        api_token = token or os.getenv("HF_TOKEN")

        if not api_token:
            logger.warning(
                "No HuggingFace token found. API access will be limited. "
                "Set HF_TOKEN environment variable or provide token parameter."
            )

        try:
            client = HFAPIClient(token=api_token, **kwargs)
            logger.info("Successfully created HuggingFace API client")
            return client
        except Exception as e:
            raise RuntimeError(f"Failed to create HuggingFace API client: {e}")


def get_hf_client(
    prefer_mcp: bool = True,
    fallback_api: bool = True,
    token: Optional[str] = None,
    **kwargs
) -> HFClientBase:
    """
    Get a HuggingFace client instance (convenience function).

    This is a convenience wrapper around HFClientFactory.create() that provides
    a simpler interface for the most common use case.

    Args:
        prefer_mcp: Whether to try MCP first (default: True)
        fallback_api: Whether to fall back to API if MCP unavailable (default: True)
        token: Optional HuggingFace token (if None, reads from HF_TOKEN env var)
        **kwargs: Additional configuration options passed to the client

    Returns:
        A HFClientBase instance (either HFMCPClient or HFAPIClient)

    Raises:
        RuntimeError: If HF_TOKEN is not set and no token provided
        RuntimeError: If no valid client can be created

    Examples:
        >>> # Simple usage - tries MCP, falls back to API
        >>> client = get_hf_client()
        >>> models = client.list_models(author="meta-llama", limit=10)

        >>> # Force API client only
        >>> client = get_hf_client(prefer_mcp=False)

        >>> # With custom configuration
        >>> client = get_hf_client(
        ...     token="hf_...",
        ...     max_retries=5,
        ...     retry_delay=2.0
        ... )
    """
    return HFClientFactory.create(
        prefer_mcp=prefer_mcp,
        fallback_api=fallback_api,
        token=token,
        **kwargs
    )


def get_api_client(token: Optional[str] = None, **kwargs) -> HFAPIClient:
    """
    Get a HuggingFace API client directly (bypass MCP).

    This is a convenience function for explicitly getting an API client
    without going through the MCP fallback logic.

    Args:
        token: Optional HuggingFace token (if None, reads from HF_TOKEN env var)
        **kwargs: Additional configuration options for HFAPIClient

    Returns:
        A HFAPIClient instance

    Raises:
        RuntimeError: If client creation fails

    Examples:
        >>> client = get_api_client()
        >>> models = client.list_models(sort="likes", limit=20)
    """
    api_token = token or os.getenv("HF_TOKEN")

    if not api_token:
        logger.warning(
            "No HuggingFace token found. API access will be limited. "
            "Set HF_TOKEN environment variable or provide token parameter."
        )

    return HFAPIClient(token=api_token, **kwargs)
