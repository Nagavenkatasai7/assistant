"""
Format Validation for ATS Compatibility
Checks for ATS-unfriendly formatting elements and provides detailed feedback
"""

import re
from typing import Dict, List, Tuple


class FormatValidator:
    """
    Validates resume formatting for ATS compatibility.

    ATS systems struggle with:
    - Tables and columns
    - Images and graphics
    - Headers and footers
    - Text boxes
    - Special characters and symbols
    - Non-standard fonts
    - Complex formatting

    This validator checks for these issues and provides actionable feedback.
    """

    # Special characters that can cause ATS parsing issues
    PROBLEMATIC_CHARS = {
        '§', '†', '‡', '©', '®', '™', '°', '•', '◦', '▪', '▫',
        '→', '⇒', '←', '↔', '↑', '↓', '✓', '✔', '✗', '✘',
        '★', '☆', '♦', '♥', '♠', '♣', '※', '◆', '◇', '■', '□',
        '▲', '△', '▼', '▽', '◀', '◁', '▶', '▷', '⊕', '⊗', '⊙'
    }

    # Standard ATS-friendly fonts
    STANDARD_FONTS = {
        'arial', 'calibri', 'cambria', 'georgia', 'helvetica',
        'times new roman', 'trebuchet', 'verdana', 'garamond',
        'palatino', 'century gothic', 'book antiqua'
    }

    def __init__(self):
        """Initialize the format validator"""
        pass

    def validate_format(self, resume_content: str, file_format: str = "pdf") -> Dict:
        """
        Comprehensive format validation for ATS compatibility.

        Args:
            resume_content: Text content of the resume
            file_format: File format (pdf, docx, txt)

        Returns:
            Dict containing:
                - total_score: Total format score (0-30 points)
                - checks: Dict of individual check results
                - issues: List of identified formatting issues
                - suggestions: List of actionable improvement suggestions
        """
        checks = {}
        issues = []
        suggestions = []

        # Check 1: Tables (5 points)
        table_result = self._check_tables(resume_content)
        checks['tables'] = table_result
        if not table_result['passed']:
            issues.append(table_result['message'])
            suggestions.append("Remove tables. Use simple bullet points and clear headers instead.")

        # Check 2: Images/Graphics (5 points)
        image_result = self._check_images(resume_content)
        checks['images'] = image_result
        if not image_result['passed']:
            issues.append(image_result['message'])
            suggestions.append("Remove all images, icons, and graphics. ATS systems cannot parse visual elements.")

        # Check 3: Headers/Footers (5 points)
        header_footer_result = self._check_headers_footers(resume_content)
        checks['headers_footers'] = header_footer_result
        if not header_footer_result['passed']:
            issues.append(header_footer_result['message'])
            suggestions.append("Move contact info and page numbers to main body. Avoid headers/footers.")

        # Check 4: Standard Fonts (5 points) - Cannot detect from text, assume pass
        font_result = self._check_fonts()
        checks['fonts'] = font_result

        # Check 5: Text Boxes (5 points)
        textbox_result = self._check_textboxes(resume_content)
        checks['textboxes'] = textbox_result
        if not textbox_result['passed']:
            issues.append(textbox_result['message'])
            suggestions.append("Avoid text boxes. Use standard paragraphs and bullet points.")

        # Check 6: Section Headers (5 points)
        section_result = self._check_section_headers(resume_content)
        checks['section_headers'] = section_result
        if not section_result['passed']:
            issues.append(section_result['message'])
            suggestions.append("Use standard section headers: EXPERIENCE, EDUCATION, SKILLS, etc.")

        # Additional Checks

        # Check 7: Special Characters
        special_char_result = self._check_special_characters(resume_content)
        checks['special_characters'] = special_char_result
        if not special_char_result['passed']:
            issues.append(special_char_result['message'])
            suggestions.append(f"Replace special characters: {', '.join(special_char_result['found_chars'][:5])}")

        # Check 8: Line Length (too long can indicate tables/columns)
        line_length_result = self._check_line_lengths(resume_content)
        checks['line_length'] = line_length_result
        if not line_length_result['passed']:
            issues.append(line_length_result['message'])
            suggestions.append("Avoid multi-column layouts. Use single-column format.")

        # Check 9: Consistent Formatting
        consistency_result = self._check_formatting_consistency(resume_content)
        checks['consistency'] = consistency_result
        if not consistency_result['passed']:
            issues.append(consistency_result['message'])
            suggestions.append("Use consistent formatting for dates, bullets, and sections.")

        # Calculate total score
        total_score = sum(check['score'] for check in checks.values())

        return {
            'total_score': round(total_score, 2),
            'max_score': 30.0,
            'checks': checks,
            'issues': issues,
            'suggestions': suggestions,
            'passed': len(issues) == 0
        }

    def _check_tables(self, content: str) -> Dict:
        """
        Check for table indicators in resume.

        ATS systems struggle with tables. Look for:
        - Multiple pipe characters (|) in a row
        - Tab-separated values indicating columns
        - Repetitive spacing patterns
        """
        # Look for table-like patterns
        table_indicators = [
            r'\|.*\|.*\|',  # Markdown-style tables
            r'[-─═]{3,}',  # Table borders
            r'[┌┐└┘├┤┬┴┼│─]',  # Box drawing characters
        ]

        for pattern in table_indicators:
            if re.search(pattern, content):
                return {
                    'passed': False,
                    'score': 0.0,
                    'max_score': 5.0,
                    'message': 'Tables detected in resume'
                }

        # Check for excessive tabs (might indicate columns)
        lines = content.split('\n')
        tab_heavy_lines = sum(1 for line in lines if line.count('\t') > 2)
        if tab_heavy_lines > 3:
            return {
                'passed': False,
                'score': 2.5,
                'max_score': 5.0,
                'message': 'Possible column layout detected (excessive tabs)'
            }

        return {
            'passed': True,
            'score': 5.0,
            'max_score': 5.0,
            'message': 'No tables detected'
        }

    def _check_images(self, content: str) -> Dict:
        """
        Check for image references or indicators.

        In plain text, images might be referenced as:
        - [Image], [Photo], [Logo]
        - File paths to images
        """
        image_patterns = [
            r'\[image\]',
            r'\[photo\]',
            r'\[logo\]',
            r'\[picture\]',
            r'\.(jpg|jpeg|png|gif|svg|bmp)',
        ]

        for pattern in image_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return {
                    'passed': False,
                    'score': 0.0,
                    'max_score': 5.0,
                    'message': 'Image references detected in resume'
                }

        return {
            'passed': True,
            'score': 5.0,
            'max_score': 5.0,
            'message': 'No images detected'
        }

    def _check_headers_footers(self, content: str) -> Dict:
        """
        Check for header/footer indicators.

        Since we're analyzing text, we check for:
        - Page numbers at start/end of pages
        - "Page X of Y" patterns
        - Repeated content that might be headers/footers
        """
        # Check for page number patterns
        page_patterns = [
            r'page\s+\d+\s+of\s+\d+',
            r'^\s*\d+\s*$',  # Standalone numbers (possible page numbers)
        ]

        for pattern in page_patterns:
            if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                return {
                    'passed': False,
                    'score': 2.5,
                    'max_score': 5.0,
                    'message': 'Possible header/footer content detected'
                }

        return {
            'passed': True,
            'score': 5.0,
            'max_score': 5.0,
            'message': 'No headers/footers detected'
        }

    def _check_fonts(self) -> Dict:
        """
        Check font usage (placeholder for document analysis).

        Note: Cannot detect fonts from plain text. In a full implementation,
        this would parse DOCX/PDF metadata.
        """
        # Assume pass since we can't detect from text
        return {
            'passed': True,
            'score': 5.0,
            'max_score': 5.0,
            'message': 'Standard fonts assumed (cannot verify from text)'
        }

    def _check_textboxes(self, content: str) -> Dict:
        """
        Check for text box indicators.

        Text boxes might be indicated by:
        - Box drawing characters
        - Unusual indentation patterns
        """
        # Check for box drawing characters
        box_chars = r'[┌┐└┘├┤┬┴┼│─═║╔╗╚╝╠╣╦╩╬]'
        if re.search(box_chars, content):
            return {
                'passed': False,
                'score': 0.0,
                'max_score': 5.0,
                'message': 'Text boxes or borders detected'
            }

        return {
            'passed': True,
            'score': 5.0,
            'max_score': 5.0,
            'message': 'No text boxes detected'
        }

    def _check_section_headers(self, content: str) -> Dict:
        """
        Check for standard resume section headers.

        ATS systems look for standard section names:
        - EXPERIENCE / WORK EXPERIENCE / PROFESSIONAL EXPERIENCE
        - EDUCATION
        - SKILLS / TECHNICAL SKILLS
        - SUMMARY / PROFESSIONAL SUMMARY
        """
        content_upper = content.upper()

        required_sections = {
            'experience': [
                'PROFESSIONAL EXPERIENCE',
                'WORK EXPERIENCE',
                'EXPERIENCE',
                'EMPLOYMENT HISTORY'
            ],
            'education': ['EDUCATION', 'ACADEMIC BACKGROUND'],
            'skills': [
                'TECHNICAL SKILLS',
                'SKILLS',
                'CORE COMPETENCIES',
                'EXPERTISE'
            ]
        }

        found_sections = []
        missing_sections = []

        for section_type, variations in required_sections.items():
            found = False
            for variation in variations:
                if variation in content_upper:
                    found = True
                    found_sections.append(variation)
                    break
            if not found:
                missing_sections.append(section_type)

        if missing_sections:
            return {
                'passed': False,
                'score': 3.0,
                'max_score': 5.0,
                'message': f'Missing standard sections: {", ".join(missing_sections)}',
                'found_sections': found_sections,
                'missing_sections': missing_sections
            }

        return {
            'passed': True,
            'score': 5.0,
            'max_score': 5.0,
            'message': 'All standard sections present',
            'found_sections': found_sections
        }

    def _check_special_characters(self, content: str) -> Dict:
        """
        Check for problematic special characters.

        ATS systems can struggle with:
        - Fancy bullets (•, ◦, →)
        - Special symbols (©, ®, ™)
        - Non-standard punctuation
        """
        found_chars = []
        for char in self.PROBLEMATIC_CHARS:
            if char in content:
                found_chars.append(char)

        if found_chars:
            # Reduce score based on number of problematic characters
            penalty = min(2.0, len(found_chars) * 0.5)
            return {
                'passed': False,
                'score': max(0, 2.0 - penalty),
                'max_score': 2.0,
                'message': f'Found {len(found_chars)} problematic special characters',
                'found_chars': found_chars
            }

        return {
            'passed': True,
            'score': 2.0,
            'max_score': 2.0,
            'message': 'No problematic special characters found',
            'found_chars': []
        }

    def _check_line_lengths(self, content: str) -> Dict:
        """
        Check for unusually long lines (might indicate tables or multi-column).

        Standard single-column text should have line lengths < 100 characters.
        """
        lines = content.split('\n')
        long_lines = [line for line in lines if len(line) > 120]

        if len(long_lines) > 5:
            return {
                'passed': False,
                'score': 1.0,
                'max_score': 2.0,
                'message': f'{len(long_lines)} lines exceed 120 characters (possible multi-column layout)'
            }

        return {
            'passed': True,
            'score': 2.0,
            'max_score': 2.0,
            'message': 'Line lengths are appropriate'
        }

    def _check_formatting_consistency(self, content: str) -> Dict:
        """
        Check for consistent date formatting and bullet usage.

        Consistent formatting helps ATS parsing:
        - Dates should follow same format (MM/YYYY or Month YYYY)
        - Bullets should be consistent
        """
        # Check date formats
        date_patterns = [
            r'\d{1,2}/\d{4}',  # MM/YYYY
            r'\d{4}',  # YYYY
            r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}',  # Month YYYY
        ]

        date_formats_found = []
        for pattern in date_patterns:
            matches = re.findall(pattern, content)
            if matches:
                date_formats_found.append(pattern)

        # Multiple date formats indicate inconsistency
        if len(date_formats_found) > 2:
            return {
                'passed': False,
                'score': 1.0,
                'max_score': 2.0,
                'message': 'Inconsistent date formatting detected'
            }

        return {
            'passed': True,
            'score': 2.0,
            'max_score': 2.0,
            'message': 'Formatting is consistent'
        }

    def validate_file_format(self, file_format: str, file_size_bytes: int = None) -> Dict:
        """
        Validate file format and size for ATS compatibility.

        Args:
            file_format: File extension (pdf, docx, txt)
            file_size_bytes: File size in bytes

        Returns:
            Dict with file format validation results
        """
        checks = {}
        issues = []
        suggestions = []

        # Check file format (5 points)
        format_lower = file_format.lower().replace('.', '')
        if format_lower == 'docx':
            format_score = 5.0
            format_message = 'DOCX format (optimal for ATS)'
        elif format_lower == 'pdf':
            format_score = 4.0
            format_message = 'PDF format (good for ATS, ensure text-based)'
            suggestions.append("Consider DOCX format for better ATS compatibility")
        elif format_lower in ['doc', 'txt']:
            format_score = 3.0
            format_message = f'{format_lower.upper()} format (acceptable but not optimal)'
            suggestions.append("Consider converting to DOCX or PDF format")
        else:
            format_score = 0.0
            format_message = f'{format_lower.upper()} format not ATS-compatible'
            issues.append("File format not supported by most ATS systems")
            suggestions.append("Convert to DOCX or PDF format")

        checks['file_format'] = {
            'score': format_score,
            'max_score': 5.0,
            'message': format_message,
            'passed': format_score >= 3.0
        }

        # Check file size (3 points)
        if file_size_bytes is not None:
            mb_size = file_size_bytes / (1024 * 1024)
            if mb_size <= 1.0:
                size_score = 3.0
                size_message = f'File size: {mb_size:.2f}MB (optimal)'
            elif mb_size <= 2.0:
                size_score = 2.0
                size_message = f'File size: {mb_size:.2f}MB (acceptable)'
                suggestions.append("Consider reducing file size below 1MB")
            else:
                size_score = 0.0
                size_message = f'File size: {mb_size:.2f}MB (too large)'
                issues.append("File size exceeds 1MB limit for many ATS systems")
                suggestions.append("Reduce file size by removing images and simplifying formatting")

            checks['file_size'] = {
                'score': size_score,
                'max_score': 3.0,
                'message': size_message,
                'passed': size_score >= 2.0
            }
        else:
            # Cannot check size, assume pass
            checks['file_size'] = {
                'score': 3.0,
                'max_score': 3.0,
                'message': 'File size not provided (assumed acceptable)',
                'passed': True
            }

        total_score = sum(check['score'] for check in checks.values())

        return {
            'total_score': round(total_score, 2),
            'max_score': 8.0,
            'checks': checks,
            'issues': issues,
            'suggestions': suggestions
        }
