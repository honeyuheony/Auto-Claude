"""
Phase Configuration Module
===========================

Handles model, thinking level, and auth provider configuration for different execution phases.
Reads configuration from task_metadata.json and provides resolved model IDs.

Auth Provider Support:
- oauth: Uses Claude Code OAuth token (default for high-quality phases)
- antigravity: Uses Antigravity proxy for cost optimization (default for coding phases)
"""

import json
import os
from pathlib import Path
from typing import Literal, TypedDict

# Model shorthand to full model ID mapping
MODEL_ID_MAP: dict[str, str] = {
    "opus": "claude-opus-4-5-20251101",
    "sonnet": "claude-sonnet-4-5-20250929",
    "haiku": "claude-haiku-4-5-20251001",
}

# Thinking level to budget tokens mapping (None = no extended thinking)
# Values must match auto-claude-ui/src/shared/constants/models.ts THINKING_BUDGET_MAP
THINKING_BUDGET_MAP: dict[str, int | None] = {
    "none": None,
    "low": 1024,
    "medium": 4096,  # Moderate analysis
    "high": 16384,  # Deep thinking for QA review
    "ultrathink": 65536,  # Maximum reasoning depth
}

# Spec runner phase-specific thinking levels
# Heavy phases use ultrathink for deep analysis
# Light phases use medium after compaction
SPEC_PHASE_THINKING_LEVELS: dict[str, str] = {
    # Heavy phases - ultrathink (discovery, spec creation, self-critique)
    "discovery": "ultrathink",
    "spec_writing": "ultrathink",
    "self_critique": "ultrathink",
    # Light phases - medium (after first invocation with compaction)
    "requirements": "medium",
    "research": "medium",
    "context": "medium",
    "planning": "medium",
    "validation": "medium",
    "quick_spec": "medium",
    "historical_context": "medium",
    "complexity_assessment": "medium",
}

# Default phase configuration (matches UI defaults)
DEFAULT_PHASE_MODELS: dict[str, str] = {
    "spec": "sonnet",
    "planning": "opus",
    "coding": "sonnet",
    "qa": "sonnet",
}

DEFAULT_PHASE_THINKING: dict[str, str] = {
    "spec": "medium",
    "planning": "high",
    "coding": "medium",
    "qa": "high",
}

# Default Auth Provider per phase
# oauth: Claude Code OAuth token (high-quality, uses API quota)
# antigravity: Antigravity proxy (cost-free, uses Gemini models via proxy)
DEFAULT_PHASE_AUTH_PROVIDERS: dict[str, str] = {
    "spec": "oauth",  # Quality critical - ultrathink phases
    "planning": "oauth",  # High reasoning needed
    "coding": "antigravity",  # Routine work - cost optimization
    "qa": "oauth",  # Quality validation critical
}

# Default Auth Provider per agent type
# Maps agent types to their default auth provider
DEFAULT_AGENT_AUTH_PROVIDERS: dict[str, str] = {
    "planner": "oauth",
    "coder": "antigravity",
    "qa_reviewer": "oauth",
    "qa_fixer": "oauth",
    # Utility agents - use antigravity for cost savings
    "commit_message": "antigravity",
    "insights": "antigravity",
    "merge_resolver": "antigravity",
    # Spec agents - quality critical
    "spec_gatherer": "oauth",
    "spec_researcher": "oauth",
    "spec_writer": "oauth",
    "spec_critic": "oauth",
    "complexity_assessor": "oauth",
}

# Default Antigravity models per phase (when using antigravity provider)
# These models are available through the Antigravity proxy
DEFAULT_PHASE_ANTIGRAVITY_MODELS: dict[str, str] = {
    "spec": "claude-opus-4-5-thinking",  # Highest quality for spec creation
    "planning": "gemini-3-pro-high",  # High-quality Gemini for planning
    "coding": "gemini-3-flash",  # Fast Gemini for coding
    "qa": "claude-sonnet-4-5-thinking",  # Thorough review with thinking
}


class PhaseModelConfig(TypedDict, total=False):
    spec: str
    planning: str
    coding: str
    qa: str


class PhaseThinkingConfig(TypedDict, total=False):
    spec: str
    planning: str
    coding: str
    qa: str


class PhaseAuthProviderConfig(TypedDict, total=False):
    spec: str
    planning: str
    coding: str
    qa: str


