"""
Universal Claude API client that works across multiple environments.

Supports:
- Ambient Code Platform (uses native Vertex AI credentials)
- Claude Code interface
- Cursor interface
- Standard Anthropic API key (sk-ant-...)
- Vertex AI with Google Cloud credentials

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
    # Check for Ambient-specific indicators first
    ambient_indicators = [
        os.getenv("AMBIENT_SESSION_ID"),
        os.getenv("AMBIENT_WORKSPACE_ID"),
        os.getenv("CLAUDECODE") == "1",
        os.getenv("RUNNER_TYPE") == "claude-agent-sdk",
    ]
    if any(ambient_indicators):
        logger.debug("Detected Ambient Code Platform environment")
        return ClaudeEnvironment.AMBIENT

    # Check for Vertex AI credentials file (might be standalone Vertex)
    vertex_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if vertex_creds and os.path.exists(vertex_creds):
        logger.debug("Detected Vertex AI with Google credentials")
        return ClaudeEnvironment.VERTEX_AI

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
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if api_key and api_key.startswith("sk-ant-"):
        logger.debug("Detected standard Anthropic API key")
        return ClaudeEnvironment.ANTHROPIC_API

    logger.debug("No specific environment detected")
    return ClaudeEnvironment.UNKNOWN


def is_anthropic_available() -> bool:
    """
    Check if Claude API access is available in any form.

    Returns:
        True if Claude can be accessed (via Ambient, Vertex, or Anthropic API)
    """
    env = detect_environment()

    # Ambient always has Claude access
    if env == ClaudeEnvironment.AMBIENT:
        return True

    # Vertex AI with credentials
    if env == ClaudeEnvironment.VERTEX_AI:
        return True

    # Standard Anthropic API
    try:
        import anthropic  # noqa: F401
        has_key = bool(os.getenv("ANTHROPIC_API_KEY"))
        return has_key
    except ImportError:
        return False


def _convert_to_vertex_model_id(standard_model: str) -> str:
    """
    Convert standard Anthropic model ID to Vertex AI format.

    Args:
        standard_model: Standard model ID (e.g., "claude-sonnet-4-20250514")

    Returns:
        Vertex model ID (e.g., "claude-sonnet-4-5@20250929")
    """
    # Map of common standard model IDs to Vertex equivalents
    model_mapping = {
        "claude-sonnet-4-20250514": "claude-sonnet-4-5@20250929",
        "claude-sonnet-4-20241022": "claude-sonnet-4-0@20241022",
        "claude-opus-4-20250514": "claude-opus-4-5@20250514",
        "claude-haiku-4-20250123": "claude-haiku-4-5@20250123",
    }

    # Return mapped version if available
    if standard_model in model_mapping:
        return model_mapping[standard_model]

    # Otherwise, try to parse and convert
    # Standard format: claude-{family}-{version}-{date}
    # Vertex format: claude-{family}-{version}@{date}
    parts = standard_model.rsplit('-', 1)
    if len(parts) == 2:
        base, date = parts
        # Replace last dash with @
        vertex_id = f"{base}@{date}"
        logger.debug(f"Converted model ID: {standard_model} -> {vertex_id}")
        return vertex_id

    # If we can't convert, return as-is and let Vertex handle it
    logger.warning(f"Could not convert model ID to Vertex format: {standard_model}")
    return standard_model


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
    - Ambient Code Platform (uses native Vertex AI)
    - Claude Code
    - Cursor
    - Standard Anthropic API

    Args:
        prompt: The user prompt/message
        system_prompt: Optional system prompt
        model: Claude model to use
        max_tokens: Maximum tokens in response
        temperature: Temperature for generation (0.0 = deterministic)
        api_key: Anthropic API key (if None, uses environment detection)

    Returns:
        Claude's response text

    Raises:
        RuntimeError: If API call fails
        ValueError: If Claude access is not available
    """
    # Detect environment
    environment = detect_environment()
    logger.info(f"Claude environment: {environment.value}")

    try:
        # Import Anthropic SDK
        try:
            from anthropic import AnthropicVertex, Anthropic
        except ImportError:
            raise RuntimeError(
                "anthropic package not installed. "
                "Install with: pip install anthropic>=0.21.0"
            )

        # Initialize client based on environment
        client = None

        if environment == ClaudeEnvironment.AMBIENT:
            # Ambient Code Platform - use Vertex AI with Google credentials
            logger.info("Using Ambient's native Vertex AI authentication")

            # Get Vertex configuration from environment
            project_id = os.getenv("ANTHROPIC_VERTEX_PROJECT_ID", "ambient-code-platform")
            region = os.getenv("ANTHROPIC_VERTEX_REGION", "us-east5")

            # Use Vertex model ID if available, otherwise convert standard model name
            vertex_model_id = os.getenv("LLM_MODEL_VERTEX_ID")
            if vertex_model_id:
                model = vertex_model_id
                logger.debug(f"Using Vertex model ID from environment: {model}")
            else:
                # Convert standard model name to Vertex format
                model = _convert_to_vertex_model_id(model)
                logger.debug(f"Converted to Vertex model ID: {model}")

            # Use Vertex AI client with Google Application Credentials
            logger.debug(f"Initializing Vertex client: project={project_id}, region={region}")
            client = AnthropicVertex(project_id=project_id, region=region)

        elif environment == ClaudeEnvironment.VERTEX_AI:
            # Standalone Vertex AI - use Google credentials
            project_id = os.getenv("ANTHROPIC_VERTEX_PROJECT_ID")
            region = os.getenv("ANTHROPIC_VERTEX_REGION", "us-east5")

            if not project_id:
                raise ValueError(
                    "ANTHROPIC_VERTEX_PROJECT_ID not set. "
                    "Required for Vertex AI authentication."
                )

            # Use Vertex model ID if available
            vertex_model_id = os.getenv("LLM_MODEL_VERTEX_ID")
            if vertex_model_id:
                model = vertex_model_id
            else:
                model = _convert_to_vertex_model_id(model)

            logger.info(f"Using Vertex AI: project={project_id}, region={region}, model={model}")
            client = AnthropicVertex(project_id=project_id, region=region)

        else:
            # Standard Anthropic API or other environments
            api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

            if not api_key:
                error_msg = _get_helpful_error_message(environment)
                raise ValueError(error_msg)

            logger.info("Using standard Anthropic API")
            client = Anthropic(api_key=api_key)

        # Build messages
        messages = [{"role": "user", "content": prompt}]

        # Make API call
        logger.debug(f"Calling Claude (model: {model}, max_tokens: {max_tokens})")

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
        # Re-raise ValueError (configuration issues)
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
        ValueError: If Claude access is not available
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


