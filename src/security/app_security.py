"""
Security Integration for Streamlit App

Provides easy-to-use security wrappers for the main application:
- Input validation
- Rate limiting
- Session management
- Security UI components
"""

import streamlit as st
from typing import Tuple, Optional
from pathlib import Path

from .input_validator import InputValidator, ValidationError
from .rate_limiter import RateLimiter, RateLimitExceeded
from .security_logger import get_security_logger, SecurityEventType
from config import SecurityConfig


class AppSecurity:
    """
    Centralized security management for Streamlit app
    """

    def __init__(self):
        """Initialize security components"""
        self.validator = InputValidator()
        self.rate_limiter = RateLimiter()
        self.security_logger = get_security_logger()

        # Configure rate limits from config
        self.rate_limiter.configure_limits(
            hourly=SecurityConfig.MAX_RESUMES_PER_HOUR,
            burst=SecurityConfig.MAX_RESUMES_PER_10MIN,
            daily=SecurityConfig.MAX_RESUMES_PER_DAY
        )

        # Initialize session-based user identifier
        if 'user_id' not in st.session_state:
            import uuid
            st.session_state.user_id = str(uuid.uuid4())

    def get_user_identifier(self) -> str:
        """
        Get unique identifier for current user

        Returns:
            User identifier string
        """
        return st.session_state.user_id

    def validate_resume_generation_inputs(
        self,
        job_description: str,
        company_name: str,
        job_url: Optional[str] = None,
        target_score: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate all inputs for resume generation

        Args:
            job_description: Job description text
            company_name: Company name
            job_url: Optional job URL
            target_score: Optional target ATS score

        Returns:
            Tuple of (is_valid, error_message)
        """
        user_id = self.get_user_identifier()

        # Validate all inputs
        is_valid, error_msg = self.validator.validate_all_inputs(
            job_description=job_description,
            company_name=company_name,
            job_url=job_url,
            target_score=target_score
        )

        if not is_valid:
            # Log validation failure
            self.security_logger.log_validation_failure(
                input_type="resume_generation",
                error_message=error_msg,
                user_identifier=user_id
            )

        return is_valid, error_msg

    def check_rate_limit(self) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Check if user has exceeded rate limits

        Returns:
            Tuple of (allowed, error_message, seconds_until_reset)
        """
        user_id = self.get_user_identifier()

        # Check all rate limits
        allowed, error_msg, reset_time = self.rate_limiter.check_all_limits(user_id)

        if not allowed:
            # Log rate limit exceeded
            self.security_logger.log_rate_limit_exceeded(
                user_identifier=user_id,
                limit_type="combined",
                current_count=0,  # Actual count tracked in rate_limiter
                max_allowed=SecurityConfig.MAX_RESUMES_PER_HOUR
            )

        return allowed, error_msg, reset_time

    def get_rate_limit_info(self) -> dict:
        """
        Get current rate limit status for user

        Returns:
            Dictionary with rate limit information
        """
        user_id = self.get_user_identifier()

        return {
            'hourly_remaining': self.rate_limiter.get_remaining_quota(user_id, 'hourly'),
            'burst_remaining': self.rate_limiter.get_remaining_quota(user_id, 'burst'),
            'daily_remaining': self.rate_limiter.get_remaining_quota(user_id, 'daily'),
            'hourly_max': SecurityConfig.MAX_RESUMES_PER_HOUR,
            'burst_max': SecurityConfig.MAX_RESUMES_PER_10MIN,
            'daily_max': SecurityConfig.MAX_RESUMES_PER_DAY
        }

    def validate_file_upload(self, uploaded_file) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded file

        Args:
            uploaded_file: Streamlit uploaded file object

        Returns:
            Tuple of (is_valid, error_message)
        """
        if uploaded_file is None:
            return False, "No file uploaded"

        user_id = self.get_user_identifier()

        # Save file temporarily for validation
        temp_path = Path(f"/tmp/{uploaded_file.name}")
        try:
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getvalue())

            # Validate file
            is_valid, error_msg = self.validator.validate_file_upload(
                str(temp_path),
                max_size_mb=SecurityConfig.MAX_FILE_SIZE_MB
            )

            # Log file upload attempt
            self.security_logger.log_file_upload(
                filename=uploaded_file.name,
                file_size=uploaded_file.size,
                success=is_valid,
                user_identifier=user_id,
                error=error_msg if not is_valid else None
            )

            return is_valid, error_msg

        except Exception as e:
            error_msg = f"Error validating file: {str(e)}"
            self.security_logger.log_file_upload(
                filename=uploaded_file.name,
                file_size=uploaded_file.size if hasattr(uploaded_file, 'size') else 0,
                success=False,
                user_identifier=user_id,
                error=error_msg
            )
            return False, error_msg

        finally:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()

    def sanitize_company_name_for_filename(self, company_name: str) -> str:
        """
        Sanitize company name for safe use in filenames

        Args:
            company_name: Company name to sanitize

        Returns:
            Sanitized company name
        """
        return self.validator.sanitize_company_name(company_name)

    def display_rate_limit_info(self):
        """
        Display rate limit information in Streamlit UI
        """
        info = self.get_rate_limit_info()

        st.sidebar.markdown("---")
        st.sidebar.subheader("Usage Limits")

        # Hourly quota
        hourly_pct = (info['hourly_remaining'] / info['hourly_max']) * 100 if info['hourly_max'] > 0 else 0
        st.sidebar.progress(hourly_pct / 100)
        st.sidebar.caption(
            f"Hourly: {info['hourly_remaining']}/{info['hourly_max']} resumes remaining"
        )

        # Daily quota
        daily_pct = (info['daily_remaining'] / info['daily_max']) * 100 if info['daily_max'] > 0 else 0
        st.sidebar.progress(daily_pct / 100)
        st.sidebar.caption(
            f"Daily: {info['daily_remaining']}/{info['daily_max']} resumes remaining"
        )

    def display_security_status(self):
        """
        Display security status in sidebar
        """
        st.sidebar.markdown("---")
        st.sidebar.subheader("Security Status")

        features = SecurityConfig.get_security_features()

        # Show enabled security features
        enabled_features = [k for k, v in features.items() if v]

        if enabled_features:
            st.sidebar.success(f"{len(enabled_features)} security features enabled")

            with st.sidebar.expander("Security Details"):
                for feature in enabled_features:
                    st.write(f"✓ {feature.replace('_', ' ').title()}")
        else:
            st.sidebar.warning("No security features enabled")


# Global security instance
_app_security: Optional[AppSecurity] = None


def get_app_security() -> AppSecurity:
    """
    Get global AppSecurity instance

    Returns:
        AppSecurity instance
    """
    global _app_security

    if _app_security is None:
        _app_security = AppSecurity()

    return _app_security


def validate_and_check_limits(
    job_description: str,
    company_name: str,
    job_url: Optional[str] = None,
    target_score: Optional[int] = None
) -> Tuple[bool, Optional[str]]:
    """
    Convenience function to validate inputs and check rate limits

    Returns:
        Tuple of (allowed, error_message)
    """
    security = get_app_security()

    # Validate inputs
    is_valid, error_msg = security.validate_resume_generation_inputs(
        job_description=job_description,
        company_name=company_name,
        job_url=job_url,
        target_score=target_score
    )

    if not is_valid:
        return False, error_msg

    # Check rate limits
    allowed, error_msg, reset_time = security.check_rate_limit()

    if not allowed:
        return False, error_msg

    return True, None
