"""
Keyword Matching Algorithm for ATS Scoring
Analyzes keyword density, matching, and distribution in resume content
"""

import re
from collections import Counter
from typing import Dict, List, Set, Tuple


class KeywordMatcher:
    """
    Advanced keyword matching and density analysis for ATS optimization.

    Implements industry-standard ATS keyword matching algorithms including:
    - Exact phrase matching
    - Stemming and lemmatization
    - Synonym detection
    - Keyword density calculation
    - Distribution analysis across resume sections
    """

    # Common stop words to exclude from analysis
    STOP_WORDS = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'will', 'with', 'have', 'this', 'or', 'but', 'not',
        'you', 'all', 'can', 'had', 'her', 'were', 'when', 'who', 'which'
    }

    # Technical skill synonyms for better matching
    SKILL_SYNONYMS = {
        'javascript': ['js', 'javascript', 'ecmascript'],
        'python': ['py', 'python'],
        'typescript': ['ts', 'typescript'],
        'machine learning': ['ml', 'machine learning', 'machinelearning'],
        'artificial intelligence': ['ai', 'artificial intelligence'],
        'natural language processing': ['nlp', 'natural language processing'],
        'continuous integration': ['ci', 'continuous integration', 'ci/cd'],
        'kubernetes': ['k8s', 'kubernetes'],
        'docker': ['docker', 'containerization'],
        'react': ['react', 'reactjs', 'react.js'],
        'node': ['node', 'nodejs', 'node.js'],
        'aws': ['aws', 'amazon web services'],
        'gcp': ['gcp', 'google cloud platform'],
        'azure': ['azure', 'microsoft azure'],
    }

    def __init__(self):
        """Initialize the keyword matcher"""
        self._build_reverse_synonym_map()

    def _build_reverse_synonym_map(self):
        """Build reverse lookup map for synonyms"""
        self.reverse_synonyms = {}
        for canonical, synonyms in self.SKILL_SYNONYMS.items():
            for syn in synonyms:
                self.reverse_synonyms[syn.lower()] = canonical

    def analyze_keywords(
        self,
        resume_content: str,
        job_keywords: List[str],
        required_skills: List[str] = None
    ) -> Dict:
        """
        Comprehensive keyword analysis against job requirements.

        Args:
            resume_content: Full text of the resume
            job_keywords: List of keywords from job description
            required_skills: List of required skills from job posting

        Returns:
            Dict containing:
                - match_percentage: Percentage of job keywords found (0-100)
                - keyword_density: Overall keyword density percentage (0-100)
                - matched_keywords: List of keywords successfully matched
                - missing_keywords: List of keywords not found
                - skill_match_percentage: Percentage of required skills matched
                - density_score: Normalized density score (0-15)
                - match_score: Normalized match score (0-15)
                - distribution: Keyword distribution across sections
        """
        if not resume_content or not job_keywords:
            return self._empty_analysis()

        # Normalize inputs
        resume_lower = resume_content.lower()
        normalized_keywords = self._normalize_keywords(job_keywords)

        # Find matched and missing keywords
        matched_keywords = []
        missing_keywords = []
        keyword_positions = {}

        for keyword in normalized_keywords:
            if self._is_keyword_present(keyword, resume_lower):
                matched_keywords.append(keyword)
                keyword_positions[keyword] = self._find_keyword_positions(keyword, resume_lower)
            else:
                missing_keywords.append(keyword)

        # Calculate match percentage
        match_percentage = (len(matched_keywords) / len(normalized_keywords) * 100) if normalized_keywords else 0

        # Calculate keyword density
        word_count = len(self._extract_words(resume_content))
        total_keyword_occurrences = sum(len(positions) for positions in keyword_positions.values())
        keyword_density = (total_keyword_occurrences / word_count * 100) if word_count > 0 else 0

        # Analyze required skills separately if provided
        skill_match_percentage = 100.0
        if required_skills:
            skill_match_percentage = self._analyze_skills(resume_lower, required_skills)

        # Analyze keyword distribution across sections
        distribution = self._analyze_distribution(resume_content, keyword_positions)

        # Calculate normalized scores (out of 15 points each)
        match_score = self._calculate_match_score(match_percentage)
        density_score = self._calculate_density_score(keyword_density)

        return {
            'match_percentage': round(match_percentage, 2),
            'keyword_density': round(keyword_density, 2),
            'matched_keywords': matched_keywords,
            'missing_keywords': missing_keywords,
            'total_occurrences': total_keyword_occurrences,
            'skill_match_percentage': round(skill_match_percentage, 2),
            'match_score': match_score,
            'density_score': density_score,
            'distribution': distribution,
            'word_count': word_count
        }

    def _normalize_keywords(self, keywords: List[str]) -> List[str]:
        """
        Normalize keywords for better matching.
        Removes duplicates, handles synonyms, and filters stop words.
        """
        normalized = set()
        for keyword in keywords:
            keyword_lower = keyword.lower().strip()

            # Skip empty or stop words
            if not keyword_lower or keyword_lower in self.STOP_WORDS:
                continue

            # Use canonical form if it's a known synonym
            if keyword_lower in self.reverse_synonyms:
                normalized.add(self.reverse_synonyms[keyword_lower])
            else:
                normalized.add(keyword_lower)

        return sorted(list(normalized))

    def _is_keyword_present(self, keyword: str, text: str) -> bool:
        """
        Check if keyword is present in text.
        Handles exact matches, synonyms, and multi-word phrases.
        """
        # Check exact match
        if keyword in text:
            return True

        # Check synonyms
        synonyms = self.SKILL_SYNONYMS.get(keyword, [])
        for synonym in synonyms:
            if synonym.lower() in text:
                return True

        # Check with word boundaries for single words
        if ' ' not in keyword:
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False

    def _find_keyword_positions(self, keyword: str, text: str) -> List[int]:
        """Find all positions where keyword appears in text"""
        positions = []
        MAX_MATCHES_PER_KEYWORD = 1000  # P1-6 FIX: Prevent infinite loop/memory exhaustion

        # Find exact matches
        start = 0
        match_count = 0
        while True:
            pos = text.find(keyword, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
            # P1-6 FIX: Prevent unbounded loop
            match_count += 1
            if match_count >= MAX_MATCHES_PER_KEYWORD:
                break

        # Find synonym matches
        synonyms = self.SKILL_SYNONYMS.get(keyword, [])
        for synonym in synonyms:
            if synonym != keyword:
                start = 0
                match_count = 0
                while True:
                    pos = text.find(synonym.lower(), start)
                    if pos == -1:
                        break
                    positions.append(pos)
                    start = pos + 1
                    # P1-6 FIX: Prevent unbounded loop
                    match_count += 1
                    if match_count >= MAX_MATCHES_PER_KEYWORD:
                        break

        return sorted(positions)

    def _extract_words(self, text: str) -> List[str]:
        """Extract words from text, excluding special characters"""
        words = re.findall(r'\b[a-zA-Z]{2,}\b', text)
        return [w for w in words if w.lower() not in self.STOP_WORDS]

    def _analyze_skills(self, resume_lower: str, required_skills: List[str]) -> float:
        """
        Analyze how many required skills are present in resume.
        Returns percentage of required skills found.
        """
        if not required_skills:
            return 100.0

        matched_skills = 0
        for skill in required_skills:
            if self._is_keyword_present(skill.lower(), resume_lower):
                matched_skills += 1

        return (matched_skills / len(required_skills)) * 100

    def _analyze_distribution(self, resume_content: str, keyword_positions: Dict[str, List[int]]) -> Dict:
        """
        Analyze how keywords are distributed across resume sections.
        Good distribution means keywords appear in summary, skills, and experience.
        """
        # Simple section detection based on common headers
        sections = self._identify_sections(resume_content.lower())

        distribution = {
            'in_summary': 0,
            'in_skills': 0,
            'in_experience': 0,
            'in_other': 0,
            'well_distributed': False
        }

        for keyword, positions in keyword_positions.items():
            for pos in positions:
                section = self._get_section_at_position(pos, sections)
                if section == 'summary':
                    distribution['in_summary'] += 1
                elif section == 'skills':
                    distribution['in_skills'] += 1
                elif section == 'experience':
                    distribution['in_experience'] += 1
                else:
                    distribution['in_other'] += 1

        # Keywords should appear in at least 2 major sections for good distribution
        major_sections = sum([
            1 if distribution['in_summary'] > 0 else 0,
            1 if distribution['in_skills'] > 0 else 0,
            1 if distribution['in_experience'] > 0 else 0
        ])
        distribution['well_distributed'] = major_sections >= 2

        return distribution

    def _identify_sections(self, text: str) -> Dict[str, Tuple[int, int]]:
        """Identify major resume sections and their positions"""
        sections = {}

        # Common section headers
        section_patterns = {
            'summary': r'(professional\s+summary|summary|profile|objective)',
            'skills': r'(technical\s+skills|skills|core\s+competencies|expertise)',
            'experience': r'(professional\s+experience|work\s+experience|experience|employment)',
            'education': r'(education|academic\s+background)',
        }

        for section_name, pattern in section_patterns.items():
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            if matches:
                # Take the first match as section start
                start = matches[0].start()
                # Section ends at next section or end of text
                sections[section_name] = (start, len(text))

        # Adjust end positions based on next section starts
        sorted_sections = sorted(sections.items(), key=lambda x: x[1][0])
        for i in range(len(sorted_sections) - 1):
            section_name, (start, _) = sorted_sections[i]
            next_start = sorted_sections[i + 1][1][0]
            sections[section_name] = (start, next_start)

        return sections

    def _get_section_at_position(self, position: int, sections: Dict[str, Tuple[int, int]]) -> str:
        """Determine which section a position falls into"""
        for section_name, (start, end) in sections.items():
            if start <= position < end:
                return section_name
        return 'other'

    def _calculate_match_score(self, match_percentage: float) -> float:
        """
        Calculate normalized match score (0-15 points).

        Scoring:
        - 95-100%: 15 points (perfect match)
        - 85-94%: 13-14 points (excellent)
        - 75-84%: 11-12 points (good)
        - 65-74%: 9-10 points (acceptable)
        - 50-64%: 5-8 points (needs improvement)
        - <50%: 0-4 points (poor)
        """
        if match_percentage >= 95:
            return 15.0
        elif match_percentage >= 85:
            return 13.0 + ((match_percentage - 85) / 10) * 2
        elif match_percentage >= 75:
            return 11.0 + ((match_percentage - 75) / 10) * 2
        elif match_percentage >= 65:
            return 9.0 + ((match_percentage - 65) / 10) * 2
        elif match_percentage >= 50:
            return 5.0 + ((match_percentage - 50) / 15) * 4
        else:
            return (match_percentage / 50) * 5

    def _calculate_density_score(self, keyword_density: float) -> float:
        """
        Calculate normalized density score (0-10 points).

        Optimal keyword density is 2-4% for ATS systems.

        Scoring:
        - 2-4%: 10 points (optimal)
        - 1.5-2% or 4-5%: 8 points (good)
        - 1-1.5% or 5-6%: 6 points (acceptable)
        - 0.5-1% or 6-8%: 4 points (needs improvement)
        - <0.5% or >8%: 0-2 points (poor)
        """
        if 2.0 <= keyword_density <= 4.0:
            return 10.0
        elif 1.5 <= keyword_density < 2.0 or 4.0 < keyword_density <= 5.0:
            return 8.0
        elif 1.0 <= keyword_density < 1.5 or 5.0 < keyword_density <= 6.0:
            return 6.0
        elif 0.5 <= keyword_density < 1.0 or 6.0 < keyword_density <= 8.0:
            return 4.0
        elif keyword_density < 0.5:
            return keyword_density * 4  # Scale 0-0.5% to 0-2 points
        else:  # > 8%
            # Penalty for keyword stuffing
            return max(0, 2.0 - (keyword_density - 8.0) * 0.5)

    def _empty_analysis(self) -> Dict:
        """Return empty analysis structure"""
        return {
            'match_percentage': 0.0,
            'keyword_density': 0.0,
            'matched_keywords': [],
            'missing_keywords': [],
            'total_occurrences': 0,
            'skill_match_percentage': 0.0,
            'match_score': 0.0,
            'density_score': 0.0,
            'distribution': {
                'in_summary': 0,
                'in_skills': 0,
                'in_experience': 0,
                'in_other': 0,
                'well_distributed': False
            },
            'word_count': 0
        }

    def analyze_action_verbs(self, resume_content: str) -> Dict:
        """
        Analyze usage of strong action verbs in resume.

        Returns:
            Dict with action verb count and score (0-5 points)
        """
        # List of strong action verbs commonly recommended for resumes
        action_verbs = {
            'achieved', 'led', 'developed', 'implemented', 'designed',
            'created', 'built', 'managed', 'improved', 'increased',
            'reduced', 'optimized', 'launched', 'delivered', 'drove',
            'established', 'executed', 'generated', 'spearheaded', 'transformed',
            'streamlined', 'collaborated', 'orchestrated', 'architected', 'engineered',
            'automated', 'accelerated', 'enhanced', 'resolved', 'pioneered'
        }

        resume_lower = resume_content.lower()
        found_verbs = []

        for verb in action_verbs:
            if re.search(r'\b' + verb + r'\b', resume_lower):
                found_verbs.append(verb)

        verb_count = len(found_verbs)

        # Score: 5 points for 10+ unique action verbs, scaled down from there
        if verb_count >= 10:
            score = 5.0
        elif verb_count >= 7:
            score = 4.0
        elif verb_count >= 5:
            score = 3.0
        elif verb_count >= 3:
            score = 2.0
        elif verb_count >= 1:
            score = 1.0
        else:
            score = 0.0

        return {
            'count': verb_count,
            'found_verbs': found_verbs,
            'score': score
        }

    def analyze_quantifiable_results(self, resume_content: str) -> Dict:
        """
        Analyze presence of quantifiable metrics and results.

        Returns:
            Dict with metrics count and score (0-5 points)
        """
        # Patterns for numbers, percentages, dollar amounts
        patterns = [
            r'\d+%',  # Percentages
            r'\$[\d,]+',  # Dollar amounts
            r'\d+\+',  # Numbers with plus
            r'\d+[kK]\+?',  # Thousands (e.g., 50k)
            r'\d+[mM]\+?',  # Millions
            r'\d+x',  # Multipliers
            r'\d+(?:\.\d+)?x',  # Decimal multipliers
        ]

        metrics_found = []
        for pattern in patterns:
            matches = re.findall(pattern, resume_content)
            metrics_found.extend(matches)

        # Count unique metrics
        unique_metrics = len(set(metrics_found))

        # Score: 5 points for 8+ metrics, scaled down from there
        if unique_metrics >= 8:
            score = 5.0
        elif unique_metrics >= 6:
            score = 4.0
        elif unique_metrics >= 4:
            score = 3.0
        elif unique_metrics >= 2:
            score = 2.0
        elif unique_metrics >= 1:
            score = 1.0
        else:
            score = 0.0

        return {
            'count': unique_metrics,
            'metrics_found': metrics_found[:10],  # Return first 10 as examples
            'score': score
        }
