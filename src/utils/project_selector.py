"""
Project Selector - Intelligently selects most relevant projects for job description
Scores and ranks projects based on keyword matching and skill alignment
"""
import re
from typing import Dict, List, Tuple


class ProjectSelector:
    """Selects most relevant projects/experiences based on job requirements"""

    def __init__(self, max_projects: int = 4):
        """
        Initialize project selector

        Args:
            max_projects: Maximum number of projects to include in resume
        """
        self.max_projects = max_projects

    def extract_projects_from_profile(self, profile_text: str) -> List[Dict]:
        """
        Extract individual projects from profile text

        Args:
            profile_text: Raw profile text

        Returns:
            List of project dictionaries with name and description
        """
        projects = []
        lines = profile_text.split('\n')

        current_project = None
        current_description = []

        for line in lines:
            line_stripped = line.strip()

            # Check if this is a project header (title with date or context)
            # Look for patterns like "Project Name | Context" or "Project Name (Date)"
            if ('|' in line_stripped or
                ('(' in line_stripped and ')' in line_stripped) or
                (line_stripped and not line_stripped.startswith('-') and
                 any(keyword in line_stripped.lower() for keyword in
                     ['project', 'platform', 'system', 'assistant', 'detection', 'published']))):

                # Save previous project if exists
                if current_project:
                    projects.append({
                        'name': current_project,
                        'description': ' '.join(current_description)
                    })

                # Start new project
                current_project = line_stripped
                current_description = []

            # Add description lines (bullets or paragraphs under project)
            elif line_stripped.startswith('-') or (line_stripped and current_project):
                current_description.append(line_stripped.lstrip('- '))

        # Add last project
        if current_project:
            projects.append({
                'name': current_project,
                'description': ' '.join(current_description)
            })

        return projects

    def score_project_relevance(
        self,
        project: Dict,
        job_analysis: Dict
    ) -> Tuple[float, Dict]:
        """
        Score a project's relevance to the job description

        Args:
            project: Project dict with name and description
            job_analysis: Job analysis with required skills and keywords

        Returns:
            Tuple of (score, breakdown) where score is 0-100 and breakdown shows details
        """
        project_text = f"{project['name']} {project['description']}".lower()

        # Get job requirements
        required_skills = [skill.lower() for skill in job_analysis.get('required_skills', [])]
        keywords = [kw.lower() for kw in job_analysis.get('keywords', [])]

        # Scoring components
        scores = {
            'skills_match': 0,
            'keyword_match': 0,
            'recency_bonus': 0,
            'impact_bonus': 0
        }

        # 1. Skills Match (0-40 points)
        if required_skills:
            matched_skills = sum(1 for skill in required_skills if skill in project_text)
            scores['skills_match'] = min(40, (matched_skills / len(required_skills)) * 40)

        # 2. Keyword Match (0-30 points)
        if keywords:
            matched_keywords = sum(1 for keyword in keywords if keyword in project_text)
            scores['keyword_match'] = min(30, (matched_keywords / len(keywords)) * 30)

        # 3. Recency Bonus (0-15 points)
        # Check for recent dates (2024, 2025, "present")
        if re.search(r'(2025|2024|present)', project_text, re.IGNORECASE):
            scores['recency_bonus'] = 15
        elif re.search(r'2023', project_text, re.IGNORECASE):
            scores['recency_bonus'] = 10

        # 4. Impact Bonus (0-15 points)
        # Look for metrics indicating high impact
        impact_indicators = [
            r'\d+\+?\s*(users|customers|clients)',
            r'\d+%\s*(improvement|increase|reduction|faster)',
            r'\$\d+',
            r'production|deployed|serving',
            r'\d+\s*papers?',
            r'cited|published'
        ]

        impact_matches = sum(1 for pattern in impact_indicators
                           if re.search(pattern, project_text, re.IGNORECASE))
        scores['impact_bonus'] = min(15, impact_matches * 3)

        # Calculate total score
        total_score = sum(scores.values())

        # Create detailed breakdown
        breakdown = {
            'total_score': round(total_score, 1),
            'skills_match': round(scores['skills_match'], 1),
            'keyword_match': round(scores['keyword_match'], 1),
            'recency_bonus': round(scores['recency_bonus'], 1),
            'impact_bonus': round(scores['impact_bonus'], 1),
            'project_name': project['name'][:80]
        }

        return total_score, breakdown

    def select_top_projects(
        self,
        profile_text: str,
        job_analysis: Dict,
        always_include_publications: bool = True
    ) -> Dict:
        """
        Select most relevant projects from profile

        Args:
            profile_text: Raw profile text
            job_analysis: Job analysis dict
            always_include_publications: Whether to always include publications

        Returns:
            Dict with selected projects and scoring details
        """
        # Extract all projects
        all_projects = self.extract_projects_from_profile(profile_text)

        # Separate publications from other projects
        publications = []
        experiences = []

        for project in all_projects:
            project_name_lower = project['name'].lower()
            if any(keyword in project_name_lower for keyword in
                   ['published', 'publication', 'paper', 'journal', 'conference']):
                publications.append(project)
            else:
                experiences.append(project)

        # Score all experiences
        scored_experiences = []
        for exp in experiences:
            score, breakdown = self.score_project_relevance(exp, job_analysis)
            scored_experiences.append({
                'project': exp,
                'score': score,
                'breakdown': breakdown
            })

        # Sort by score (highest first)
        scored_experiences.sort(key=lambda x: x['score'], reverse=True)

        # Select top N experiences
        selected_experiences = scored_experiences[:self.max_projects]

        # Always include publications if requested
        selected_projects = selected_experiences.copy()
        if always_include_publications:
            for pub in publications:
                score, breakdown = self.score_project_relevance(pub, job_analysis)
                selected_projects.append({
                    'project': pub,
                    'score': score,
                    'breakdown': breakdown,
                    'is_publication': True
                })

        return {
            'selected_count': len(selected_experiences),
            'publication_count': len(publications) if always_include_publications else 0,
            'total_projects_analyzed': len(all_projects),
            'selected_projects': selected_projects,
            'excluded_projects': scored_experiences[self.max_projects:] if len(scored_experiences) > self.max_projects else []
        }

    def generate_selection_report(self, selection_result: Dict) -> str:
        """
        Generate human-readable report of project selection

        Args:
            selection_result: Result from select_top_projects()

        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 80)
        report.append("PROJECT SELECTION REPORT")
        report.append("=" * 80)
        report.append(f"\nTotal Projects Analyzed: {selection_result['total_projects_analyzed']}")
        report.append(f"Selected Experiences: {selection_result['selected_count']}")
        report.append(f"Selected Publications: {selection_result['publication_count']}")

        report.append("\n" + "=" * 80)
        report.append("SELECTED PROJECTS (Ranked by Relevance):")
        report.append("=" * 80)

        for i, item in enumerate(selection_result['selected_projects'], 1):
            breakdown = item['breakdown']
            is_pub = item.get('is_publication', False)
            project_type = "PUBLICATION" if is_pub else "EXPERIENCE"

            report.append(f"\n{i}. [{project_type}] {breakdown['project_name']}")
            report.append(f"   Total Score: {breakdown['total_score']:.1f}/100")
            report.append(f"   - Skills Match: {breakdown['skills_match']:.1f}/40")
            report.append(f"   - Keyword Match: {breakdown['keyword_match']:.1f}/30")
            report.append(f"   - Recency: {breakdown['recency_bonus']:.1f}/15")
            report.append(f"   - Impact: {breakdown['impact_bonus']:.1f}/15")

        if selection_result['excluded_projects']:
            report.append("\n" + "=" * 80)
            report.append("EXCLUDED PROJECTS (Lower Relevance):")
            report.append("=" * 80)

            for i, item in enumerate(selection_result['excluded_projects'], 1):
                breakdown = item['breakdown']
                report.append(f"\n{i}. {breakdown['project_name']}")
                report.append(f"   Score: {breakdown['total_score']:.1f}/100")

        report.append("\n" + "=" * 80)

        return '\n'.join(report)
