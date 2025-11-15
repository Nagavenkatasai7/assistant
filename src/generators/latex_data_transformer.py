"""
Data transformer to convert AI-generated resume data into LaTeX-safe format
"""
from typing import Dict, List, Any
from ..utils.latex_utils import LaTeXEscaper, LaTeXValidator


class LaTeXDataTransformer:
    """Transform AI-generated resume data into LaTeX template format"""

    # Required fields for template
    REQUIRED_FIELDS = [
        'header.name',
        'header.email',
        'summary',
        'projects'
    ]

    def __init__(self):
        self.escaper = LaTeXEscaper()
        self.validator = LaTeXValidator()

    def transform(self, ai_resume_data: dict) -> dict:
        """
        Main transformation pipeline.

        Args:
            ai_resume_data: Raw resume data from AI (JSON/dict format)

        Returns:
            LaTeX-safe data dictionary ready for Jinja2 template

        Raises:
            ValueError: If required fields missing or data invalid
        """
        # Step 1: Validate required fields
        missing = self.validator.validate_required_fields(
            ai_resume_data,
            self.REQUIRED_FIELDS
        )
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")

        # Step 2: Transform each section
        latex_data = {
            'header': self._transform_header(ai_resume_data.get('header', {})),
            'summary': self._transform_summary(ai_resume_data.get('summary', '')),
            'skills': self._transform_skills(ai_resume_data.get('skills', {})),
            'education': self._transform_education(ai_resume_data.get('education', [])),
            'projects': self._transform_projects(ai_resume_data.get('projects', [])),
            'additional': self._transform_additional(ai_resume_data.get('additional', {})),
        }

        # Step 3: Transform dynamic sections
        if 'dynamic_sections' in ai_resume_data and ai_resume_data['dynamic_sections']:
            latex_data['dynamic_sections'] = self._transform_dynamic_sections(
                ai_resume_data['dynamic_sections']
            )
        else:
            latex_data['dynamic_sections'] = {}

        # Step 4: Add optional fields
        if 'projects_section_title' in ai_resume_data:
            latex_data['projects_section_title'] = self.escaper.escape(
                ai_resume_data['projects_section_title']
            )

        return latex_data

    def _transform_header(self, header: dict) -> dict:
        """
        Transform header section.

        Args:
            header: Dict with name, location, email, linkedin, github, portfolio

        Returns:
            LaTeX-safe header dict
        """
        transformed = {}

        # Required fields
        transformed['name'] = self.escaper.escape(header.get('name', ''))
        transformed['location'] = self.escaper.escape(header.get('location', ''))
        transformed['email'] = header.get('email', '')  # Don't escape email

        # Optional fields with URL sanitization
        if 'linkedin' in header and header['linkedin']:
            transformed['linkedin'] = self.validator.sanitize_url(header['linkedin'])

        if 'github' in header and header['github']:
            transformed['github'] = self.validator.sanitize_url(header['github'])

        if 'portfolio' in header and header['portfolio']:
            transformed['portfolio'] = self.validator.sanitize_url(header['portfolio'])

        # Optional title field
        if 'title' in header:
            transformed['title'] = self.escaper.escape(header['title'])

        return transformed

    def _transform_summary(self, summary: str) -> str:
        """
        Transform summary text.

        Args:
            summary: Summary paragraph text

        Returns:
            LaTeX-escaped summary
        """
        return self.escaper.escape(summary)

    def _transform_skills(self, skills: dict) -> dict:
        """
        Transform skills section.

        Args:
            skills: Dict with skill categories (ai_ml, product_dev, programming)

        Returns:
            Dict with escaped skill lists
        """
        transformed = {}

        # Handle different skill category formats
        skill_categories = {
            'ai_ml': skills.get('ai_ml', skills.get('AI/ML', skills.get('ai', []))),
            'product_dev': skills.get('product_dev', skills.get('Product Development', skills.get('product', []))),
            'programming': skills.get('programming', skills.get('Programming', skills.get('tools', [])))
        }

        for category, skill_list in skill_categories.items():
            if skill_list:
                # Ensure it's a list
                if isinstance(skill_list, str):
                    # Split by comma if string
                    skill_list = [s.strip() for s in skill_list.split(',')]

                # Escape each skill
                transformed[category] = [
                    self.escaper.escape(skill) for skill in skill_list
                ]

        return transformed

    def _transform_education(self, education: List[dict]) -> List[dict]:
        """
        Transform education entries.

        Args:
            education: List of education dicts

        Returns:
            List of LaTeX-safe education entries
        """
        transformed = []

        for edu in education:
            entry = {
                'institution': self.escaper.escape(edu.get('institution', '')),
                'degree': self.escaper.escape(edu.get('degree', '')),
                'dates': self.escaper.escape(edu.get('dates', '')),
            }

            # Optional fields
            if 'gpa' in edu and edu['gpa']:
                entry['gpa'] = self.escaper.escape(str(edu['gpa']))

            if 'research_role' in edu and edu['research_role']:
                entry['research_role'] = self.escaper.escape(edu['research_role'])

            if 'advisor' in edu and edu['advisor']:
                entry['advisor'] = self.escaper.escape(edu['advisor'])

            transformed.append(entry)

        return transformed

    def _transform_projects(self, projects: List[dict]) -> List[dict]:
        """
        Transform project entries.

        Args:
            projects: List of project dicts

        Returns:
            List of LaTeX-safe project entries
        """
        transformed = []

        for project in projects:
            # Validate bullets
            bullets = project.get('bullets', project.get('achievements', []))
            if not self.validator.validate_bullets(bullets):
                raise ValueError(f"Invalid bullets for project: {project.get('title', 'Unknown')}")

            entry = {
                'title': self.escaper.escape(project.get('title', '')),
                'dates': self.escaper.escape(project.get('dates', '')),
                'bullets': [self.escaper.escape(bullet) for bullet in bullets]
            }

            # Optional fields
            if 'technologies' in project and project['technologies']:
                entry['technologies'] = self.escaper.escape(project['technologies'])

            if 'github' in project and project['github']:
                entry['github'] = project['github']  # Don't escape URLs in href

            if 'url' in project and project['url']:
                entry['url'] = project['url']

            transformed.append(entry)

        return transformed

    def _transform_additional(self, additional: dict) -> dict:
        """
        Transform additional contributions section.

        Args:
            additional: Dict with open_source, research, hackathons

        Returns:
            LaTeX-safe additional dict
        """
        transformed = {}

        fields = ['open_source', 'research', 'hackathons', 'awards', 'publications']

        for field in fields:
            if field in additional and additional[field]:
                transformed[field] = self.escaper.escape(additional[field])

        return transformed

    def _transform_dynamic_sections(self, dynamic_sections: dict) -> dict:
        """
        Transform dynamic sections to LaTeX-safe format.

        Args:
            dynamic_sections: OrderedDict of dynamic sections from parser

        Returns:
            Dict with LaTeX-escaped content
        """
        from collections import OrderedDict
        transformed = OrderedDict()

        for section_name, section_data in dynamic_sections.items():
            content_type = section_data.get('type', 'text')
            content = section_data.get('content')

            # Transform based on content type
            if content_type == 'structured':
                transformed_content = self._transform_structured_items(content)
            elif content_type == 'list':
                transformed_content = [self.escaper.escape(item) for item in content]
            elif content_type == 'nested':
                transformed_content = self._transform_nested_sections(content)
            else:  # 'text'
                transformed_content = self.escaper.escape(content)

            transformed[section_name] = {
                'type': content_type,
                'content': transformed_content,
                'display_name': self.escaper.escape(section_data.get('display_name', section_name)),
                'order': section_data.get('order', 999)
            }

        return transformed

    def _transform_structured_items(self, items: list) -> list:
        """Transform structured items (publications, awards) to LaTeX-safe format"""
        transformed = []

        for item in items:
            transformed_item = {}
            for key, value in item.items():
                # Escape all text fields, preserve URLs
                if key in ['url', 'link', 'github']:
                    transformed_item[key] = value  # Don't escape URLs
                else:
                    transformed_item[key] = self.escaper.escape(str(value))
            transformed.append(transformed_item)

        return transformed

    def _transform_nested_sections(self, nested: dict) -> dict:
        """Transform nested subsections to LaTeX-safe format"""
        from collections import OrderedDict
        transformed = OrderedDict()

        for subsection_name, lines in nested.items():
            # Join lines and escape
            content = ' '.join(line.strip() for line in lines if line.strip())
            transformed[subsection_name] = {
                'name': self.escaper.escape(subsection_name),
                'content': self.escaper.escape(content)
            }

        return transformed

    def validate_output(self, data: dict) -> List[str]:
        """
        Validate transformed data before passing to template.

        Args:
            data: Transformed LaTeX data

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check header
        if not data.get('header', {}).get('name'):
            errors.append("Missing header name")

        if not data.get('header', {}).get('email'):
            errors.append("Missing header email")

        # Check summary
        if not data.get('summary'):
            errors.append("Missing summary")

        # Check projects
        projects = data.get('projects', [])
        if not projects:
            errors.append("No projects provided")
        else:
            for i, project in enumerate(projects):
                if not project.get('title'):
                    errors.append(f"Project {i+1} missing title")
                if not project.get('bullets'):
                    errors.append(f"Project {i+1} missing bullets")

        return errors


def create_sample_resume_data() -> dict:
    """
    Create sample resume data for testing.

    Returns:
        Sample resume data dictionary
    """
    return {
        'header': {
            'name': 'John Smith',
            'location': 'Boston, MA',
            'email': 'john.smith@example.com',
            'linkedin': 'linkedin.com/in/johnsmith',
            'github': 'github.com/johnsmith',
            'portfolio': 'johnsmith.dev',
            'title': 'AI Product Developer'
        },
        'summary': (
            'Software Engineer with 5+ years building AI-powered products. '
            'Expert in GPT-4, LangChain, and RAG systems. '
            'Deployed 10+ production ML applications serving 100K+ users with 98% satisfaction. '
            'Seeking AI Product Developer role to leverage LLM expertise & drive innovation.'
        ),
        'skills': {
            'ai_ml': [
                'GPT-4', 'Claude', 'LangChain', 'RAG Systems', 'Vector Databases',
                'Prompt Engineering', 'Fine-tuning', 'Multi-Agent Systems'
            ],
            'product_dev': [
                'FastAPI', 'Streamlit', 'Docker', 'A/B Testing', 'API Design',
                'User Research', 'Performance Optimization'
            ],
            'programming': [
                'Python', 'PyTorch', 'TensorFlow', 'SQL', 'Git', 'AWS', 'CI/CD'
            ]
        },
        'education': [
            {
                'institution': 'MIT',
                'degree': 'Master of Science in Computer Science',
                'gpa': '4.0/4.0',
                'dates': 'Expected May 2026',
                'research_role': 'Graduate Research Assistant - Multi-Agent AI Systems'
            },
            {
                'institution': 'UC Berkeley',
                'degree': 'Bachelor of Science in Computer Science',
                'gpa': '3.9/4.0',
                'dates': '2020 – 2024'
            }
        ],
        'projects': [
            {
                'title': 'Multi-Agent Market Research Platform',
                'dates': 'Aug 2024 – Present',
                'technologies': 'Python, CrewAI, GPT-4',
                'github': 'https://github.com/user/project',
                'bullets': [
                    'Architected autonomous multi-agent system generating 3,700+ word reports in 5 seconds',
                    'Achieved 98% accuracy in financial modeling through prompt optimization',
                    'Reduced API costs by 45% through intelligent caching while maintaining quality',
                    'Implemented TAM/SAM/SOM calculation agents with custom evaluation metrics'
                ]
            },
            {
                'title': 'Enterprise RAG System',
                'dates': 'Jan 2025 – Present',
                'technologies': 'LangChain, FAISS, Claude',
                'bullets': [
                    'Built production RAG system processing 100MB documents with 95% accuracy',
                    'Integrated Claude, Grok, and Kimi-K2 with intelligent routing',
                    'Designed "Chat with Docs" feature combining knowledge graphs with LLMs',
                    'Achieved 40% improvement in response accuracy through prompt optimization'
                ]
            },
            {
                'title': 'Conversational AI Platform',
                'dates': 'Oct 2024 – Dec 2024',
                'technologies': 'FastAPI, GPT-4, Streamlit',
                'bullets': [
                    'Deployed chatbot serving 1000+ daily queries with 95% user satisfaction',
                    'Implemented context-aware routing with session management',
                    'Built evaluation framework measuring faithfulness, relevance, grounding',
                    'Reduced response latency by 60% through FAISS optimization'
                ]
            }
        ],
        'additional': {
            'open_source': 'Contributed to LangChain (RAG improvements), 500+ GitHub stars on prompt templates',
            'research': 'Published 3 papers on AI/ML applications in top-tier conferences',
            'hackathons': 'Winner of Best AI Innovation Award at MIT AI Hackathon 2024'
        },
        'projects_section_title': 'AI Product Development Projects'
    }
