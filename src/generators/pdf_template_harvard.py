"""
Harvard Business School Resume Template
Ultra ATS-optimized single-column format following HBS guidelines
"""
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from pathlib import Path
import re


class HarvardBusinessTemplate:
    """
    Harvard Business School Resume Template

    Key ATS Optimizations:
    - Single-column format (100% ATS compatible)
    - Times New Roman font (most ATS-friendly)
    - Clear section delineation with lines
    - Strict hierarchical structure
    - No tables, graphics, or complex formatting
    - Left-aligned text throughout
    - Standard section names in ALL CAPS
    - Consistent date formatting (Month Year - Month Year)
    """

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup Harvard Business School style guidelines"""

        # Name - Centered, larger font
        self.styles.add(ParagraphStyle(
            name='HBSName',
            parent=self.styles['Heading1'],
            fontSize=14,
            textColor='#000000',
            spaceAfter=2,
            alignment=TA_CENTER,
            fontName='Times-Bold',
            leading=16
        ))

        # Contact info - Centered, smaller
        self.styles.add(ParagraphStyle(
            name='HBSContact',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor='#000000',
            spaceAfter=8,
            alignment=TA_CENTER,
            fontName='Times-Roman',
            leading=12
        ))

        # Section headers - ALL CAPS with underline effect
        self.styles.add(ParagraphStyle(
            name='HBSSectionHeader',
            parent=self.styles['Heading2'],
            fontSize=11,
            textColor='#000000',
            spaceAfter=4,
            spaceBefore=8,
            fontName='Times-Bold',
            alignment=TA_LEFT,
            borderWidth=1,
            borderColor='#000000',
            borderPadding=(0, 0, 2, 0),
            leading=13
        ))

        # Organization/School name - Bold
        self.styles.add(ParagraphStyle(
            name='HBSOrganization',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor='#000000',
            spaceAfter=0,
            fontName='Times-Bold',
            alignment=TA_LEFT,
            leading=13
        ))

        # Job title/Degree - Regular with location right-aligned
        self.styles.add(ParagraphStyle(
            name='HBSTitle',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor='#000000',
            spaceAfter=2,
            fontName='Times-Italic',
            alignment=TA_LEFT,
            leading=13
        ))

        # Date line - Italics
        self.styles.add(ParagraphStyle(
            name='HBSDate',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor='#000000',
            spaceAfter=3,
            fontName='Times-Italic',
            alignment=TA_LEFT,
            leading=12
        ))

        # Normal body text
        self.styles.add(ParagraphStyle(
            name='HBSNormal',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor='#000000',
            spaceAfter=4,
            fontName='Times-Roman',
            leading=13,
            alignment=TA_LEFT
        ))

        # Bullet points - Indented
        self.styles.add(ParagraphStyle(
            name='HBSBullet',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor='#000000',
            spaceAfter=2,
            fontName='Times-Roman',
            leftIndent=18,
            bulletIndent=6,
            leading=13,
            alignment=TA_LEFT
        ))

        # Sub-bullet points - More indented
        self.styles.add(ParagraphStyle(
            name='HBSSubBullet',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor='#000000',
            spaceAfter=2,
            fontName='Times-Roman',
            leftIndent=36,
            bulletIndent=24,
            leading=12,
            alignment=TA_LEFT
        ))

    def markdown_to_pdf(self, markdown_content, output_path):
        """Convert markdown resume to Harvard Business School PDF format"""

        # Create PDF with specific margins (HBS uses 0.5" to 1")
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=0.6*inch,
            leftMargin=0.6*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )

        # Parse and build story
        story = self._parse_markdown_hbs_style(markdown_content)

        # Generate PDF
        doc.build(story)
        return output_path

    def _parse_markdown_hbs_style(self, markdown_content):
        """Parse markdown following HBS structure guidelines"""
        story = []
        lines = markdown_content.split('\n')

        # Track current section for proper formatting
        current_section = None
        in_experience = False
        current_org = None

        # Infinite loop protection - prevent runaway parsing
        MAX_ITERATIONS = 100000
        iteration_count = 0

        i = 0
        while i < len(lines):
            # Safety check to prevent infinite loops
            iteration_count += 1
            if iteration_count > MAX_ITERATIONS:
                print(f"WARNING: Markdown parsing exceeded {MAX_ITERATIONS} iterations. Content may be truncated.")
                break
            line = lines[i].strip()

            # Skip empty lines but add small spacing
            if not line:
                if len(story) > 0 and not isinstance(story[-1], Spacer):
                    story.append(Spacer(1, 3))
                i += 1
                continue

            # Name (H1)
            if line.startswith('# '):
                name = line[2:].strip().upper()  # HBS often uses all caps for name
                story.append(Paragraph(name, self.styles['HBSName']))
                i += 1
                continue

            # Contact info (usually after name)
            if i > 0 and '|' in line and '@' in line:
                # Format contact info on one or two lines
                contact_parts = line.split('|')

                # Process each contact part separately to make ALL links clickable
                clickable_parts = []
                for part in contact_parts:
                    part = part.strip()

                    # Email - make clickable
                    if '@' in part and '.' in part:
                        part = f'<link href="mailto:{part}" color="#0066cc"><u>{part}</u></link>'
                    # LinkedIn - make clickable
                    elif 'linkedin.com' in part.lower() or 'linkedin' in part.lower():
                        url = part if part.startswith('http') else f'https://{part}'
                        part = f'<link href="{url}" color="#0066cc"><u>{part}</u></link>'
                    # GitHub - make clickable
                    elif 'github.com' in part.lower() or 'github' in part.lower():
                        url = part if part.startswith('http') else f'https://{part}'
                        part = f'<link href="{url}" color="#0066cc"><u>{part}</u></link>'
                    # Portfolio or other URLs - make clickable
                    elif ('http://' in part or 'https://' in part or '.com' in part or '.io' in part or 'portfolio' in part.lower()):
                        url = part if part.startswith('http') else f'https://{part}'
                        part = f'<link href="{url}" color="#0066cc"><u>{part}</u></link>'

                    clickable_parts.append(part)

                contact_line = ' • '.join(clickable_parts)
                story.append(Paragraph(contact_line, self.styles['HBSContact']))
                story.append(Spacer(1, 6))
                i += 1
                continue

            # Section headers (H2)
            if line.startswith('## '):
                header = line[3:].strip().upper()

                # Add section line/separator
                story.append(Spacer(1, 4))
                story.append(Paragraph(f'<b>{header}</b>', self.styles['HBSSectionHeader']))
                story.append(Spacer(1, 2))

                # Track which section we're in
                if 'EXPERIENCE' in header or 'EMPLOYMENT' in header:
                    current_section = 'experience'
                    in_experience = True
                elif 'EDUCATION' in header:
                    current_section = 'education'
                    in_experience = False
                elif 'SKILL' in header:
                    current_section = 'skills'
                    in_experience = False
                elif 'SUMMARY' in header or 'OBJECTIVE' in header:
                    current_section = 'summary'
                    in_experience = False
                elif 'PUBLICATION' in header or 'RESEARCH' in header or 'PAPER' in header:
                    current_section = 'publications'
                    in_experience = False
                else:
                    current_section = 'other'
                    in_experience = False

                i += 1
                continue

            # Job titles/Education entries (H3)
            if line.startswith('### '):
                content = line[4:].strip()

                # Parse organization, title, and location
                # Format: "Company Name | Job Title | Location" or similar variations
                if '|' in content:
                    parts = content.split('|')
                    if len(parts) >= 2:
                        org = parts[0].strip()
                        title = parts[1].strip()
                        location = parts[2].strip() if len(parts) > 2 else ''

                        # Organization name (bold)
                        story.append(Paragraph(f'<b>{org}</b>', self.styles['HBSOrganization']))

                        # Title and location on same line if possible
                        if location:
                            # Create a table-like effect with title left and location right
                            title_loc = f'{title} <font color="white">{"." * 50}</font> {location}'
                            story.append(Paragraph(title, self.styles['HBSTitle']))
                        else:
                            story.append(Paragraph(title, self.styles['HBSTitle']))

                        current_org = org
                else:
                    # Fallback - just display as is
                    story.append(Paragraph(f'<b>{content}</b>', self.styles['HBSOrganization']))
                    current_org = content

                i += 1
                continue

            # Dates (italic text between asterisks)
            if line.startswith('*') and line.endswith('*'):
                date_text = line[1:-1].strip()
                story.append(Paragraph(f'<i>{date_text}</i>', self.styles['HBSDate']))
                i += 1
                continue

            # Bullet points
            if line.startswith('- ') or line.startswith('• '):
                bullet_text = line[2:].strip()

                # Clean markdown formatting
                bullet_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', bullet_text)
                bullet_text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', bullet_text)

                # Check if this might be a sub-bullet (starts with more spaces in original)
                if i > 0 and len(lines[i]) - len(lines[i].lstrip()) > 2:
                    story.append(Paragraph(f'◦ {bullet_text}', self.styles['HBSSubBullet']))
                else:
                    story.append(Paragraph(f'• {bullet_text}', self.styles['HBSBullet']))

                i += 1
                continue

            # Skills section - special handling
            if current_section == 'skills':
                if ':' in line:
                    # Format: "Category: skill1, skill2, skill3"
                    category, skills = line.split(':', 1)
                    formatted = f'<b>{category}:</b>{skills}'
                    story.append(Paragraph(formatted, self.styles['HBSNormal']))
                else:
                    story.append(Paragraph(line, self.styles['HBSNormal']))
                i += 1
                continue

            # Summary/Objective text
            if current_section == 'summary':
                # Clean any markdown formatting
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
                story.append(Paragraph(text, self.styles['HBSNormal']))
                i += 1
                continue

            # Default paragraph handling
            if line:
                text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', text)
                story.append(Paragraph(text, self.styles['HBSNormal']))

            i += 1

        return story


def test_harvard_template():
    """Test the Harvard Business School template"""
    sample_markdown = """# MICHAEL CHEN
