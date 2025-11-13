"""
Main ATS Scoring Engine
Orchestrates all scoring components to provide comprehensive ATS compatibility analysis
"""

import time
from typing import Dict, List, Optional
from .keyword_matcher import KeywordMatcher
from .format_validator import FormatValidator
from .section_analyzer import SectionAnalyzer


class ATSScorer:
    """
    Comprehensive ATS (Applicant Tracking System) Scoring Engine.

    Evaluates resumes across multiple dimensions:
    - Content Quality (40 points): Keyword matching, action verbs, quantifiable results
    - Format Compliance (30 points): ATS-friendly formatting, no problematic elements
    - Structure Completeness (20 points): Required sections, contact info, dates
    - File Compatibility (10 points): File format and size

    Total Score: 0-100 points
    - 80-100: Excellent (Green) - Highly likely to pass ATS
    - 60-79: Good (Yellow) - Will likely pass with minor improvements
    - 0-59: Needs Improvement (Red) - Requires significant changes

    Target Accuracy: ±5% of real ATS systems
    """

    # Score thresholds for color coding
    THRESHOLD_EXCELLENT = 80
    THRESHOLD_GOOD = 60

    # Minimum score for auto-retry
    MIN_ACCEPTABLE_SCORE = 80

    def __init__(self):
        """Initialize the ATS scorer with all components"""
        self.keyword_matcher = KeywordMatcher()
        self.format_validator = FormatValidator()
        self.section_analyzer = SectionAnalyzer()

    def score_resume(
        self,
        resume_content: str,
        job_keywords: List[str] = None,
        required_skills: List[str] = None,
        file_format: str = "pdf",
        file_size_bytes: int = None
    ) -> Dict:
        """
        Score resume for ATS compatibility.

        Args:
            resume_content: Full text content of the resume
            job_keywords: List of keywords from job description
            required_skills: List of required skills from job posting
            file_format: File format (pdf, docx, txt)
            file_size_bytes: File size in bytes (optional)

        Returns:
            Dict containing:
                - score: Overall ATS score (0-100)
                - grade: Letter grade (A+, A, B+, B, C+, C, D, F)
                - color: Color coding (green, yellow, red)
                - category_scores: Breakdown by category
                - checks: Detailed results of all checks
                - summary: Overall assessment
                - top_suggestions: Top 5 actionable improvements
                - pass_probability: Estimated probability of passing ATS (%)
                - processing_time: Time taken to score (seconds)
        """
        start_time = time.time()

        # Initialize results structure
        category_scores = {
            'content': {'score': 0, 'max': 40, 'checks': {}},
            'format': {'score': 0, 'max': 30, 'checks': {}},
            'structure': {'score': 0, 'max': 20, 'checks': {}},
            'compatibility': {'score': 0, 'max': 10, 'checks': {}}
        }

        all_suggestions = []

        # ==================== CONTENT CHECKS (40 points) ====================

        # 1. Keyword Matching (15 points)
        if job_keywords:
            keyword_analysis = self.keyword_matcher.analyze_keywords(
                resume_content,
                job_keywords,
                required_skills
            )
            category_scores['content']['checks']['keyword_match'] = {
                'score': keyword_analysis['match_score'],
                'max': 15,
                'status': self._get_status(keyword_analysis['match_score'], 15),
                'message': f"{keyword_analysis['match_percentage']:.0f}% of job keywords matched",
                'details': keyword_analysis,
                'suggestions': self._generate_keyword_suggestions(keyword_analysis)
            }
            all_suggestions.extend(self._generate_keyword_suggestions(keyword_analysis))
        else:
            # No job keywords provided, give benefit of doubt
            category_scores['content']['checks']['keyword_match'] = {
                'score': 12,
                'max': 15,
                'status': 'good',
                'message': 'No job keywords provided for comparison',
                'details': {},
                'suggestions': []
            }

        # 2. Keyword Density (10 points)
        if job_keywords:
            density_score = keyword_analysis['density_score']
            category_scores['content']['checks']['keyword_density'] = {
                'score': density_score,
                'max': 10,
                'status': self._get_status(density_score, 10),
                'message': f"Keyword density: {keyword_analysis['keyword_density']:.1f}% (optimal: 2-4%)",
                'details': keyword_analysis,
                'suggestions': self._generate_density_suggestions(keyword_analysis)
            }
            all_suggestions.extend(self._generate_density_suggestions(keyword_analysis))
        else:
            category_scores['content']['checks']['keyword_density'] = {
                'score': 8,
                'max': 10,
                'status': 'good',
                'message': 'Keyword density not assessed (no job keywords)',
                'details': {},
                'suggestions': []
            }

        # 3. Quantifiable Results (5 points)
        metrics_analysis = self.keyword_matcher.analyze_quantifiable_results(resume_content)
        category_scores['content']['checks']['quantifiable_results'] = {
            'score': metrics_analysis['score'],
            'max': 5,
            'status': self._get_status(metrics_analysis['score'], 5),
            'message': f"{metrics_analysis['count']} quantifiable metrics found",
            'details': metrics_analysis,
            'suggestions': self._generate_metrics_suggestions(metrics_analysis)
        }
        all_suggestions.extend(self._generate_metrics_suggestions(metrics_analysis))

        # 4. Action Verbs (5 points)
        verb_analysis = self.keyword_matcher.analyze_action_verbs(resume_content)
        category_scores['content']['checks']['action_verbs'] = {
            'score': verb_analysis['score'],
            'max': 5,
            'status': self._get_status(verb_analysis['score'], 5),
            'message': f"{verb_analysis['count']} strong action verbs used",
            'details': verb_analysis,
            'suggestions': self._generate_verb_suggestions(verb_analysis)
        }
        all_suggestions.extend(self._generate_verb_suggestions(verb_analysis))

        # 5. Skills Section (5 points)
        section_analysis = self.section_analyzer.analyze_sections(resume_content)
        skills_check = section_analysis['checks'].get('skills', {})
        skill_score = min(5, skills_check.get('score', 0) * 5)  # Scale bonus score to 5 points
        category_scores['content']['checks']['skills_section'] = {
            'score': skill_score,
            'max': 5,
            'status': self._get_status(skill_score, 5),
            'message': skills_check.get('message', 'Skills section assessment'),
            'details': skills_check,
            'suggestions': ['Add a dedicated SKILLS section with 15-20 relevant skills'] if skill_score < 4 else []
        }
        if skill_score < 4:
            all_suggestions.append('Add a dedicated SKILLS section with 15-20 relevant skills')

        # Calculate content total
        category_scores['content']['score'] = sum(
            check['score'] for check in category_scores['content']['checks'].values()
        )

        # ==================== FORMAT CHECKS (30 points) ====================

        format_results = self.format_validator.validate_format(resume_content, file_format)
        category_scores['format']['checks'] = format_results['checks']
        category_scores['format']['score'] = format_results['total_score']
        all_suggestions.extend(format_results['suggestions'])

        # ==================== STRUCTURE CHECKS (20 points) ====================

        category_scores['structure']['checks'] = section_analysis['checks']
        category_scores['structure']['score'] = section_analysis['total_score']
        all_suggestions.extend(section_analysis['suggestions'])

        # ==================== COMPATIBILITY CHECKS (10 points) ====================

        file_validation = self.format_validator.validate_file_format(file_format, file_size_bytes)
        category_scores['compatibility']['checks'] = file_validation['checks']
        category_scores['compatibility']['score'] = file_validation['total_score']
        all_suggestions.extend(file_validation['suggestions'])

        # ==================== CALCULATE FINAL SCORE ====================

        total_score = sum(cat['score'] for cat in category_scores.values())
        total_score = min(100, max(0, total_score))  # Clamp to 0-100

        # Calculate grade and color
        grade = self._calculate_grade(total_score)
        color = self._get_color(total_score)

        # Estimate pass probability
        pass_probability = self._estimate_pass_probability(total_score, category_scores)

        # Generate summary
        summary = self._generate_summary(total_score, category_scores)

        # Select top 5 most impactful suggestions
        top_suggestions = self._prioritize_suggestions(all_suggestions, category_scores)[:5]

        processing_time = time.time() - start_time

        return {
            'score': round(total_score, 1),
            'grade': grade,
            'color': color,
            'category_scores': category_scores,
            'summary': summary,
            'top_suggestions': top_suggestions,
            'pass_probability': round(pass_probability, 1),
            'processing_time': round(processing_time, 3),
            'timestamp': time.time(),
            'needs_improvement': total_score < self.MIN_ACCEPTABLE_SCORE
        }

    def _get_status(self, score: float, max_score: float) -> str:
        """Determine status based on score percentage"""
        percentage = (score / max_score) * 100 if max_score > 0 else 0

        if percentage >= 90:
            return 'excellent'
        elif percentage >= 75:
            return 'good'
        elif percentage >= 60:
            return 'acceptable'
        elif percentage >= 40:
            return 'needs_improvement'
        else:
            return 'poor'

    def _get_color(self, score: float) -> str:
        """Get color coding for score"""
        if score >= self.THRESHOLD_EXCELLENT:
            return 'green'
        elif score >= self.THRESHOLD_GOOD:
            return 'yellow'
        else:
            return 'red'

    def _calculate_grade(self, score: float) -> str:
        """Calculate letter grade from score"""
        if score >= 97:
            return 'A+'
        elif score >= 93:
            return 'A'
        elif score >= 90:
            return 'A-'
        elif score >= 87:
            return 'B+'
        elif score >= 83:
            return 'B'
        elif score >= 80:
            return 'B-'
        elif score >= 77:
            return 'C+'
        elif score >= 73:
            return 'C'
        elif score >= 70:
            return 'C-'
        elif score >= 67:
            return 'D+'
        elif score >= 63:
            return 'D'
        elif score >= 60:
            return 'D-'
        else:
            return 'F'

    def _generate_summary(self, score: float, category_scores: Dict) -> str:
        """Generate human-readable summary of ATS compatibility"""
        if score >= 90:
            base = "Excellent! Your resume is highly optimized for ATS systems."
        elif score >= 80:
            base = "Very Good! Your resume is well-optimized for ATS systems with minor improvements needed."
        elif score >= 70:
            base = "Good. Your resume is ATS-compatible but has room for improvement."
        elif score >= 60:
            base = "Acceptable. Your resume may pass ATS systems but needs several improvements."
        else:
            base = "Needs Improvement. Your resume requires significant changes to pass ATS systems."

        # Identify weakest category
        weakest_category = min(
            category_scores.items(),
            key=lambda x: (x[1]['score'] / x[1]['max']) * 100
        )[0]

        weakness_map = {
            'content': 'Focus on improving keyword matching and content quality.',
            'format': 'Focus on formatting - remove tables, images, and complex layouts.',
            'structure': 'Focus on structure - ensure all required sections are present.',
            'compatibility': 'Focus on file format and size optimization.'
        }

        return f"{base} {weakness_map.get(weakest_category, '')}"

    def _estimate_pass_probability(self, score: float, category_scores: Dict) -> float:
        """
        Estimate probability of passing typical ATS systems.

        Based on industry research:
        - 90+ score: ~95% pass rate
        - 80-89 score: ~85% pass rate
        - 70-79 score: ~70% pass rate
        - 60-69 score: ~50% pass rate
        - <60 score: ~25% pass rate

        Adjusted based on critical failures.
        """
        # Base probability from score
        if score >= 90:
            base_prob = 95
        elif score >= 80:
            base_prob = 85
        elif score >= 70:
            base_prob = 70
        elif score >= 60:
            base_prob = 50
        else:
            base_prob = 25

        # Adjust for critical failures
        content_percentage = (category_scores['content']['score'] / category_scores['content']['max']) * 100
        format_percentage = (category_scores['format']['score'] / category_scores['format']['max']) * 100

        # Critical: content score below 60%
        if content_percentage < 60:
            base_prob *= 0.8

        # Critical: format score below 70%
        if format_percentage < 70:
            base_prob *= 0.85

        return min(99, max(1, base_prob))

    def _generate_keyword_suggestions(self, analysis: Dict) -> List[str]:
        """Generate suggestions for keyword optimization"""
        suggestions = []

        if analysis['match_percentage'] < 80:
            missing = analysis.get('missing_keywords', [])
            if missing:
                top_missing = missing[:5]
                suggestions.append(f"Add missing keywords: {', '.join(top_missing)}")

        if analysis['match_percentage'] < 60:
            suggestions.append("Critically low keyword match. Review job description and add relevant keywords.")

        # Check distribution
        dist = analysis.get('distribution', {})
        if not dist.get('well_distributed', False):
            suggestions.append("Distribute keywords across Summary, Skills, and Experience sections")

        return suggestions

    def _generate_density_suggestions(self, analysis: Dict) -> List[str]:
        """Generate suggestions for keyword density"""
        suggestions = []
        density = analysis.get('keyword_density', 0)

        if density < 1.5:
            suggestions.append(f"Keyword density too low ({density:.1f}%). Aim for 2-4% by adding more relevant keywords.")
        elif density > 6:
            suggestions.append(f"Keyword density too high ({density:.1f}%). Reduce keyword stuffing - aim for 2-4%.")
        elif density < 2:
            suggestions.append(f"Increase keyword density slightly (current: {density:.1f}%, optimal: 2-4%)")
        elif density > 4:
            suggestions.append(f"Reduce keyword density slightly (current: {density:.1f}%, optimal: 2-4%)")

        return suggestions

    def _generate_metrics_suggestions(self, analysis: Dict) -> List[str]:
        """Generate suggestions for quantifiable metrics"""
        suggestions = []
        count = analysis.get('count', 0)

        if count < 3:
            suggestions.append(f"Add more quantifiable results (current: {count}, recommended: 8+)")
            suggestions.append("Include metrics like: percentages, dollar amounts, team sizes, time saved")
        elif count < 6:
            suggestions.append(f"Add {8 - count} more quantifiable metrics to strengthen your resume")

        return suggestions

    def _generate_verb_suggestions(self, analysis: Dict) -> List[str]:
        """Generate suggestions for action verbs"""
        suggestions = []
        count = analysis.get('count', 0)

        if count < 5:
            suggestions.append(f"Use more strong action verbs (current: {count}, recommended: 10+)")
            suggestions.append("Examples: achieved, led, developed, optimized, implemented, delivered")
        elif count < 8:
            suggestions.append(f"Add {10 - count} more action verbs to make your resume more impactful")

        return suggestions

    def _prioritize_suggestions(self, suggestions: List[str], category_scores: Dict) -> List[str]:
        """
        Prioritize suggestions based on impact.

        Priority order:
        1. Critical failures (missing required sections, very low scores)
        2. High-impact improvements (keyword matching, format issues)
        3. Medium-impact improvements (density, metrics)
        4. Low-impact improvements (minor formatting)
        """
        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for sugg in suggestions:
            if sugg not in seen:
                seen.add(sugg)
                unique_suggestions.append(sugg)

        # Simple prioritization: critical keywords first
        priority_keywords = [
            'missing keywords',
            'missing sections',
            'missing contact',
            'remove tables',
            'remove images',
            'file format',
            'critically low',
            'density too',
        ]

        prioritized = []
        remaining = []

        for sugg in unique_suggestions:
            is_priority = any(keyword in sugg.lower() for keyword in priority_keywords)
            if is_priority:
                prioritized.append(sugg)
            else:
                remaining.append(sugg)

        return prioritized + remaining

    def quick_check(self, resume_content: str) -> Dict:
        """
        Quick ATS compatibility check without detailed analysis.

        Returns basic score and pass/fail status in <0.5 seconds.
        Useful for real-time feedback during resume editing.
        """
        start_time = time.time()

        # Quick checks
        has_email = '@' in resume_content
        has_phone = bool(self.section_analyzer._check_contact_info(resume_content)['fields']['phone'])
        has_experience = 'experience' in resume_content.lower()
        has_education = 'education' in resume_content.lower()
        word_count = len(resume_content.split())

        # Simple scoring
        score = 0
        if has_email:
            score += 10
        if has_phone:
            score += 10
        if has_experience:
            score += 30
        if has_education:
            score += 20
        if word_count >= 300:
            score += 20
        if word_count >= 500:
            score += 10

        processing_time = time.time() - start_time

        return {
            'score': min(100, score),
            'color': self._get_color(score),
            'passed': score >= 60,
            'processing_time': round(processing_time, 3),
            'quick_check': True
        }


# Convenience function for quick scoring
def score_resume(resume_content: str, job_keywords: List[str] = None, **kwargs) -> Dict:
    """
    Convenience function to score a resume.

    Args:
        resume_content: Full text of the resume
        job_keywords: Optional list of keywords from job description
        **kwargs: Additional arguments (required_skills, file_format, file_size_bytes)

    Returns:
        Dict with comprehensive ATS scoring results
    """
    scorer = ATSScorer()
    return scorer.score_resume(resume_content, job_keywords, **kwargs)
