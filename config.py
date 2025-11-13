"""
Security Configuration for Ultra ATS Resume Generator

Centralized configuration for all security settings including:
- Rate limiting parameters
- Input validation constraints
- API settings
- File upload limits
- Security features flags
"""

from typing import Dict, Any


class SecurityConfig:
    """
    Security configuration constants
    """

    # ==========================================
    # RATE LIMITING CONFIGURATION
    # ==========================================

    # Maximum resumes that can be generated
    MAX_RESUMES_PER_HOUR = 10
    MAX_RESUMES_PER_10MIN = 3
    MAX_RESUMES_PER_DAY = 50

    # Rate limit for other operations
    MAX_API_CALLS_PER_MINUTE = 20

    # Admin bypass (set user IDs that bypass rate limits)
    RATE_LIMIT_BYPASS_USERS = []

    # ==========================================
    # INPUT VALIDATION CONFIGURATION
    # ==========================================

    # Job Description limits
    MIN_JOB_DESC_LENGTH = 100
    MAX_JOB_DESC_LENGTH = 50000
    MAX_JOB_DESC_WORDS = 10000

    # Company Name limits
    MIN_COMPANY_NAME_LENGTH = 2
    MAX_COMPANY_NAME_LENGTH = 100

    # URL limits
    MAX_URL_LENGTH = 2048

    # Target ATS Score limits
    MIN_ATS_SCORE = 85
    MAX_ATS_SCORE = 100

    # ==========================================
    # FILE UPLOAD CONFIGURATION
    # ==========================================

    # File size limits
    MAX_FILE_SIZE_MB = 10
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

    # Allowed file types
    ALLOWED_FILE_TYPES = ['application/pdf']
    ALLOWED_FILE_EXTENSIONS = ['.pdf']

    # ==========================================
    # API CONFIGURATION
    # ==========================================

    # API timeout settings (increased for Kimi K2 Thinking model)
    API_TIMEOUT_SECONDS = 180  # 3 minutes for deep reasoning tasks
    MAX_API_RETRIES = 3
    RETRY_DELAY_SECONDS = 2

    # Token limits
    MAX_TOKENS_PER_REQUEST = 16000

    # Cost limits (USD)
    MAX_COST_PER_REQUEST = 1.0
    DAILY_COST_LIMIT = 50.0

    # ==========================================
    # PROMPT INJECTION PROTECTION
    # ==========================================

    # Enable/disable prompt sanitization
    ENABLE_PROMPT_SANITIZATION = True

    # Enable/disable injection detection logging
    LOG_INJECTION_ATTEMPTS = True

    # Block requests with detected injections
    BLOCK_SUSPICIOUS_REQUESTS = True

    # ==========================================
    # SECRETS MANAGEMENT
    # ==========================================

    # Required API keys
    REQUIRED_API_KEYS = [
        'KIMI_API_KEY',
        'TAVILY_API_KEY'
    ]

    # Optional API keys
    OPTIONAL_API_KEYS = []

    # Enable API key validation on startup
    VALIDATE_KEYS_ON_STARTUP = True

    # ==========================================
    # LOGGING CONFIGURATION
    # ==========================================

    # Enable security logging
    ENABLE_SECURITY_LOGGING = True

    # Log directory
    LOG_DIRECTORY = "logs"

    # Log retention (days)
    LOG_RETENTION_DAYS = 90

    # Log sensitive data (WARNING: Disable in production)
    LOG_SENSITIVE_DATA = False

    # ==========================================
    # DATABASE SECURITY
    # ==========================================

    # Use parameterized queries only
    USE_PARAMETERIZED_QUERIES = True

    # Enable query logging
    LOG_DATABASE_QUERIES = False

    # ==========================================
    # SESSION SECURITY
    # ==========================================

    # Session timeout (minutes)
    SESSION_TIMEOUT_MINUTES = 60

    # Enable session validation
    ENABLE_SESSION_VALIDATION = True

    # ==========================================
    # CONTENT SECURITY
    # ==========================================

    # Enable XSS protection
    ENABLE_XSS_PROTECTION = True

    # Sanitize all outputs
    SANITIZE_OUTPUTS = True

    # ==========================================
    # FEATURE FLAGS
    # ==========================================

    # Enable/disable features
    ENABLE_COMPANY_RESEARCH = True
    ENABLE_COVER_LETTER = True
    ENABLE_PDF_GENERATION = True

    # ==========================================
    # ENVIRONMENT SETTINGS
    # ==========================================

    # Production mode (stricter security)
    PRODUCTION_MODE = False

    # Debug mode (less strict, more logging)
    DEBUG_MODE = True

    @classmethod
    def get_rate_limits(cls) -> Dict[str, Dict[str, int]]:
        """
        Get rate limit configuration

        Returns:
            Dictionary of rate limit settings
        """
        return {
            'hourly': {
                'max_requests': cls.MAX_RESUMES_PER_HOUR,
                'window_minutes': 60
            },
            'burst': {
                'max_requests': cls.MAX_RESUMES_PER_10MIN,
                'window_minutes': 10
            },
            'daily': {
                'max_requests': cls.MAX_RESUMES_PER_DAY,
                'window_minutes': 1440
            }
        }

    @classmethod
    def get_validation_limits(cls) -> Dict[str, Any]:
        """
        Get validation limit configuration

        Returns:
            Dictionary of validation settings
        """
        return {
            'job_description': {
                'min_length': cls.MIN_JOB_DESC_LENGTH,
                'max_length': cls.MAX_JOB_DESC_LENGTH,
                'max_words': cls.MAX_JOB_DESC_WORDS
            },
            'company_name': {
                'min_length': cls.MIN_COMPANY_NAME_LENGTH,
                'max_length': cls.MAX_COMPANY_NAME_LENGTH
            },
            'file_upload': {
                'max_size_mb': cls.MAX_FILE_SIZE_MB,
                'allowed_types': cls.ALLOWED_FILE_TYPES,
                'allowed_extensions': cls.ALLOWED_FILE_EXTENSIONS
            },
            'ats_score': {
                'min_value': cls.MIN_ATS_SCORE,
                'max_value': cls.MAX_ATS_SCORE
            }
        }

    @classmethod
    def is_production(cls) -> bool:
        """
        Check if running in production mode

        Returns:
            True if production mode enabled
        """
        return cls.PRODUCTION_MODE

    @classmethod
    def get_security_features(cls) -> Dict[str, bool]:
        """
        Get enabled security features

        Returns:
            Dictionary of security feature flags
        """
        return {
            'prompt_sanitization': cls.ENABLE_PROMPT_SANITIZATION,
            'injection_detection': cls.LOG_INJECTION_ATTEMPTS,
            'block_suspicious': cls.BLOCK_SUSPICIOUS_REQUESTS,
            'security_logging': cls.ENABLE_SECURITY_LOGGING,
            'xss_protection': cls.ENABLE_XSS_PROTECTION,
            'output_sanitization': cls.SANITIZE_OUTPUTS,
            'session_validation': cls.ENABLE_SESSION_VALIDATION,
            'key_validation': cls.VALIDATE_KEYS_ON_STARTUP
        }

    @classmethod
    def apply_production_settings(cls):
        """
        Apply production-grade security settings
        """
        cls.PRODUCTION_MODE = True
        cls.DEBUG_MODE = False

        # Stricter rate limits in production
        cls.MAX_RESUMES_PER_HOUR = 5
        cls.MAX_RESUMES_PER_10MIN = 2
        cls.MAX_RESUMES_PER_DAY = 20

        # Enable all security features
        cls.ENABLE_PROMPT_SANITIZATION = True
        cls.LOG_INJECTION_ATTEMPTS = True
        cls.BLOCK_SUSPICIOUS_REQUESTS = True
        cls.ENABLE_SECURITY_LOGGING = True
        cls.ENABLE_XSS_PROTECTION = True
        cls.SANITIZE_OUTPUTS = True
        cls.VALIDATE_KEYS_ON_STARTUP = True

        # Disable sensitive logging
        cls.LOG_SENSITIVE_DATA = False
        cls.LOG_DATABASE_QUERIES = False

    @classmethod
    def apply_development_settings(cls):
        """
        Apply development settings (less strict)
        """
        cls.PRODUCTION_MODE = False
        cls.DEBUG_MODE = True

        # More lenient rate limits in development
        cls.MAX_RESUMES_PER_HOUR = 20
        cls.MAX_RESUMES_PER_10MIN = 5
        cls.MAX_RESUMES_PER_DAY = 100

        # Enable logging for debugging
        cls.LOG_INJECTION_ATTEMPTS = True
        cls.LOG_DATABASE_QUERIES = True


