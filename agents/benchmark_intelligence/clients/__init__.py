"""
HuggingFace client abstraction layer.

This module provides a unified interface for interacting with HuggingFace,
supporting both direct API access and MCP (Model Context Protocol) integration.
"""

from .base import HFClientBase, ModelInfo
from .api_client import HFAPIClient
from .mcp_client import HFMCPClient
from .factory import get_hf_client

__all__ = [
    "HFClientBase",
    "ModelInfo",
    "HFAPIClient",
    "HFMCPClient",
    "get_hf_client",
]
