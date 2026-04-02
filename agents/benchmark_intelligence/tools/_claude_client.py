"""
Internal Claude API client helper for AI-powered benchmark extraction tools.

This module provides a wrapper around the Anthropic API for use in
benchmark extraction, consolidation, and classification tasks.
"""

import os
import logging
from typing import Dict, Any, Optional
import json

logger = logging.getLogger(__name__)


def call_claude(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 4096,
    temperature: float = 0.0,
    api_key: Optional[str] = None,
) -> str:
    """
    Call Claude API with a prompt.

    Args:
        prompt: The user prompt/message
        system_prompt: Optional system prompt
        model: Claude model to use
        max_tokens: Maximum tokens in response
        temperature: Temperature for generation (0.0 = deterministic)
        api_key: Anthropic API key (if None, reads from ANTHROPIC_API_KEY env var)

    Returns:
        Claude's response text

    Raises:
        RuntimeError: If API call fails
        ValueError: If API key is not found
    """
    try:
        # Try to import anthropic
        try:
            from anthropic import Anthropic
        except ImportError:
            raise RuntimeError(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )

        # Get API key
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment variables. "
                "Set the environment variable or pass api_key parameter."
            )

        # Initialize client
        client = Anthropic(api_key=api_key)

        # Build messages
        messages = [{"role": "user", "content": prompt}]

        # Make API call
        logger.debug(f"Calling Claude API (model: {model})")

        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = client.messages.create(**kwargs)

        # Extract text from response
        if response.content and len(response.content) > 0:
            return response.content[0].text

        raise RuntimeError("Empty response from Claude API")

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Claude API call failed: {e}")
        raise RuntimeError(f"Failed to call Claude API: {e}")


def call_claude_json(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 4096,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Call Claude API and parse JSON response.

    Similar to call_claude but expects and parses a JSON response.

    Args:
        prompt: The user prompt/message
        system_prompt: Optional system prompt
        model: Claude model to use
        max_tokens: Maximum tokens in response
        api_key: Anthropic API key

    Returns:
        Parsed JSON response as dictionary

    Raises:
        RuntimeError: If API call fails or response is not valid JSON
        ValueError: If API key is not found
    """
    # Add JSON instruction to prompt
    if "```json" not in prompt.lower():
        prompt = prompt + "\n\nProvide your response as a JSON object."

    # Call Claude
    response_text = call_claude(
        prompt=prompt,
        system_prompt=system_prompt,
        model=model,
        max_tokens=max_tokens,
        temperature=0.0,
        api_key=api_key,
    )

    # Extract JSON from response (handle markdown code blocks)
    json_text = _extract_json_from_response(response_text)

    # Parse JSON
    try:
        return json.loads(json_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.debug(f"Response text: {response_text}")
        raise RuntimeError(f"Invalid JSON response from Claude: {e}")


def _extract_json_from_response(text: str) -> str:
    """
    Extract JSON from Claude's response.

    Handles responses wrapped in markdown code blocks.

    Args:
        text: Response text from Claude

    Returns:
        Extracted JSON string
    """
    # Try to find JSON in code block
    import re

    # Pattern 1: ```json ... ```
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Pattern 2: ``` ... ``` (no language specified)
    match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # No code block, assume entire response is JSON
    return text.strip()


def is_anthropic_available() -> bool:
    """
    Check if Anthropic API is available.

    Returns:
        True if API key is set and anthropic package is installed
    """
    try:
        import anthropic  # noqa: F401

        return bool(os.getenv("ANTHROPIC_API_KEY"))
    except ImportError:
        return False