michael.chen@hbs.edu | (617) 555-0123 | linkedin.com/in/michaelchen | Boston, MA 02163

## EDUCATION

### Harvard Business School | Master of Business Administration | Boston, MA
*September 2022 - May 2024 (Expected)*
- Finance and Technology Management concentrations; GPA: 3.8/4.0
- Leadership: VP of Finance, Technology Club; Case Team Leader, Consulting Club
- Relevant Coursework: Financial Management, Data Analytics, Strategic Management

### Massachusetts Institute of Technology | Bachelor of Science, Computer Science | Cambridge, MA
*September 2014 - June 2018*
- Summa Cum Laude, GPA: 3.9/4.0; Dean's List all semesters
- Activities: President, Computer Science Society; Captain, Varsity Tennis Team

## PROFESSIONAL EXPERIENCE

### McKinsey & Company | Senior Business Analyst | New York, NY
*July 2020 - August 2022*
- Led cross-functional team of 8 consultants on digital transformation for Fortune 500 retail client
- Developed machine learning model to optimize inventory management, reducing costs by $45M annually
- Designed and implemented new e-commerce strategy increasing online revenue by 65% in 18 months
- Presented strategic recommendations to C-suite executives, securing $200M investment approval
- Managed 3 junior analysts, providing mentorship and performance feedback