def _get_helpful_error_message(environment: ClaudeEnvironment) -> str:
    """
    Get helpful error message based on detected environment.

    Args:
        environment: Detected environment

    Returns:
        Helpful error message with environment-specific guidance
    """
    base_msg = "Claude API access not configured."

    guidance = {
        ClaudeEnvironment.AMBIENT: (
            "\n\nFor Ambient Code Platform:\n"
            "Claude should be available automatically via Vertex AI.\n"
            "If you see this error, please check:\n"
            "1. ANTHROPIC_VERTEX_PROJECT_ID is set\n"
            "2. GOOGLE_APPLICATION_CREDENTIALS points to valid credentials\n"
            "3. Contact Ambient support if the issue persists"
        ),
        ClaudeEnvironment.VERTEX_AI: (
            "\n\nFor Vertex AI:\n"
            "1. Set ANTHROPIC_VERTEX_PROJECT_ID to your GCP project ID\n"
            "2. Set GOOGLE_APPLICATION_CREDENTIALS to your service account key file\n"
            "3. Ensure Anthropic Claude is enabled in your GCP project"
        ),
        ClaudeEnvironment.CLAUDE_CODE: (
            "\n\nFor Claude Code:\n"
            "1. Set environment variable: export ANTHROPIC_API_KEY='sk-ant-...'\n"
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
            "3. Or set up Vertex AI with GOOGLE_APPLICATION_CREDENTIALS"
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

    if "authentication" in error.lower() or "401" in error or "403" in error:
        if environment == ClaudeEnvironment.AMBIENT:
            logger.error(
                "Ambient authentication failed. Check that:\n"
                "  1. GOOGLE_APPLICATION_CREDENTIALS is set correctly\n"
                "  2. Service account has Vertex AI permissions\n"
                "  3. Anthropic Claude is enabled in GCP project"
            )
        elif environment == ClaudeEnvironment.VERTEX_AI:
            logger.error(
                "Vertex AI authentication failed. Check that:\n"
                "  1. ANTHROPIC_VERTEX_PROJECT_ID is correct\n"
                "  2. GOOGLE_APPLICATION_CREDENTIALS points to valid key file\n"
                "  3. Service account has required permissions"
            )
        else:
            logger.error(
                "Authentication failed. Check that:\n"
                "  1. ANTHROPIC_API_KEY is set correctly\n"
                "  2. API key is valid and not expired\n"
                "  3. Key format matches environment"
            )

    elif "rate_limit" in error.lower() or "429" in error:
        logger.error(
            "Rate limit exceeded. Consider:\n"
            "  1. Adding delays between API calls\n"
            "  2. Reducing models_per_lab in config\n"
            "  3. Upgrading API tier if using Anthropic API"
        )

    elif "invalid_request" in error.lower() or "400" in error:
        logger.error(
            "Invalid request. Check:\n"
            "  1. Model name is correct and supported\n"
            "  2. Request parameters are valid\n"
            "  3. Prompt is properly formatted"
        )
