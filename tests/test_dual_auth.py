#!/usr/bin/env python3
"""
Tests for Dual Authentication System
=====================================

Tests the dual auth (OAuth + Antigravity) functionality including:
- Phase-based auth provider selection
- Agent-type to auth provider mapping
- Antigravity health check and fallback
- CLI override environment variables
"""

import os
from pathlib import Path
from unittest.mock import patch

import pytest


# =============================================================================
# Test Setup
# =============================================================================


@pytest.fixture
def temp_spec_dir(tmp_path):
    """Create a temporary spec directory with task_metadata.json."""
    spec_dir = tmp_path / "spec-001"
    spec_dir.mkdir()
    return spec_dir


@pytest.fixture
def clean_env():
    """Ensure clean environment for each test."""
    # Save current env vars
    saved_vars = {}
    env_keys = [
        "CLI_AUTH_PROVIDER_OVERRIDE",
        "AUTH_PROVIDER_SPEC",
        "AUTH_PROVIDER_PLANNING",
        "AUTH_PROVIDER_CODING",
        "AUTH_PROVIDER_QA",
        "ANTIGRAVITY_BASE_URL",
        "ANTIGRAVITY_AUTH_TOKEN",
    ]
    for key in env_keys:
        if key in os.environ:
            saved_vars[key] = os.environ[key]
            del os.environ[key]

    yield

    # Restore env vars
    for key in env_keys:
        if key in os.environ:
            del os.environ[key]
    for key, value in saved_vars.items():
        os.environ[key] = value


# =============================================================================
# Phase Auth Provider Tests
# =============================================================================


class TestPhaseAuthProvider:
    """Tests for phase-based auth provider selection."""

    def test_default_phase_auth_providers(self, temp_spec_dir, clean_env):
        """Test default auth providers for each phase."""
        from phase_config import get_phase_auth_provider

        # Quality-critical phases should use OAuth
        assert get_phase_auth_provider(temp_spec_dir, "spec") == "oauth"
        assert get_phase_auth_provider(temp_spec_dir, "planning") == "oauth"
        assert get_phase_auth_provider(temp_spec_dir, "qa") == "oauth"

        # Coding phase should use Antigravity for cost optimization
        assert get_phase_auth_provider(temp_spec_dir, "coding") == "antigravity"

    def test_cli_override_takes_precedence(self, temp_spec_dir, clean_env):
        """Test that CLI argument overrides all other settings."""
        from phase_config import get_phase_auth_provider

        # CLI override should work for any phase
        assert (
            get_phase_auth_provider(temp_spec_dir, "coding", cli_auth_provider="oauth")
            == "oauth"
        )
        assert (
            get_phase_auth_provider(
                temp_spec_dir, "planning", cli_auth_provider="antigravity"
            )
            == "antigravity"
        )

    def test_cli_global_override_env_var(self, temp_spec_dir, clean_env):
        """Test CLI_AUTH_PROVIDER_OVERRIDE environment variable."""
        from phase_config import get_phase_auth_provider

        os.environ["CLI_AUTH_PROVIDER_OVERRIDE"] = "oauth"

        # All phases should use OAuth when global override is set
        assert get_phase_auth_provider(temp_spec_dir, "spec") == "oauth"
        assert get_phase_auth_provider(temp_spec_dir, "planning") == "oauth"
        assert get_phase_auth_provider(temp_spec_dir, "coding") == "oauth"
        assert get_phase_auth_provider(temp_spec_dir, "qa") == "oauth"

    def test_phase_specific_env_override(self, temp_spec_dir, clean_env):
        """Test AUTH_PROVIDER_<PHASE> environment variables."""
        from phase_config import get_phase_auth_provider

        # Override only coding phase
        os.environ["AUTH_PROVIDER_CODING"] = "oauth"

        assert get_phase_auth_provider(temp_spec_dir, "coding") == "oauth"
        # Other phases should still use defaults
        assert get_phase_auth_provider(temp_spec_dir, "planning") == "oauth"

    def test_task_metadata_phase_auth_providers(self, temp_spec_dir, clean_env):
        """Test phaseAuthProviders from task_metadata.json."""
        import json

        from phase_config import get_phase_auth_provider

        # Create task_metadata.json with custom phase auth providers
        metadata = {
            "isAutoProfile": True,
            "phaseAuthProviders": {
                "spec": "antigravity",
                "planning": "antigravity",
                "coding": "oauth",
                "qa": "antigravity",
            },
        }
        (temp_spec_dir / "task_metadata.json").write_text(json.dumps(metadata))

        # Should use values from task_metadata.json
        assert get_phase_auth_provider(temp_spec_dir, "spec") == "antigravity"
        assert get_phase_auth_provider(temp_spec_dir, "coding") == "oauth"


# =============================================================================
# Agent Auth Provider Tests
# =============================================================================