class PhaseAntigravityModelConfig(TypedDict, total=False):
    spec: str
    planning: str
    coding: str
    qa: str


class TaskMetadataConfig(TypedDict, total=False):
    """Structure of model-related fields in task_metadata.json"""

    isAutoProfile: bool
    phaseModels: PhaseModelConfig
    phaseThinking: PhaseThinkingConfig
    phaseAuthProviders: PhaseAuthProviderConfig
    phaseAntigravityModels: PhaseAntigravityModelConfig
    model: str
    thinkingLevel: str
    authProvider: str  # Global auth provider override
    antigravityModel: str  # Global antigravity model override


Phase = Literal["spec", "planning", "coding", "qa"]
AuthProvider = Literal["oauth", "antigravity"]


def resolve_model_id(model: str) -> str:
    """
    Resolve a model shorthand (haiku, sonnet, opus) to a full model ID.
    If the model is already a full ID, return it unchanged.

    Priority:
    1. Environment variable override (from API Profile)
    2. Hardcoded MODEL_ID_MAP
    3. Pass through unchanged (assume full model ID)

    Args:
        model: Model shorthand or full ID

    Returns:
        Full Claude model ID
    """
    # Check for environment variable override (from API Profile custom model mappings)
    if model in MODEL_ID_MAP:
        env_var_map = {
            "haiku": "ANTHROPIC_DEFAULT_HAIKU_MODEL",
            "sonnet": "ANTHROPIC_DEFAULT_SONNET_MODEL",
            "opus": "ANTHROPIC_DEFAULT_OPUS_MODEL",
        }
        env_var = env_var_map.get(model)
        if env_var:
            env_value = os.environ.get(env_var)
            if env_value:
                return env_value

        # Fall back to hardcoded mapping
        return MODEL_ID_MAP[model]

    # Already a full model ID or unknown shorthand
    return model


def get_thinking_budget(thinking_level: str) -> int | None:
    """
    Get the thinking budget for a thinking level.

    Args:
        thinking_level: Thinking level (none, low, medium, high, ultrathink)

    Returns:
        Token budget or None for no extended thinking
    """
    import logging

    if thinking_level not in THINKING_BUDGET_MAP:
        valid_levels = ", ".join(THINKING_BUDGET_MAP.keys())
        logging.warning(
            f"Invalid thinking_level '{thinking_level}'. Valid values: {valid_levels}. "
            f"Defaulting to 'medium'."
        )
        return THINKING_BUDGET_MAP["medium"]

    return THINKING_BUDGET_MAP[thinking_level]


