"""
Secrets Management Module

Provides secure handling of API keys and sensitive configuration:
- Environment-based secret loading
- Validation on startup
- Masked logging
- Key rotation support
"""

import os
from typing import Optional, Dict
from pathlib import Path


class SecretsManager:
    """
    Manages secure access to API keys and secrets
    """

    # Required secrets for the application
    REQUIRED_SECRETS = [
        'KIMI_API_KEY',
        'TAVILY_API_KEY',
    ]

    # Optional secrets
    OPTIONAL_SECRETS = []

    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize secrets manager

        Args:
            env_file: Path to .env file (optional, uses environment if not provided)
        """
        self.env_file = env_file
        self.secrets_cache: Dict[str, str] = {}

        # Load environment variables if env_file provided
        if env_file and Path(env_file).exists():
            self._load_env_file(env_file)

    def _load_env_file(self, env_file: str):
        """
        Load environment variables from file

        Args:
            env_file: Path to .env file
        """
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
        except ImportError:
            print("Warning: python-dotenv not installed, cannot load .env file")
        except Exception as e:
            print(f"Warning: Could not load .env file: {e}")

    def get_secret(self, key: str, required: bool = True) -> Optional[str]:
        """
        Get secret value from environment

        Args:
            key: Secret key name
            required: Whether this secret is required

        Returns:
            Secret value or None if not found and not required

        Raises:
            ValueError: If required secret is not found
        """
        # Check cache first
        if key in self.secrets_cache:
            return self.secrets_cache[key]

        # Get from environment
        value = os.getenv(key)

        if required and not value:
            raise ValueError(
                f"Required secret '{key}' not found in environment. "
                f"Please set it in your .env file or environment variables."
            )

        # Cache the value
        if value:
            self.secrets_cache[key] = value

        return value

    def validate_all_secrets(self) -> tuple[bool, list[str]]:
        """
        Validate that all required secrets are present

        Returns:
            Tuple of (all_valid, list of missing secrets)
        """
        missing_secrets = []

        for secret in self.REQUIRED_SECRETS:
            try:
                value = self.get_secret(secret, required=True)
                if not value:
                    missing_secrets.append(secret)
            except ValueError:
                missing_secrets.append(secret)

        all_valid = len(missing_secrets) == 0

        return all_valid, missing_secrets

    def get_kimi_api_key(self) -> str:
        """
        Get Kimi K2 API key

        Returns:
            API key

        Raises:
            ValueError: If API key not found
        """
        return self.get_secret('KIMI_API_KEY', required=True)

    def get_tavily_api_key(self) -> str:
        """
        Get Tavily API key

        Returns:
            API key

        Raises:
            ValueError: If API key not found
        """
        return self.get_secret('TAVILY_API_KEY', required=True)

    @staticmethod
    def mask_secret(secret: str, show_chars: int = 4) -> str:
        """
        Mask secret for safe logging

        Args:
            secret: Secret value to mask
            show_chars: Number of characters to show at start and end

        Returns:
            Masked secret (e.g., "sk-ab...xyz")
        """
        if not secret:
            return "***"

        if len(secret) <= show_chars * 2:
            return "*" * len(secret)

        # Show first and last N characters
        return f"{secret[:show_chars]}...{secret[-show_chars:]}"

    @staticmethod
    def is_valid_kimi_key(key: str) -> bool:
        """
        Validate Kimi API key format

        Args:
            key: API key to validate

        Returns:
            True if valid format, False otherwise
        """
        if not key:
            return False

        # Kimi keys start with 'sk-'
        if not key.startswith('sk-'):
            return False

        # Should be reasonable length
        if len(key) < 20:
            return False

        return True

    @staticmethod
    def is_valid_tavily_key(key: str) -> bool:
        """
        Validate Tavily API key format

        Args:
            key: API key to validate

        Returns:
            True if valid format, False otherwise
        """
        if not key:
            return False

        # Tavily keys start with 'tvly-'
        if not key.startswith('tvly-'):
            return False

        # Should be reasonable length
        if len(key) < 20:
            return False

        return True

    def verify_secrets_format(self) -> Dict[str, bool]:
        """
        Verify format of all configured secrets

        Returns:
            Dictionary of {secret_name: is_valid}
        """
        results = {}

        # Check Kimi key
        kimi_key = self.get_secret('KIMI_API_KEY', required=False)
        if kimi_key:
            results['KIMI_API_KEY'] = self.is_valid_kimi_key(kimi_key)
        else:
            results['KIMI_API_KEY'] = False

        # Check Tavily key
        tavily_key = self.get_secret('TAVILY_API_KEY', required=False)
        if tavily_key:
            results['TAVILY_API_KEY'] = self.is_valid_tavily_key(tavily_key)
        else:
            results['TAVILY_API_KEY'] = False

        return results

    def get_secrets_status(self) -> Dict[str, str]:
        """
        Get status of all secrets (for display)

        Returns:
            Dictionary with status of each secret
        """
        status = {}

        # Required secrets
        for secret in self.REQUIRED_SECRETS:
            try:
                value = self.get_secret(secret, required=False)
                if value:
                    status[secret] = f"Configured ({self.mask_secret(value)})"
                else:
                    status[secret] = "Missing (Required)"
            except Exception as e:
                status[secret] = f"Error: {e}"

        # Optional secrets
        for secret in self.OPTIONAL_SECRETS:
            try:
                value = self.get_secret(secret, required=False)
                if value:
                    status[secret] = f"Configured ({self.mask_secret(value)})"
                else:
                    status[secret] = "Not configured (Optional)"
            except Exception as e:
                status[secret] = f"Error: {e}"

        return status

    def clear_cache(self):
        """
        Clear the secrets cache (useful for key rotation)
        """
        self.secrets_cache.clear()

    @staticmethod
    def log_secret_access(secret_name: str, success: bool):
        """
        Log secret access attempt (for audit trail)

        Args:
            secret_name: Name of secret accessed
            success: Whether access was successful
        """
        # This would integrate with SecurityLogger
        from datetime import datetime

        timestamp = datetime.now().isoformat()
        status = "SUCCESS" if success else "FAILED"

        # In production, this would write to secure audit log
        print(f"[{timestamp}] Secret Access: {secret_name} - {status}")


def main():
    """Test secrets manager"""
    secrets = SecretsManager()

    print("=== Secrets Manager Test ===\n")

    # Validate all secrets
    all_valid, missing = secrets.validate_all_secrets()
    print(f"All secrets valid: {all_valid}")
    if missing:
        print(f"Missing secrets: {', '.join(missing)}")

    print("\n--- Secrets Status ---")
    status = secrets.get_secrets_status()
    for key, value in status.items():
        print(f"{key}: {value}")

    print("\n--- Secret Format Validation ---")
    format_results = secrets.verify_secrets_format()
    for key, is_valid in format_results.items():
        if is_valid is None:
            print(f"{key}: Not configured (optional)")
        elif is_valid:
            print(f"{key}: Valid format")
        else:
            print(f"{key}: Invalid format")

    # Test masking
    print("\n--- Masking Test ---")
    test_secrets = [
        "sk-test1234567890abcdefghijklmnopqrstuvwxyz1234567890AB",
        "tvly-dev-test1234567890abcdefghijklmnop",
        "short",
    ]

    for secret in test_secrets:
        masked = SecretsManager.mask_secret(secret)
        print(f"Original length: {len(secret)} -> Masked: {masked}")


if __name__ == "__main__":
    main()