### Goldman Sachs | Technology Analyst | New York, NY
*July 2018 - June 2020*
- Built algorithmic trading platform processing 1M+ transactions daily with 99.99% uptime
- Optimized database queries reducing latency by 75% and saving $2M in infrastructure costs
- Collaborated with traders to develop real-time risk analytics dashboard used by 200+ users
- Led migration of legacy systems to cloud infrastructure, completing project 3 months ahead of schedule

### Microsoft | Software Engineering Intern | Redmond, WA
*June 2017 - August 2017*
- Developed features for Microsoft Teams serving 250M+ users globally
- Implemented automated testing framework reducing QA time by 40%
- Won intern hackathon with innovative collaboration tool prototype

## ADDITIONAL INFORMATION

**Technical Skills:** Python, Java, SQL, R, Tableau, AWS, Machine Learning, Financial Modeling
**Languages:** English (Native), Mandarin Chinese (Fluent), Spanish (Conversational)
**Interests:** Venture Capital, FinTech Innovation, Marathon Running (Boston 2023: 3:15:42)
**Leadership:** Board Member, Boston Youth Mentorship Program (2020-Present)
"""

    generator = HarvardBusinessTemplate()
    output_path = "/Users/nagavenkatasaichennu/Library/Mobile Documents/com~apple~CloudDocs/Downloads/new_assistant/assistant/test_harvard_resume.pdf"

    try:
        generator.markdown_to_pdf(sample_markdown, output_path)
        print(f"✓ Harvard Business School PDF generated successfully: {output_path}")
    except Exception as e:
        print(f"✗ PDF generation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_harvard_template()