class TestAgentAuthProvider:
    """Tests for agent-type to auth provider mapping."""

    def test_agent_type_mapping(self, temp_spec_dir, clean_env):
        """Test that agent types map to correct phases."""
        from phase_config import get_agent_auth_provider

        # Planner should use planning phase config (OAuth)
        assert get_agent_auth_provider(temp_spec_dir, "planner") == "oauth"

        # Coder should use coding phase config (Antigravity)
        assert get_agent_auth_provider(temp_spec_dir, "coder") == "antigravity"

        # QA agents should use QA phase config (OAuth)
        assert get_agent_auth_provider(temp_spec_dir, "qa_reviewer") == "oauth"
        assert get_agent_auth_provider(temp_spec_dir, "qa_fixer") == "oauth"

    def test_spec_agents_use_oauth(self, temp_spec_dir, clean_env):
        """Test that spec agents use OAuth for quality."""
        from phase_config import get_agent_auth_provider

        spec_agents = [
            "spec_gatherer",
            "spec_researcher",
            "spec_writer",
            "spec_critic",
            "complexity_assessor",
        ]
        for agent_type in spec_agents:
            assert get_agent_auth_provider(temp_spec_dir, agent_type) == "oauth"

    def test_utility_agents_use_antigravity(self, temp_spec_dir, clean_env):
        """Test that utility agents use Antigravity for cost savings."""
        from phase_config import get_agent_auth_provider

        utility_agents = ["commit_message", "insights", "merge_resolver"]
        for agent_type in utility_agents:
            assert get_agent_auth_provider(temp_spec_dir, agent_type) == "antigravity"


# =============================================================================
# Antigravity Health Check Tests
# =============================================================================


class TestAntigravityHealthCheck:
    """Tests for Antigravity proxy health check functionality."""

    def test_health_check_returns_false_when_proxy_not_running(self, clean_env):
        """Test that health check returns False when proxy is not available."""
        from core.auth import check_antigravity_health

        # Default URL (localhost:8080) should not be running
        assert check_antigravity_health(timeout=0.5) is False

    def test_health_check_custom_url(self, clean_env):
        """Test health check with custom URL."""
        from core.auth import check_antigravity_health, get_antigravity_base_url

        os.environ["ANTIGRAVITY_BASE_URL"] = "http://localhost:9999"
        assert get_antigravity_base_url() == "http://localhost:9999"
        assert check_antigravity_health(timeout=0.5) is False

    @patch("httpx.get")
    def test_health_check_returns_true_on_success(self, mock_get, clean_env):
        """Test health check returns True when proxy responds with 200."""
        from core.auth import check_antigravity_health

        mock_response = type("Response", (), {"status_code": 200})()
        mock_get.return_value = mock_response

        assert check_antigravity_health() is True


# =============================================================================
# SDK Env Vars Tests
# =============================================================================


class TestSdkEnvVars:
    """Tests for SDK environment variable generation."""

    def test_oauth_env_vars(self, clean_env):
        """Test OAuth environment variable configuration."""
        from core.auth import get_sdk_env_vars_for_provider

        os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = "test-token"

        env = get_sdk_env_vars_for_provider("oauth")

        assert "CLAUDE_CODE_OAUTH_TOKEN" in env
        assert "ANTHROPIC_BASE_URL" not in env

    def test_antigravity_env_vars(self, clean_env):
        """Test Antigravity environment variable configuration."""
        from core.auth import get_sdk_env_vars_for_provider

        os.environ["ANTIGRAVITY_BASE_URL"] = "http://localhost:8080"
        os.environ["ANTIGRAVITY_AUTH_TOKEN"] = "test-auth"

        env = get_sdk_env_vars_for_provider("antigravity")

        assert env.get("ANTHROPIC_BASE_URL") == "http://localhost:8080"
        assert env.get("ANTHROPIC_AUTH_TOKEN") == "test-auth"
        assert "CLAUDE_CODE_OAUTH_TOKEN" not in env

    def test_fallback_to_oauth_when_proxy_unavailable(self, clean_env):
        """Test automatic fallback to OAuth when Antigravity is unavailable."""
        from core.auth import get_sdk_env_vars_with_fallback

        os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = "test-token"

        # Request Antigravity but proxy is not running
        env, actual_provider = get_sdk_env_vars_with_fallback("antigravity")

        # Should fall back to OAuth
        assert actual_provider == "oauth"
        assert "CLAUDE_CODE_OAUTH_TOKEN" in env


# =============================================================================
# Is Antigravity Enabled Tests
# =============================================================================


class TestIsAntigravityEnabled:
    """Tests for is_antigravity_enabled function."""

    def test_returns_false_by_default(self, clean_env):
        """Test that Antigravity is disabled by default."""
        from phase_config import is_antigravity_enabled

        assert is_antigravity_enabled() is False

    def test_returns_true_when_configured(self, clean_env):
        """Test that Antigravity is enabled when URL is set."""
        from phase_config import is_antigravity_enabled

        os.environ["ANTIGRAVITY_BASE_URL"] = "http://localhost:8080"
        assert is_antigravity_enabled() is True