class APIConfig:
    """
    API-specific configuration
    """

    # Kimi K2 API (Moonshot AI)
    KIMI_MODEL = "kimi-k2-thinking"  # Full thinking model with deep reasoning
    KIMI_MAX_TOKENS = 4096
    KIMI_TEMPERATURE = 0.6  # Optimized for reasoning tasks
    KIMI_BASE_URL = "https://api.moonshot.ai/v1"  # Use .ai domain

    # Claude Opus 4.1 API (Anthropic)
    CLAUDE_MODEL = "claude-opus-4-20250514"  # Claude Opus 4.1 model
    CLAUDE_MAX_TOKENS = 8192
    CLAUDE_TEMPERATURE = 0.7  # Good balance for resume generation

    # Tavily AI Search API
    TAVILY_SEARCH_DEPTH = "advanced"  # "basic" or "advanced"
    TAVILY_MAX_RESULTS = 10
    TAVILY_INCLUDE_ANSWER = True
    TAVILY_INCLUDE_RAW_CONTENT = False

    @classmethod
    def get_kimi_config(cls) -> Dict[str, Any]:
        """
        Get Kimi K2 API configuration

        Returns:
            Configuration dictionary
        """
        return {
            'model': cls.KIMI_MODEL,
            'max_tokens': cls.KIMI_MAX_TOKENS,
            'temperature': cls.KIMI_TEMPERATURE,
            'base_url': cls.KIMI_BASE_URL,
            'timeout': SecurityConfig.API_TIMEOUT_SECONDS
        }

    @classmethod
    def get_claude_config(cls) -> Dict[str, Any]:
        """
        Get Claude Opus 4.1 API configuration

        Returns:
            Configuration dictionary
        """
        return {
            'model': cls.CLAUDE_MODEL,
            'max_tokens': cls.CLAUDE_MAX_TOKENS,
            'temperature': cls.CLAUDE_TEMPERATURE,
            'timeout': SecurityConfig.API_TIMEOUT_SECONDS
        }

    @classmethod
    def get_tavily_config(cls) -> Dict[str, Any]:
        """
        Get Tavily API configuration

        Returns:
            Configuration dictionary
        """
        return {
            'search_depth': cls.TAVILY_SEARCH_DEPTH,
            'max_results': cls.TAVILY_MAX_RESULTS,
            'include_answer': cls.TAVILY_INCLUDE_ANSWER,
            'include_raw_content': cls.TAVILY_INCLUDE_RAW_CONTENT,
            'timeout': SecurityConfig.API_TIMEOUT_SECONDS
        }


