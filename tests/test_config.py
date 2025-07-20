"""
Comprehensive tests for configuration management.
Tests validation, loading, and error handling.
"""

import pytest
import os
import tempfile
from unittest.mock import patch

from src.config import Config, THEMES


class TestConfigValidation:
    """Test configuration validation."""
    
    def test_valid_config_creation(self):
        """Test creating a valid config instance."""
        config = Config(
            openai_api_key="test-key-123",
            theme="cyberpunk",
            openai_model="gpt-4o-mini"
        )
        assert config.openai_api_key == "test-key-123"
        assert config.theme == "cyberpunk"
        assert config.openai_model == "gpt-4o-mini"
        assert config.openai_base_url == "https://api.openai.com/v1"
    
    def test_default_values(self):
        """Test default configuration values."""
        config = Config(openai_api_key="test-key-123")
        assert config.openai_base_url == "https://api.openai.com/v1"
        assert config.openai_model == "gpt-4o-mini"
        assert config.theme == "cyberpunk"
        assert "Context7" in config.rag_system_prompt


class TestConfigLoading:
    """Test configuration loading from environment."""
    
    def test_load_with_valid_env(self):
        """Test loading config with valid environment variables."""
        env_vars = {
            "OPENAI_API_KEY": "test-api-key",
            "OPENAI_BASE_URL": "https://custom-api.com/v1",
            "OPENAI_MODEL": "gpt-4o",
            "CONTEXT7_THEME": "ocean"
        }
        
        with patch.dict(os.environ, env_vars):
            config = Config.load()
            assert config.openai_api_key == "test-api-key"
            assert config.openai_base_url == "https://custom-api.com/v1"
            assert config.openai_model == "gpt-4o"
            assert config.theme == "ocean"
    
    def test_load_missing_api_key(self):
        """Test loading config with missing API key raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                Config.load()
            assert "OPENAI_API_KEY is required" in str(exc_info.value)
    
    def test_load_invalid_theme(self):
        """Test loading config with invalid theme raises error."""
        env_vars = {
            "OPENAI_API_KEY": "test-key",
            "CONTEXT7_THEME": "invalid-theme"
        }
        
        with patch.dict(os.environ, env_vars):
            with pytest.raises(ValueError) as exc_info:
                Config.load()
            assert "Invalid theme" in str(exc_info.value)
            assert "cyberpunk, ocean, forest, sunset" in str(exc_info.value)
    
    def test_load_with_env_file(self):
        """Test loading config from .env file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("OPENAI_API_KEY=env-file-key\n")
            f.write("CONTEXT7_THEME=forest\n")
            env_file = f.name
        
        try:
            with patch.dict(os.environ, {}, clear=True):
                with patch('src.config.load_dotenv') as mock_load:
                    # Simulate loading from .env file
                    os.environ["OPENAI_API_KEY"] = "env-file-key"
                    os.environ["CONTEXT7_THEME"] = "forest"
                    
                    config = Config.load()
                    assert config.openai_api_key == "env-file-key"
                    assert config.theme == "forest"
        finally:
            os.unlink(env_file)


class TestConfigValidation:
    """Test individual configuration validation."""
    
    def test_all_valid_themes(self):
        """Test all valid themes are accepted."""
        for theme in THEMES:
            config = Config(
                openai_api_key="test-key",
                theme=theme
            )
            assert config.theme == theme
    
    def test_custom_history_path(self):
        """Test custom history file path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_path = os.path.join(temp_dir, "custom_history.json")
            config = Config(
                openai_api_key="test-key",
                history_file=custom_path
            )
            assert config.history_file == custom_path
    
    def test_custom_system_prompt(self):
        """Test custom system prompt."""
        custom_prompt = "Custom system prompt"
        config = Config(
            openai_api_key="test-key",
            rag_system_prompt=custom_prompt
        )
        assert config.rag_system_prompt == custom_prompt
    
    def test_empty_api_key_raises_error(self):
        """Test empty API key raises validation error."""
        with pytest.raises(ValueError):
            Config.load()


class TestConfigBackwardCompatibility:
    """Test backward compatibility."""
    
    def test_minimal_config(self):
        """Test config with only required fields."""
        config = Config(openai_api_key="test-key")
        assert config.openai_api_key == "test-key"
        assert config.openai_base_url == "https://api.openai.com/v1"
        assert config.openai_model == "gpt-4o-mini"
        assert config.theme == "cyberpunk"
    
    def test_environment_fallback(self):
        """Test environment variables as fallback."""
        env_vars = {
            "OPENAI_API_KEY": "fallback-key",
            "OPENAI_BASE_URL": "https://fallback.com/v1"
        }
        
        with patch.dict(os.environ, env_vars):
            config = Config.load()
            assert config.openai_api_key == "fallback-key"
            assert config.openai_base_url == "https://fallback.com/v1"
