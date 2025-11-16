"""
Voice and Personality Analysis for Resume Personalization

This module analyzes a candidate's existing profile to determine:
- Writing tone (technical/creative/leadership/analytical)
- Formality level (formal/semi-formal/conversational)
- Metrics usage patterns (high/medium/low)
- Preferred section organization
- Personality traits to emphasize

Purpose: Avoid template-like resumes by maintaining candidate's authentic voice
and creating varied structures based on their background.
"""
import re
from typing import Dict, List, Optional


class VoiceAnalyzer:
    """
    Analyzes candidate's profile to extract voice patterns and personality traits
    for resume personalization.
    """

    def __init__(self):
        # Action verb categories for tone detection
        self.creative_verbs = [
            'designed', 'crafted', 'innovated', 'pioneered', 'created',
            'envisioned', 'conceptualized', 'imagined', 'invented'
        ]
        self.technical_verbs = [
            'implemented', 'optimized', 'architected', 'deployed', 'configured',
            'developed', 'engineered', 'built', 'coded', 'debugged'
        ]
        self.leadership_verbs = [
            'led', 'managed', 'directed', 'mentored', 'coordinated',
            'supervised', 'guided', 'spearheaded', 'championed'
        ]
        self.analytical_verbs = [
            'analyzed', 'evaluated', 'measured', 'assessed', 'calculated',
            'determined', 'investigated', 'researched', 'studied'
        ]

    def analyze_profile_voice(self, profile_text: str) -> Dict:
        """
        Comprehensive voice and personality analysis of candidate's profile.

        Args:
            profile_text: Raw text from candidate's existing resume/profile

        Returns:
            Dictionary containing:
            - dominant_tone: technical/creative/leadership/analytical
            - formality_level: formal/semi-formal/conversational
            - metrics_density: high/medium/low
            - action_verb_style: matches dominant_tone
            - section_preference: how to structure the resume
            - personality_traits: list of traits to emphasize
            - estimated_experience_years: approximate experience level
        """
        analysis = {
            "dominant_tone": "technical",
            "formality_level": "semi-formal",
            "metrics_density": "medium",
            "action_verb_style": "technical",
            "section_preference": "chronological",
            "personality_traits": [],
            "estimated_experience_years": 3,
        }

        # Analyze metrics usage density
        metrics_patterns = [
            r'\d+\s*%',  # percentages: "40%"
            r'\$\s*\d+',  # dollar amounts: "$100K"
            r'\d+\s*[KkMm]\+?',  # thousands/millions: "100K", "2M+"
            r'\d+\+',  # "100+"
            r'\d+x',  # "10x improvement"
            r'\d+\.\d+',  # decimals: "3.5"
        ]

        metric_count = 0
        for pattern in metrics_patterns:
            metric_count += len(re.findall(pattern, profile_text))

        # Classify metrics density
        text_length = len(profile_text)
        if text_length > 0:
            metrics_per_1000 = (metric_count / text_length) * 1000
            if metrics_per_1000 > 5:
                analysis["metrics_density"] = "high"
            elif metrics_per_1000 < 2:
                analysis["metrics_density"] = "low"

        # Analyze action verbs to determine dominant tone
        verb_counts = {
            "creative": sum(1 for verb in self.creative_verbs if verb in profile_text.lower()),
            "technical": sum(1 for verb in self.technical_verbs if verb in profile_text.lower()),
            "leadership": sum(1 for verb in self.leadership_verbs if verb in profile_text.lower()),
            "analytical": sum(1 for verb in self.analytical_verbs if verb in profile_text.lower()),
        }

        # Determine dominant tone (default to technical if ties)
        max_count = max(verb_counts.values())
        if max_count > 0:
            analysis["dominant_tone"] = max(verb_counts, key=verb_counts.get)
            analysis["action_verb_style"] = analysis["dominant_tone"]

        # Detect personality traits from keyword patterns
        trait_keywords = {
            "collaborative": ['collaborated', 'teamwork', 'partnered', 'cross-functional', 'team player'],
            "detail-oriented": ['meticulous', 'thorough', 'comprehensive', 'detailed', 'precise'],
            "innovative": ['innovative', 'novel', 'creative', 'pioneered', 'invented', 'cutting-edge'],
            "results-driven": ['achieved', 'delivered', 'exceeded', 'accomplished', 'drove results'],
            "adaptable": ['adapted', 'versatile', 'flexible', 'learned', 'transitioned'],
            "proactive": ['initiated', 'volunteered', 'self-directed', 'took ownership', 'proactive'],
        }

        for trait, keywords in trait_keywords.items():
            if any(kw in profile_text.lower() for kw in keywords):
                analysis["personality_traits"].append(trait)

        # Analyze formality level
        informal_indicators = ['worked on', 'helped with', 'got', 'made', 'did']
        formal_indicators = ['executed', 'facilitated', 'orchestrated', 'spearheaded', 'leveraged']

        informal_count = sum(1 for ind in informal_indicators if ind in profile_text.lower())
        formal_count = sum(1 for ind in formal_indicators if ind in profile_text.lower())

        if formal_count > informal_count * 2:
            analysis["formality_level"] = "formal"
        elif informal_count > formal_count:
            analysis["formality_level"] = "conversational"

        # Estimate experience level based on content patterns
        years_match = re.search(r'(\d+)\+?\s*years?', profile_text, re.IGNORECASE)
        if years_match:
            analysis["estimated_experience_years"] = int(years_match.group(1))
        else:
            # Heuristic: count number of job positions
            job_patterns = [r'software engineer', r'developer', r'analyst', r'manager']
            job_count = sum(len(re.findall(pattern, profile_text, re.IGNORECASE)) for pattern in job_patterns)
            analysis["estimated_experience_years"] = max(1, job_count * 2)  # Rough estimate

        # Determine section preference based on profile structure
        profile_lower = profile_text.lower()
        if 'publications' in profile_lower or 'research' in profile_lower[:1000]:
            analysis["section_preference"] = "academic-focused"
        elif 'phd' in profile_lower or 'doctorate' in profile_lower:
            analysis["section_preference"] = "academic-focused"
        elif analysis["estimated_experience_years"] < 2:
            analysis["section_preference"] = "education-first"
        elif 'skills' in profile_lower[:500]:  # Skills section appears early
            analysis["section_preference"] = "skills-first"
        else:
            analysis["section_preference"] = "chronological"

        return analysis

    def generate_personalization_instructions(self, voice_analysis: Dict) -> str:
        """
        Generate prompt instructions based on voice analysis to maintain candidate's
        authentic voice and avoid template-like output.

        Args:
            voice_analysis: Dictionary from analyze_profile_voice()

        Returns:
            String with personalization instructions for the AI prompt
        """
        instructions = f"""
## PERSONALITY & VOICE PERSONALIZATION

**CRITICAL**: Maintain the candidate's authentic voice - avoid robotic, template language.

Based on analysis of the candidate's existing profile, customize the resume with these characteristics:

**Writing Tone: {voice_analysis['dominant_tone'].upper()}**
"""

        # Tone-specific instructions
        if voice_analysis['dominant_tone'] == 'technical':
            instructions += """
- Use precise, technical terminology
- Lead with technical stack and architecture details
- Emphasize system design, scalability, performance optimizations
- Action verbs to prefer: implemented, architected, optimized, deployed, engineered, configured
- Focus on HOW solutions were built (technical depth)
"""
        elif voice_analysis['dominant_tone'] == 'creative':
            instructions += """
- Use dynamic, innovative language
- Emphasize design thinking and novel solutions
- Highlight user experience impact and creative problem-solving
- Action verbs to prefer: designed, crafted, pioneered, innovated, created, envisioned
- Focus on creative approaches and innovative solutions
"""
        elif voice_analysis['dominant_tone'] == 'leadership':
            instructions += """
- Emphasize team impact and mentorship
- Highlight project leadership and cross-functional collaboration
- Focus on organizational and people impact
- Action verbs to prefer: led, directed, mentored, coordinated, championed, guided
- Show progression and increasing responsibility
"""
        elif voice_analysis['dominant_tone'] == 'analytical':
            instructions += """
- Lead with data-driven insights and measurable outcomes
- Emphasize analysis, optimization, and evidence-based decision-making
- Include detailed metrics and ROI
- Action verbs to prefer: analyzed, optimized, measured, evaluated, determined, assessed
- Focus on quantitative impact and analytical approach
"""

        # Metrics density instructions
        instructions += f"""
**Metrics Usage Pattern: {voice_analysis['metrics_density'].upper()}**
"""
        if voice_analysis['metrics_density'] == 'high':
            instructions += """- This candidate is highly metrics-driven
- Include quantitative metrics in 70%+ of bullets
- Lead every achievement with numbers when possible
- Use precise figures (e.g., "23.4%" not "~25%")
- Emphasize data-driven approach in summary
"""
        elif voice_analysis['metrics_density'] == 'low':
            instructions += """- This candidate emphasizes qualitative impact
- Focus on scope, technologies, and methodologies
- Include metrics where natural but don't force them
- Emphasize breadth of technologies and complexity of systems
- More descriptive about HOW work was done
"""
        else:
            instructions += """- Balanced approach to metrics and description
- Include metrics for major achievements (40-50% of bullets)
- Mix quantitative data with technical context
- Show both impact (numbers) and approach (how)
"""

        # Personality traits emphasis
        if voice_analysis['personality_traits']:
            traits_str = ", ".join(voice_analysis['personality_traits'][:3])  # Top 3 traits
            instructions += f"""
**Personality Traits to Emphasize: {traits_str}**
- Weave these traits naturally into experience bullets
- Show concrete examples demonstrating these characteristics
- Mention in Professional Summary if space allows
- Use these traits to differentiate from generic resumes
"""

        # Formality level guidance
        instructions += f"""
**Formality Level: {voice_analysis['formality_level'].upper()}**
"""
        if voice_analysis['formality_level'] == 'formal':
            instructions += """- Maintain formal, professional tone throughout
- Use sophisticated vocabulary and complete sentences
- Avoid contractions and casual language
- Professional summary should be polished and executive-level
"""
        elif voice_analysis['formality_level'] == 'conversational':
            instructions += """- Use clear, direct language
- Avoid overly formal or stuffy phrasing
- Focus on readability and accessibility
- Professional tone but approachable
"""
        else:  # semi-formal
            instructions += """- Balance professionalism with accessibility
- Clear, concise language without being too casual
- Standard professional resume tone
"""

        instructions += "\n**CRITICAL**: Maintain this personalized voice consistently throughout the entire resume. The resume should feel authentic to THIS candidate, not like a generic template.\n"

        return instructions

    def generate_structure_variation(self, voice_analysis: Dict, job_analysis: Dict) -> str:
        """
        Generate varied resume structures based on candidate profile and job requirements.
        Avoids the "everyone has the same template" problem.

        Args:
            voice_analysis: Dictionary from analyze_profile_voice()
            job_analysis: Dictionary with job title, company, requirements

        Returns:
            String with customized structure recommendations
        """
        job_title = job_analysis.get('job_title', '').lower()
        years_exp = voice_analysis.get('estimated_experience_years', 3)
        section_pref = voice_analysis.get('section_preference', 'chronological')

        # Determine optimal structure based on candidate profile
        if section_pref == 'academic-focused':
            # Research/academic structure
            structure = """
**Recommended Structure for Academic/Research Profile:**

# [CANDIDATE NAME]
[Contact Line]

## PROFESSIONAL SUMMARY
[Brief, impact-focused summary highlighting research contributions]

## EDUCATION
[Degrees with thesis/research focus, GPA, honors]

## PUBLICATIONS
[Peer-reviewed publications, conferences]

## RESEARCH EXPERIENCE
[Research positions and projects]

## TECHNICAL SKILLS
[Research methodologies, tools, programming languages]

## PROFESSIONAL EXPERIENCE (if applicable)
[Industry positions]

## ADDITIONAL SECTIONS
[Awards, Grants, Teaching Experience, etc.]
"""
        elif years_exp < 2 or section_pref == 'education-first':
            # Recent grad / early career structure
            structure = """
**Recommended Structure for Early-Career Professional:**

# [CANDIDATE NAME]
[Contact Line]

## PROFESSIONAL SUMMARY
[3-line summary emphasizing education, relevant coursework, and passion]

## EDUCATION
[Degrees with GPA (if strong), relevant coursework, honors, leadership roles]

## TECHNICAL SKILLS
[Organized by category - showcase breadth of knowledge]

## PROJECTS
[Academic and personal projects demonstrating skills]

## PROFESSIONAL EXPERIENCE
[Internships, part-time work, relevant positions]

## CERTIFICATIONS / AWARDS / EXTRACURRICULARS
[Additional credentials]
"""
        elif 'senior' in job_title or 'lead' in job_title or 'principal' in job_title or years_exp > 7:
            # Senior/leadership structure
            structure = """
**Recommended Structure for Senior/Leadership Role:**

# [CANDIDATE NAME]
[Contact Line]

## PROFESSIONAL SUMMARY
[Leadership-focused summary emphasizing impact, team building, strategic contributions]

## PROFESSIONAL EXPERIENCE
[Reverse chronological, emphasizing leadership, scope, impact]

## TECHNICAL SKILLS & EXPERTISE
[Advanced technologies, architectures, domain expertise]

## EDUCATION
[Degrees only - concise]

## LEADERSHIP & ACHIEVEMENTS
[Notable contributions, awards, speaking engagements]
"""
        else:
            # Standard mid-level professional structure
            structure = """
**Recommended Structure for Mid-Level Professional:**

# [CANDIDATE NAME]
[Contact Line]

## PROFESSIONAL SUMMARY
[3-4 line impactful summary]

## TECHNICAL SKILLS
[Organized by category, prioritizing job requirements]

## EDUCATION
[Degrees with relevant details]

## PROJECTS / PROFESSIONAL EXPERIENCE
[Combined or separate based on profile - emphasize relevant work]

## ADDITIONAL SECTIONS
[Publications, Certifications, Awards as applicable]
"""

        return structure

    def get_varied_section_headers(self, voice_analysis: Dict) -> Dict[str, List[str]]:
        """
        Provide varied section header options to avoid template uniformity.

        Args:
            voice_analysis: Dictionary from analyze_profile_voice()

        Returns:
            Dictionary mapping section types to header options
        """
        tone = voice_analysis.get('dominant_tone', 'technical')

        if tone == 'creative':
            return {
                'summary': ['Professional Profile', 'About Me', 'Career Summary'],
                'skills': ['Core Competencies', 'Technical Toolkit', 'Areas of Expertise'],
                'experience': ['Professional Journey', 'Key Contributions', 'Career Highlights'],
                'projects': ['Notable Projects', 'Featured Work', 'Project Portfolio'],
                'education': ['Academic Background', 'Education', 'Academic Credentials'],
            }
        elif tone == 'technical':
            return {
                'summary': ['Professional Summary', 'Technical Profile', 'Summary'],
                'skills': ['Technical Skills', 'Technology Stack', 'Technical Proficiencies'],
                'experience': ['Professional Experience', 'Technical Experience', 'Work History'],
                'projects': ['Technical Projects', 'Engineering Projects', 'Development Work'],
                'education': ['Education', 'Academic Background', 'Qualifications'],
            }
        elif tone == 'leadership':
            return {
                'summary': ['Executive Summary', 'Leadership Profile', 'Professional Summary'],
                'skills': ['Core Competencies', 'Leadership Skills', 'Professional Skills'],
                'experience': ['Professional Experience', 'Career Progression', 'Leadership History'],
                'projects': ['Key Initiatives', 'Strategic Projects', 'Major Accomplishments'],
                'education': ['Education', 'Academic Credentials', 'Qualifications'],
            }
        else:  # analytical
            return {
                'summary': ['Professional Summary', 'Analytical Profile', 'Summary'],
                'skills': ['Technical & Analytical Skills', 'Core Competencies', 'Skillset'],
                'experience': ['Professional Experience', 'Analytical Experience', 'Work Experience'],
                'projects': ['Key Projects', 'Analysis & Research', 'Project Experience'],
                'education': ['Education', 'Academic Background', 'Credentials'],
            }


