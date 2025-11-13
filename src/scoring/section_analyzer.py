"""
Resume Section Analysis for ATS Scoring
Validates resume structure and completeness of required sections
"""

import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class SectionAnalyzer:
    """
    Analyzes resume sections for completeness and structure.

    Validates:
    - Contact information (email, phone, location)
    - Professional summary/objective
    - Work experience with proper formatting
    - Education section
    - Skills section
    - Date formatting consistency
    - Section ordering and structure
    """

    # Email regex pattern
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    # Phone number patterns (various formats)
    PHONE_PATTERNS = [
        r'\+?1?\s*\(?([0-9]{3})\)?[\s.-]?([0-9]{3})[\s.-]?([0-9]{4})',  # US format
        r'\+?[0-9]{1,3}[\s.-]?[0-9]{3,4}[\s.-]?[0-9]{3,4}[\s.-]?[0-9]{3,4}',  # International
    ]

    # Date patterns
    DATE_PATTERNS = [
        r'\b(?:0?[1-9]|1[0-2])/\d{4}\b',  # MM/YYYY
        r'\b\d{4}\b',  # YYYY
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\b',  # Month YYYY
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',
    ]

    def __init__(self):
        """Initialize the section analyzer"""
        pass

    def analyze_sections(self, resume_content: str) -> Dict:
        """
        Comprehensive section analysis for resume structure.

        Args:
            resume_content: Full text of the resume

        Returns:
            Dict containing:
                - total_score: Total structure score (0-20 points)
                - checks: Dict of individual section checks
                - missing_sections: List of missing required sections
                - suggestions: List of improvement suggestions
        """
        checks = {}
        missing = []
        suggestions = []

        # Check 1: Contact Information (5 points)
        contact_result = self._check_contact_info(resume_content)
        checks['contact_info'] = contact_result
        if not contact_result['complete']:
            missing.extend(contact_result['missing_fields'])
            suggestions.append(f"Add missing contact info: {', '.join(contact_result['missing_fields'])}")

        # Check 2: Work Experience Section (5 points)
        experience_result = self._check_experience_section(resume_content)
        checks['experience'] = experience_result
        if not experience_result['passed']:
            suggestions.append("Add a clear EXPERIENCE section with job titles, companies, and dates")

        # Check 3: Education Section (5 points)
        education_result = self._check_education_section(resume_content)
        checks['education'] = education_result
        if not education_result['passed']:
            suggestions.append("Add an EDUCATION section with degree, institution, and graduation date")

        # Check 4: Date Formatting (5 points)
        date_result = self._check_date_formatting(resume_content)
        checks['date_formatting'] = date_result
        if not date_result['consistent']:
            suggestions.append("Use consistent date formatting throughout (MM/YYYY recommended)")

        # Additional checks for bonus points

        # Check 5: Professional Summary
        summary_result = self._check_summary(resume_content)
        checks['summary'] = summary_result
        if not summary_result['passed']:
            suggestions.append("Add a Professional Summary section at the top of your resume")

        # Check 6: Skills Section
        skills_result = self._check_skills_section(resume_content)
        checks['skills'] = skills_result
        if not skills_result['passed']:
            suggestions.append("Add a SKILLS or TECHNICAL SKILLS section")
        elif skills_result['skill_count'] < 10:
            suggestions.append(f"Add more skills (current: {skills_result['skill_count']}, recommended: 15-20)")

        # Calculate total score
        total_score = sum(check['score'] for check in checks.values())

        return {
            'total_score': round(total_score, 2),
            'max_score': 20.0,
            'checks': checks,
            'missing_sections': missing,
            'suggestions': suggestions,
            'complete': len(missing) == 0
        }

    def _check_contact_info(self, content: str) -> Dict:
        """
        Check for presence and completeness of contact information.

        Required fields:
        - Email address
        - Phone number
        - Location (city, state or city, country)
        - LinkedIn (optional but recommended)
        """
        contact_fields = {
            'email': False,
            'phone': False,
            'location': False,
            'linkedin': False
        }

        # Check for email
        if re.search(self.EMAIL_PATTERN, content):
            contact_fields['email'] = True

        # Check for phone
        for pattern in self.PHONE_PATTERNS:
            if re.search(pattern, content):
                contact_fields['phone'] = True
                break

        # Check for location
        # Look for city/state patterns or common location indicators
        location_patterns = [
            r'\b[A-Z][a-z]+,\s*[A-Z]{2}\b',  # City, ST
            r'\b[A-Z][a-z]+,\s*[A-Z][a-z]+\b',  # City, State or City, Country
        ]
        for pattern in location_patterns:
            if re.search(pattern, content):
                contact_fields['location'] = True
                break

        # Check for LinkedIn
        linkedin_patterns = [
            r'linkedin\.com',
            r'linkedin',
            r'LinkedIn'
        ]
        for pattern in linkedin_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                contact_fields['linkedin'] = True
                break

        # Calculate score
        required_fields = ['email', 'phone', 'location']
        present_required = sum(1 for field in required_fields if contact_fields[field])

        if present_required == 3 and contact_fields['linkedin']:
            score = 5.0
            message = "Complete contact information"
        elif present_required == 3:
            score = 4.5
            message = "Contact information present (consider adding LinkedIn)"
        elif present_required == 2:
            score = 3.0
            message = "Partial contact information"
        elif present_required == 1:
            score = 1.5
            message = "Minimal contact information"
        else:
            score = 0.0
            message = "Missing contact information"

        missing_fields = [field for field in required_fields if not contact_fields[field]]

        return {
            'score': score,
            'max_score': 5.0,
            'passed': present_required == 3,
            'complete': present_required == 3 and contact_fields['linkedin'],
            'message': message,
            'fields': contact_fields,
            'missing_fields': missing_fields
        }

    def _check_experience_section(self, content: str) -> Dict:
        """
        Check for work experience section and its quality.

        Looks for:
        - Section header (EXPERIENCE, WORK EXPERIENCE, etc.)
        - Job titles
        - Company names
        - Dates
        - Bullet points describing responsibilities
        """
        content_upper = content.upper()

        # Check for experience section header
        experience_headers = [
            'PROFESSIONAL EXPERIENCE',
            'WORK EXPERIENCE',
            'EXPERIENCE',
            'EMPLOYMENT HISTORY',
            'CAREER HISTORY'
        ]

        has_header = False
        header_found = None
        for header in experience_headers:
            if header in content_upper:
                has_header = True
                header_found = header
                break

        if not has_header:
            return {
                'score': 0.0,
                'max_score': 5.0,
                'passed': False,
                'message': 'No experience section found',
                'header_found': None,
                'entry_count': 0
            }

        # Estimate number of experience entries
        # Look for patterns like "Company Name | Location" or job title headers
        entry_count = self._count_experience_entries(content)

        # Check for bullet points (indicating detailed descriptions)
        bullet_patterns = [r'^\s*[-•*]\s+', r'^\s*\d+\.\s+']
        bullet_count = 0
        for pattern in bullet_patterns:
            bullet_count += len(re.findall(pattern, content, re.MULTILINE))

        # Score based on completeness
        if entry_count >= 2 and bullet_count >= 6:
            score = 5.0
            message = f"Well-structured experience section ({entry_count} entries)"
        elif entry_count >= 1 and bullet_count >= 3:
            score = 4.0
            message = f"Good experience section ({entry_count} entries)"
        elif entry_count >= 1:
            score = 2.5
            message = "Experience section present but needs more detail"
        else:
            score = 1.0
            message = "Experience section found but incomplete"

        return {
            'score': score,
            'max_score': 5.0,
            'passed': score >= 4.0,
            'message': message,
            'header_found': header_found,
            'entry_count': entry_count,
            'bullet_count': bullet_count
        }

    def _count_experience_entries(self, content: str) -> int:
        """
        Estimate number of work experience entries.

        Look for patterns like:
        - Job Title | Company
        - Company Name | Location
        - Dates followed by job titles
        """
        # Look for date ranges (indicating separate jobs)
        date_range_pattern = r'\d{4}\s*[-–—]\s*(?:\d{4}|Present|Current)'
        date_ranges = re.findall(date_range_pattern, content, re.IGNORECASE)

        # Also look for patterns like "Company Name | Location"
        pipe_pattern = r'^[A-Z][^|]+\|[^|]+$'
        pipe_entries = re.findall(pipe_pattern, content, re.MULTILINE)

        # Use the maximum as the entry count estimate
        return max(len(date_ranges), len(pipe_entries))

    def _check_education_section(self, content: str) -> Dict:
        """
        Check for education section and its completeness.

        Looks for:
        - Section header (EDUCATION, ACADEMIC BACKGROUND)
        - Degree names (Bachelor's, Master's, PhD, etc.)
        - University/Institution names
        - Graduation dates
        """
        content_upper = content.upper()

        # Check for education section header
        education_headers = [
            'EDUCATION',
            'ACADEMIC BACKGROUND',
            'ACADEMIC CREDENTIALS',
            'EDUCATIONAL BACKGROUND'
        ]

        has_header = False
        header_found = None
        for header in education_headers:
            if header in content_upper:
                has_header = True
                header_found = header
                break

        if not has_header:
            return {
                'score': 0.0,
                'max_score': 5.0,
                'passed': False,
                'message': 'No education section found',
                'header_found': None,
                'has_degree': False
            }

        # Check for degree keywords
        degree_keywords = [
            r'\bB\.?S\.?\b', r'\bB\.?A\.?\b', r'\bBachelor',
            r'\bM\.?S\.?\b', r'\bM\.?A\.?\b', r'\bMaster',
            r'\bPh\.?D\.?\b', r'\bDoctorate',
            r'\bAssociate', r'\bA\.?A\.?\b', r'\bA\.?S\.?\b'
        ]

        has_degree = False
        for pattern in degree_keywords:
            if re.search(pattern, content, re.IGNORECASE):
                has_degree = True
                break

        # Check for graduation dates
        has_dates = self._has_dates_in_section(content, header_found)

        # Score based on completeness
        if has_degree and has_dates:
            score = 5.0
            message = "Complete education section"
        elif has_degree:
            score = 4.0
            message = "Education section present (add graduation date)"
        else:
            score = 2.0
            message = "Education section incomplete"

        return {
            'score': score,
            'max_score': 5.0,
            'passed': score >= 4.0,
            'message': message,
            'header_found': header_found,
            'has_degree': has_degree,
            'has_dates': has_dates
        }

    def _has_dates_in_section(self, content: str, section_header: str) -> bool:
        """Check if dates are present near a section header"""
        if not section_header:
            return False

        # Extract text around the section header (next 500 characters)
        idx = content.upper().find(section_header)
        if idx == -1:
            return False

        section_text = content[idx:idx + 500]

        # Check for any date pattern
        for pattern in self.DATE_PATTERNS:
            if re.search(pattern, section_text):
                return True

        return False

    def _check_date_formatting(self, content: str) -> Dict:
        """
        Check for consistent date formatting throughout resume.

        Best practice: Use MM/YYYY or Month YYYY consistently.
        """
        # Find all dates and categorize by format
        date_formats_found = {
            'MM/YYYY': [],
            'YYYY': [],
            'Month YYYY': [],
            'Full Month YYYY': []
        }

        # MM/YYYY format
        mm_yyyy = re.findall(r'\b(?:0?[1-9]|1[0-2])/\d{4}\b', content)
        date_formats_found['MM/YYYY'] = mm_yyyy

        # YYYY only (standalone years)
        yyyy = re.findall(r'\b\d{4}\b', content)
        date_formats_found['YYYY'] = yyyy

        # Month YYYY (abbreviated)
        month_yyyy = re.findall(
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}\b',
            content
        )
        date_formats_found['Month YYYY'] = month_yyyy

        # Full Month YYYY
        full_month = re.findall(
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',
            content
        )
        date_formats_found['Full Month YYYY'] = full_month

        # Count which formats are used
        formats_used = [fmt for fmt, dates in date_formats_found.items() if len(dates) > 0]
        total_dates = sum(len(dates) for dates in date_formats_found.values())

        # Determine consistency
        if len(formats_used) == 0:
            return {
                'score': 2.5,
                'max_score': 5.0,
                'consistent': True,
                'message': 'No dates found in resume',
                'formats_found': []
            }
        elif len(formats_used) == 1:
            score = 5.0
            message = f"Consistent date formatting ({formats_used[0]})"
            consistent = True
        elif len(formats_used) == 2:
            score = 3.5
            message = f"Mostly consistent dates (uses {' and '.join(formats_used)})"
            consistent = False
        else:
            score = 2.0
            message = f"Inconsistent date formatting ({len(formats_used)} different formats)"
            consistent = False

        return {
            'score': score,
            'max_score': 5.0,
            'consistent': consistent,
            'message': message,
            'formats_found': formats_used,
            'total_dates': total_dates
        }

    def _check_summary(self, content: str) -> Dict:
        """
        Check for professional summary/objective section.

        This should appear near the top of the resume, after contact info.
        """
        content_upper = content.upper()

        summary_headers = [
            'PROFESSIONAL SUMMARY',
            'SUMMARY',
            'PROFILE',
            'OBJECTIVE',
            'CAREER OBJECTIVE',
            'PROFESSIONAL PROFILE'
        ]

        has_summary = False
        header_found = None
        for header in summary_headers:
            if header in content_upper:
                has_summary = True
                header_found = header
                break

        if not has_summary:
            return {
                'score': 0.0,
                'max_score': 0.0,  # Bonus, not required
                'passed': False,
                'message': 'No professional summary found',
                'header_found': None
            }

        # Check if summary appears in first 30% of document (should be near top)
        idx = content_upper.find(header_found)
        position_score = 1.0 if idx < len(content) * 0.3 else 0.5

        return {
            'score': position_score,
            'max_score': 0.0,  # Bonus
            'passed': True,
            'message': f'Professional summary present ({header_found})',
            'header_found': header_found,
            'position': 'top' if position_score == 1.0 else 'middle'
        }

    def _check_skills_section(self, content: str) -> Dict:
        """
        Check for skills section and estimate number of skills listed.

        A good skills section should have 15-20 relevant skills.
        """
        content_upper = content.upper()

        skills_headers = [
            'TECHNICAL SKILLS',
            'SKILLS',
            'CORE COMPETENCIES',
            'EXPERTISE',
            'PROFESSIONAL SKILLS',
            'KEY SKILLS'
        ]

        has_skills = False
        header_found = None
        for header in skills_headers:
            if header in content_upper:
                has_skills = True
                header_found = header
                break

        if not has_skills:
            return {
                'score': 0.0,
                'max_score': 0.0,  # Bonus
                'passed': False,
                'message': 'No skills section found',
                'header_found': None,
                'skill_count': 0
            }

        # Estimate skill count by looking at section content
        idx = content_upper.find(header_found)
        # Look at next 1000 characters after header
        skills_text = content[idx:idx + 1000]

        # Count potential skills (comma-separated items, bullet points)
        skill_count = len(re.findall(r',', skills_text))  # Comma-separated
        skill_count += len(re.findall(r'^\s*[-•*]\s+', skills_text, re.MULTILINE))  # Bullets

        # Estimate based on patterns
        if skill_count >= 15:
            score = 1.0
            message = f'Comprehensive skills section ({skill_count}+ skills)'
        elif skill_count >= 10:
            score = 0.7
            message = f'Good skills section ({skill_count}+ skills)'
        elif skill_count >= 5:
            score = 0.4
            message = f'Skills section present ({skill_count}+ skills, add more)'
        else:
            score = 0.2
            message = 'Skills section incomplete'

        return {
            'score': score,
            'max_score': 0.0,  # Bonus
            'passed': skill_count >= 10,
            'message': message,
            'header_found': header_found,
            'skill_count': skill_count
        }

    def analyze_section_order(self, content: str) -> Dict:
        """
        Analyze the order of resume sections.

        Standard ATS-friendly order:
        1. Contact Info
        2. Professional Summary
        3. Technical Skills (for technical roles) or Experience
        4. Experience
        5. Education
        6. Certifications (optional)
        """
        sections_found = []
        content_upper = content.upper()

        # Map of section types to their headers
        section_map = {
            'summary': ['PROFESSIONAL SUMMARY', 'SUMMARY', 'PROFILE', 'OBJECTIVE'],
            'skills': ['TECHNICAL SKILLS', 'SKILLS', 'CORE COMPETENCIES'],
            'experience': ['PROFESSIONAL EXPERIENCE', 'WORK EXPERIENCE', 'EXPERIENCE'],
            'education': ['EDUCATION', 'ACADEMIC BACKGROUND'],
            'certifications': ['CERTIFICATIONS', 'CERTIFICATES', 'LICENSES']
        }

        # Find positions of each section
        for section_type, headers in section_map.items():
            for header in headers:
                idx = content_upper.find(header)
                if idx != -1:
                    sections_found.append((section_type, idx, header))
                    break  # Found this section type, move to next

        # Sort by position
        sections_found.sort(key=lambda x: x[1])

        # Determine if order is optimal
        section_order = [s[0] for s in sections_found]

        # Optimal orders (experience before or after skills is acceptable)
        optimal_orders = [
            ['summary', 'skills', 'experience', 'education', 'certifications'],
            ['summary', 'experience', 'skills', 'education', 'certifications'],
            ['summary', 'skills', 'experience', 'education'],
            ['summary', 'experience', 'skills', 'education'],
            ['skills', 'experience', 'education'],
            ['experience', 'skills', 'education'],
            ['experience', 'education'],
        ]

        is_optimal = section_order in optimal_orders

        return {
            'sections_found': [{'type': s[0], 'position': s[1], 'header': s[2]} for s in sections_found],
            'section_order': section_order,
            'is_optimal': is_optimal,
            'message': 'Optimal section order' if is_optimal else 'Consider reordering sections'
        }