def main():
    """Display current configuration"""
    print("=== Security Configuration ===\n")

    print("--- Rate Limits ---")
    rate_limits = SecurityConfig.get_rate_limits()
    for limit_type, config in rate_limits.items():
        print(f"{limit_type}: {config['max_requests']} requests per {config['window_minutes']} minutes")

    print("\n--- Validation Limits ---")
    validation = SecurityConfig.get_validation_limits()
    for input_type, limits in validation.items():
        print(f"{input_type}: {limits}")

    print("\n--- Security Features ---")
    features = SecurityConfig.get_security_features()
    for feature, enabled in features.items():
        status = "ENABLED" if enabled else "DISABLED"
        print(f"{feature}: {status}")

    print("\n--- API Configuration ---")
    print(f"Kimi K2 Model: {APIConfig.KIMI_MODEL}")
    print(f"Tavily Search Depth: {APIConfig.TAVILY_SEARCH_DEPTH}")
    print(f"Timeout: {SecurityConfig.API_TIMEOUT_SECONDS}s")
    print(f"Max Retries: {SecurityConfig.MAX_API_RETRIES}")

    print("\n--- Environment ---")
    print(f"Production Mode: {SecurityConfig.PRODUCTION_MODE}")
    print(f"Debug Mode: {SecurityConfig.DEBUG_MODE}")


if __name__ == "__main__":
    main()
