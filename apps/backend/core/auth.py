"""
Authentication helpers for Auto Claude.

Provides centralized authentication token resolution with fallback support
for multiple environment variables, and SDK environment variable passthrough
for custom API endpoints.

Dual Auth Support:
- OAuth: Claude Code OAuth token for high-quality phases
- Antigravity: Proxy-based authentication for cost optimization
"""

import json
import logging
import os
import platform
import subprocess

logger = logging.getLogger(__name__)

# Priority order for auth token resolution
# NOTE: We intentionally do NOT fall back to ANTHROPIC_API_KEY.
# Auto Claude is designed to use Claude Code OAuth tokens only.
# This prevents silent billing to user's API credits when OAuth fails.
AUTH_TOKEN_ENV_VARS = [
    "CLAUDE_CODE_OAUTH_TOKEN",  # OAuth token from Claude Code CLI
    "ANTHROPIC_AUTH_TOKEN",  # CCR/proxy token (for enterprise setups)
]

# Environment variables to pass through to SDK subprocess
# NOTE: ANTHROPIC_API_KEY is intentionally excluded to prevent silent API billing
SDK_ENV_VARS = [
    # API endpoint configuration
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_AUTH_TOKEN",
    # Model overrides (from API Profile custom model mappings)
    "ANTHROPIC_MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
    # SDK behavior configuration
    "NO_PROXY",
    "DISABLE_TELEMETRY",
    "DISABLE_COST_WARNINGS",
    "API_TIMEOUT_MS",
]


def get_token_from_keychain() -> str | None:
    """
    Get authentication token from system credential store.

    Reads Claude Code credentials from:
    - macOS: Keychain
    - Windows: Credential Manager
    - Linux: Not yet supported (use env var)

    Returns:
        Token string if found, None otherwise
    """
    system = platform.system()

    if system == "Darwin":
        return _get_token_from_macos_keychain()
    elif system == "Windows":
        return _get_token_from_windows_credential_files()
    else:
        # Linux: secret-service not yet implemented
        return None


