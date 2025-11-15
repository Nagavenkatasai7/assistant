"""
Parser to extract structured data from AI-generated markdown resume.
Converts markdown resume into structured format for LaTeX template.
"""
import re
from typing import Dict, List, Any, Optional
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)


class SectionDetector:
    """Detects and classifies resume sections from markdown"""

    # Core sections requiring special parsing
    CORE_SECTIONS = {
        'summary', 'professional summary', 'profile', 'about',
        'skills', 'technical skills', 'core competencies',
        'education', 'academic background',
        'experience', 'projects', 'professional experience', 'work experience'
    }

    # Section name normalization
    SECTION_ALIASES = {
        'professional summary': 'summary',
        'profile': 'summary',
        'about': 'summary',
        'technical skills': 'skills',
        'core competencies': 'skills',
        'professional experience': 'experience',
        'work experience': 'experience',
        'academic background': 'education',
    }

    @staticmethod
    def detect_sections(markdown: str) -> OrderedDict:
        """
        Detect all sections from markdown content.

        Returns:
            OrderedDict[section_name, dict{'start', 'end', 'lines', 'level'}]
        """
        lines = markdown.split('\n')
        sections = OrderedDict()
        current_section = None
        section_start = 0

        for i, line in enumerate(lines):
            # Detect section headers (## Header or # Header)
            header_match = re.match(r'^(#{1,2})\s+(.+)$', line.strip())

            if header_match:
                # Save previous section
                if current_section:
                    sections[current_section['name']] = {
                        'start': section_start,
                        'end': i - 1,
                        'lines': lines[section_start:i],
                        'level': current_section['level']
                    }

                # Start new section
                level = len(header_match.group(1))  # 1 or 2 hashes
                section_name = header_match.group(2).strip()
                normalized_name = SectionDetector._normalize_name(section_name)

                current_section = {
                    'name': normalized_name,
                    'original_name': section_name,
                    'level': level
                }
                section_start = i + 1

        # Save last section
        if current_section:
            sections[current_section['name']] = {
                'start': section_start,
                'end': len(lines) - 1,
                'lines': lines[section_start:],
                'level': current_section['level']
            }

        return sections

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize section name"""
        normalized = name.lower().strip()
        return SectionDetector.SECTION_ALIASES.get(normalized, normalized)

    @staticmethod
    def is_core_section(section_name: str) -> bool:
        """Check if section requires special parsing"""
        normalized = section_name.lower()
        return normalized in SectionDetector.CORE_SECTIONS

    @staticmethod
    def detect_content_type(lines: List[str]) -> str:
        """
        Detect content structure type.

        Returns: 'text', 'list', 'structured', or 'nested'
        """
        if not lines:
            return 'text'

        # Count bullets
        bullet_count = sum(1 for line in lines if re.match(r'^\s*[-*•]\s+', line))

        # Check for metadata patterns (publications, awards)
        has_metadata = any(
            re.search(r'\*\*[^:]+:\*\*', line) or
            re.search(r'^[A-Z][a-z]+:\s+', line)
            for line in lines
        )

        # Check for subsections
        has_subsections = any(re.match(r'^#{3,}\s+', line) for line in lines)

        if has_subsections:
            return 'nested'
        elif has_metadata and bullet_count > 0:
            return 'structured'
        elif bullet_count / max(len(lines), 1) > 0.5:
            return 'list'
        else:
            return 'text'


class AIResumeParser:
    """Parse AI-generated markdown resume into structured data"""

    def __init__(self):
        self.sections = {}
        self.current_section = None

    def parse_markdown_resume(self, markdown_content: str) -> Dict[str, Any]:
        """
        Parse markdown resume into structured format for LaTeX.
        Now supports dynamic sections detection.

        Args:
            markdown_content: AI-generated resume in markdown format

        Returns:
            Structured dictionary with all resume sections
        """
        if not markdown_content:
            logger.error("Empty markdown content provided")
            return self._get_default_structure()

        lines = markdown_content.split('\n')
        structured_data = self._get_default_structure()

        # Step 1: Detect ALL sections dynamically
        all_sections = SectionDetector.detect_sections(markdown_content)

        logger.info(f"Detected {len(all_sections)} sections: {list(all_sections.keys())}")

        # Step 2: Extract header (from top of document, before first section)
        structured_data['header'] = self._extract_header(lines)

        # Step 3: Parse core sections with specialized extractors
        for section_name, section_data in all_sections.items():
            section_lines = section_data['lines']

            if section_name in ['summary', 'professional summary', 'profile', 'about']:
                structured_data['summary'] = self._extract_text_content(section_lines)

            elif section_name in ['skills', 'technical skills', 'core competencies']:
                # Use existing skills extraction (it needs the full context)
                structured_data['skills'] = self._extract_skills(lines)

            elif section_name == 'education':
                # Use existing education extraction
                structured_data['education'] = self._extract_education(lines)

            elif section_name in ['projects', 'experience', 'professional experience', 'work experience']:
                # Merge into projects (primary content)
                # Use existing projects extraction
                structured_data['projects'] = self._extract_projects(lines)

        # Step 4: Extract dynamic sections (Publications, Awards, etc.)
        # FIX: Pass extracted header name to enable dynamic name filtering
        header_name = structured_data['header'].get('name', '')
        structured_data['dynamic_sections'] = self._extract_dynamic_sections(all_sections, header_name)

        # Step 5: Extract legacy additional sections
        structured_data['additional'] = self._extract_additional(lines)

        logger.info(
            f"Successfully parsed resume: {len(structured_data['projects'])} projects, "
            f"{len(structured_data.get('dynamic_sections', {}))} dynamic sections"
        )

        return structured_data

    def _get_default_structure(self) -> Dict[str, Any]:
        """Return default resume structure with dynamic sections support"""
        return {
            'header': {
                'name': 'Venkat Sai',
                'location': 'United States',
                'email': 'contact@example.com',
                'linkedin': '',
                'github': '',
                'title': 'Software Engineer'
            },
            'summary': '',
            'skills': {
                'ai_ml': [],
                'product_dev': [],
                'programming': []
            },
            'education': [],
            'projects': [],
            'additional': {},
            'dynamic_sections': OrderedDict()  # NEW: Store dynamic sections
        }

    def _extract_header(self, lines: List[str]) -> Dict[str, str]:
        """Extract header information from resume"""
        header = {
            'name': 'Venkat Sai',
            'location': 'United States',
            'email': 'contact@example.com',
            'linkedin': '',
            'github': '',
            'title': ''
        }

        # Look for name (usually first non-empty line or after # Name)
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            if line.startswith('# '):
                # Extract name from markdown header
                name = line[2:].strip()
                # Make sure it's not a section header
                if name and not name.lower() in ['professional summary', 'summary', 'profile', 'education', 'experience', 'projects', 'skills']:
                    header['name'] = name
                    break
            elif line.strip() and not line.startswith('#') and '@' not in line and 'github' not in line.lower():
                # Check if it looks like a name (2-4 words, title case)
                words = line.strip().split()
                if 2 <= len(words) <= 4 and all(word[0].isupper() for word in words if word):
                    header['name'] = line.strip()
                    break

        # Extract contact info
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        linkedin_pattern = r'linkedin\.com/in/[A-Za-z0-9-]+'
        github_pattern = r'github\.com/[A-Za-z0-9-]+'

        full_text = '\n'.join(lines[:30])  # Check first 30 lines for contact info

        emails = re.findall(email_pattern, full_text)
        if emails:
            header['email'] = emails[0]

        linkedins = re.findall(linkedin_pattern, full_text)
        if linkedins:
            header['linkedin'] = linkedins[0]

        githubs = re.findall(github_pattern, full_text)
        if githubs:
            header['github'] = githubs[0]

        # Extract location (look for City, STATE format in first few lines)
        location_patterns = [
            r'([A-Za-z\s]+,\s*[A-Z]{2}(?:\s+\d{5})?)',  # City, STATE or City, STATE ZIP
            r'Location:\s*(.+)',
            r'Based in\s+(.+)',
        ]
        for i, line in enumerate(lines[:5]):  # Check first 5 lines only
            if '@' not in line and 'github' not in line.lower():
                for pattern in location_patterns:
                    matches = re.search(pattern, line, re.IGNORECASE)
                    if matches:
                        header['location'] = matches.group(1).strip()
                        break
                if header['location'] != 'United States':
                    break

        return header

    def _extract_summary(self, lines: List[str]) -> str:
        """Extract professional summary"""
        summary_lines = []
        in_summary = False

        for i, line in enumerate(lines):
            # Check for summary section headers
            if re.match(r'^#{1,2}\s*(Professional\s*)?Summary|^#{1,2}\s*Profile|^#{1,2}\s*About', line, re.IGNORECASE):
                in_summary = True
                continue
            elif in_summary and re.match(r'^#{1,2}\s+\w', line):
                # Hit another section header
                break
            elif in_summary and line.strip():
                summary_lines.append(line.strip())

        # If no explicit summary section, try to extract from top of resume
        if not summary_lines:
            for i, line in enumerate(lines[2:15]):  # Skip name, check next lines
                if line.strip() and not line.startswith('#') and not '@' in line and not 'github' in line.lower():
                    # Looks like descriptive text
                    if len(line) > 50:  # Likely a summary sentence
                        summary_lines.append(line.strip())
                        if len(' '.join(summary_lines)) > 150:
                            break

        summary = ' '.join(summary_lines)
        # Clean up summary
        summary = re.sub(r'\s+', ' ', summary).strip()

        if not summary:
            summary = "Experienced software engineer with expertise in AI/ML and modern technologies."

        return summary

    def _extract_skills(self, lines: List[str]) -> Dict[str, List[str]]:
        """Extract and categorize skills for LaTeX template"""
        skills = {
            'ai_ml': [],
            'product_dev': [],
            'programming': []
        }

        # Keywords for categorization
        ai_ml_keywords = ['ai', 'ml', 'machine learning', 'deep learning', 'neural', 'tensorflow',
                         'pytorch', 'scikit', 'nlp', 'computer vision', 'llm', 'gpt', 'claude',
                         'transformers', 'bert', 'hugging', 'langchain', 'vector', 'rag', 'prompt']

        product_keywords = ['product', 'agile', 'scrum', 'jira', 'design', 'ux', 'ui', 'figma',
                           'roadmap', 'strategy', 'analytics', 'customer', 'user research', 'mvp',
                           'feature', 'requirements', 'stakeholder', 'cross-functional']

        in_skills = False
        skill_text = []

        for line in lines:
            # Check for skills section
            if re.match(r'^#{1,2}\s*(Technical\s*)?Skills|^#{1,2}\s*Core\s*Competencies', line, re.IGNORECASE):
                in_skills = True
                continue
            elif in_skills and re.match(r'^#{1,2}\s+\w', line) and not re.match(r'^#{3,}', line):
                # Hit another major section
                break
            elif in_skills and line.strip():
                skill_text.append(line.strip())

        # Parse skill text
        all_skills = []
        for line in skill_text:
            # Remove bullet points and categories
            line = re.sub(r'^[\*\-\•]\s*', '', line)
            line = re.sub(r'^\*\*[^:]+:\*\*\s*', '', line)
            line = re.sub(r'^[^:]+:\s*', '', line)
            # Remove any remaining markdown formatting
            line = re.sub(r'\*\*', '', line)
            line = re.sub(r'`', '', line)

            # Split by common delimiters
            skills_in_line = re.split(r'[,;|•]', line)
            for skill in skills_in_line:
                skill = skill.strip()
                if skill and len(skill) < 50:  # Avoid long phrases
                    all_skills.append(skill)

        # Categorize skills
        for skill in all_skills:
            skill_lower = skill.lower()

            # Check AI/ML category
            if any(keyword in skill_lower for keyword in ai_ml_keywords):
                skills['ai_ml'].append(skill)
            # Check Product category
            elif any(keyword in skill_lower for keyword in product_keywords):
                skills['product_dev'].append(skill)
            # Everything else goes to programming
            else:
                skills['programming'].append(skill)

        # Ensure we have some skills in each category (for template)
        if not skills['ai_ml']:
            skills['ai_ml'] = ['Machine Learning', 'Deep Learning', 'LLMs', 'RAG Systems']
        if not skills['product_dev']:
            skills['product_dev'] = ['Agile/Scrum', 'Product Strategy', 'User Research', 'Cross-functional Leadership']
        if not skills['programming']:
            skills['programming'] = ['Python', 'JavaScript', 'SQL', 'Git', 'Docker', 'AWS']

        # Limit to reasonable number
        skills['ai_ml'] = skills['ai_ml'][:8]
        skills['product_dev'] = skills['product_dev'][:8]
        skills['programming'] = skills['programming'][:10]

        return skills

    def _extract_education(self, lines: List[str]) -> List[Dict[str, str]]:
        """Extract education information"""
        education = []
        in_education = False
        current_edu = {}

        for line in lines:
            if re.match(r'^#{1,2}\s*Education', line, re.IGNORECASE):
                in_education = True
                continue
            elif in_education and re.match(r'^#{1,2}\s+\w', line) and not re.match(r'^#{3,}', line):
                if current_edu:
                    education.append(current_edu)
                break
            elif in_education and line.strip():
                # Look for institution patterns
                if '**' in line or re.match(r'^###', line):
                    if current_edu:
                        education.append(current_edu)
                    current_edu = {}

                    # Extract institution and degree
                    clean_line = re.sub(r'\*\*|###\s*', '', line).strip()
                    parts = re.split(r'[|,]', clean_line)

                    if parts:
                        current_edu['institution'] = parts[0].strip()
                        if len(parts) > 1:
                            current_edu['degree'] = parts[1].strip()
                        else:
                            current_edu['degree'] = 'Bachelor of Science'

                # Look for dates
                date_match = re.search(r'(\d{4})\s*[-–]\s*(\d{4}|Present)', line)
                if date_match and current_edu:
                    current_edu['dates'] = f"{date_match.group(1)} – {date_match.group(2)}"

                # Look for GPA
                gpa_match = re.search(r'GPA:?\s*([\d.]+)', line, re.IGNORECASE)
                if gpa_match and current_edu:
                    current_edu['gpa'] = gpa_match.group(1)

        if current_edu:
            education.append(current_edu)

        # Deduplicate education entries
        # FIX: Include dates and GPA in uniqueness check to prevent data loss for multiple degrees from same institution
        # Examples: BS + MS from same school, double majors, repeated coursework with different GPAs
        seen = set()
        deduplicated = []

        for edu in education:
            # Extract and normalize all fields for uniqueness comparison
            institution = edu.get('institution', '').lower().strip()
            degree = edu.get('degree', '').lower().strip()
            dates = edu.get('dates', '').lower().strip()  # Include dates to distinguish temporal attendance
            gpa = edu.get('gpa', '').lower().strip()      # Include GPA to distinguish repeated coursework

            # Create comprehensive unique key (institution + degree + dates + gpa)
            # This preserves multiple degrees from same institution with different time periods
            key = (institution, degree, dates, gpa)

            # Skip only if truly empty (all fields blank) or exact duplicate
            is_empty = key == ('', '', '', '')
            is_duplicate = key in seen

            if not is_empty and not is_duplicate:
                seen.add(key)
                deduplicated.append(edu)
                logger.debug(f"Keeping education entry: {institution} | {degree} | {dates}")
            elif is_duplicate:
                # Log when we skip a true duplicate for debugging
                logger.info(f"Skipping exact duplicate education entry: {institution} - {degree} ({dates})")
            # Note: Empty entries are silently dropped (no logging spam)

        education = deduplicated

        # Provide default if no education found
        if not education:
            education = [{
                'institution': 'University',
                'degree': 'Bachelor of Science in Computer Science',
                'dates': '2020 – 2024',
                'gpa': '3.8/4.0'
            }]

        return education

    def _extract_projects(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Extract project information"""
        projects = []
        in_projects = False
        current_project = None

        for i, line in enumerate(lines):
            # Check for project section
            if re.match(r'^#{1,2}\s*(Technical\s*)?Projects|^#{1,2}\s*Experience|^#{1,2}\s*Work', line, re.IGNORECASE):
                in_projects = True
                continue
            elif in_projects and re.match(r'^#{1,2}\s+\w', line) and 'project' not in line.lower():
                # Hit another major section (not a subsection)
                if current_project and current_project.get('bullets'):
                    projects.append(current_project)
                break
            elif in_projects:
                # Check for new project (usually ### or **)
                if (line.startswith('###') or line.startswith('**')) and not line.startswith('####'):
                    # Save previous project
                    if current_project and current_project.get('bullets'):
                        projects.append(current_project)

                    # Start new project
                    current_project = {
                        'title': '',
                        'dates': '',
                        'technologies': '',
                        'bullets': []
                    }

                    # Extract title
                    title = re.sub(r'^###\s*|\*\*|\*\*$', '', line).strip()
                    # Remove dates from title if present
                    date_match = re.search(r'\(?([\d]{4})\s*[-–]\s*([\d]{4}|Present)\)?', title)
                    if date_match:
                        current_project['dates'] = f"{date_match.group(1)} – {date_match.group(2)}"
                        title = re.sub(r'\(?([\d]{4})\s*[-–]\s*([\d]{4}|Present)\)?', '', title).strip()

                    current_project['title'] = title.strip(' |,-')

                # Extract technologies
                elif current_project and re.match(r'^(Technologies?|Tech Stack|Tools?):', line, re.IGNORECASE):
                    tech = re.sub(r'^[^:]+:\s*', '', line).strip()
                    current_project['technologies'] = tech

                # Extract bullets
                elif current_project and re.match(r'^[\*\-\•]\s+', line):
                    bullet = re.sub(r'^[\*\-\•]\s+', '', line).strip()
                    if bullet:
                        current_project['bullets'].append(bullet)

                # Check for inline dates
                elif current_project and not current_project['dates']:
                    date_match = re.search(r'(\d{4})\s*[-–]\s*(\d{4}|Present)', line)
                    if date_match:
                        current_project['dates'] = f"{date_match.group(1)} – {date_match.group(2)}"

        # Add last project
        if current_project and current_project.get('bullets'):
            projects.append(current_project)

        # Ensure we have at least 2 projects
        while len(projects) < 2:
            default_project = {
                'title': f'AI/ML Project {len(projects) + 1}',
                'dates': '2024 – Present',
                'technologies': 'Python, TensorFlow, FastAPI, Docker',
                'bullets': [
                    'Developed and deployed machine learning models for production use',
                    'Implemented scalable data pipelines and API endpoints',
                    'Optimized model performance achieving significant improvements',
                    'Collaborated with cross-functional teams to deliver solutions'
                ]
            }
            projects.append(default_project)

        # Ensure dates are set
        for project in projects:
            if not project.get('dates'):
                project['dates'] = '2024 – Present'

        return projects[:5]  # Limit to 5 projects for space

    def _extract_additional(self, lines: List[str]) -> Dict[str, str]:
        """Extract additional information like certifications, languages, etc."""
        additional = {}

        # Look for certifications
        for i, line in enumerate(lines):
            if re.match(r'^#{1,2}\s*Certifications?', line, re.IGNORECASE):
                cert_lines = []
                for j in range(i+1, min(i+10, len(lines))):
                    if re.match(r'^#{1,2}\s+\w', lines[j]):
                        break
                    if lines[j].strip():
                        cert_lines.append(re.sub(r'^[\*\-\•]\s*', '', lines[j].strip()))
                if cert_lines:
                    additional['certifications'] = ', '.join(cert_lines[:3])

        # Look for languages
        for i, line in enumerate(lines):
            if re.match(r'^#{1,2}\s*Languages?', line, re.IGNORECASE):
                lang_lines = []
                for j in range(i+1, min(i+5, len(lines))):
                    if re.match(r'^#{1,2}\s+\w', lines[j]):
                        break
                    if lines[j].strip():
                        lang_lines.append(re.sub(r'^[\*\-\•]\s*', '', lines[j].strip()))
                if lang_lines:
                    additional['languages'] = ', '.join(lang_lines[:2])

        return additional

    def _extract_dynamic_sections(self, all_sections: OrderedDict, header_name: str = '') -> OrderedDict:
        """
        Extract non-core sections dynamically with user-specific name filtering.

        Args:
            all_sections: All detected sections from markdown
            header_name: Extracted user name from header for dynamic filtering

        Returns:
            OrderedDict of dynamic sections with metadata
        """
        dynamic_sections = OrderedDict()
        order = 1

        # FIX: Extract name parts dynamically from header for reusable filtering
        # Split header name into individual parts for case-insensitive matching
        # Example: "Naga Venkata Sai Chennu" → ['naga', 'venkata', 'sai', 'chennu']
        name_parts = [part.lower() for part in header_name.split() if part] if header_name else []
        logger.debug(f"Using dynamic name parts for filtering: {name_parts}")

        # FIX: Refactored filter logic to reduce redundancy
        # Helper function for contact info detection (extracted to avoid duplication)
        def has_contact_indicators(text: str) -> bool:
            """Check if text contains contact information indicators."""
            contact_patterns = ['@', 'linkedin.com', 'github.com', 'http', '+1',
                              'phone', 'email', 'portfolio', '.com', '.edu', '.org', 'www.']
            return any(indicator in text for indicator in contact_patterns)

        # Helper function for name-like pattern detection (consolidates multiple checks)
        def is_name_like_section(section_name: str, name_parts: List[str]) -> tuple[bool, str]:
            """
            Check if section name matches name-like patterns.
            Returns (is_name_like, reason) tuple.
            """
            words = section_name.split()
            word_count = len(words)

            # Pattern 1: All alphabetic words (2-6 words)
            all_alpha = all(word.replace('-', '').isalpha() for word in words if word)
            if 2 <= word_count <= 6 and all_alpha:
                return True, "all alpha words"

            # Pattern 2: Title-case or uppercase pattern (2-5 words)
            is_title_case = all(word[0].isupper() for word in words if word)
            if 2 <= word_count <= 5 and is_title_case:
                return True, "title case pattern"

            # Pattern 3: All caps (screaming case names like "JOHN DOE")
            is_all_caps = all(word.isupper() for word in words if word and word.isalpha())
            if is_all_caps and word_count >= 2:
                return True, "all caps"

            # Pattern 4: Contains user's actual name parts (dynamic matching)
            if name_parts:
                section_lower = section_name.lower()
                matched_parts = [part for part in name_parts if len(part) > 2 and part in section_lower]
                if matched_parts:
                    return True, f"contains name parts: {matched_parts}"

            return False, ""

        for section_name, section_data in all_sections.items():
            # Skip core sections (already handled)
            if SectionDetector.is_core_section(section_name):
                continue

            # DYNAMIC FILTER: Skip sections that look like person names or contact blocks
            section_text = '\n'.join(section_data['lines']).lower()
            has_contact = has_contact_indicators(section_text)
            is_name_like, reason = is_name_like_section(section_name, name_parts)

            # Consolidated filter: Skip if name-like AND has contact info
            if is_name_like and has_contact:
                logger.info(f"Skipping name/contact section ({reason}): {section_name}")
                continue

            # Additional check: Skip very short sections (< 5 lines) with contact info
            # These are usually contact blocks or headers
            if len(section_data['lines']) < 5 and has_contact:
                logger.info(f"Skipping short contact section (< 5 lines): {section_name}")
                continue

            # Detect content type
            content_type = SectionDetector.detect_content_type(section_data['lines'])

            # Extract content based on type
            if content_type == 'structured':
                content = self._extract_structured_content(section_data['lines'])
            elif content_type == 'list':
                content = self._extract_list_content(section_data['lines'])
            elif content_type == 'nested':
                content = self._extract_nested_content(section_data['lines'])
            else:  # 'text'
                content = self._extract_text_content(section_data['lines'])

            # Store with metadata
            dynamic_sections[section_name] = {
                'type': content_type,
                'order': order,
                'content': content,
                'display_name': section_name.title()  # Convert to title case
            }

            order += 1

        return dynamic_sections

    def _extract_structured_content(self, lines: List[str]) -> List[Dict[str, str]]:
        """
        Extract structured content (e.g., Publications with title, authors, venue).

        Returns list of dicts with metadata.
        """
        items = []
        current_item = {}
        in_bullet = False

        for line in lines:
            line = line.strip()
            if not line:
                # Save current item if complete
                if current_item:
                    items.append(current_item)
                    current_item = {}
                in_bullet = False
                continue

            # Check for bullet point (new item)
            bullet_match = re.match(r'^[-*•]\s+(.+)$', line)
            if bullet_match:
                # Save previous item
                if current_item:
                    items.append(current_item)

                current_item = {'text': bullet_match.group(1)}
                in_bullet = True
                continue

            # Check for metadata pattern (e.g., "**Authors:** John Doe")
            metadata_match = re.match(r'\*\*([^:]+):\*\*\s*(.+)', line)
            if metadata_match and in_bullet:
                field = metadata_match.group(1).lower().strip()
                value = metadata_match.group(2).strip()
                current_item[field] = value
                continue

            # Continuation of previous line
            if in_bullet and 'text' in current_item:
                current_item['text'] += ' ' + line

        # Save last item
        if current_item:
            items.append(current_item)

        return items

    def _extract_list_content(self, lines: List[str]) -> List[str]:
        """Extract simple bullet list content"""
        items = []

        for line in lines:
            line = line.strip()
            # Match bullet points
            bullet_match = re.match(r'^[-*•]\s+(.+)$', line)
            if bullet_match:
                items.append(bullet_match.group(1))

        return items

    def _extract_nested_content(self, lines: List[str]) -> Dict[str, Any]:
        """Extract nested subsections"""
        subsections = OrderedDict()
        current_subsection = None
        current_lines = []

        for line in lines:
            # Detect subsection header (### Subsection)
            subsection_match = re.match(r'^#{3,}\s+(.+)$', line.strip())

            if subsection_match:
                # Save previous subsection
                if current_subsection:
                    subsections[current_subsection] = current_lines

                # Start new subsection
                current_subsection = subsection_match.group(1).strip()
                current_lines = []
            else:
                if current_subsection:
                    current_lines.append(line)

        # Save last subsection
        if current_subsection:
            subsections[current_subsection] = current_lines

        return subsections

    def _extract_text_content(self, lines: List[str]) -> str:
        """Extract paragraph text content"""
        # Join non-empty lines, preserving paragraph breaks
        paragraphs = []
        current_para = []

        for line in lines:
            line = line.strip()
            if line:
                current_para.append(line)
            elif current_para:
                paragraphs.append(' '.join(current_para))
                current_para = []

        if current_para:
            paragraphs.append(' '.join(current_para))

        return '\n\n'.join(paragraphs)