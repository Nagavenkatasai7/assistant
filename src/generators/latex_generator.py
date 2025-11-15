"""
LaTeX resume generator using Jinja2 templates
"""
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class LaTeXGenerator:
    """Generate LaTeX resumes from Jinja2 templates"""

    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize LaTeX generator with Jinja2 environment.

        Args:
            template_dir: Directory containing .tex.j2 templates
                         (defaults to src/templates)
        """
        if template_dir is None:
            # Default to src/templates relative to this file
            template_dir = Path(__file__).parent.parent / 'templates'

        self.template_dir = Path(template_dir)

        if not self.template_dir.exists():
            raise FileNotFoundError(f"Template directory not found: {self.template_dir}")

        # Configure Jinja2 with custom delimiters to avoid LaTeX conflicts
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape([]),  # No auto-escaping (we do it manually)
            block_start_string='<BLOCK>',
            block_end_string='</BLOCK>',
            variable_start_string='<VAR>',
            variable_end_string='</VAR>',
            comment_start_string='<#',
            comment_end_string='#>',
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )

        logger.info(f"LaTeX generator initialized with template directory: {self.template_dir}")

    def render_resume(self, data: dict, template_name: str = 'resume_template.tex.j2') -> str:
        """
        Render LaTeX resume template with data.

        Args:
            data: Resume data dictionary (already LaTeX-escaped)
            template_name: Template filename (default: resume_template.tex.j2)

        Returns:
            Rendered LaTeX source code as string

        Raises:
            TemplateNotFound: If template file doesn't exist
            Exception: If rendering fails
        """
        try:
            template = self.env.get_template(template_name)
            latex_content = template.render(**data)

            logger.info(f"Successfully rendered template {template_name}")
            logger.debug(f"Rendered LaTeX length: {len(latex_content)} characters")

            return latex_content

        except TemplateNotFound:
            logger.error(f"Template not found: {template_name} in {self.template_dir}")
            raise

        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            raise

    def save_tex_file(self, latex_content: str, output_path: str) -> Path:
        """
        Save rendered LaTeX content to .tex file.

        Args:
            latex_content: Rendered LaTeX source code
            output_path: Path to save .tex file

        Returns:
            Path object of saved file

        Raises:
            IOError: If file cannot be written
        """
        output_path = Path(output_path)

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure .tex extension
        if output_path.suffix != '.tex':
            output_path = output_path.with_suffix('.tex')

        try:
            output_path.write_text(latex_content, encoding='utf-8')
            logger.info(f"Saved LaTeX file: {output_path}")
            return output_path

        except IOError as e:
            logger.error(f"Failed to save LaTeX file {output_path}: {e}")
            raise

    def generate_and_save(self, data: dict, output_path: str,
                          template_name: str = 'resume_template.tex.j2') -> Path:
        """
        Render template and save to file in one step.

        Args:
            data: Resume data dictionary
            output_path: Path to save .tex file
            template_name: Template filename

        Returns:
            Path to saved .tex file
        """
        latex_content = self.render_resume(data, template_name)
        return self.save_tex_file(latex_content, output_path)

    def validate_template(self, template_name: str = 'resume_template.tex.j2') -> bool:
        """
        Validate that template exists and can be loaded.

        Args:
            template_name: Template filename to validate

        Returns:
            True if template is valid
        """
        try:
            self.env.get_template(template_name)
            return True
        except TemplateNotFound:
            return False
        except Exception as e:
            logger.error(f"Template validation error: {e}")
            return False

    def list_available_templates(self) -> list:
        """
        List all available .tex.j2 templates.

        Returns:
            List of template filenames
        """
        if not self.template_dir.exists():
            return []

        templates = list(self.template_dir.glob('*.tex.j2'))
        return [t.name for t in templates]


def test_latex_generator():
    """Test the LaTeX generator with sample data"""
    from .latex_data_transformer import create_sample_resume_data, LaTeXDataTransformer

    print("Testing LaTeX Generator...")

    # Create sample data
    raw_data = create_sample_resume_data()
    print(f"✓ Created sample resume data")

    # Transform data
    transformer = LaTeXDataTransformer()
    latex_data = transformer.transform(raw_data)
    print(f"✓ Transformed data for LaTeX")

    # Validate
    errors = transformer.validate_output(latex_data)
    if errors:
        print(f"✗ Validation errors: {errors}")
        return False

    print(f"✓ Data validation passed")

    # Generate LaTeX
    generator = LaTeXGenerator()
    latex_content = generator.render_resume(latex_data)
    print(f"✓ Rendered LaTeX template ({len(latex_content)} characters)")

    # Save to file
    output_path = Path(__file__).parent.parent.parent / 'test_output' / 'sample_resume.tex'
    saved_path = generator.save_tex_file(latex_content, str(output_path))
    print(f"✓ Saved LaTeX file: {saved_path}")

    # Show preview
    print("\nFirst 500 characters of generated LaTeX:")
    print("=" * 80)
    print(latex_content[:500])
    print("=" * 80)

    print("\n✓ LaTeX generator test completed successfully!")
    print(f"\nNext step: Compile {saved_path} with pdflatex or Docker")

    return True


if __name__ == '__main__':
    test_latex_generator()
