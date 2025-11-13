"""
Disk Space Validation Utility

Checks available disk space before file operations to prevent storage issues.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Tuple


class DiskSpaceError(Exception):
    """Raised when insufficient disk space is available"""
    pass


class DiskSpaceValidator:
    """
    Validates available disk space before file operations

    Features:
    - Check available space on filesystem
    - Configurable minimum space requirements
    - Safety margins for file operations
    - Human-readable space formatting
    """

    def __init__(self, min_free_space_mb: int = 100):
        """
        Initialize disk space validator

        Args:
            min_free_space_mb: Minimum free space required in MB (default: 100MB)
        """
        self.min_free_space_mb = min_free_space_mb
        self.min_free_space_bytes = min_free_space_mb * 1024 * 1024

    def get_disk_usage(self, path: str = ".") -> Dict[str, int]:
        """
        Get disk usage statistics for a path

        Args:
            path: Path to check (default: current directory)

        Returns:
            Dictionary with total, used, and free space in bytes
        """
        try:
            usage = shutil.disk_usage(path)
            return {
                'total_bytes': usage.total,
                'used_bytes': usage.used,
                'free_bytes': usage.free,
                'total_mb': round(usage.total / (1024 * 1024), 2),
                'used_mb': round(usage.used / (1024 * 1024), 2),
                'free_mb': round(usage.free / (1024 * 1024), 2),
                'total_gb': round(usage.total / (1024 * 1024 * 1024), 2),
                'used_gb': round(usage.used / (1024 * 1024 * 1024), 2),
                'free_gb': round(usage.free / (1024 * 1024 * 1024), 2),
                'percent_used': round((usage.used / usage.total) * 100, 1)
            }
        except Exception as e:
            print(f"Error getting disk usage: {e}")
            return {
                'total_bytes': 0,
                'used_bytes': 0,
                'free_bytes': 0,
                'total_mb': 0,
                'used_mb': 0,
                'free_mb': 0,
                'total_gb': 0,
                'used_gb': 0,
                'free_gb': 0,
                'percent_used': 0
            }

    def has_sufficient_space(
        self,
        required_bytes: int = 0,
        path: str = ".",
        safety_margin_mb: int = 50
    ) -> Tuple[bool, str]:
        """
        Check if sufficient disk space is available

        Args:
            required_bytes: Bytes needed for operation (0 = just check minimum)
            path: Path to check
            safety_margin_mb: Additional safety margin in MB

        Returns:
            Tuple of (has_space: bool, message: str)
        """
        usage = self.get_disk_usage(path)
        free_bytes = usage['free_bytes']

        # Calculate total required space
        safety_margin_bytes = safety_margin_mb * 1024 * 1024
        total_required = self.min_free_space_bytes + required_bytes + safety_margin_bytes

        if free_bytes < total_required:
            free_mb = usage['free_mb']
            required_mb = round(total_required / (1024 * 1024), 2)
            return (
                False,
                f"Insufficient disk space. Available: {free_mb} MB, "
                f"Required: {required_mb} MB (including {safety_margin_mb} MB safety margin)"
            )

        return True, f"Sufficient space available: {usage['free_mb']} MB free"

    def validate_before_write(
        self,
        estimated_file_size_bytes: int,
        path: str = "."
    ) -> None:
        """
        Validate disk space before writing a file (raises exception if insufficient)

        Args:
            estimated_file_size_bytes: Estimated size of file to write
            path: Path where file will be written

        Raises:
            DiskSpaceError: If insufficient space available
        """
        has_space, message = self.has_sufficient_space(
            required_bytes=estimated_file_size_bytes,
            path=path
        )

        if not has_space:
            raise DiskSpaceError(message)

    def validate_upload(
        self,
        file_size_bytes: int,
        max_file_size_mb: int = 10,
        path: str = "."
    ) -> Tuple[bool, str]:
        """
        Validate file upload

        Args:
            file_size_bytes: Size of uploaded file
            max_file_size_mb: Maximum allowed file size
            path: Upload destination path

        Returns:
            Tuple of (is_valid: bool, message: str)
        """
        # Check file size limit
        max_size_bytes = max_file_size_mb * 1024 * 1024
        if file_size_bytes > max_size_bytes:
            return (
                False,
                f"File too large. Maximum size: {max_file_size_mb} MB, "
                f"Uploaded: {round(file_size_bytes / (1024 * 1024), 2)} MB"
            )

        # Check disk space
        has_space, space_message = self.has_sufficient_space(
            required_bytes=file_size_bytes,
            path=path
        )

        if not has_space:
            return False, space_message

        return True, "File size and disk space validated successfully"

    def estimate_pdf_size(self, content_length: int) -> int:
        """
        Estimate PDF file size based on content length

        Args:
            content_length: Length of content in characters

        Returns:
            Estimated file size in bytes
        """
        # Rough estimate: 1 page ~ 50KB, 1 page ~ 500 characters
        # Add 20% overhead for formatting
        estimated_pages = max(1, content_length / 500)
        estimated_bytes = int(estimated_pages * 50 * 1024 * 1.2)
        return estimated_bytes

    def estimate_docx_size(self, content_length: int) -> int:
        """
        Estimate DOCX file size based on content length

        Args:
            content_length: Length of content in characters

        Returns:
            Estimated file size in bytes
        """
        # DOCX files are typically larger than plain text
        # Rough estimate: 1KB per 100 characters + 30KB overhead
        estimated_bytes = int((content_length / 100) * 1024) + (30 * 1024)
        return estimated_bytes

    def get_low_space_warning(self, path: str = ".") -> str:
        """
        Get warning message if disk space is low

        Args:
            path: Path to check

        Returns:
            Warning message or empty string if space is adequate
        """
        usage = self.get_disk_usage(path)
        free_mb = usage['free_mb']
        percent_used = usage['percent_used']

        # Warning thresholds
        if percent_used >= 95 or free_mb < 500:
            return (
                f"⚠️ CRITICAL: Very low disk space! "
                f"{free_mb} MB free ({100 - percent_used:.1f}% available). "
                f"Please free up space immediately."
            )
        elif percent_used >= 90 or free_mb < 1000:
            return (
                f"⚠️ WARNING: Low disk space! "
                f"{free_mb} MB free ({100 - percent_used:.1f}% available). "
                f"Consider freeing up space soon."
            )
        elif percent_used >= 80 or free_mb < 2000:
            return (
                f"ℹ️ Notice: Disk space getting low. "
                f"{free_mb} MB free ({100 - percent_used:.1f}% available)."
            )

        return ""

    def format_bytes(self, bytes_value: int) -> str:
        """
        Format bytes into human-readable string

        Args:
            bytes_value: Number of bytes

        Returns:
            Formatted string (e.g., "1.5 GB", "250 MB")
        """
        if bytes_value < 1024:
            return f"{bytes_value} B"
        elif bytes_value < 1024 * 1024:
            return f"{bytes_value / 1024:.1f} KB"
        elif bytes_value < 1024 * 1024 * 1024:
            return f"{bytes_value / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_value / (1024 * 1024 * 1024):.2f} GB"

    def print_disk_usage(self, path: str = ".") -> None:
        """Print formatted disk usage information"""
        usage = self.get_disk_usage(path)

        print("\n" + "=" * 60)
        print("DISK SPACE USAGE")
        print("=" * 60)
        print(f"Path: {os.path.abspath(path)}")
        print(f"Total:     {usage['total_gb']:.2f} GB")
        print(f"Used:      {usage['used_gb']:.2f} GB ({usage['percent_used']:.1f}%)")
        print(f"Free:      {usage['free_gb']:.2f} GB")
        print("=" * 60)

        warning = self.get_low_space_warning(path)
        if warning:
            print(warning)
        print()


def main():
    """Test disk space validator"""
    validator = DiskSpaceValidator(min_free_space_mb=100)

    # Print current usage
    validator.print_disk_usage()

    # Test space check
    has_space, message = validator.has_sufficient_space(required_bytes=10 * 1024 * 1024)
    print(f"Space check (10 MB): {message}")

    # Test PDF size estimation
    content = "This is sample content. " * 1000
    pdf_size = validator.estimate_pdf_size(len(content))
    print(f"Estimated PDF size for {len(content)} chars: {validator.format_bytes(pdf_size)}")

    # Test upload validation
    test_file_size = 5 * 1024 * 1024  # 5 MB
    is_valid, msg = validator.validate_upload(test_file_size)
    print(f"Upload validation (5 MB): {msg}")

    # Get any warnings
    warning = validator.get_low_space_warning()
    if warning:
        print(f"\n{warning}")
    else:
        print("\n✓ Disk space is adequate")


if __name__ == "__main__":
    main()