def load_task_metadata(spec_dir: Path) -> TaskMetadataConfig | None:
    """
    Load task_metadata.json from the spec directory.

    Args:
        spec_dir: Path to the spec directory

    Returns:
        Parsed task metadata or None if not found
    """
    metadata_path = spec_dir / "task_metadata.json"
    if not metadata_path.exists():
        return None

    try:
        with open(metadata_path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def get_phase_model(
    spec_dir: Path,
    phase: Phase,
    cli_model: str | None = None,
) -> str:
    """
    Get the resolved model ID for a specific execution phase.

    Priority:
    1. CLI argument (if provided)
    2. Phase-specific config from task_metadata.json (if auto profile)
    3. Single model from task_metadata.json (if not auto profile)
    4. Default phase configuration

    Args:
        spec_dir: Path to the spec directory
        phase: Execution phase (spec, planning, coding, qa)
        cli_model: Model from CLI argument (optional)

    Returns:
        Resolved full model ID
    """
    # CLI argument takes precedence
    if cli_model:
        return resolve_model_id(cli_model)

    # Load task metadata
    metadata = load_task_metadata(spec_dir)

    if metadata:
        # Check for auto profile with phase-specific config
        if metadata.get("isAutoProfile") and metadata.get("phaseModels"):
            phase_models = metadata["phaseModels"]
            model = phase_models.get(phase, DEFAULT_PHASE_MODELS[phase])
            return resolve_model_id(model)

        # Non-auto profile: use single model
        if metadata.get("model"):
            return resolve_model_id(metadata["model"])

    # Fall back to default phase configuration
    return resolve_model_id(DEFAULT_PHASE_MODELS[phase])


def get_phase_thinking(
    spec_dir: Path,
    phase: Phase,
    cli_thinking: str | None = None,
) -> str:
    """
    Get the thinking level for a specific execution phase.

    Priority:
    1. CLI argument (if provided)
    2. Phase-specific config from task_metadata.json (if auto profile)
    3. Single thinking level from task_metadata.json (if not auto profile)
    4. Default phase configuration

    Args:
        spec_dir: Path to the spec directory
        phase: Execution phase (spec, planning, coding, qa)
        cli_thinking: Thinking level from CLI argument (optional)

    Returns:
        Thinking level string
    """
    # CLI argument takes precedence
    if cli_thinking:
        return cli_thinking

    # Load task metadata
    metadata = load_task_metadata(spec_dir)

    if metadata:
        # Check for auto profile with phase-specific config
        if metadata.get("isAutoProfile") and metadata.get("phaseThinking"):
            phase_thinking = metadata["phaseThinking"]
            return phase_thinking.get(phase, DEFAULT_PHASE_THINKING[phase])

        # Non-auto profile: use single thinking level
        if metadata.get("thinkingLevel"):
            return metadata["thinkingLevel"]

    # Fall back to default phase configuration
    return DEFAULT_PHASE_THINKING[phase]


def get_phase_thinking_budget(
    spec_dir: Path,
    phase: Phase,
    cli_thinking: str | None = None,
) -> int | None:
    """
    Get the thinking budget tokens for a specific execution phase.

    Args:
        spec_dir: Path to the spec directory
        phase: Execution phase (spec, planning, coding, qa)
        cli_thinking: Thinking level from CLI argument (optional)

    Returns:
        Token budget or None for no extended thinking
    """
    thinking_level = get_phase_thinking(spec_dir, phase, cli_thinking)
    return get_thinking_budget(thinking_level)


def get_phase_config(
    spec_dir: Path,
    phase: Phase,
    cli_model: str | None = None,
    cli_thinking: str | None = None,
) -> tuple[str, str, int | None]:
    """
    Get the full configuration for a specific execution phase.

    Args:
        spec_dir: Path to the spec directory
        phase: Execution phase (spec, planning, coding, qa)
        cli_model: Model from CLI argument (optional)
        cli_thinking: Thinking level from CLI argument (optional)

    Returns:
        Tuple of (model_id, thinking_level, thinking_budget)
    """
    model_id = get_phase_model(spec_dir, phase, cli_model)
    thinking_level = get_phase_thinking(spec_dir, phase, cli_thinking)
    thinking_budget = get_thinking_budget(thinking_level)

    return model_id, thinking_level, thinking_budget


def get_spec_phase_thinking_budget(phase_name: str) -> int | None:
    """
    Get the thinking budget for a specific spec runner phase.

    This maps granular spec phases (discovery, spec_writing, etc.) to their
    appropriate thinking budgets based on SPEC_PHASE_THINKING_LEVELS.

    Args:
        phase_name: Name of the spec phase (e.g., 'discovery', 'spec_writing')

    Returns:
        Token budget for extended thinking, or None for no extended thinking
    """
    thinking_level = SPEC_PHASE_THINKING_LEVELS.get(phase_name, "medium")
    return get_thinking_budget(thinking_level)


# =============================================================================
# Auth Provider Configuration
# =============================================================================


def get_phase_auth_provider(
    spec_dir: Path,
    phase: Phase,
    cli_auth_provider: str | None = None,
) -> str:
    """
    Get the auth provider for a specific execution phase.

    Priority:
    1. CLI argument (if provided)
    2. CLI global override (CLI_AUTH_PROVIDER_OVERRIDE env var)
    3. Environment variable override (AUTH_PROVIDER_<PHASE>)
    4. Phase-specific config from task_metadata.json (if auto profile)
    5. Single auth provider from task_metadata.json (if not auto profile)
    6. Default phase configuration

    Args:
        spec_dir: Path to the spec directory
        phase: Execution phase (spec, planning, coding, qa)
        cli_auth_provider: Auth provider from CLI argument (optional)

    Returns:
        Auth provider string ("oauth" or "antigravity")
    """
    # CLI argument takes precedence
    if cli_auth_provider:
        return cli_auth_provider

    # CLI global override (from --force-oauth/--force-antigravity flags)
    cli_global_override = os.environ.get("CLI_AUTH_PROVIDER_OVERRIDE")
    if cli_global_override:
        return cli_global_override

    # Environment variable override (e.g., AUTH_PROVIDER_CODING=antigravity)
    env_override = os.environ.get(f"AUTH_PROVIDER_{phase.upper()}")
    if env_override:
        return env_override

    # Load task metadata
    metadata = load_task_metadata(spec_dir)

    if metadata:
        # Check for auto profile with phase-specific config
        if metadata.get("isAutoProfile") and metadata.get("phaseAuthProviders"):
            phase_auth = metadata["phaseAuthProviders"]
            return phase_auth.get(phase, DEFAULT_PHASE_AUTH_PROVIDERS[phase])

        # Non-auto profile: use single auth provider
        if metadata.get("authProvider"):
            return metadata["authProvider"]

    # Fall back to default phase configuration
    return DEFAULT_PHASE_AUTH_PROVIDERS[phase]


def get_agent_auth_provider(
    spec_dir: Path,
    agent_type: str,
    cli_auth_provider: str | None = None,
) -> str:
    """
    Get the auth provider for a specific agent type.

    Maps agent types to their corresponding phase, then uses phase auth provider logic.

    Args:
        spec_dir: Path to the spec directory
        agent_type: Agent type (e.g., 'coder', 'planner', 'qa_reviewer')
        cli_auth_provider: Auth provider from CLI argument (optional)

    Returns:
        Auth provider string ("oauth" or "antigravity")
    """
    # CLI argument takes precedence
    if cli_auth_provider:
        return cli_auth_provider

    # Map agent type to phase for phase-based lookup
    agent_to_phase: dict[str, Phase] = {
        "planner": "planning",
        "coder": "coding",
        "qa_reviewer": "qa",
        "qa_fixer": "qa",
        "spec_gatherer": "spec",
        "spec_researcher": "spec",
        "spec_writer": "spec",
        "spec_critic": "spec",
        "complexity_assessor": "spec",
    }

    # If agent type maps to a phase, use phase-based lookup
    if agent_type in agent_to_phase:
        phase = agent_to_phase[agent_type]
        return get_phase_auth_provider(spec_dir, phase, cli_auth_provider)

    # For utility agents not mapped to a phase, use agent-specific default
    return DEFAULT_AGENT_AUTH_PROVIDERS.get(agent_type, "oauth")


def get_phase_antigravity_model(
    spec_dir: Path,
    phase: Phase,
    cli_antigravity_model: str | None = None,
) -> str:
    """
    Get the Antigravity model for a specific execution phase.

    Priority:
    1. CLI argument (if provided)
    2. Environment variable override (ANTIGRAVITY_MODEL_<PHASE>)
    3. Phase-specific config from task_metadata.json (if auto profile)
    4. Single antigravity model from task_metadata.json (if not auto profile)
    5. Default phase configuration

    Args:
        spec_dir: Path to the spec directory
        phase: Execution phase (spec, planning, coding, qa)
        cli_antigravity_model: Antigravity model from CLI argument (optional)

    Returns:
        Antigravity model string (e.g., "claude-sonnet-4-5", "gemini-2.5-pro")
    """
    # CLI argument takes precedence
    if cli_antigravity_model:
        return cli_antigravity_model

    # Environment variable override (e.g., ANTIGRAVITY_MODEL_CODING=claude-sonnet-4-5)
    env_override = os.environ.get(f"ANTIGRAVITY_MODEL_{phase.upper()}")
    if env_override:
        return env_override

    # Load task metadata
    metadata = load_task_metadata(spec_dir)

    if metadata:
        # Check for auto profile with phase-specific config
        if metadata.get("isAutoProfile") and metadata.get("phaseAntigravityModels"):
            phase_models = metadata["phaseAntigravityModels"]
            return phase_models.get(phase, DEFAULT_PHASE_ANTIGRAVITY_MODELS[phase])

        # Non-auto profile: use single antigravity model
        if metadata.get("antigravityModel"):
            return metadata["antigravityModel"]

    # Fall back to default phase configuration
    return DEFAULT_PHASE_ANTIGRAVITY_MODELS[phase]


def get_agent_antigravity_model(
    spec_dir: Path,
    agent_type: str,
    cli_antigravity_model: str | None = None,
) -> str:
    """
    Get the Antigravity model for a specific agent type.

    Maps agent types to their corresponding phase, then uses phase antigravity model logic.

    Args:
        spec_dir: Path to the spec directory
        agent_type: Agent type (e.g., 'coder', 'planner', 'qa_reviewer')
        cli_antigravity_model: Antigravity model from CLI argument (optional)

    Returns:
        Antigravity model string (e.g., "claude-sonnet-4-5", "gemini-2.5-pro")
    """
    # CLI argument takes precedence
    if cli_antigravity_model:
        return cli_antigravity_model

    # Map agent type to phase for phase-based lookup
    agent_to_phase: dict[str, Phase] = {
        "planner": "planning",
        "coder": "coding",
        "qa_reviewer": "qa",
        "qa_fixer": "qa",
        "spec_gatherer": "spec",
        "spec_researcher": "spec",
        "spec_writer": "spec",
        "spec_critic": "spec",
        "complexity_assessor": "spec",
    }

    # If agent type maps to a phase, use phase-based lookup
    if agent_type in agent_to_phase:
        phase = agent_to_phase[agent_type]
        return get_phase_antigravity_model(spec_dir, phase, cli_antigravity_model)

    # For utility agents not mapped to a phase, use default coding phase model
    return DEFAULT_PHASE_ANTIGRAVITY_MODELS["coding"]


def is_antigravity_enabled() -> bool:
    """
    Check if Antigravity proxy is configured.

    Returns True if ANTIGRAVITY_BASE_URL is set in environment.
    """
    return bool(os.environ.get("ANTIGRAVITY_BASE_URL"))


# =============================================================================
# Setting Sources Configuration
# =============================================================================

# Valid setting sources for Claude Agent SDK
VALID_SETTING_SOURCES = ["user", "project", "local"]


def get_setting_sources() -> list[str] | None:
    """
    Get the setting sources configuration for Claude Agent SDK.

    Setting sources control which filesystem-based settings are loaded:
    - "user": Load from ~/.claude/ (skills, hooks, commands, settings.json)
    - "project": Load from .claude/ in project (CLAUDE.md, settings.json)
    - "local": Load from .claude/settings.local.json

    Environment variable: CLAUDE_SETTING_SOURCES (comma-separated)
    Examples:
        CLAUDE_SETTING_SOURCES=user,project  # Load user and project settings
        CLAUDE_SETTING_SOURCES=project       # Load project settings only
        CLAUDE_SETTING_SOURCES=              # Disable filesystem settings (default)

    Returns:
        List of setting sources, or None if disabled
    """
    env_value = os.environ.get("CLAUDE_SETTING_SOURCES", "").strip()

    if not env_value:
        return None

    # Parse comma-separated list
    sources = [s.strip().lower() for s in env_value.split(",") if s.strip()]

    # Validate sources
    valid_sources = [s for s in sources if s in VALID_SETTING_SOURCES]

    if not valid_sources:
        return None

    # Warn about invalid sources
    invalid_sources = [s for s in sources if s not in VALID_SETTING_SOURCES]
    if invalid_sources:
        import logging
        logging.warning(
            f"Invalid setting sources ignored: {invalid_sources}. "
            f"Valid values: {VALID_SETTING_SOURCES}"
        )

    return valid_sources


def get_full_phase_config(
    spec_dir: Path,
    phase: Phase,
    cli_model: str | None = None,
    cli_thinking: str | None = None,
    cli_auth_provider: str | None = None,
) -> tuple[str, str, int | None, str]:
    """
    Get the full configuration for a specific execution phase including auth provider.

    Args:
        spec_dir: Path to the spec directory
        phase: Execution phase (spec, planning, coding, qa)
        cli_model: Model from CLI argument (optional)
        cli_thinking: Thinking level from CLI argument (optional)
        cli_auth_provider: Auth provider from CLI argument (optional)

    Returns:
        Tuple of (model_id, thinking_level, thinking_budget, auth_provider)
    """
    model_id = get_phase_model(spec_dir, phase, cli_model)
    thinking_level = get_phase_thinking(spec_dir, phase, cli_thinking)
    thinking_budget = get_thinking_budget(thinking_level)
    auth_provider = get_phase_auth_provider(spec_dir, phase, cli_auth_provider)

    return model_id, thinking_level, thinking_budget, auth_provider
