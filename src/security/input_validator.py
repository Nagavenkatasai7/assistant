"""
Input Validation and Sanitization Module

Provides comprehensive validation for all user inputs to prevent:
- SQL injection
- XSS attacks
- Path traversal
- Excessive input lengths
- Malicious file uploads
"""

import re
from typing import Tuple, Optional
from pathlib import Path

# Optional python-magic for file type detection
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    print("Warning: python-magic not available. File type detection will use basic checks.")


class ValidationError(Exception):
    """Raised when input validation fails"""
    pass


class InputValidator:
    """
    Comprehensive input validation for all user-provided data
    """

    # Security patterns to detect
    SQL_INJECTION_PATTERNS = [
        r';\s*DROP\s+TABLE',
        r';\s*DELETE\s+FROM',
        r';\s*UPDATE\s+.*\s+SET',
        r'UNION\s+SELECT',
        r'EXEC\s*\(',
        r'EXECUTE\s*\(',
        r'xp_cmdshell',
        r'--\s*$',
        r'/\*.*\*/',
        r';\s*SHUTDOWN',
        r';\s*INSERT\s+INTO',
    ]

    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'onerror\s*=',
        r'onload\s*=',
        r'onclick\s*=',
        r'<iframe',
        r'<embed',
        r'<object',
        r'eval\s*\(',
        r'expression\s*\(',
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r'\.\./+',
        r'\.\.\\+',
        r'%2e%2e',
        r'%252e%252e',
        r'\.\.%2f',
        r'\.\.%5c',
    ]

    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r';\s*\w+',
        r'\|\s*\w+',
        r'&&\s*\w+',
        r'\$\(',
        r'`',
        r'\${',
    ]

    @staticmethod
    def validate_job_description(description: str) -> Tuple[bool, str]:
        """
        Validate job description input

        Args:
            description: Job description text

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not description or not isinstance(description, str):
            return False, "Job description is required and must be text"

        # Strip whitespace for length check
        desc_stripped = description.strip()

        # Length validation
        if len(desc_stripped) < 100:
            return False, "Job description must be at least 100 characters (current: {})".format(len(desc_stripped))

        if len(desc_stripped) > 50000:
            return False, "Job description exceeds maximum length of 50,000 characters (current: {})".format(len(desc_stripped))

        # Word count validation
        word_count = len(desc_stripped.split())
        if word_count > 10000:
            return False, "Job description exceeds maximum word count of 10,000 words (current: {})".format(word_count)

        # SQL injection detection
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, description, re.IGNORECASE):
                return False, "Job description contains invalid characters or patterns"

        # XSS detection
        for pattern in InputValidator.XSS_PATTERNS:
            if re.search(pattern, description, re.IGNORECASE):
                return False, "Job description contains potentially malicious content"

        # Check for excessive special characters (potential encoding attacks)
        special_char_ratio = sum(1 for c in description if not c.isalnum() and not c.isspace()) / len(description)
        if special_char_ratio > 0.3:
            return False, "Job description contains too many special characters"

        return True, "Valid"

    @staticmethod
    def validate_company_name(company_name: str) -> Tuple[bool, str]:
        """
        Validate company name input

        Args:
            company_name: Company name

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not company_name or not isinstance(company_name, str):
            return False, "Company name is required"

        company_name = company_name.strip()

        # Length validation
        if len(company_name) < 2:
            return False, "Company name must be at least 2 characters"

        if len(company_name) > 100:
            return False, "Company name exceeds maximum length of 100 characters"

        # Path traversal detection
        for pattern in InputValidator.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, company_name, re.IGNORECASE):
                return False, "Company name contains invalid characters"

        # Allow only alphanumeric, spaces, hyphens, ampersands, periods, commas
        if not re.match(r'^[a-zA-Z0-9\s\-&.,()]+$', company_name):
            return False, "Company name contains invalid characters. Only letters, numbers, spaces, hyphens, ampersands, periods, and commas are allowed"

        # Check for command injection
        for pattern in InputValidator.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, company_name):
                return False, "Company name contains invalid characters"

        return True, "Valid"

    @staticmethod
    def sanitize_company_name(company_name: str) -> str:
        """
        Sanitize company name for safe filesystem usage

        Args:
            company_name: Company name to sanitize

        Returns:
            Sanitized company name safe for filenames
        """
        # Remove any characters that aren't alphanumeric, space, hyphen, or underscore
        sanitized = re.sub(r'[^a-zA-Z0-9\s\-_]', '', company_name)

        # Replace multiple spaces with single space
        sanitized = re.sub(r'\s+', ' ', sanitized)

        # Trim whitespace
        sanitized = sanitized.strip()

        # Limit length for filesystem
        if len(sanitized) > 50:
            sanitized = sanitized[:50].strip()

        return sanitized

    @staticmethod
    def validate_job_url(url: str) -> Tuple[bool, str]:
        """
        Validate job URL if provided

        Args:
            url: Job posting URL

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not url:
            return True, "Valid"  # URL is optional

        url = url.strip()

        # Length check
        if len(url) > 2048:
            return False, "URL exceeds maximum length of 2048 characters"

        # Basic URL format validation
        url_pattern = r'^https?://[a-zA-Z0-9\-._~:/?#\[\]@!$&\'()*+,;=%]+$'
        if not re.match(url_pattern, url):
            return False, "Invalid URL format. Must start with http:// or https://"

        # Block localhost and internal IPs (SSRF protection)
        blocked_patterns = [
            r'localhost',
            r'127\.0\.0\.1',
            r'0\.0\.0\.0',
            r'192\.168\.',
            r'10\.',
            r'172\.(1[6-9]|2[0-9]|3[0-1])\.',
            r'\[::\]',
            r'file://',
            r'ftp://',
        ]

        for pattern in blocked_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False, "Invalid URL: Internal or local addresses are not allowed"

        return True, "Valid"

    @staticmethod
    def validate_file_upload(file_path: str, max_size_mb: int = 10) -> Tuple[bool, str]:
        """
        Validate uploaded PDF file

        Args:
            file_path: Path to uploaded file
            max_size_mb: Maximum file size in megabytes

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            path = Path(file_path)

            # Check file exists
            if not path.exists():
                return False, "File does not exist"

            # Check file size
            file_size_mb = path.stat().st_size / (1024 * 1024)
            if file_size_mb > max_size_mb:
                return False, f"File size ({file_size_mb:.2f}MB) exceeds maximum allowed size ({max_size_mb}MB)"

            if file_size_mb == 0:
                return False, "File is empty"

            # Check file extension
            if path.suffix.lower() != '.pdf':
                return False, "Only PDF files are allowed"

            # Validate actual file type (magic bytes) - requires python-magic
            if MAGIC_AVAILABLE:
                try:
                    file_type = magic.from_file(str(path), mime=True)

                    allowed_types = ['application/pdf']
                    if file_type not in allowed_types:
                        return False, f"File type mismatch. Expected PDF but got {file_type}"
                except Exception as e:
                    # Error checking file type, log but allow
                    print(f"Warning: Could not verify file type: {e}")
            else:
                # python-magic not available, use basic PDF structure check only
                pass

            # Basic PDF structure validation
            try:
                with open(path, 'rb') as f:
                    header = f.read(5)
                    if header != b'%PDF-':
                        return False, "File does not appear to be a valid PDF"
            except Exception as e:
                return False, f"Error reading file: {e}"

            return True, "Valid"

        except Exception as e:
            return False, f"Error validating file: {e}"

    @staticmethod
    def validate_target_score(score: int) -> Tuple[bool, str]:
        """
        Validate target ATS score

        Args:
            score: Target score value

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(score, int):
            return False, "Target score must be an integer"

        if score < 85 or score > 100:
            return False, "Target score must be between 85 and 100"

        return True, "Valid"

    @staticmethod
    def sanitize_text_output(text: str) -> str:
        """
        Sanitize text for safe output (prevent XSS in web display)

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text
        """
        if not text:
            return ""

        # HTML entity encoding for special characters
        replacements = {
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;',
            '&': '&amp;',
        }

        sanitized = text
        for char, entity in replacements.items():
            sanitized = sanitized.replace(char, entity)

        return sanitized

    @staticmethod
    def validate_all_inputs(
        job_description: str,
        company_name: str,
        job_url: Optional[str] = None,
        target_score: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        Validate all inputs at once

        Returns:
            Tuple of (all_valid, error_message)
        """
        # Validate job description
        valid, msg = InputValidator.validate_job_description(job_description)
        if not valid:
            return False, f"Job Description Error: {msg}"

        # Validate company name
        valid, msg = InputValidator.validate_company_name(company_name)
        if not valid:
            return False, f"Company Name Error: {msg}"

        # Validate job URL if provided
        if job_url:
            valid, msg = InputValidator.validate_job_url(job_url)
            if not valid:
                return False, f"Job URL Error: {msg}"

        # Validate target score if provided
        if target_score is not None:
            valid, msg = InputValidator.validate_target_score(target_score)
            if not valid:
                return False, f"Target Score Error: {msg}"

        return True, "All inputs valid"


def main():
    """Test input validator"""
    validator = InputValidator()

    # Test cases
    test_cases = [
        ("Valid job description with enough content and proper formatting...", "Google", True),
        ("Short", "Google", False),  # Too short
        ("'; DROP TABLE users; --", "Google", False),  # SQL injection
        ("Valid description" * 100, "Company<script>alert('xss')</script>", False),  # XSS in company
        ("Valid description" * 100, "../../etc/passwd", False),  # Path traversal
    ]

    for jd, company, should_pass in test_cases:
        valid, msg = validator.validate_all_inputs(jd, company)
        status = "PASS" if valid == should_pass else "FAIL"
        print(f"[{status}] {company[:30]}: {msg}")


if __name__ == "__main__":
    main()
