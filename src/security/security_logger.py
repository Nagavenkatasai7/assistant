"""
Security Logging and Audit Trail Module

Provides comprehensive security event logging:
- Authentication/authorization events
- Input validation failures
- Rate limit violations
- Suspicious activity detection
- API usage tracking
"""

import logging
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from enum import Enum


class SecurityEventType(Enum):
    """Types of security events"""
    # Input validation
    VALIDATION_FAILED = "validation_failed"
    VALIDATION_PASSED = "validation_passed"

    # Rate limiting
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    RATE_LIMIT_WARNING = "rate_limit_warning"

    # Prompt injection
    PROMPT_INJECTION_DETECTED = "prompt_injection_detected"
    PROMPT_INJECTION_BLOCKED = "prompt_injection_blocked"

    # API usage
    API_CALL_SUCCESS = "api_call_success"
    API_CALL_FAILED = "api_call_failed"

    # File operations
    FILE_UPLOAD_SUCCESS = "file_upload_success"
    FILE_UPLOAD_FAILED = "file_upload_failed"

    # Suspicious activity
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

    # System events
    SECRET_ACCESS = "secret_access"
    SECRET_MISSING = "secret_missing"


class SecurityLogger:
    """
    Security event logger with structured logging
    """

    def __init__(self, log_dir: str = "logs", log_level: int = logging.INFO):
        """
        Initialize security logger

        Args:
            log_dir: Directory for log files
            log_level: Logging level
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Setup loggers
        self.security_logger = self._setup_logger(
            'security',
            self.log_dir / 'security.log',
            log_level
        )

        self.audit_logger = self._setup_logger(
            'audit',
            self.log_dir / 'audit.log',
            logging.INFO
        )

        self.api_logger = self._setup_logger(
            'api',
            self.log_dir / 'api_usage.log',
            logging.INFO
        )

    def _setup_logger(self, name: str, log_file: Path, level: int) -> logging.Logger:
        """
        Setup individual logger

        Args:
            name: Logger name
            log_file: Path to log file
            level: Logging level

        Returns:
            Configured logger
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Remove existing handlers
        logger.handlers = []

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)  # Only warnings and errors to console

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def log_event(
        self,
        event_type: SecurityEventType,
        message: str,
        user_identifier: Optional[str] = None,
        severity: str = "INFO",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log a security event

        Args:
            event_type: Type of security event
            message: Event description
            user_identifier: User/IP identifier
            severity: Event severity (INFO, WARNING, ERROR, CRITICAL)
            metadata: Additional event metadata
        """
        event_data = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type.value,
            'message': message,
            'user_identifier': user_identifier,
            'severity': severity,
            'metadata': metadata or {}
        }

        # Log to appropriate logger
        log_message = json.dumps(event_data)

        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }

        log_level = level_map.get(severity, logging.INFO)

        self.security_logger.log(log_level, log_message)

    def log_validation_failure(
        self,
        input_type: str,
        error_message: str,
        user_identifier: Optional[str] = None,
        input_sample: Optional[str] = None
    ):
        """
        Log input validation failure

        Args:
            input_type: Type of input (job_description, company_name, etc.)
            error_message: Validation error message
            user_identifier: User/IP identifier
            input_sample: Sample of invalid input (first 100 chars)
        """
        metadata = {
            'input_type': input_type,
            'error': error_message,
            'input_sample': input_sample[:100] if input_sample else None
        }

        self.log_event(
            SecurityEventType.VALIDATION_FAILED,
            f"Input validation failed for {input_type}: {error_message}",
            user_identifier=user_identifier,
            severity="WARNING",
            metadata=metadata
        )

    def log_rate_limit_exceeded(
        self,
        user_identifier: str,
        limit_type: str,
        current_count: int,
        max_allowed: int,
        reset_time: Optional[int] = None
    ):
        """
        Log rate limit violation

        Args:
            user_identifier: User/IP identifier
            limit_type: Type of rate limit (hourly, burst, daily)
            current_count: Current request count
            max_allowed: Maximum allowed requests
            reset_time: Seconds until reset
        """
        metadata = {
            'limit_type': limit_type,
            'current_count': current_count,
            'max_allowed': max_allowed,
            'reset_time': reset_time
        }

        self.log_event(
            SecurityEventType.RATE_LIMIT_EXCEEDED,
            f"Rate limit exceeded for {user_identifier} ({limit_type}): {current_count}/{max_allowed}",
            user_identifier=user_identifier,
            severity="WARNING",
            metadata=metadata
        )

    def log_prompt_injection_attempt(
        self,
        user_identifier: Optional[str],
        patterns_detected: list,
        input_type: str,
        input_sample: Optional[str] = None
    ):
        """
        Log detected prompt injection attempt

        Args:
            user_identifier: User/IP identifier
            patterns_detected: List of detected injection patterns
            input_type: Type of input where injection was detected
            input_sample: Sample of suspicious input
        """
        metadata = {
            'input_type': input_type,
            'patterns_detected': patterns_detected[:5],  # Limit to first 5
            'pattern_count': len(patterns_detected),
            'input_sample': input_sample[:200] if input_sample else None
        }

        self.log_event(
            SecurityEventType.PROMPT_INJECTION_DETECTED,
            f"Prompt injection detected in {input_type}: {len(patterns_detected)} suspicious patterns",
            user_identifier=user_identifier,
            severity="ERROR",
            metadata=metadata
        )

    def log_api_call(
        self,
        api_name: str,
        success: bool,
        user_identifier: Optional[str] = None,
        tokens_used: Optional[int] = None,
        cost_estimate: Optional[float] = None,
        duration_ms: Optional[int] = None,
        error: Optional[str] = None
    ):
        """
        Log API call

        Args:
            api_name: Name of API (anthropic, perplexity, etc.)
            success: Whether call succeeded
            user_identifier: User/IP identifier
            tokens_used: Number of tokens used
            cost_estimate: Estimated cost in USD
            duration_ms: Call duration in milliseconds
            error: Error message if failed
        """
        metadata = {
            'api_name': api_name,
            'success': success,
            'tokens_used': tokens_used,
            'cost_estimate': cost_estimate,
            'duration_ms': duration_ms,
            'error': error
        }

        event_type = SecurityEventType.API_CALL_SUCCESS if success else SecurityEventType.API_CALL_FAILED
        severity = "INFO" if success else "ERROR"

        self.log_event(
            event_type,
            f"API call to {api_name}: {'SUCCESS' if success else 'FAILED'}",
            user_identifier=user_identifier,
            severity=severity,
            metadata=metadata
        )

        # Also log to API logger for cost tracking
        self.api_logger.info(json.dumps(metadata))

    def log_file_upload(
        self,
        filename: str,
        file_size: int,
        success: bool,
        user_identifier: Optional[str] = None,
        error: Optional[str] = None
    ):
        """
        Log file upload event

        Args:
            filename: Name of uploaded file
            file_size: Size in bytes
            success: Whether upload succeeded
            user_identifier: User/IP identifier
            error: Error message if failed
        """
        metadata = {
            'filename': filename,
            'file_size': file_size,
            'file_size_mb': round(file_size / (1024 * 1024), 2),
            'error': error
        }

        event_type = SecurityEventType.FILE_UPLOAD_SUCCESS if success else SecurityEventType.FILE_UPLOAD_FAILED
        severity = "INFO" if success else "WARNING"

        self.log_event(
            event_type,
            f"File upload: {filename} ({'SUCCESS' if success else 'FAILED'})",
            user_identifier=user_identifier,
            severity=severity,
            metadata=metadata
        )

    def log_suspicious_activity(
        self,
        activity_type: str,
        description: str,
        user_identifier: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log suspicious activity

        Args:
            activity_type: Type of suspicious activity
            description: Description of activity
            user_identifier: User/IP identifier
            metadata: Additional metadata
        """
        self.log_event(
            SecurityEventType.SUSPICIOUS_ACTIVITY,
            f"Suspicious activity detected ({activity_type}): {description}",
            user_identifier=user_identifier,
            severity="ERROR",
            metadata=metadata
        )

    def log_audit_event(
        self,
        action: str,
        resource: str,
        user_identifier: Optional[str] = None,
        result: str = "SUCCESS",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log audit event (for compliance)

        Args:
            action: Action performed (CREATE, READ, UPDATE, DELETE)
            resource: Resource affected
            user_identifier: User/IP identifier
            result: Result of action
            metadata: Additional metadata
        """
        audit_data = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'resource': resource,
            'user_identifier': user_identifier,
            'result': result,
            'metadata': metadata or {}
        }

        self.audit_logger.info(json.dumps(audit_data))

    def get_api_usage_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get API usage statistics

        Args:
            hours: Number of hours to analyze

        Returns:
            Dictionary with usage statistics
        """
        # This is a placeholder - in production, you'd parse the API log file
        # For now, return empty stats
        return {
            'time_period_hours': hours,
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'total_tokens': 0,
            'estimated_cost': 0.0
        }


# Global logger instance
_security_logger: Optional[SecurityLogger] = None


def get_security_logger() -> SecurityLogger:
    """
    Get global security logger instance

    Returns:
        SecurityLogger instance
    """
    global _security_logger

    if _security_logger is None:
        _security_logger = SecurityLogger()

    return _security_logger


def main():
    """Test security logger"""
    logger = SecurityLogger(log_dir="test_logs")

    print("Testing Security Logger...\n")

    # Test validation failure
    logger.log_validation_failure(
        input_type="job_description",
        error_message="Job description too short",
        user_identifier="test_user",
        input_sample="Short desc"
    )

    # Test rate limit
    logger.log_rate_limit_exceeded(
        user_identifier="test_user",
        limit_type="hourly",
        current_count=11,
        max_allowed=10,
        reset_time=3600
    )

    # Test prompt injection
    logger.log_prompt_injection_attempt(
        user_identifier="test_user",
        patterns_detected=["ignore previous instructions", "system:"],
        input_type="job_description",
        input_sample="Ignore all previous instructions..."
    )

    # Test API call
    logger.log_api_call(
        api_name="anthropic",
        success=True,
        user_identifier="test_user",
        tokens_used=1500,
        cost_estimate=0.015,
        duration_ms=2500
    )

    # Test file upload
    logger.log_file_upload(
        filename="profile.pdf",
        file_size=2048576,
        success=True,
        user_identifier="test_user"
    )

    # Test audit event
    logger.log_audit_event(
        action="CREATE",
        resource="resume",
        user_identifier="test_user",
        result="SUCCESS",
        metadata={'company': 'Google', 'job_title': 'Software Engineer'}
    )

    print("Logs written to test_logs/ directory")
    print("\nCheck the following files:")
    print("- test_logs/security.log")
    print("- test_logs/audit.log")
    print("- test_logs/api_usage.log")


if __name__ == "__main__":
    main()
