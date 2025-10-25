"""
Cover Letter PDF Generator using ReportLab
Converts text/markdown cover letter to professional business letter PDF
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.colors import HexColor
from pathlib import Path
import re


class CoverLetterPDFGenerator:
    def __init__(self, output_dir="generated_coverletters"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_pdf(self, cover_letter_text, company_name, job_title):
        """
        Generate professional business letter PDF from cover letter text

        Args:
            cover_letter_text: The cover letter content (markdown/text)
            company_name: Company name for filename
            job_title: Job title for filename

        Returns:
            str: Path to generated PDF file
        """
        # Create filename
        safe_company = re.sub(r'[^\w\s-]', '', company_name).strip().replace(' ', '_')
        safe_job = re.sub(r'[^\w\s-]', '', job_title).strip().replace(' ', '_')
        filename = f"{safe_company}_{safe_job}_CoverLetter.pdf"
        output_path = self.output_dir / filename

        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=letter,
            rightMargin=1*inch,
            leftMargin=1*inch,
            topMargin=1*inch,
            bottomMargin=1*inch
        )

        # Build story (content)
        story = []
        styles = self._create_styles()

        # Parse and add content
        lines = cover_letter_text.strip().split('\n')

        in_header = True
        in_recipient = False
        paragraph_buffer = []

        for line in lines:
            stripped = line.strip()

            # Skip empty lines initially, use them as paragraph separators later
            if not stripped:
                # If we have buffered paragraph text, add it
                if paragraph_buffer:
                    para_text = ' '.join(paragraph_buffer)
                    story.append(Paragraph(para_text, styles['body']))
                    story.append(Spacer(1, 0.15*inch))
                    paragraph_buffer = []
                continue

            # Header section (sender contact info)
            if in_header and not stripped.startswith('[') and not re.match(r'\d{1,2}/\d{1,2}/\d{4}', stripped):
                # Contact info lines
                if '|' in stripped or '@' in stripped or 'linkedin.com' in stripped.lower():
                    # Format contact line with clickable links
                    formatted_line = self._format_contact_line(stripped)
                    story.append(Paragraph(formatted_line, styles['header']))
                else:
                    story.append(Paragraph(stripped, styles['header']))
                continue

            # Date line
            if re.match(r'\d{1,2}/\d{1,2}/\d{4}', stripped) or re.match(r'[A-Z][a-z]+ \d{1,2}, \d{4}', stripped):
                in_header = False
                story.append(Spacer(1, 0.2*inch))  # Space after header
                story.append(Paragraph(stripped, styles['body']))
                story.append(Spacer(1, 0.2*inch))  # Space after date
                in_recipient = True
                continue

            # Recipient section (before greeting)
            if in_recipient:
                if stripped.startswith('Dear'):
                    in_recipient = False
                    story.append(Spacer(1, 0.1*inch))
                    story.append(Paragraph(stripped, styles['body']))
                    story.append(Spacer(1, 0.15*inch))
                else:
                    # Recipient address lines
                    story.append(Paragraph(stripped, styles['body']))
                continue

            # Closing section
            if stripped in ['Sincerely,', 'Best regards,', 'Thank you,', 'Regards,']:
                # Flush any remaining paragraph
                if paragraph_buffer:
                    para_text = ' '.join(paragraph_buffer)
                    story.append(Paragraph(para_text, styles['body']))
                    paragraph_buffer = []

                story.append(Spacer(1, 0.15*inch))
                story.append(Paragraph(stripped, styles['body']))
                story.append(Spacer(1, 0.6*inch))  # Space for signature
                continue

            # Final signature name
            if story and any(closing in str(story[-2]) for closing in ['Sincerely', 'Best regards', 'Thank you', 'Regards']):
                story.append(Paragraph(stripped, styles['body']))
                continue

            # Regular body paragraph text
            # Accumulate lines into paragraphs
            paragraph_buffer.append(stripped)

        # Flush any remaining paragraph
        if paragraph_buffer:
            para_text = ' '.join(paragraph_buffer)
            story.append(Paragraph(para_text, styles['body']))

        # Build PDF
        try:
            doc.build(story)
            print(f"✓ Cover letter PDF generated: {output_path}")
            return str(output_path)
        except Exception as e:
            print(f"Error generating cover letter PDF: {e}")
            return None

    def _create_styles(self):
        """Create custom styles for professional business letter"""
        styles = getSampleStyleSheet()

        # Header style (sender contact info)
        styles.add(ParagraphStyle(
            name='header',
            parent=styles['Normal'],
            fontSize=11,
            leading=14,
            alignment=TA_LEFT,
            spaceAfter=2,
            textColor=HexColor('#000000')
        ))

        # Body style (all letter content)
        styles.add(ParagraphStyle(
            name='body',
            parent=styles['Normal'],
            fontSize=11,
            leading=16,
            alignment=TA_LEFT,
            textColor=HexColor('#000000'),
            spaceAfter=0
        ))

        return styles

    def _format_contact_line(self, line):
        """Format contact line with clickable links"""
        # Add hyperlinks for LinkedIn, GitHub, Portfolio
        formatted = line

        # LinkedIn
        if 'linkedin.com/in/' in formatted.lower():
            formatted = re.sub(
                r'(linkedin\.com/in/[\w-]+)',
                r'<link href="https://\1" color="blue"><u>LinkedIn</u></link>',
                formatted,
                flags=re.IGNORECASE
            )
        elif 'LinkedIn' in formatted and 'linkedin.com/in/' not in formatted.lower():
            # If just the word LinkedIn without URL
            formatted = formatted.replace(
                'LinkedIn',
                '<link href="https://linkedin.com/in/naga-venkata-sai-chennu" color="blue"><u>LinkedIn</u></link>'
            )

        # GitHub
        if 'github.com/' in formatted.lower():
            formatted = re.sub(
                r'(github\.com/[\w-]+)',
                r'<link href="https://\1" color="blue"><u>GitHub</u></link>',
                formatted,
                flags=re.IGNORECASE
            )
        elif 'GitHub' in formatted and 'github.com/' not in formatted.lower():
            formatted = formatted.replace(
                'GitHub',
                '<link href="https://github.com/nagavenkatasai7" color="blue"><u>GitHub</u></link>'
            )

        # Portfolio
        if 'nagavenkatasai7.github.io' in formatted.lower():
            formatted = re.sub(
                r'(nagavenkatasai7\.github\.io/[\w/-]*)',
                r'<link href="https://\1" color="blue"><u>Portfolio</u></link>',
                formatted,
                flags=re.IGNORECASE
            )
        elif 'Portfolio' in formatted:
            formatted = formatted.replace(
                'Portfolio',
                '<link href="https://nagavenkatasai7.github.io/portfolio/" color="blue"><u>Portfolio</u></link>'
            )

        return formatted


def main():
    """Test cover letter PDF generator"""
    sample_cover_letter = """Naga Venkata Sai Chennu
