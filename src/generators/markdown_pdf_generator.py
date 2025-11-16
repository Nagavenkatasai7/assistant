"""
Professional ATS-Friendly Resume Generator using ReportLab
Based on industry best practices for 2025
"""
from pathlib import Path
from typing import Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether, HRFlowable
from reportlab.lib import colors
import logging

logger = logging.getLogger(__name__)


class ResumeMarkdownPDFGenerator:
    """Generate professional ATS-friendly resume PDFs using ReportLab"""

    def __init__(self):
        self.styles = None
        self._setup_styles()

    def _setup_styles(self):
        """Setup professional resume styles"""
        self.styles = getSampleStyleSheet()

        # Name style - prominent, professional, clean
        self.styles.add(ParagraphStyle(
            name='ResumeName',
            parent=self.styles['Heading1'],
            fontSize=20,  # Larger for better visual hierarchy
            textColor=colors.HexColor('#2c3e50'),  # Professional dark gray-blue (matches headers)
            spaceAfter=8,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
            leading=24  # Better line height
        ))

        # Contact style - small, centered
        self.styles.add(ParagraphStyle(
            name='Contact',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            spaceAfter=2
        ))

        # Section header - clean, elegant design with subtle underline (modern ATS-friendly)
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,  # Slightly larger for better hierarchy
            textColor=colors.HexColor('#2c3e50'),  # Professional dark gray-blue
            spaceBefore=12,
            spaceAfter=8,
            fontName='Helvetica-Bold',
            # Clean bottom border only - elegant, not boxy
            borderWidth=0,
            borderPadding=0,
            # Add subtle underline effect using different approach
            leftIndent=0,
            rightIndent=0,
        ))

        # Job title / Project name - bold
        self.styles.add(ParagraphStyle(
            name='JobTitle',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
            spaceBefore=6,
            spaceAfter=2
        ))

        # Dates - italic, smaller
        self.styles.add(ParagraphStyle(
            name='Dates',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Oblique',
            spaceAfter=4
        ))

        # Bullet point
        self.styles.add(ParagraphStyle(
            name='ResumeBullet',
            parent=self.styles['Normal'],
            fontSize=9,
            leftIndent=20,
            spaceBefore=2,
            spaceAfter=2,
            bulletIndent=10
        ))

        # Regular paragraph
        self.styles.add(ParagraphStyle(
            name='ResumeParagraph',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6
        ))

    def _clean_text(self, text: str) -> str:
        """Clean special characters for PDF compatibility"""
        text = text.replace('–', '-').replace('—', '-')
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace("'", "'").replace("'", "'")
        text = text.replace('…', '...').replace('•', '-')
        # Escape XML special characters for ReportLab
        text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        return text

    def generate_pdf(self, markdown_content: str, output_path: str) -> tuple[str, Optional[str]]:
        """Generate professional ATS-friendly PDF from markdown"""
        try:
            pdf_path = f"{output_path}.pdf"

            # Create PDF with 0.75 inch margins
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=letter,
                rightMargin=0.75 * inch,
                leftMargin=0.75 * inch,
                topMargin=0.6 * inch,
                bottomMargin=0.6 * inch
            )

            # Build story (list of flowables)
            story = []

            # Process markdown
            lines = markdown_content.split('\n')
            in_bullets = False
            current_section = []

            for line in lines:
                line = line.rstrip()

                if not line.strip():
                    if in_bullets:
                        in_bullets = False
                    continue

                # NAME
                if line.startswith('# '):
                    name = self._clean_text(line[2:].strip())
                    story.append(Paragraph(name, self.styles['ResumeName']))

                # SECTION HEADER with elegant underline
                elif line.startswith('## '):
                    title = self._clean_text(line[3:].strip()).upper()
                    story.append(Spacer(1, 0.1 * inch))
                    story.append(Paragraph(f'<b>{title}</b>', self.styles['SectionHeader']))
                    # Add clean underline (modern, not boxy)
                    story.append(HRFlowable(
                        width="100%",
                        thickness=1.5,
                        color=colors.HexColor('#2c3e50'),  # Matches header color
                        spaceBefore=2,
                        spaceAfter=6
                    ))

                # JOB TITLE / PROJECT
                elif line.startswith('### '):
                    text = self._clean_text(line[4:].strip().replace('**', '').replace('*', ''))
                    story.append(Paragraph(f'<b>{text}</b>', self.styles['JobTitle']))

                # BULLET
                elif line.startswith('- '):
                    in_bullets = True
                    text = self._clean_text(line[2:].strip().replace('**', '').replace('*', ''))
                    # Use bullet character
                    story.append(Paragraph(f'• {text}', self.styles['ResumeBullet']))

                # DATES
                elif line.startswith('*') and line.endswith('*') and '**' not in line:
                    in_bullets = False
                    text = self._clean_text(line.strip('*').strip())
                    story.append(Paragraph(f'<i>{text}</i>', self.styles['Dates']))

                # CONTACT or PARAGRAPH
                else:
                    in_bullets = False

                    if '|' in line or ('@' in line and 'http' in line):
                        # Contact information
                        if '|' in line:
                            parts = [self._clean_text(p.strip()) for p in line.split('|')]
                            for part in parts:
                                if part:
                                    story.append(Paragraph(part, self.styles['Contact']))
                        else:
                            story.append(Paragraph(self._clean_text(line), self.styles['Contact']))
                        story.append(Spacer(1, 0.1 * inch))
                    else:
                        # Regular paragraph
                        text = self._clean_text(line.replace('**', '').replace('*', ''))
                        story.append(Paragraph(text, self.styles['ResumeParagraph']))

            # Build PDF
            doc.build(story)

            logger.info(f"✓ Professional ATS-friendly PDF generated: {pdf_path}")
            return pdf_path, None

        except Exception as e:
            error_msg = f"PDF generation failed: {str(e)}"
            logger.error(error_msg)
            import traceback
            logger.error(traceback.format_exc())
            return None, error_msg
