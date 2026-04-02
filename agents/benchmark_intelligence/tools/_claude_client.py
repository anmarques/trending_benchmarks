"""
Universal Claude API client that works across multiple environments.

Supports:
- Ambient Code Platform (with environment API keys)
- Claude Code interface
- Cursor interface
- Standard Anthropic API key (sk-ant-...)
- Vertex AI keys (automatically detected and handled)

The client automatically detects the environment and uses the appropriate
authentication method, providing seamless Claude access across all platforms.
"""

import os
import logging
import json
import re
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ClaudeEnvironment(Enum):
    """Detected environment for Claude access."""
    AMBIENT = "ambient"
    CLAUDE_CODE = "claude_code"
    CURSOR = "cursor"
    ANTHROPIC_API = "anthropic_api"
    VERTEX_AI = "vertex_ai"
    UNKNOWN = "unknown"


def detect_environment() -> ClaudeEnvironment:
    """
    Detect which environment we're running in.

    Returns:
        ClaudeEnvironment enum indicating detected environment
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "")

    # Check for Vertex AI key pattern
    if api_key.startswith("vertex-"):
        logger.debug("Detected Vertex AI key pattern")
        return ClaudeEnvironment.VERTEX_AI

    # Check for Ambient-specific environment variables
    if os.getenv("AMBIENT_SESSION_ID") or os.getenv("AMBIENT_WORKSPACE_ID"):
        logger.debug("Detected Ambient Code Platform environment")
        return ClaudeEnvironment.AMBIENT

    # Check for Claude Code environment
    if os.getenv("CLAUDE_CODE_SESSION"):
        logger.debug("Detected Claude Code environment")
        return ClaudeEnvironment.CLAUDE_CODE

    # Check for Cursor environment
    cursor_indicators = [
        os.getenv("CURSOR_SESSION"),
        "cursor" in os.getenv("TERM_PROGRAM", "").lower(),
        os.getenv("CURSOR_WORKSPACE"),
    ]
    if any(cursor_indicators):
        logger.debug("Detected Cursor environment")
        return ClaudeEnvironment.CURSOR

    # Check for standard Anthropic API key
    if api_key.startswith("sk-ant-"):
        logger.debug("Detected standard Anthropic API key")
        return ClaudeEnvironment.ANTHROPIC_API

    # Check if any API key is present (might work even if unknown format)
    if api_key:
        logger.debug(f"Detected API key with unknown format: {api_key[:10]}...")
        return ClaudeEnvironment.ANTHROPIC_API

    logger.debug("No Claude access detected")
    return ClaudeEnvironment.UNKNOWN


def is_anthropic_available() -> bool:
    """
    Check if Anthropic API is available.

    Returns:
        True if API key is set and anthropic package is installed
    """
    try:
        import anthropic  # noqa: F401
        has_key = bool(os.getenv("ANTHROPIC_API_KEY"))
        logger.debug(f"Anthropic available check: package=True, has_key={has_key}")
        return has_key
    except ImportError:
        logger.debug("Anthropic package not installed")
        return False


def call_claude(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: str = "claude-sonnet-4-20250514",
    max_tokens: int = 4096,
    temperature: float = 0.0,
    api_key: Optional[str] = None,
) -> str:
    """
    Call Claude API with a prompt (universal method).

    This function works across all environments:
    - Ambient Code Platform
    - Claude Code
    - Cursor
    - Standard Anthropic API

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
        ValueError: If API key is not found or invalid
    """
    # Detect environment
    environment = detect_environment()
    logger.info(f"Claude environment: {environment.value}")

    try:
        # Try to import anthropic
        try:
            from anthropic import Anthropic
        except ImportError:
            raise RuntimeError(
                "anthropic package not installed. "
                "Install with: pip install anthropic>=0.21.0"
            )

        # Get API key with fallbacks
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            error_msg = _get_helpful_error_message(environment)
            raise ValueError(error_msg)

        # Validate key format and provide helpful warnings
        if not _validate_api_key(api_key, environment):
            logger.warning(
                f"API key format may be incompatible with environment {environment.value}. "
                "If you get authentication errors, check your API key."
            )

        # Initialize client
        logger.debug(f"Initializing Anthropic client with key: {api_key[:15]}...")
        client = Anthropic(api_key=api_key)

        # Build messages
        messages = [{"role": "user", "content": prompt}]

        # Make API call
        logger.debug(f"Calling Claude API (model: {model}, max_tokens: {max_tokens})")

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
            result = response.content[0].text
            logger.debug(f"Claude API call successful, response length: {len(result)}")
            return result

        raise RuntimeError("Empty response from Claude API")

    except ValueError:
        # Re-raise ValueError (API key issues)
        raise
    except Exception as e:
        logger.error(f"Claude API call failed: {e}")
        _log_troubleshooting_info(environment, str(e))
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
    # Add JSON instruction to prompt if not already present
    if "```json" not in prompt.lower() and "provide your response as a json" not in prompt.lower():
        prompt = prompt + "\n\nProvide your response as a JSON object in a ```json code block."

    # Call Claude
    response_text = call_claude(
        prompt=prompt,
        system_prompt=system_prompt,
        model=model,
        max_tokens=max_tokens,
        temperature=0.0,
        api_key=api_key,
    )

    # Extract JSON from response
    json_text = _extract_json_from_response(response_text)

    # Parse JSON
    try:
        result = json.loads(json_text)
        logger.debug(f"Successfully parsed JSON response: {len(json_text)} chars")
        return result
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.debug(f"Attempted to parse: {json_text[:500]}...")
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
    # Pattern 1: ```json ... ```
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Pattern 2: ``` ... ``` (no language specified)
    match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        content = match.group(1).strip()
        # Check if it looks like JSON
        if content.startswith('{') or content.startswith('['):
            return content

    # Pattern 3: Look for JSON object directly in text
    match = re.search(r'(\{.*\})', text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Pattern 4: Look for JSON array directly in text
    match = re.search(r'(\[.*\])', text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # No pattern matched, return the whole text and let JSON parser fail
    return text.strip()


def _validate_api_key(api_key: str, environment: ClaudeEnvironment) -> bool:
    """
    Validate API key format for the detected environment.

    Args:
        api_key: The API key to validate
        environment: Detected environment

    Returns:
        True if key format is valid for environment, False if potentially incompatible
    """
    if environment == ClaudeEnvironment.ANTHROPIC_API:
        # Standard Anthropic keys should start with sk-ant-
        is_valid = api_key.startswith("sk-ant-")
        if not is_valid:
            logger.warning(
                f"API key does not match standard Anthropic format (sk-ant-...). "
                f"Got: {api_key[:10]}..."
            )
        return is_valid

    elif environment == ClaudeEnvironment.VERTEX_AI:
        # Vertex keys have different format
        is_valid = api_key.startswith("vertex-")
        if not is_valid:
            logger.warning("Detected Vertex AI environment but key doesn't match expected format")
        return is_valid

    # For other environments (Ambient, Claude Code, Cursor), we're less strict
    # since they might use platform-managed keys
    return True


def _get_helpful_error_message(environment: ClaudeEnvironment) -> str:
    """
    Get helpful error message based on detected environment.

    Args:
        environment: Detected environment

    Returns:
        Helpful error message with environment-specific guidance
    """
    base_msg = "ANTHROPIC_API_KEY not found in environment variables."

    guidance = {
        ClaudeEnvironment.AMBIENT: (
            "\n\nFor Ambient Code Platform:\n"
            "1. Go to Workspace Settings\n"
            "2. Add ANTHROPIC_API_KEY to environment variables\n"
            "3. Get your key from: https://console.anthropic.com/settings/keys"
        ),
        ClaudeEnvironment.CLAUDE_CODE: (
            "\n\nFor Claude Code:\n"
            "1. Set the environment variable: export ANTHROPIC_API_KEY='sk-ant-...'\n"
            "2. Or add to your shell profile (~/.bashrc or ~/.zshrc)\n"
            "3. Get your key from: https://console.anthropic.com/settings/keys"
        ),
        ClaudeEnvironment.CURSOR: (
            "\n\nFor Cursor:\n"
            "1. Add to Cursor settings or workspace configuration\n"
            "2. Or set in terminal: export ANTHROPIC_API_KEY='sk-ant-...'\n"
            "3. Get your key from: https://console.anthropic.com/settings/keys"
        ),
        ClaudeEnvironment.UNKNOWN: (
            "\n\nTo fix:\n"
            "1. Set environment variable: export ANTHROPIC_API_KEY='sk-ant-...'\n"
            "2. Get your key from: https://console.anthropic.com/settings/keys\n"
            "3. Restart your environment after setting the variable"
        ),
    }

    return base_msg + guidance.get(environment, guidance[ClaudeEnvironment.UNKNOWN])


def _log_troubleshooting_info(environment: ClaudeEnvironment, error: str):
    """
    Log troubleshooting information based on error and environment.

    Args:
        environment: Detected environment
        error: Error message
    """
    logger.error(f"Troubleshooting info for {environment.value}:")

    if "authentication_error" in error.lower() or "401" in error:
        logger.error(
            "Authentication failed. Check that:\n"
            "  1. ANTHROPIC_API_KEY is set correctly\n"
            f"  2. Key format matches environment (current: {environment.value})\n"
            "  3. API key is valid and has not expired\n"
            "  4. For Vertex AI, ensure you're using the correct authentication method"
        )

    elif "rate_limit" in error.lower() or "429" in error:
        logger.error(
            "Rate limit exceeded. Consider:\n"
            "  1. Adding delays between API calls\n"
            "  2. Upgrading your Anthropic API tier\n"
            "  3. Reducing the number of models processed"
        )

    elif "invalid_request" in error.lower() or "400" in error:
        logger.error(
            "Invalid request. Check:\n"
            "  1. Model name is correct and supported\n"
            "  2. Request parameters are valid\n"
            "  3. Prompt is not empty and properly formatted"
        )