Arlington, VA 22204
naga.chennu@example.com | +1 571-546-6207
LinkedIn | GitHub | Portfolio

January 25, 2025

Hiring Manager
Google Inc.
1600 Amphitheatre Parkway
Mountain View, CA 94043

Dear Hiring Manager,

I am writing to express my strong interest in the Senior Software Engineer position at Google. With over 5 years of experience building scalable distributed systems and a proven track record of delivering high-impact projects, I am excited about the opportunity to contribute to Google's mission of organizing the world's information.

In my current role at TechCorp, I led the architecture and implementation of a microservices platform that now handles over 10 million requests per day with 99.99% uptime. This experience has given me deep expertise in Python, distributed systems, and cloud infrastructure - skills that directly align with the requirements for this role. I am particularly drawn to Google's emphasis on innovation and technical excellence, and I believe my background in building scalable systems would enable me to make meaningful contributions to your team.

I am impressed by Google's commitment to solving complex technical challenges at scale, and I am eager to bring my experience in system design and cloud architecture to help drive your projects forward. I would welcome the opportunity to discuss how my skills and experience align with your team's needs.

Thank you for considering my application. I look forward to the possibility of contributing to Google's continued success.

Sincerely,

Naga Venkata Sai Chennu"""

    generator = CoverLetterPDFGenerator()
    output_path = generator.generate_pdf(
        sample_cover_letter,
        "Google",
        "Senior Software Engineer"
    )

    if output_path:
        print(f"\n✓ Test cover letter PDF created successfully")
        print(f"✓ Location: {output_path}")
    else:
        print("\n✗ Failed to create test cover letter PDF")


if __name__ == "__main__":
    main()
