"""
Complete LaTeX resume generation pipeline
Integrates data transformation, template rendering, and compilation
"""
from pathlib import Path
from typing import Optional, Tuple
import logging

from .latex_data_transformer import LaTeXDataTransformer
from .latex_generator import LaTeXGenerator
from .latex_compiler import compile_with_retry

logger = logging.getLogger(__name__)


class LaTeXResumePipeline:
    """End-to-end pipeline for LaTeX resume generation"""

    def __init__(self, template_name: str = 'resume_template.tex.j2'):
        """
        Initialize pipeline.

        Args:
            template_name: Jinja2 template filename
        """
        self.template_name = template_name
        self.transformer = LaTeXDataTransformer()
        self.generator = LaTeXGenerator()

    def generate_resume(
        self,
        resume_data: dict,
        output_path: str,
        compile_pdf: bool = True
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Generate LaTeX resume from AI data.

        Args:
            resume_data: Raw resume data from AI (JSON/dict format)
            output_path: Path for output PDF (or .tex if compile_pdf=False)
            compile_pdf: Whether to compile .tex to PDF (requires Docker/pdflatex)

        Returns:
            Tuple of (tex_path, pdf_path, error_message)
            - tex_path: Path to generated .tex file
            - pdf_path: Path to generated PDF (None if not compiled or failed)
            - error_message: Error description (None if successful)

        Example:
            >>> pipeline = LaTeXResumePipeline()
            >>> tex, pdf, err = pipeline.generate_resume(ai_data, 'resume.pdf')
            >>> if pdf:
            >>>     print(f"Success! PDF: {pdf}")
            >>> else:
            >>>     print(f"LaTeX generated: {tex}")
            >>>     print(f"Compile manually with: pdflatex {tex}")
        """
        try:
            # Step 1: Transform data
            logger.info("Transforming resume data for LaTeX...")
            latex_data = self.transformer.transform(resume_data)

            # Step 2: Validate
            errors = self.transformer.validate_output(latex_data)
            if errors:
                error_msg = f"Data validation failed: {', '.join(errors)}"
                logger.error(error_msg)
                return None, None, error_msg

            # Step 3: Render template
            logger.info("Rendering LaTeX template...")
            latex_content = self.generator.render_resume(latex_data, self.template_name)

            # Step 4: Save .tex file
            output_path = Path(output_path)
            if compile_pdf and output_path.suffix == '.pdf':
                tex_path = output_path.with_suffix('.tex')
            else:
                tex_path = output_path if output_path.suffix == '.tex' else output_path.with_suffix('.tex')

            tex_path = self.generator.save_tex_file(latex_content, str(tex_path))
            logger.info(f"LaTeX source saved: {tex_path}")

            # Step 5: Compile (if requested and tools available)
            if not compile_pdf:
                logger.info("Skipping PDF compilation (compile_pdf=False)")
                return str(tex_path), None, None

            logger.info("Compiling LaTeX to PDF...")
            pdf_path, compile_error = compile_with_retry(str(tex_path))

            if compile_error:
                warning = (
                    f"PDF compilation failed: {compile_error}. "
                    f"LaTeX source saved at {tex_path}. "
                    f"Compile manually with: pdflatex {tex_path}"
                )
                logger.warning(warning)
                return str(tex_path), None, warning

            logger.info(f"PDF generated successfully: {pdf_path}")
            return str(tex_path), pdf_path, None

        except Exception as e:
            error_msg = f"Resume generation failed: {e}"
            logger.error(error_msg, exc_info=True)
            return None, None, error_msg


def generate_latex_resume(
    ai_resume_data: dict,
    output_path: str,
    compile_to_pdf: bool = True
) -> dict:
    """
    Convenience function for LaTeX resume generation.

    Args:
        ai_resume_data: Resume data from AI generation
        output_path: Output file path (.pdf or .tex)
        compile_to_pdf: Attempt PDF compilation (requires LaTeX)

    Returns:
        Dictionary with:
            - success: bool
            - tex_file: path to .tex file (always generated)
            - pdf_file: path to .pdf file (if compilation successful)
            - error: error message (if failed)
            - warning: warning message (if .tex generated but PDF failed)
    """
    pipeline = LaTeXResumePipeline()
    tex_path, pdf_path, error_or_warning = pipeline.generate_resume(
        ai_resume_data,
        output_path,
        compile_pdf=compile_to_pdf
    )

    result = {
        'success': tex_path is not None,
        'tex_file': tex_path,
        'pdf_file': pdf_path,
        'error': None,
        'warning': None
    }

    if error_or_warning:
        if pdf_path is None and tex_path is not None:
            # .tex generated but PDF compilation failed
            result['warning'] = error_or_warning
        else:
            # Complete failure
            result['error'] = error_or_warning
            result['success'] = False

    return result


# Convenience alias
generate_resume_latex = generate_latex_resume