def main():
    """Test the voice analyzer with sample profile text"""
    sample_profile = """
    Software Engineer with 4 years of experience building scalable web applications.

    Technical Skills:
    - Languages: Python, JavaScript, Java
    - Frameworks: React, Django, Flask
    - Tools: Git, Docker, AWS

    Experience:

    Software Engineer | TechCorp | 2020-Present
    - Architected microservices platform handling 1M+ daily requests
    - Optimized database queries reducing latency by 65%
    - Mentored 3 junior developers on React best practices
    - Collaborated with product team across 3 time zones

    Education:
    BS Computer Science | State University | 2020
    GPA: 3.8/4.0
    """

    analyzer = VoiceAnalyzer()

    print("=== Voice Analysis Results ===\n")
    analysis = analyzer.analyze_profile_voice(sample_profile)

    for key, value in analysis.items():
        print(f"{key}: {value}")

    print("\n=== Personalization Instructions ===\n")
    instructions = analyzer.generate_personalization_instructions(analysis)
    print(instructions)

    print("\n=== Structure Variation ===\n")
    job_analysis = {"job_title": "Senior Software Engineer", "company_name": "Microsoft"}
    structure = analyzer.generate_structure_variation(analysis, job_analysis)
    print(structure)


if __name__ == "__main__":
    main()