def _get_token_from_macos_keychain() -> str | None:
    """Get token from macOS Keychain."""
    try:
        result = subprocess.run(
            [
                "/usr/bin/security",
                "find-generic-password",
                "-s",
                "Claude Code-credentials",
                "-w",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            return None

        credentials_json = result.stdout.strip()
        if not credentials_json:
            return None

        data = json.loads(credentials_json)
        token = data.get("claudeAiOauth", {}).get("accessToken")

        if not token:
            return None

        # Validate token format (Claude OAuth tokens start with sk-ant-oat01-)
        if not token.startswith("sk-ant-oat01-"):
            return None

        return token

    except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError, Exception):
        return None


def _get_token_from_windows_credential_files() -> str | None:
    """Get token from Windows credential files.

    Claude Code on Windows stores credentials in ~/.claude/.credentials.json
    """
    try:
        # Claude Code stores credentials in ~/.claude/.credentials.json
        cred_paths = [
            os.path.expandvars(r"%USERPROFILE%\.claude\.credentials.json"),
            os.path.expandvars(r"%USERPROFILE%\.claude\credentials.json"),
            os.path.expandvars(r"%LOCALAPPDATA%\Claude\credentials.json"),
            os.path.expandvars(r"%APPDATA%\Claude\credentials.json"),
        ]

        for cred_path in cred_paths:
            if os.path.exists(cred_path):
                with open(cred_path, encoding="utf-8") as f:
                    data = json.load(f)
                    token = data.get("claudeAiOauth", {}).get("accessToken")
                    if token and token.startswith("sk-ant-oat01-"):
                        return token

        return None

    except (json.JSONDecodeError, KeyError, FileNotFoundError, Exception):
        return None


def get_auth_token() -> str | None:
    """
    Get authentication token from environment variables or system credential store.

    Checks multiple sources in priority order:
    1. CLAUDE_CODE_OAUTH_TOKEN (env var)
    2. ANTHROPIC_AUTH_TOKEN (CCR/proxy env var for enterprise setups)
    3. System credential store (macOS Keychain, Windows Credential Manager)

    NOTE: ANTHROPIC_API_KEY is intentionally NOT supported to prevent
    silent billing to user's API credits when OAuth is misconfigured.

    Returns:
        Token string if found, None otherwise
    """
    # First check environment variables
    for var in AUTH_TOKEN_ENV_VARS:
        token = os.environ.get(var)
        if token:
            return token

    # Fallback to system credential store
    return get_token_from_keychain()


def get_auth_token_source() -> str | None:
    """Get the name of the source that provided the auth token."""
    # Check environment variables first
    for var in AUTH_TOKEN_ENV_VARS:
        if os.environ.get(var):
            return var

    # Check if token came from system credential store
    if get_token_from_keychain():
        system = platform.system()
        if system == "Darwin":
            return "macOS Keychain"
        elif system == "Windows":
            return "Windows Credential Files"
        else:
            return "System Credential Store"

    return None


def require_auth_token() -> str:
    """
    Get authentication token or raise ValueError.

    Raises:
        ValueError: If no auth token is found in any supported source
    """
    token = get_auth_token()
    if not token:
        error_msg = (
            "No OAuth token found.\n\n"
            "Auto Claude requires Claude Code OAuth authentication.\n"
            "Direct API keys (ANTHROPIC_API_KEY) are not supported.\n\n"
        )
        # Provide platform-specific guidance
        system = platform.system()
        if system == "Darwin":
            error_msg += (
                "To authenticate:\n"
                "  1. Run: claude setup-token\n"
                "  2. The token will be saved to macOS Keychain automatically\n\n"
                "Or set CLAUDE_CODE_OAUTH_TOKEN in your .env file."
            )
        elif system == "Windows":
            error_msg += (
                "To authenticate:\n"
                "  1. Run: claude setup-token\n"
                "  2. The token should be saved to Windows Credential Manager\n\n"
                "If auto-detection fails, set CLAUDE_CODE_OAUTH_TOKEN in your .env file.\n"
                "Check: %LOCALAPPDATA%\\Claude\\credentials.json"
            )
        else:
            error_msg += (
                "To authenticate:\n"
                "  1. Run: claude setup-token\n"
                "  2. Set CLAUDE_CODE_OAUTH_TOKEN in your .env file"
            )
        raise ValueError(error_msg)
    return token


def get_sdk_env_vars() -> dict[str, str]:
    """
    Get environment variables to pass to SDK.

    Collects relevant env vars (ANTHROPIC_BASE_URL, etc.) that should
    be passed through to the claude-agent-sdk subprocess.

    Returns:
        Dict of env var name -> value for non-empty vars
    """
    env = {}
    for var in SDK_ENV_VARS:
        value = os.environ.get(var)
        if value:
            env[var] = value
    return env


def ensure_claude_code_oauth_token() -> None:
    """
    Ensure CLAUDE_CODE_OAUTH_TOKEN is set (for SDK compatibility).

    If not set but other auth tokens are available, copies the value
    to CLAUDE_CODE_OAUTH_TOKEN so the underlying SDK can use it.
    """
    if os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        return

    token = get_auth_token()
    if token:
        os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = token


# =============================================================================
# Antigravity Proxy Support
# =============================================================================

# Default Antigravity proxy settings
DEFAULT_ANTIGRAVITY_BASE_URL = "http://localhost:8080"
DEFAULT_ANTIGRAVITY_AUTH_TOKEN = "test"


def get_antigravity_base_url() -> str:
    """Get the Antigravity proxy base URL."""
    return os.environ.get("ANTIGRAVITY_BASE_URL", DEFAULT_ANTIGRAVITY_BASE_URL)


def get_antigravity_auth_token() -> str:
    """Get the Antigravity proxy auth token."""
    return os.environ.get("ANTIGRAVITY_AUTH_TOKEN", DEFAULT_ANTIGRAVITY_AUTH_TOKEN)


def check_antigravity_health(timeout: float = 2.0) -> bool:
    """
    Check if Antigravity proxy is running and healthy.

    Args:
        timeout: Request timeout in seconds

    Returns:
        True if proxy is healthy, False otherwise
    """
    try:
        import httpx

        base_url = get_antigravity_base_url()
        response = httpx.get(f"{base_url}/health", timeout=timeout)
        return response.status_code == 200
    except Exception as e:
        logger.debug(f"Antigravity health check failed: {e}")
        return False


def get_antigravity_account_limits(timeout: float = 5.0) -> dict | None:
    """
    Get Antigravity proxy account limits and quota information.

    Args:
        timeout: Request timeout in seconds

    Returns:
        Dict with account limits or None if unavailable
    """
    try:
        import httpx

        base_url = get_antigravity_base_url()
        response = httpx.get(f"{base_url}/account-limits", timeout=timeout)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.debug(f"Failed to get Antigravity account limits: {e}")
    return None


def get_auth_config(provider: str) -> dict[str, str]:
    """
    Get authentication configuration for a specific provider.

    Args:
        provider: Auth provider ("oauth" or "antigravity")

    Returns:
        Dict of auth configuration values
    """
    if provider == "antigravity":
        return {
            "ANTHROPIC_BASE_URL": get_antigravity_base_url(),
            "ANTHROPIC_AUTH_TOKEN": get_antigravity_auth_token(),
        }
    else:  # oauth
        return {
            "CLAUDE_CODE_OAUTH_TOKEN": require_auth_token(),
        }


def get_sdk_env_vars_for_provider(provider: str) -> dict[str, str]:
    """
    Get SDK environment variables configured for a specific auth provider.

    For OAuth: Uses Claude Code OAuth token with default Anthropic API
    For Antigravity: Routes through proxy with ANTHROPIC_BASE_URL override

    Args:
        provider: Auth provider ("oauth" or "antigravity")

    Returns:
        Dict of environment variables to pass to SDK subprocess
    """
    # Start with base SDK env vars
    base_env = get_sdk_env_vars()

    if provider == "antigravity":
        # Configure for Antigravity proxy
        base_env["ANTHROPIC_BASE_URL"] = get_antigravity_base_url()
        base_env["ANTHROPIC_AUTH_TOKEN"] = get_antigravity_auth_token()
        # Remove OAuth token - proxy handles auth
        base_env.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
    else:  # oauth
        # Configure for direct Anthropic API with OAuth
        # Remove any base URL override to use default API
        base_env.pop("ANTHROPIC_BASE_URL", None)
        base_env["CLAUDE_CODE_OAUTH_TOKEN"] = require_auth_token()

    return base_env


def get_sdk_env_vars_with_fallback(provider: str) -> tuple[dict[str, str], str]:
    """
    Get SDK environment variables with automatic fallback on Antigravity failure.

    If Antigravity is requested but unavailable, falls back to OAuth.

    Args:
        provider: Requested auth provider ("oauth" or "antigravity")

    Returns:
        Tuple of (env_vars_dict, actual_provider_used)
    """
    if provider == "antigravity":
        # Check if Antigravity proxy is available
        if check_antigravity_health():
            return get_sdk_env_vars_for_provider("antigravity"), "antigravity"
        else:
            logger.warning(
                "Antigravity proxy unavailable, falling back to OAuth. "
                f"Check if proxy is running at {get_antigravity_base_url()}"
            )
            return get_sdk_env_vars_for_provider("oauth"), "oauth"

    return get_sdk_env_vars_for_provider(provider), provider
