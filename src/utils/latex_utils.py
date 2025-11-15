"""
LaTeX utility functions for escaping special characters and validation
"""
import re
from typing import Any, Dict, List
from urllib.parse import urlparse


class LaTeXEscaper:
    """Handle LaTeX special character escaping"""

    # Characters that need escaping in LaTeX
    LATEX_SPECIAL_CHARS = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
        '\\': r'\textbackslash{}',
    }

    @classmethod
    def escape(cls, text: str) -> str:
        """
        Escape LaTeX special characters in text.

        Args:
            text: String that may contain LaTeX special characters

        Returns:
            Escaped string safe for LaTeX

        Examples:
            >>> LaTeXEscaper.escape("Increased revenue by 50% & reduced costs by $10K")
            'Increased revenue by 50\\% \\& reduced costs by \\$10K'
        """
        if not isinstance(text, str):
            return str(text)

        # Replace backslash first to avoid double-escaping
        result = text.replace('\\', r'\textbackslash{}')

        # Replace other special characters
        for char, escaped in cls.LATEX_SPECIAL_CHARS.items():
            if char != '\\':  # Already handled
                result = result.replace(char, escaped)

        return result

    @classmethod
    def escape_recursive(cls, data: Any) -> Any:
        """
        Recursively escape LaTeX special characters in data structures.

        Args:
            data: Can be str, list, dict, or primitive type

        Returns:
            Data structure with all strings escaped
        """
        if isinstance(data, str):
            return cls.escape(data)
        elif isinstance(data, list):
            return [cls.escape_recursive(item) for item in data]
        elif isinstance(data, dict):
            return {key: cls.escape_recursive(value) for key, value in data.items()}
        else:
            # Numbers, booleans, None - return as-is
            return data


class LaTeXValidator:
    """Validate data before LaTeX compilation"""

    @staticmethod
    def validate_url(url: str) -> bool:
        """
        Validate URL format.

        Args:
            url: URL string to validate

        Returns:
            True if valid URL
        """
        if not url:
            return False

        # Add https:// if no scheme
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    @staticmethod
    def sanitize_url(url: str) -> str:
        """
        Clean and standardize URL.

        Args:
            url: Raw URL string

        Returns:
            Cleaned URL
        """
        if not url:
            return ''

        # Remove common prefixes that users might include
        url = url.replace('https://', '').replace('http://', '')

        # Remove trailing slashes
        url = url.rstrip('/')

        return url

    @staticmethod
    def validate_required_fields(data: dict, required_fields: List[str]) -> List[str]:
        """
        Check for required fields in data dictionary.

        Args:
            data: Data dictionary to validate
            required_fields: List of required field paths (e.g., 'header.name')

        Returns:
            List of missing fields (empty list if all present)
        """
        missing = []

        for field_path in required_fields:
            parts = field_path.split('.')
            current = data

            try:
                for part in parts:
                    current = current[part]

                # Check if value is empty
                if not current:
                    missing.append(field_path)
            except (KeyError, TypeError):
                missing.append(field_path)

        return missing

    @staticmethod
    def validate_bullets(bullets: List[str], max_bullets: int = 10) -> bool:
        """
        Validate bullet point list.

        Args:
            bullets: List of bullet point strings
            max_bullets: Maximum allowed bullets

        Returns:
            True if valid
        """
        if not isinstance(bullets, list):
            return False

        if len(bullets) > max_bullets:
            return False

        # Check each bullet is non-empty string
        return all(isinstance(b, str) and b.strip() for b in bullets)


def get_nested_value(data: dict, path: str, default=None):
    """
    Get value from nested dictionary using dot notation.

    Args:
        data: Dictionary to search
        path: Dot-separated path (e.g., 'header.name')
        default: Default value if path not found

    Returns:
        Value at path or default

    Examples:
        >>> data = {'header': {'name': 'John'}}
        >>> get_nested_value(data, 'header.name')
        'John'
    """
    parts = path.split('.')
    current = data

    try:
        for part in parts:
            current = current[part]
        return current
    except (KeyError, TypeError):
        return default


def flatten_dict(data: dict, parent_key: str = '', sep: str = '.') -> dict:
    """
    Flatten nested dictionary.

    Args:
        data: Nested dictionary
        parent_key: Prefix for keys
        sep: Separator for nested keys

    Returns:
        Flattened dictionary

    Examples:
        >>> flatten_dict({'a': {'b': 1, 'c': 2}})
        {'a.b': 1, 'a.c': 2}
    """
    items = []

    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key

        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, sep=sep).items())
        else:
            items.append((new_key, value))

    return dict(items)


# Convenience functions
def escape_latex(text: str) -> str:
    """Shorthand for LaTeXEscaper.escape()"""
    return LaTeXEscaper.escape(text)


def escape_latex_dict(data: dict) -> dict:
    """Shorthand for recursive escaping of dictionary"""
    return LaTeXEscaper.escape_recursive(data)
