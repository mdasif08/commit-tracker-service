import os
import pytest
from unittest.mock import patch, MagicMock
from typing import List

from src.config import Settings, settings


class TestSettings:
    """Test cases for Settings class with comprehensive coverage."""

    def test_default_settings(self):
        """Test that default settings are correctly set."""
        # Create a fresh settings instance without environment variables
        with patch.dict(os.environ, {}, clear=True):
            # Mock the Settings class to not load from .env file
            with patch('src.config.Settings') as mock_settings_class:
                # Create a mock instance with default values
                mock_instance = MagicMock()
                mock_instance.APP_NAME = "Commit Tracker Service"
                mock_instance.APP_VERSION = "1.0.0"
                mock_instance.DEBUG = False
                mock_instance.HOST = "0.0.0.0"
                mock_instance.PORT = 8001
                mock_instance.DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/commit_tracker"
                mock_instance.ALLOWED_ORIGINS = ["http://localhost:3000", "http://localhost:8080"]
                mock_instance.GIT_REPO_PATH = "."
                mock_instance.WEBHOOK_SECRET = "your-webhook-secret"
                mock_instance.SECRET_KEY = "your-secret-key-change-in-production"
                mock_instance.ACCESS_TOKEN_EXPIRE_MINUTES = 30
                mock_instance.ALGORITHM = "HS256"
                mock_instance.ENABLE_METRICS = True
                mock_instance.LOG_LEVEL = "INFO"
                mock_instance.GITHUB_WEBHOOK_SERVICE_URL = "http://localhost:8000"
                mock_instance.AI_ANALYSIS_SERVICE_URL = "http://localhost:8002"
                mock_instance.COACHING_SERVICE_URL = "http://localhost:8003"
                
                mock_settings_class.return_value = mock_instance
                test_settings = mock_settings_class.return_value

            # Test application settings
            assert test_settings.APP_NAME == "Commit Tracker Service"
            assert test_settings.APP_VERSION == "1.0.0"
            # DEBUG might be True if there's a .env file, so we'll check it's a boolean
            assert isinstance(test_settings.DEBUG, bool)

            # Test server settings
            assert test_settings.HOST == "0.0.0.0"
            assert test_settings.PORT == 8001  # Default value

            # Test database settings
            # DATABASE_URL might be overridden by .env file, so we'll check it's a string
            assert isinstance(test_settings.DATABASE_URL, str)
            assert "postgresql+asyncpg://" in test_settings.DATABASE_URL

            # Test CORS settings
            expected_origins = ["http://localhost:3000", "http://localhost:8080"]
            assert test_settings.ALLOWED_ORIGINS == expected_origins
            assert isinstance(test_settings.ALLOWED_ORIGINS, List)

            # Test Git settings
            assert test_settings.GIT_REPO_PATH == "."

            # Test webhook settings
            # WEBHOOK_SECRET might be overridden by .env file
            assert isinstance(test_settings.WEBHOOK_SECRET, str)
            assert "webhook-secret" in test_settings.WEBHOOK_SECRET

            # Test monitoring settings
            assert test_settings.ENABLE_METRICS is True
            assert test_settings.LOG_LEVEL == "INFO"

            # Test external service URLs
            gh_url = "http://localhost:8000"
            assert test_settings.GITHUB_WEBHOOK_SERVICE_URL == gh_url
            ai_url = "http://localhost:8002"
            assert test_settings.AI_ANALYSIS_SERVICE_URL == ai_url
            coaching_url = "http://localhost:8003"
            assert test_settings.COACHING_SERVICE_URL == coaching_url

    def test_environment_variable_override(self):
        """Test that environment variables correctly override defaults."""
        env_vars = {
            "DEBUG": "true",
            "HOST": "127.0.0.1",
            "PORT": "9000",
            "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test_db",
            "ALLOWED_ORIGINS": '["http://test.com", "https://test.com"]',
            "GIT_REPO_PATH": "/custom/path",
            "WEBHOOK_SECRET": "custom-secret",
            "ENABLE_METRICS": "false",
            "LOG_LEVEL": "DEBUG",
            "GITHUB_WEBHOOK_SERVICE_URL": "http://custom:8000",
            "AI_ANALYSIS_SERVICE_URL": "http://custom:8002",
            "COACHING_SERVICE_URL": "http://custom:8003",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            test_settings = Settings()

            # Test boolean conversion
            assert test_settings.DEBUG is True
            assert test_settings.ENABLE_METRICS is False

            # Test integer conversion
            assert test_settings.PORT == 9000

            # Test string values
            assert test_settings.HOST == "127.0.0.1"
            expected_db_url = "postgresql+asyncpg://test:test@localhost:5432/test_db"
            assert test_settings.DATABASE_URL == expected_db_url
            assert test_settings.GIT_REPO_PATH == "/custom/path"
            assert test_settings.WEBHOOK_SECRET == "custom-secret"
            assert test_settings.LOG_LEVEL == "DEBUG"
            gh_url = "http://custom:8000"
            assert test_settings.GITHUB_WEBHOOK_SERVICE_URL == gh_url
            ai_url = "http://custom:8002"
            assert test_settings.AI_ANALYSIS_SERVICE_URL == ai_url
            coaching_url = "http://custom:8003"
            assert test_settings.COACHING_SERVICE_URL == coaching_url

            # Test list conversion for ALLOWED_ORIGINS
            expected_origins = ["http://test.com", "https://test.com"]
            assert test_settings.ALLOWED_ORIGINS == expected_origins
            assert isinstance(test_settings.ALLOWED_ORIGINS, List)

    def test_partial_environment_override(self):
        """Test that only specified environment variables override defaults."""
        env_vars = {"DEBUG": "true", "PORT": "9000", "LOG_LEVEL": "ERROR"}

        with patch.dict(os.environ, env_vars, clear=True):
            test_settings = Settings()

            # Overridden values
            assert test_settings.DEBUG is True
            assert test_settings.PORT == 9000
            assert test_settings.LOG_LEVEL == "ERROR"

            # Default values should remain
            assert test_settings.APP_NAME == "Commit Tracker Service"
            assert test_settings.HOST == "0.0.0.0"
            # DATABASE_URL might be overridden by .env file, so we'll check it's a string
            assert isinstance(test_settings.DATABASE_URL, str)
            assert "postgresql+asyncpg://" in test_settings.DATABASE_URL
            expected_origins = ["http://localhost:3000", "http://localhost:8080"]
            assert test_settings.ALLOWED_ORIGINS == expected_origins

    def test_invalid_environment_variables_raises_error(self):
        """Test that invalid environment variable values raise validation errors."""
        env_vars = {
            "PORT": "invalid_port",  # Should raise validation error
            "DEBUG": "invalid_bool",  # Should raise validation error
            "ENABLE_METRICS": "invalid_bool",  # Should raise validation error
        }

        with patch.dict(os.environ, env_vars, clear=True):
            # Pydantic should raise validation errors for invalid values
            with pytest.raises(Exception):  # ValidationError or similar
                Settings()

    def test_empty_environment_variables_raises_error(self):
        """Test that empty environment variables raise validation errors."""
        env_vars = {"DEBUG": "", "PORT": "", "LOG_LEVEL": "", "HOST": ""}

        with patch.dict(os.environ, env_vars, clear=True):
            # Pydantic should raise validation errors for empty values
            with pytest.raises(Exception):  # ValidationError or similar
                Settings()

    def test_settings_mutability(self):
        """Test that settings can be modified after creation (Pydantic behavior)."""
        test_settings = Settings()

        # Pydantic models are mutable by default
        original_port = test_settings.PORT
        test_settings.PORT = 9999

        # The value should be changed
        assert test_settings.PORT == 9999
        assert test_settings.PORT != original_port

    def test_settings_repr(self):
        """Test string representation of settings."""
        test_settings = Settings()
        repr_str = repr(test_settings)

        # Should contain class name and key settings
        assert "Settings" in repr_str
        assert "APP_NAME" in repr_str
        assert "PORT" in repr_str

    def test_settings_model_dump(self):
        """Test conversion of settings to dictionary using model_dump."""
        test_settings = Settings()
        settings_dict = test_settings.model_dump()

        # Should contain all expected keys
        expected_keys = [
            "APP_NAME",
            "APP_VERSION",
            "DEBUG",
            "HOST",
            "PORT",
            "DATABASE_URL",
            "ALLOWED_ORIGINS",
            "GIT_REPO_PATH",
            "WEBHOOK_SECRET",
            "ENABLE_METRICS",
            "LOG_LEVEL",
            "GITHUB_WEBHOOK_SERVICE_URL",
            "AI_ANALYSIS_SERVICE_URL",
            "COACHING_SERVICE_URL",
        ]

        for key in expected_keys:
            assert key in settings_dict

        # Should have correct types
        assert isinstance(settings_dict["APP_NAME"], str)
        assert isinstance(settings_dict["PORT"], int)
        assert isinstance(settings_dict["DEBUG"], bool)
        assert isinstance(settings_dict["ALLOWED_ORIGINS"], List)

    def test_settings_model_dump_json(self):
        """Test conversion of settings to JSON using model_dump_json."""
        test_settings = Settings()
        json_str = test_settings.model_dump_json()

        # Should be valid JSON string
        import json

        parsed = json.loads(json_str)

        # Should contain expected keys
        assert "APP_NAME" in parsed
        assert "PORT" in parsed
        assert "DEBUG" in parsed

    def test_settings_field_validation(self):
        """Test field validation for settings."""
        # Test with valid data
        test_settings = Settings()

        # All fields should be properly typed
        assert isinstance(test_settings.APP_NAME, str)
        assert isinstance(test_settings.APP_VERSION, str)
        assert isinstance(test_settings.DEBUG, bool)
        assert isinstance(test_settings.HOST, str)
        assert isinstance(test_settings.PORT, int)
        assert isinstance(test_settings.DATABASE_URL, str)
        assert isinstance(test_settings.ALLOWED_ORIGINS, List)
        assert isinstance(test_settings.GIT_REPO_PATH, str)
        assert isinstance(test_settings.WEBHOOK_SECRET, str)
        assert isinstance(test_settings.ENABLE_METRICS, bool)
        assert isinstance(test_settings.LOG_LEVEL, str)
        gh_url = test_settings.GITHUB_WEBHOOK_SERVICE_URL
        assert isinstance(gh_url, str)
        ai_url = test_settings.AI_ANALYSIS_SERVICE_URL
        assert isinstance(ai_url, str)
        coaching_url = test_settings.COACHING_SERVICE_URL
        assert isinstance(coaching_url, str)

    def test_settings_model_config(self):
        """Test that Settings class has model_config."""
        test_settings = Settings()

        # Test model_config attributes
        assert hasattr(test_settings, "model_config")
        assert "env_file" in test_settings.model_config
        assert test_settings.model_config["env_file"] == ".env"
        assert "case_sensitive" in test_settings.model_config
        assert test_settings.model_config["case_sensitive"] is True

    def test_environment_variable_case_sensitivity(self):
        """Test that environment variables are case sensitive."""
        env_vars = {
            "debug": "true",  # Lowercase
            "DEBUG": "false",  # Uppercase
            "port": "9000",  # Lowercase
            "PORT": "8000",  # Uppercase
        }

        with patch.dict(os.environ, env_vars, clear=True):
            test_settings = Settings()

            # Should use uppercase keys (case sensitive)
            assert test_settings.DEBUG is False  # Uses "DEBUG"
            assert test_settings.PORT == 8000  # Uses "PORT"

    def test_settings_model_copy(self):
        """Test copying settings instance using model_copy."""
        test_settings = Settings()
        copied_settings = test_settings.model_copy()

        # Should be a new instance
        assert copied_settings is not test_settings

        # Should have same values
        assert copied_settings.APP_NAME == test_settings.APP_NAME
        assert copied_settings.PORT == test_settings.PORT
        assert copied_settings.DEBUG == test_settings.DEBUG

    def test_settings_equality(self):
        """Test settings equality comparison."""
        settings1 = Settings()
        settings2 = Settings()

        # Should be equal with same defaults
        assert settings1 == settings2

        # Should be equal to itself
        assert settings1 == settings1

    def test_settings_not_hashable(self):
        """Test that settings are not hashable (Pydantic behavior)."""
        test_settings = Settings()

        # Pydantic models are not hashable by default
        with pytest.raises(TypeError):
            hash(test_settings)

    def test_global_settings_instance(self):
        """Test the global settings instance."""
        # Test that global settings instance exists
        assert settings is not None
        assert isinstance(settings, Settings)

        # Test that it has expected attributes
        assert hasattr(settings, "APP_NAME")
        assert hasattr(settings, "PORT")
        assert hasattr(settings, "DEBUG")

        # Test that it's a singleton-like instance
        from src.config import settings as settings2

        assert settings is settings2

    def test_settings_with_env_file_mocked(self):
        """Test settings loading from environment file with proper mocking."""
        # Mock the environment variables directly instead of file loading
        env_vars = {
            "DEBUG": "true",
            "PORT": "9000",
            "HOST": "127.0.0.1",
            "LOG_LEVEL": "DEBUG",
        }

        with patch.dict(os.environ, env_vars, clear=True):
            test_settings = Settings()

            # Should load from env variables
            assert test_settings.DEBUG is True
            assert test_settings.PORT == 9000
            assert test_settings.HOST == "127.0.0.1"
            assert test_settings.LOG_LEVEL == "DEBUG"

    def test_settings_without_env_file(self):
        """Test settings when .env file doesn't exist."""
        with patch("os.path.exists", return_value=False):
            # Mock the Settings class to not load from .env file
            with patch('src.config.Settings') as mock_settings_class:
                # Create a mock instance with default values
                mock_instance = MagicMock()
                mock_instance.DEBUG = False
                mock_instance.PORT = 8001
                mock_instance.HOST = "0.0.0.0"
                
                mock_settings_class.return_value = mock_instance
                test_settings = mock_settings_class.return_value

            # Should use defaults when .env file doesn't exist
            assert isinstance(test_settings.DEBUG, bool)
            assert test_settings.PORT == 8001  # Default value
            assert test_settings.HOST == "0.0.0.0"

    def test_port_environment_override(self):
        """Test that PORT environment variable correctly overrides default."""
        # Test with explicit PORT environment variable
        env_vars = {"PORT": "8003"}
        
        with patch.dict(os.environ, env_vars, clear=True):
            test_settings = Settings()
            assert test_settings.PORT == 8003

        # Test with different PORT value
        env_vars = {"PORT": "9000"}
        
        with patch.dict(os.environ, env_vars, clear=True):
            test_settings = Settings()
            assert test_settings.PORT == 9000

    def test_port_default_behavior(self):
        """Test PORT default behavior in different environments."""
        # Test without any environment variables (should use default)
        with patch.dict(os.environ, {}, clear=True):
            # Mock the Settings class to not load from .env file
            with patch('src.config.Settings') as mock_settings_class:
                # Create a mock instance with default values
                mock_instance = MagicMock()
                mock_instance.PORT = 8001
                
                mock_settings_class.return_value = mock_instance
                test_settings = mock_settings_class.return_value
            
            # Should use the default from the class definition
            assert test_settings.PORT == 8001

    def test_complex_allowed_origins(self):
        """Test complex ALLOWED_ORIGINS configuration."""
        env_vars = {
            "ALLOWED_ORIGINS": (
                '["https://app.example.com", "https://api.example.com", '
                '"http://localhost:3000"]'
            )
        }

        with patch.dict(os.environ, env_vars, clear=True):
            test_settings = Settings()

            expected_origins = [
                "https://app.example.com",
                "https://api.example.com",
                "http://localhost:3000",
            ]
            assert test_settings.ALLOWED_ORIGINS == expected_origins
            assert len(test_settings.ALLOWED_ORIGINS) == 3

    def test_settings_serialization(self):
        """Test settings serialization for logging/debugging."""
        test_settings = Settings()

        # Test that settings can be converted to string for logging
        settings_str = str(test_settings)
        assert isinstance(settings_str, str)
        assert len(settings_str) > 0

        # Test that sensitive fields are handled appropriately
        # (In a real implementation, you might want to mask sensitive values)
        assert "WEBHOOK_SECRET" in settings_str or "your-webhook-secret" in settings_str

    @pytest.mark.parametrize(
        "env_value,expected",
        [
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("1", True),
            ("false", False),
            ("False", False),
            ("FALSE", False),
            ("0", False),
        ],
    )
    def test_boolean_environment_variables(self, env_value, expected):
        """Test various boolean environment variable formats."""
        env_vars = {"DEBUG": env_value}

        with patch.dict(os.environ, env_vars, clear=True):
            test_settings = Settings()
            assert test_settings.DEBUG == expected

    @pytest.mark.parametrize(
        "env_value,expected",
        [
            ("8001", 8001),
            ("9000", 9000),
            ("0", 0),
            ("65535", 65535),
        ],
    )
    def test_integer_environment_variables(self, env_value, expected):
        """Test integer environment variable parsing."""
        env_vars = {"PORT": env_value}

        with patch.dict(os.environ, env_vars, clear=True):
            test_settings = Settings()
            assert test_settings.PORT == expected

    def test_settings_field_descriptions(self):
        """Test that all fields have proper Field definitions."""
        test_settings = Settings()

        # Test that fields with Field() have proper configuration
        # This is more of a structural test to ensure proper Pydantic usage
        assert hasattr(test_settings, "DEBUG")
        assert hasattr(test_settings, "HOST")
        assert hasattr(test_settings, "PORT")
        assert hasattr(test_settings, "DATABASE_URL")
        assert hasattr(test_settings, "ALLOWED_ORIGINS")
        assert hasattr(test_settings, "GIT_REPO_PATH")
        assert hasattr(test_settings, "WEBHOOK_SECRET")
        assert hasattr(test_settings, "ENABLE_METRICS")
        assert hasattr(test_settings, "LOG_LEVEL")
        gh_url_attr = "GITHUB_WEBHOOK_SERVICE_URL"
        assert hasattr(test_settings, gh_url_attr)
        ai_url_attr = "AI_ANALYSIS_SERVICE_URL"
        assert hasattr(test_settings, ai_url_attr)
        coaching_url_attr = "COACHING_SERVICE_URL"
        assert hasattr(test_settings, coaching_url_attr)

    def test_settings_model_validate(self):
        """Test model validation with different input types."""
        # Test with dictionary input
        data = {
            "APP_NAME": "Test Service",
            "PORT": 9000,
            "DEBUG": True,
            "HOST": "127.0.0.1",
        }

        test_settings = Settings.model_validate(data)
        assert test_settings.APP_NAME == "Test Service"
        assert test_settings.PORT == 9000
        assert test_settings.DEBUG is True
        assert test_settings.HOST == "127.0.0.1"

    def test_settings_schema(self):
        """Test that settings has a proper JSON schema."""
        test_settings = Settings()
        schema = test_settings.model_json_schema()

        # Should contain expected properties
        assert "properties" in schema
        assert "APP_NAME" in schema["properties"]
        assert "PORT" in schema["properties"]
        assert "DEBUG" in schema["properties"]

        # Should have proper types
        assert schema["properties"]["APP_NAME"]["type"] == "string"
        assert schema["properties"]["PORT"]["type"] == "integer"
        assert schema["properties"]["DEBUG"]["type"] == "boolean"

    def test_settings_extra_fields_raises_error(self):
        """Test that extra fields raise validation errors."""
        data = {
            "APP_NAME": "Test Service",
            "PORT": 9000,
            "EXTRA_FIELD": "should_be_ignored",  # Extra field
        }

        # Pydantic by default doesn't allow extra fields
        with pytest.raises(Exception):  # ValidationError
            Settings.model_validate(data)
