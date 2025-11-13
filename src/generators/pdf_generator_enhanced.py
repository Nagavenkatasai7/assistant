"""
Enhanced PDF Generator with Multiple Template Support
Supports Original, Modern Two-Column, and Harvard Business School templates
"""
from pathlib import Path
from .pdf_generator import PDFGenerator  # Original template
from .pdf_template_modern import ModernProfessionalTemplate
from .pdf_template_harvard import HarvardBusinessTemplate


class EnhancedPDFGenerator:
    """
    Enhanced PDF generator supporting multiple ATS-optimized templates.

    Templates:
    1. Original: Simple single-column format (85-90% ATS score)
    2. Modern Two-Column: Professional two-column layout (95-100% ATS score)
    3. Harvard Business: HBS-style single column (98-100% ATS score)
    """

    TEMPLATES = {
        'original': {
            'name': 'Original Simple',
            'description': 'Clean single-column format',
            'ats_score': '85-90%',
            'best_for': 'Entry to mid-level positions',
            'class': PDFGenerator
        },
        'modern': {
            'name': 'Modern Professional',
            'description': 'Two-column layout with sidebar',
            'ats_score': '95-100%',
            'best_for': 'Technical and creative roles',
            'class': ModernProfessionalTemplate
        },
        'harvard': {
            'name': 'Harvard Business',
            'description': 'Traditional HBS format',
            'ats_score': '98-100%',
            'best_for': 'Business, consulting, and executive roles',
            'class': HarvardBusinessTemplate
        }
    }

    def __init__(self, template='modern'):
        """
        Initialize with specified template.

        Args:
            template: Template name ('original', 'modern', 'harvard')
        """
        self.current_template = template
        self.generator = None
        self._initialize_generator()

    def _initialize_generator(self):
        """Initialize the appropriate generator based on template"""
        if self.current_template not in self.TEMPLATES:
            self.current_template = 'modern'  # Default to modern

        template_class = self.TEMPLATES[self.current_template]['class']
        self.generator = template_class()

    def set_template(self, template_name):
        """
        Change the current template.

        Args:
            template_name: Name of template to use
        """
        if template_name in self.TEMPLATES:
            self.current_template = template_name
            self._initialize_generator()
            return True
        return False

    def get_template_info(self, template_name=None):
        """
        Get information about a template.

        Args:
            template_name: Template to get info for (current if None)

        Returns:
            Dict with template information
        """
        name = template_name or self.current_template
        if name in self.TEMPLATES:
            return self.TEMPLATES[name].copy()
        return None

    def get_all_templates(self):
        """
        Get information about all available templates.

        Returns:
            Dict of all template information
        """
        return {
            key: {
                'name': val['name'],
                'description': val['description'],
                'ats_score': val['ats_score'],
                'best_for': val['best_for']
            }
            for key, val in self.TEMPLATES.items()
        }

    def markdown_to_pdf(self, markdown_content, output_path, template=None):
        """
        Convert markdown to PDF using specified or current template.

        Args:
            markdown_content: Resume content in markdown format
            output_path: Path to save PDF
            template: Optional template override

        Returns:
            Path to generated PDF
        """
        # Use specified template if provided
        if template and template != self.current_template:
            original_template = self.current_template
            self.set_template(template)
            result = self.generator.markdown_to_pdf(markdown_content, output_path)
            self.set_template(original_template)  # Restore original
            return result

        # Use current template
        return self.generator.markdown_to_pdf(markdown_content, output_path)

    def generate_comparison_pdfs(self, markdown_content, output_dir):
        """
        Generate PDFs using all templates for comparison.

        Args:
            markdown_content: Resume content in markdown format
            output_dir: Directory to save PDFs

        Returns:
            Dict mapping template names to file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        results = {}

        for template_key in self.TEMPLATES:
            output_path = output_dir / f"resume_{template_key}.pdf"
            try:
                self.markdown_to_pdf(markdown_content, str(output_path), template=template_key)
                results[template_key] = str(output_path)
                print(f"✓ Generated {template_key} template: {output_path}")
            except Exception as e:
                print(f"✗ Failed to generate {template_key} template: {e}")
                results[template_key] = None

        return results

    def get_recommended_template(self, job_title=None, industry=None, experience_years=None):
        """
        Recommend best template based on criteria.

        Args:
            job_title: Target job title
            industry: Target industry
            experience_years: Years of experience

        Returns:
            Recommended template key
        """
        # Business roles → Harvard
        if industry and any(keyword in industry.lower() for keyword in
                           ['consulting', 'finance', 'banking', 'investment', 'private equity']):
            return 'harvard'

        if job_title and any(keyword in job_title.lower() for keyword in
                            ['director', 'vp', 'president', 'executive', 'partner', 'manager']):
            return 'harvard'

        # Technical/Creative roles → Modern
        if job_title and any(keyword in job_title.lower() for keyword in
                            ['engineer', 'developer', 'designer', 'architect', 'data', 'analyst']):
            return 'modern'

        # Entry level → Original
        if experience_years and experience_years < 3:
            return 'original'

        # Default to modern for best ATS scores
        return 'modern'


def test_enhanced_generator():
    """Test the enhanced PDF generator"""
    sample_markdown = """# Alex Thompson
alex.thompson@email.com | (555) 987-6543 | linkedin.com/in/alexthompson | New York, NY

## PROFESSIONAL SUMMARY
Data Scientist with 5+ years of experience in machine learning and predictive analytics. Expert in Python, TensorFlow, and cloud-based ML solutions.

## TECHNICAL SKILLS
**Languages:** Python, R, SQL, Java
**ML/AI:** TensorFlow, PyTorch, Scikit-learn, XGBoost
**Tools:** Docker, Kubernetes, AWS, Tableau

## PROFESSIONAL EXPERIENCE

### Senior Data Scientist | DataCorp | New York, NY
*2020 - Present*
- Built recommendation system improving user engagement by 40%
- Deployed ML models serving 10M+ predictions daily
- Led team of 4 data scientists on customer segmentation project

### Data Analyst | Analytics Inc. | Boston, MA
*2018 - 2020*
- Developed predictive models for customer churn
- Created dashboards used by 50+ stakeholders

## EDUCATION

### Master of Science in Data Science | Columbia University
*2016 - 2018*

### Bachelor of Science in Mathematics | MIT
*2012 - 2016*
"""

    generator = EnhancedPDFGenerator()

    # Test all templates
    print("Testing all templates...")
    results = generator.generate_comparison_pdfs(
        sample_markdown,
        "/Users/nagavenkatasaichennu/Library/Mobile Documents/com~apple~CloudDocs/Downloads/new_assistant/assistant/test_templates"
    )

    print(f"\nGenerated PDFs:")
    for template, path in results.items():
        if path:
            info = generator.get_template_info(template)
            print(f"  {info['name']}: {path}")
            print(f"    ATS Score: {info['ats_score']}")
            print(f"    Best for: {info['best_for']}")

    # Test recommendation
    print("\nTemplate Recommendations:")
    print(f"  Consultant: {generator.get_recommended_template(job_title='Management Consultant')}")
    print(f"  Engineer: {generator.get_recommended_template(job_title='Software Engineer')}")
    print(f"  Entry Level: {generator.get_recommended_template(experience_years=1)}")


if __name__ == "__main__":
    test_enhanced_generator()