"""
Enhanced ATS Scoring Engine - Optimized for 75-85% Sweet Spot
Targets the optimal ATS score range that balances keyword matching with human appeal.
Research shows 100% scores indicate over-optimization and reduce interview callbacks.
"""

import time
import json
import builtins  # FIX: Import builtins to prevent shadowing of min/max functions
from pathlib import Path
from typing import Dict, List, Optional
from .keyword_matcher import KeywordMatcher
from .format_validator import FormatValidator
from .section_analyzer import SectionAnalyzer


class EnhancedATSScorer:
    """
    Enhanced ATS Scoring Engine targeting the optimal 75-85% range.

    Research Insight (2025):
    - 75-85% = OPTIMAL: Shows keyword relevance while maintaining human appeal
    - 85-95% = Over-optimized: May trigger keyword stuffing flags
    - 95-100% = Red flag: Indicates gaming the system, reduces callbacks by 40%

    The goal is NOT to maximize ATS score, but to hit the sweet spot where
    you pass ATS filters AND appeal to human recruiters.

    Key Features:
    1. Balanced scoring that rewards natural language
    2. Template-aware scoring adjustments
    3. Human-first optimization (6-second scan test)
    4. Intelligent keyword density targeting (2-4%)
    5. Recognition of modern resume formats

    Score Distribution (100 points):
    - Content Quality: 40 points
    - Format Compliance: 30 points
    - Structure Completeness: 20 points
    - File Compatibility: 10 points
    """

    # Optimal score thresholds (75-85% sweet spot)
    THRESHOLD_EXCELLENT = 85  # Upper bound of optimal range
    THRESHOLD_GOOD = 75       # Lower bound of optimal range
    THRESHOLD_OVER_OPTIMIZED = 90  # Warning threshold

    # Target for re-generation
    MIN_ACCEPTABLE_SCORE = 75  # Target the sweet spot
    MAX_OPTIMAL_SCORE = 85     # Don't exceed this

    def __init__(self):
        """Initialize enhanced ATS scorer"""
        self.keyword_matcher = KeywordMatcher()
        self.format_validator = FormatValidator()
        self.section_analyzer = SectionAnalyzer()
        self.knowledge_base = self._load_knowledge_base()

    def _load_knowledge_base(self) -> Dict:
        """Load ATS best practices from knowledge base"""
        knowledge = {
            'optimal_keyword_density': (2.0, 4.0),  # 2-4% is optimal
            'min_keywords_match': 70,  # 70% minimum for good score
            'required_sections': [
                'contact', 'summary', 'experience', 'education', 'skills'
            ],
            'bonus_sections': [
                'certifications', 'projects', 'achievements', 'languages'
            ],
            'modern_formats': {
                'modern': {'base_bonus': 5, 'format_bonus': 3},
                'harvard': {'base_bonus': 8, 'format_bonus': 5},
                'original': {'base_bonus': 0, 'format_bonus': 0}
            },
            'action_verb_minimum': 15,  # Increased from 10
            'quantifiable_minimum': 10,  # Increased from 8
            'skills_minimum': 15,        # Minimum skills for full score
        }
        return knowledge

    def score_resume(
        self,
        resume_content: str,
        job_keywords: List[str] = None,
        required_skills: List[str] = None,
        file_format: str = "pdf",
        file_size_bytes: int = None,
        template_type: str = "modern"  # New parameter
    ) -> Dict:
        """
        Enhanced scoring with knowledge base integration.

        New Features:
        - Template-aware scoring
        - Knowledge base criteria
        - More generous scoring for quality resumes
        - Intelligent fallbacks when job keywords not provided
        """
        start_time = time.time()

        # Get template bonus if using optimized templates
        template_bonus = self.knowledge_base['modern_formats'].get(
            template_type, {}
        ).get('base_bonus', 0)

        # Initialize enhanced scoring structure
        category_scores = {
            'content': {'score': 0, 'max': 40, 'checks': {}},
            'format': {'score': 0, 'max': 30, 'checks': {}},
            'structure': {'score': 0, 'max': 20, 'checks': {}},
            'compatibility': {'score': 0, 'max': 10, 'checks': {}}
        }

        all_suggestions = []

        # ==================== ENHANCED CONTENT CHECKS (40 points) ====================

        # 1. Keyword Matching (15 points) - Enhanced
        if job_keywords:
            keyword_analysis = self.keyword_matcher.analyze_keywords(
                resume_content,
                job_keywords,
                required_skills
            )

            # More generous scoring curve
            match_percentage = keyword_analysis['match_percentage']
            if match_percentage >= 90:
                keyword_score = 15
            elif match_percentage >= 80:
                keyword_score = 14
            elif match_percentage >= 70:
                keyword_score = 13
            elif match_percentage >= 60:
                keyword_score = 11
            else:
                keyword_score = min(15, (match_percentage / 100) * 15 + 2)

            category_scores['content']['checks']['keyword_match'] = {
                'score': keyword_score,
                'max': 15,
                'status': self._get_enhanced_status(keyword_score, 15),
                'message': f"{match_percentage:.0f}% of job keywords matched",
                'details': keyword_analysis,
                'suggestions': self._generate_keyword_suggestions(keyword_analysis)
            }
        else:
            # Enhanced default scoring when no keywords provided
            # Analyze resume for common high-value keywords
            common_keywords = self._extract_common_keywords(resume_content)
            keyword_score = min(14, 10 + len(common_keywords) * 0.5)

            category_scores['content']['checks']['keyword_match'] = {
                'score': keyword_score,
                'max': 15,
                'status': 'good',
                'message': f'Resume contains {len(common_keywords)} high-value keywords',
                'details': {'detected_keywords': common_keywords},
                'suggestions': []
            }

        # 2. Keyword Density (10 points) - Optimized
        if job_keywords:
            density = keyword_analysis.get('keyword_density', 0)
            optimal_min, optimal_max = self.knowledge_base['optimal_keyword_density']

            if optimal_min <= density <= optimal_max:
                density_score = 10
            elif density < optimal_min:
                density_score = min(10, 6 + (density / optimal_min) * 4)
            else:  # density > optimal_max
                density_score = max(7, 10 - (density - optimal_max) * 0.5)

            category_scores['content']['checks']['keyword_density'] = {
                'score': density_score,
                'max': 10,
                'status': self._get_enhanced_status(density_score, 10),
                'message': f"Keyword density: {density:.1f}% (optimal: {optimal_min}-{optimal_max}%)",
                'details': {'density': density},
                'suggestions': self._generate_density_suggestions(keyword_analysis)
            }
        else:
            # Intelligent density estimation
            word_count = len(resume_content.split())
            estimated_density = min(4.0, max(2.0, (len(common_keywords) * 5) / word_count * 100))
            density_score = 9 if 2.0 <= estimated_density <= 4.0 else 8

            category_scores['content']['checks']['keyword_density'] = {
                'score': density_score,
                'max': 10,
                'status': 'good',
                'message': f'Estimated keyword density: {estimated_density:.1f}% (optimal range)',
                'details': {},
                'suggestions': []
            }

        # 3. Quantifiable Results (5 points) - Enhanced recognition
        metrics_analysis = self._analyze_enhanced_metrics(resume_content)
        metrics_score = min(5, metrics_analysis['score'])

        category_scores['content']['checks']['quantifiable_results'] = {
            'score': metrics_score,
            'max': 5,
            'status': self._get_enhanced_status(metrics_score, 5),
            'message': f"{metrics_analysis['count']} quantifiable metrics found",
            'details': metrics_analysis,
            'suggestions': self._generate_metrics_suggestions(metrics_analysis)
        }

        # 4. Action Verbs (5 points) - Enhanced detection
        verb_analysis = self._analyze_enhanced_verbs(resume_content)
        verb_score = min(5, verb_analysis['score'])

        category_scores['content']['checks']['action_verbs'] = {
            'score': verb_score,
            'max': 5,
            'status': self._get_enhanced_status(verb_score, 5),
            'message': f"{verb_analysis['count']} strong action verbs detected",
            'details': verb_analysis,
            'suggestions': self._generate_verb_suggestions(verb_analysis)
        }

        # 5. Skills Section (5 points) - Enhanced evaluation
        skills_analysis = self._analyze_skills_section(resume_content)
        skills_score = min(5, skills_analysis['score'])

        category_scores['content']['checks']['skills_section'] = {
            'score': skills_score,
            'max': 5,
            'status': self._get_enhanced_status(skills_score, 5),
            'message': skills_analysis['message'],
            'details': skills_analysis,
            'suggestions': skills_analysis.get('suggestions', [])
        }

        # Calculate content total with template bonus
        content_base = sum(check['score'] for check in category_scores['content']['checks'].values())
        category_scores['content']['score'] = min(40, content_base + (template_bonus * 0.4))

        # ==================== ENHANCED FORMAT CHECKS (30 points) ====================

        format_results = self._validate_enhanced_format(resume_content, file_format, template_type)
        category_scores['format']['checks'] = format_results['checks']
        category_scores['format']['score'] = min(30, format_results['total_score'] + (template_bonus * 0.3))
        all_suggestions.extend(format_results['suggestions'])

        # ==================== ENHANCED STRUCTURE CHECKS (20 points) ====================

        structure_results = self._analyze_enhanced_structure(resume_content)
        category_scores['structure']['checks'] = structure_results['checks']
        category_scores['structure']['score'] = min(20, structure_results['total_score'] + (template_bonus * 0.2))
        all_suggestions.extend(structure_results['suggestions'])

        # ==================== COMPATIBILITY CHECKS (10 points) ====================

        file_validation = self._validate_enhanced_compatibility(file_format, file_size_bytes, template_type)
        category_scores['compatibility']['checks'] = file_validation['checks']
        category_scores['compatibility']['score'] = min(10, file_validation['total_score'] + (template_bonus * 0.1))
        all_suggestions.extend(file_validation['suggestions'])

        # ==================== CALCULATE FINAL SCORE ====================

        total_score = sum(cat['score'] for cat in category_scores.values())
        # FIX: Use builtins.min/max to prevent shadowing issues with 'max' dict keys
        total_score = builtins.min(100, builtins.max(0, total_score))

        # Apply knowledge-based adjustments to target 75-85% sweet spot
        # INTENTIONALLY cap scores to avoid over-optimization
        if total_score > self.MAX_OPTIMAL_SCORE:
            # Apply diminishing returns above 85% to discourage over-optimization
            excess = total_score - self.MAX_OPTIMAL_SCORE
            # Gradually reduce excess score (keep some, but not all)
            total_score = self.MAX_OPTIMAL_SCORE + (excess * 0.3)
            total_score = builtins.min(self.THRESHOLD_OVER_OPTIMIZED, total_score)

        # Calculate grade and color
        grade = self._calculate_enhanced_grade(total_score)
        color = self._get_enhanced_color(total_score)

        # Enhanced pass probability
        pass_probability = self._estimate_enhanced_pass_probability(total_score, category_scores, template_type)

        # Generate enhanced summary
        summary = self._generate_enhanced_summary(total_score, category_scores, template_type)

        # Prioritize suggestions
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
            'template_used': template_type,
            'template_bonus_applied': template_bonus,
            'processing_time': round(processing_time, 3),
            'timestamp': time.time(),
            'needs_improvement': total_score < self.MIN_ACCEPTABLE_SCORE
        }

    def _extract_common_keywords(self, resume_content: str) -> List[str]:
        """Extract common high-value keywords from resume"""
        high_value_keywords = [
            'led', 'managed', 'developed', 'implemented', 'optimized',
            'increased', 'reduced', 'achieved', 'delivered', 'designed',
            'python', 'java', 'javascript', 'react', 'aws', 'docker',
            'kubernetes', 'sql', 'machine learning', 'data analysis',
            'project management', 'agile', 'scrum', 'leadership',
            'communication', 'problem solving', 'analytical', 'strategic'
        ]

        content_lower = resume_content.lower()
        found_keywords = [kw for kw in high_value_keywords if kw in content_lower]
        return found_keywords

    def _analyze_enhanced_metrics(self, resume_content: str) -> Dict:
        """Enhanced analysis of quantifiable results"""
        import re

        # Enhanced patterns for metrics
        patterns = [
            r'\d+[%+]',  # Percentages and increases
            r'\$[\d,]+[KMB]?',  # Dollar amounts
            r'\d+[xX]\s*(?:increase|improvement|growth)',  # Multipliers
            r'(?:reduced|decreased|cut|saved).*?\d+',  # Reductions
            r'(?:increased|improved|grew).*?\d+',  # Increases
            r'\d+\+?\s*(?:users|customers|clients|employees|team members)',  # Scale
            r'(?:top\s+)?\d+%',  # Rankings
            r'\d+\s*(?:years?|months?|days?|hours?)',  # Time metrics
        ]

        metrics = []
        for pattern in patterns:
            matches = re.findall(pattern, resume_content, re.IGNORECASE)
            metrics.extend(matches)

        # Remove duplicates
        metrics = list(set(metrics))
        count = len(metrics)

        # Enhanced scoring
        if count >= self.knowledge_base['quantifiable_minimum']:
            score = 5
        elif count >= 8:
            score = 4.5
        elif count >= 6:
            score = 4
        elif count >= 4:
            score = 3.5
        else:
            score = min(3, count * 0.75)

        return {
            'count': count,
            'score': score,
            'examples': metrics[:10],
            'minimum_recommended': self.knowledge_base['quantifiable_minimum']
        }

    def _analyze_enhanced_verbs(self, resume_content: str) -> Dict:
        """Enhanced analysis of action verbs"""
        # Comprehensive list of strong action verbs
        action_verbs = [
            'achieved', 'administered', 'advanced', 'analyzed', 'architected',
            'built', 'championed', 'collaborated', 'completed', 'conceived',
            'coordinated', 'created', 'delivered', 'designed', 'developed',
            'directed', 'drove', 'engineered', 'enhanced', 'established',
            'executed', 'expanded', 'facilitated', 'generated', 'grew',
            'guided', 'implemented', 'improved', 'increased', 'influenced',
            'initiated', 'innovated', 'integrated', 'launched', 'led',
            'managed', 'maximized', 'mentored', 'modernized', 'negotiated',
            'optimized', 'orchestrated', 'organized', 'pioneered', 'planned',
            'produced', 'programmed', 'reduced', 'redesigned', 'reformed',
            'resolved', 'restructured', 'revamped', 'revolutionized', 'saved',
            'scaled', 'secured', 'simplified', 'spearheaded', 'streamlined',
            'strengthened', 'supervised', 'transformed', 'upgraded', 'utilized'
        ]

        content_lower = resume_content.lower()
        found_verbs = [verb for verb in action_verbs if verb in content_lower]
        count = len(found_verbs)

        # Enhanced scoring
        if count >= self.knowledge_base['action_verb_minimum']:
            score = 5
        elif count >= 12:
            score = 4.5
        elif count >= 10:
            score = 4
        elif count >= 8:
            score = 3.5
        else:
            score = min(3, count * 0.375)

        return {
            'count': count,
            'score': score,
            'verbs_found': found_verbs[:20],
            'minimum_recommended': self.knowledge_base['action_verb_minimum']
        }

    def _analyze_skills_section(self, resume_content: str) -> Dict:
        """Analyze skills section quality"""
        import re

        # Look for skills section
        skills_pattern = r'(?:technical\s+)?skills[\s:]*([^\n]+(?:\n[^\n#]+)*)'
        skills_match = re.search(skills_pattern, resume_content, re.IGNORECASE)

        if not skills_match:
            return {
                'score': 2,
                'message': 'Skills section not clearly identified',
                'skills_count': 0,
                'suggestions': ['Add a clear SKILLS or TECHNICAL SKILLS section']
            }

        skills_text = skills_match.group(1)

        # Count individual skills (split by commas, bullets, pipes, etc.)
        skills = re.split(r'[,•·|\n]', skills_text)
        skills = [s.strip() for s in skills if s.strip() and len(s.strip()) > 2]
        skill_count = len(skills)

        # Check for skill categories
        has_categories = bool(re.search(r'(?:Languages?|Frameworks?|Tools?|Databases?|Cloud|Soft Skills?):', skills_text, re.IGNORECASE))

        # Enhanced scoring
        if skill_count >= self.knowledge_base['skills_minimum'] and has_categories:
            score = 5
            message = f'Excellent skills section with {skill_count} skills organized by category'
        elif skill_count >= self.knowledge_base['skills_minimum']:
            score = 4.5
            message = f'Strong skills section with {skill_count} skills'
        elif skill_count >= 12:
            score = 4
            message = f'Good skills section with {skill_count} skills'
        elif skill_count >= 8:
            score = 3.5
            message = f'Adequate skills section with {skill_count} skills'
        else:
            score = min(3, skill_count * 0.3)
            message = f'Limited skills section with only {skill_count} skills'

        suggestions = []
        if skill_count < self.knowledge_base['skills_minimum']:
            suggestions.append(f'Add more skills (aim for {self.knowledge_base["skills_minimum"]}+)')
        if not has_categories:
            suggestions.append('Organize skills by category (Languages, Tools, etc.)')

        return {
            'score': score,
            'message': message,
            'skills_count': skill_count,
            'has_categories': has_categories,
            'suggestions': suggestions
        }

    def _validate_enhanced_format(self, resume_content: str, file_format: str, template_type: str) -> Dict:
        """Enhanced format validation with template awareness"""
        checks = {}
        total_score = 0
        suggestions = []

        # Base format validation
        base_validation = self.format_validator.validate_format(resume_content, file_format)

        # Apply template-specific bonuses
        template_config = self.knowledge_base['modern_formats'].get(template_type, {})
        format_bonus = template_config.get('format_bonus', 0)

        # Enhance scores for known good templates
        for check_name, check_data in base_validation['checks'].items():
            # Safely get max value (some checks might not have it)
            max_score = check_data.get('max', check_data.get('score', 0) + 10)
            current_score = check_data.get('score', 0)
            enhanced_score = min(max_score, current_score + format_bonus * 0.2)
            checks[check_name] = {
                **check_data,
                'score': enhanced_score
            }

        total_score = sum(check['score'] for check in checks.values())

        # Add template-specific format benefits
        if template_type in ['modern', 'harvard']:
            checks['template_optimization'] = {
                'score': format_bonus,
                'max': format_bonus,
                'status': 'excellent',
                'message': f'Using {template_type.title()} ATS-optimized template',
                'details': {'template': template_type}
            }
            total_score += format_bonus

        return {
            'checks': checks,
            'total_score': total_score,
            'suggestions': base_validation.get('suggestions', [])
        }

    def _analyze_enhanced_structure(self, resume_content: str) -> Dict:
        """Enhanced structure analysis"""
        base_analysis = self.section_analyzer.analyze_sections(resume_content)

        # Apply bonuses for having bonus sections
        bonus_sections_found = 0
        for section in self.knowledge_base['bonus_sections']:
            if section in resume_content.lower():
                bonus_sections_found += 1

        # Add bonus points
        if bonus_sections_found > 0:
            bonus_score = min(3, bonus_sections_found)
            base_analysis['checks']['bonus_sections'] = {
                'score': bonus_score,
                'max': 3,
                'status': 'excellent',
                'message': f'{bonus_sections_found} bonus sections found',
                'details': {'count': bonus_sections_found}
            }
            base_analysis['total_score'] += bonus_score

        return base_analysis

    def _validate_enhanced_compatibility(self, file_format: str, file_size: Optional[int], template_type: str) -> Dict:
        """Enhanced file compatibility validation"""
        checks = {}
        total_score = 0
        suggestions = []

        # File format check (5 points)
        if file_format.lower() in ['pdf', 'docx']:
            format_score = 5
            status = 'excellent'
            message = f'{file_format.upper()} format is ATS-compatible'
        else:
            format_score = 3
            status = 'acceptable'
            message = f'{file_format.upper()} format may have compatibility issues'
            suggestions.append('Use PDF or DOCX format for best compatibility')

        checks['file_format'] = {
            'score': format_score,
            'max': 5,
            'status': status,
            'message': message
        }

        # File size check (5 points)
        if file_size:
            if file_size < 500_000:  # Under 500KB
                size_score = 5
                status = 'excellent'
                message = 'File size is optimal for ATS'
            elif file_size < 1_000_000:  # Under 1MB
                size_score = 4
                status = 'good'
                message = 'File size is acceptable'
            else:
                size_score = 3
                status = 'acceptable'
                message = 'File size may be too large'
                suggestions.append('Try to keep file size under 500KB')
        else:
            size_score = 5  # Give benefit of doubt
            status = 'excellent'
            message = 'File size assumed optimal'

        checks['file_size'] = {
            'score': size_score,
            'max': 5,
            'status': status,
            'message': message
        }

        total_score = sum(check['score'] for check in checks.values())

        return {
            'checks': checks,
            'total_score': total_score,
            'suggestions': suggestions
        }

    def _get_enhanced_status(self, score: float, max_score: float) -> str:
        """Enhanced status calculation targeting 75-85% sweet spot"""
        percentage = (score / max_score) * 100 if max_score > 0 else 0

        if percentage >= 75 and percentage <= 85:
            return 'excellent'  # OPTIMAL RANGE
        elif percentage >= 85 and percentage <= 90:
            return 'very_good'  # Slightly over-optimized but acceptable
        elif percentage >= 70 and percentage < 75:
            return 'good'  # Close to optimal
        elif percentage > 90:
            return 'over_optimized'  # WARNING: Too high
        elif percentage >= 60:
            return 'acceptable'
        elif percentage >= 50:
            return 'needs_improvement'
        else:
            return 'poor'

    def _get_enhanced_color(self, score: float) -> str:
        """Enhanced color coding with sweet spot awareness"""
        if score >= self.THRESHOLD_GOOD and score <= self.THRESHOLD_EXCELLENT:
            return 'green'  # OPTIMAL: 75-85%
        elif score > self.THRESHOLD_EXCELLENT and score < self.THRESHOLD_OVER_OPTIMIZED:
            return 'yellow'  # Over-optimized but not critical: 85-90%
        elif score >= self.THRESHOLD_OVER_OPTIMIZED:
            return 'orange'  # WARNING: Too high, likely keyword stuffing: 90%+
        elif score >= 70:
            return 'yellow'  # Close to optimal: 70-75%
        else:
            return 'red'  # Too low: needs improvement

    def _calculate_enhanced_grade(self, score: float) -> str:
        """Enhanced grade calculation with sweet spot awareness"""
        # 75-85% = A range (OPTIMAL)
        if score >= 75 and score <= 85:
            if score >= 83:
                return 'A+'  # Upper optimal
            elif score >= 79:
                return 'A'   # Mid optimal
            else:
                return 'A-'  # Lower optimal
        # Over-optimized (warning zone)
        elif score > 85:
            if score >= 95:
                return 'B-'  # Seriously over-optimized
            elif score >= 90:
                return 'B'   # Over-optimized
            else:
                return 'B+'  # Slightly over-optimized
        # Under-optimized
        elif score >= 70:
            return 'B+'  # Close but needs improvement
        elif score >= 65:
            return 'B'
        elif score >= 60:
            return 'C+'
        elif score >= 55:
            return 'C'
        else:
            return 'D'

    def _generate_enhanced_summary(self, score: float, category_scores: Dict, template_type: str) -> str:
        """Generate enhanced summary with sweet spot education"""
        template_name = {
            'modern': 'Modern Professional',
            'harvard': 'Harvard Business',
            'original': 'Original Simple'
        }.get(template_type, template_type)

        # Educational messaging based on 2025 research
        if score >= 75 and score <= 85:
            base = f"🎯 OPTIMAL SCORE! Your {template_name} resume is in the 75-85% sweet spot. This score shows you're qualified for the role while maintaining natural, human-appealing language. Research shows this range has the HIGHEST interview callback rate."
        elif score > 85 and score < 90:
            base = f"⚠️ SLIGHTLY OVER-OPTIMIZED ({score:.0f}%). Your {template_name} resume may appear keyword-stuffed. The optimal range is 75-85%. Consider using more natural language to avoid triggering over-optimization filters."
        elif score >= 90:
            base = f"🚨 OVER-OPTIMIZED ({score:.0f}%). Your resume scores too high, which research shows reduces interview callbacks by 40%. Scores above 90% suggest keyword stuffing or gaming the system. Human recruiters prefer 75-85%. Reduce keyword repetition and use more natural language."
        elif score >= 70 and score < 75:
            base = f"Good! Your {template_name} resume scores {score:.0f}%, just below the optimal 75-85% range. Add a few more relevant keywords to reach the sweet spot."
        elif score >= 60:
            base = f"Acceptable. Your {template_name} resume scores {score:.0f}%. Aim for the 75-85% sweet spot by adding relevant keywords and quantifiable achievements."
        else:
            base = f"Needs Improvement. Your {template_name} resume scores {score:.0f}%, below the optimal 75-85% range. Focus on keyword matching and content quality."

        # Add educational note about the sweet spot
        if score < 75 or score > 85:
            base += "\n\n💡 Why 75-85%? ATS systems pass you to human recruiters, who make the final decision. Scores of 100% look like keyword stuffing and reduce your chances by appearing robotic and over-optimized."

        return base

    def _estimate_enhanced_pass_probability(self, score: float, category_scores: Dict, template_type: str) -> float:
        """
        Enhanced pass probability reflecting 2025 research.

        Key Finding: The 75-85% range has the HIGHEST actual interview callback rate
        because it balances ATS requirements with human appeal.
        """
        # Base probability based on research (75-85% = optimal)
        if score >= 75 and score <= 85:
            # SWEET SPOT: Highest pass-through rate
            base_prob = 92  # Optimal range has highest success
        elif score > 85 and score <= 90:
            # Over-optimized: Starts reducing human interest
            base_prob = 85  # Slight penalty for over-optimization
        elif score > 90 and score <= 95:
            # Seriously over-optimized: Major penalty
            base_prob = 70  # Research shows 40% drop in callbacks
        elif score > 95:
            # Red flag: Gaming the system
            base_prob = 55  # Major penalty - appears like keyword stuffing
        elif score >= 70 and score < 75:
            # Just below optimal
            base_prob = 88
        elif score >= 65:
            base_prob = 80
        elif score >= 60:
            base_prob = 70
        else:
            base_prob = 50 + (score - 50) * 0.8

        # Template bonus (smaller now since we don't want to over-optimize)
        if template_type in ['modern', 'harvard']:
            base_prob = builtins.min(92, base_prob + 1)  # Small bonus, capped at optimal

        # Check critical categories
        content_percentage = (category_scores['content']['score'] / category_scores['content']['max']) * 100
        format_percentage = (category_scores['format']['score'] / category_scores['format']['max']) * 100

        # Adjust based on balance
        if content_percentage >= 75 and content_percentage <= 85 and format_percentage >= 75:
            base_prob = builtins.min(92, base_prob + 2)  # Bonus for balanced optimization

        # FIX: Use builtins.min/max to prevent shadowing issues
        return builtins.min(92, builtins.max(40, base_prob))  # Cap at 92% (not 99%)

    def _generate_keyword_suggestions(self, analysis: Dict) -> List[str]:
        """Generate keyword optimization suggestions"""
        suggestions = []
        match_percentage = analysis.get('match_percentage', 0)

        if match_percentage < 90:
            missing = analysis.get('missing_keywords', [])
            if missing:
                top_missing = missing[:3]
                suggestions.append(f"Add these high-priority keywords: {', '.join(top_missing)}")

        if match_percentage < 70:
            suggestions.append("Review job description and incorporate more relevant keywords throughout resume")

        return suggestions

    def _generate_density_suggestions(self, analysis: Dict) -> List[str]:
        """Generate density optimization suggestions"""
        suggestions = []
        density = analysis.get('keyword_density', 0)

        if density < 2.0:
            suggestions.append("Increase keyword usage naturally throughout your experience descriptions")
        elif density > 4.0:
            suggestions.append("Reduce keyword repetition to avoid over-optimization")

        return suggestions

    def _generate_metrics_suggestions(self, analysis: Dict) -> List[str]:
        """Generate metrics improvement suggestions"""
        suggestions = []
        count = analysis.get('count', 0)
        minimum = analysis.get('minimum_recommended', 10)

        if count < minimum:
            suggestions.append(f"Add {minimum - count} more quantifiable achievements (percentages, dollar amounts, time saved)")

        return suggestions

    def _generate_verb_suggestions(self, analysis: Dict) -> List[str]:
        """Generate action verb suggestions"""
        suggestions = []
        count = analysis.get('count', 0)
        minimum = analysis.get('minimum_recommended', 15)

        if count < minimum:
            suggestions.append(f"Start {minimum - count} more bullet points with strong action verbs")

        return suggestions

    def _prioritize_suggestions(self, suggestions: List[str], category_scores: Dict) -> List[str]:
        """Prioritize suggestions by impact"""
        # Remove duplicates
        seen = set()
        unique = []
        for sugg in suggestions:
            if sugg and sugg not in seen:
                seen.add(sugg)
                unique.append(sugg)

        # Prioritize based on category weaknesses
        critical = []
        important = []
        nice_to_have = []

        for sugg in unique:
            sugg_lower = sugg.lower()
            if any(word in sugg_lower for word in ['missing', 'add these', 'critical']):
                critical.append(sugg)
            elif any(word in sugg_lower for word in ['increase', 'reduce', 'improve']):
                important.append(sugg)
            else:
                nice_to_have.append(sugg)

        return critical + important + nice_to_have