"""
Modern Professional PDF Template Generator

A two-column professional template with modern styling.
Handles multi-page documents with intelligent layout flow.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from pathlib import Path


class ModernProfessionalTemplate:
    """Modern two-column professional template with multi-page support"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_styles()

    def _setup_styles(self):
        """Setup custom styles for the modern template"""

        # Name style - Large and bold
        self.styles.add(ParagraphStyle(
            name='ModernName',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

        # Title style - Professional title under name
        self.styles.add(ParagraphStyle(
            name='ModernTitle',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))

        # Section headers
        self.styles.add(ParagraphStyle(
            name='ModernSectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#2980b9'),
            spaceAfter=6,
            spaceBefore=12,
            fontName='Helvetica-Bold',
            borderColor=colors.HexColor('#2980b9'),
            borderWidth=0,
            borderPadding=0,
        ))

        # Job title style
        self.styles.add(ParagraphStyle(
            name='ModernJobTitle',
            parent=self.styles['Normal'],
            fontSize=11,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=2
        ))

        # Company style
        self.styles.add(ParagraphStyle(
            name='ModernCompany',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Oblique',
            textColor=colors.HexColor('#34495e'),
            spaceAfter=2
        ))

        # Date style
        self.styles.add(ParagraphStyle(
            name='ModernDate',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#7f8c8d'),
            spaceAfter=4,
            fontName='Helvetica-Oblique'
        ))

        # Bullet points
        self.styles.add(ParagraphStyle(
            name='ModernBullet',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2c3e50'),
            leftIndent=12,
            spaceAfter=3,
            alignment=TA_JUSTIFY
        ))

        # Contact info style
        self.styles.add(ParagraphStyle(
            name='ModernContact',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=2,
            alignment=TA_CENTER
        ))

        # Summary style
        self.styles.add(ParagraphStyle(
            name='ModernSummary',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#2c3e50'),
            alignment=TA_JUSTIFY,
            spaceAfter=6
        ))

        # Skills style
        self.styles.add(ParagraphStyle(
            name='ModernSkills',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=3
        ))

    def generate(self, markdown_content, output_path):
        """Generate PDF from markdown content using hybrid layout approach"""

        # Create the PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            leftMargin=0.5*inch,
            rightMargin=0.5*inch
        )

        # Parse the markdown content
        sections = self._parse_markdown_sections(markdown_content)

        # Build the hybrid layout
        story = self._build_hybrid_layout(sections)

        # Generate PDF
        doc.build(story)
        return output_path

    def _parse_markdown_sections(self, markdown_content):
        """Parse markdown into structured sections"""
        sections = {
            'name': '',
            'contact': '',
            'title': '',
            'summary': '',
            'skills': [],
            'experience': [],
            'education': [],
            'certifications': [],
            'projects': [],
            'publications': []
        }

        lines = markdown_content.split('\n')
        current_section = None
        current_subsection = None

        # Safety limit to prevent infinite loops in malformed markdown
        MAX_LINES = 100000
        line_count = 0

        for line in lines:
            # Infinite loop protection - bail out if processing too many lines
            line_count += 1
            if line_count > MAX_LINES:
                # Log the issue but continue with what we've parsed so far
                print(f"WARNING: Markdown parsing exceeded {MAX_LINES} lines limit. Content may be truncated.")
                break
            line = line.strip()

            # Parse name (H1)
            if line.startswith('# '):
                sections['name'] = line[2:].strip()
                continue

            # Parse contact info (usually right after name)
            if sections['name'] and not sections['contact'] and '|' in line:
                sections['contact'] = line
                continue

            # Parse title - DISABLED for students who don't want a title
            # (Title parsing commented out - shows only name, no professional title)
            # if sections['contact'] and not sections['title'] and not line.startswith('#') and line and not current_section:
            #     if len(line) < 100 and '"' not in line and 'demonstrated' not in line.lower():
            #         sections['title'] = line
            #     continue

            # Parse section headers (H2)
            if line.startswith('## '):
                header = line[3:].strip().lower()

                # Save previous subsection
                if current_subsection and current_section:
                    sections[current_section].append(current_subsection)
                    current_subsection = None

                # Map headers to section names
                if 'experience' in header or 'professional experience' in header:
                    current_section = 'experience'
                elif 'education' in header:
                    current_section = 'education'
                elif 'skills' in header or 'technical' in header:
                    current_section = 'skills'
                elif 'summary' in header or 'objective' in header:
                    current_section = 'summary'
                elif 'certification' in header:
                    current_section = 'certifications'
                elif 'project' in header:
                    current_section = 'projects'
                elif 'publication' in header or 'research' in header or 'paper' in header:
                    current_section = 'publications'
                else:
                    current_section = None
                continue

            # Parse subsection headers (H3) for experience, education, projects
            if line.startswith('### '):
                if current_subsection and current_section:
                    sections[current_section].append(current_subsection)

                title = line[4:].strip()

                if current_section == 'experience':
                    current_subsection = {
                        'title': title,
                        'company': '',
                        'location': '',
                        'date': '',
                        'bullets': []
                    }
                elif current_section == 'education':
                    current_subsection = {
                        'degree': title,
                        'school': '',
                        'date': '',
                        'bullets': []
                    }
                elif current_section == 'projects':
                    current_subsection = {
                        'title': title,
                        'date': '',
                        'bullets': []
                    }
                elif current_section == 'publications':
                    current_subsection = {
                        'title': title,
                        'date': '',
                        'bullets': []
                    }
                continue

            # Parse job/education details
            if current_subsection:
                if current_section == 'experience':
                    # Company and location
                    if not current_subsection['company'] and line and not line.startswith('-'):
                        # Check for location pattern (ends with state abbreviation or country)
                        if ',' in line:
                            parts = line.split(',')
                            if len(parts[-1].strip()) <= 3 or 'USA' in parts[-1] or any(country in parts[-1] for country in ['United States', 'Canada', 'UK']):
                                current_subsection['company'] = ','.join(parts[:-1]).strip()
                                current_subsection['location'] = parts[-1].strip()
                            else:
                                current_subsection['company'] = line
                        else:
                            current_subsection['company'] = line
                    # Date
                    elif not current_subsection['date'] and line and not line.startswith('-'):
                        if any(month in line for month in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']) or 'Present' in line or '20' in line:
                            current_subsection['date'] = line
                    # Bullet points
                    elif line.startswith('- ') or line.startswith('• '):
                        current_subsection['bullets'].append(line[2:].strip())

                elif current_section == 'education':
                    # School
                    if not current_subsection['school'] and line and not line.startswith('-'):
                        current_subsection['school'] = line
                    # Date
                    elif not current_subsection['date'] and line and not line.startswith('-'):
                        if any(month in line for month in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']) or '20' in line:
                            current_subsection['date'] = line
                    # Bullet points
                    elif line.startswith('- ') or line.startswith('• '):
                        current_subsection['bullets'].append(line[2:].strip())

                elif current_section == 'projects':
                    # Date
                    if not current_subsection['date'] and line and not line.startswith('-'):
                        if any(month in line for month in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']) or '20' in line:
                            current_subsection['date'] = line
                    # Bullet points
                    elif line.startswith('- ') or line.startswith('• '):
                        current_subsection['bullets'].append(line[2:].strip())

                elif current_section == 'publications':
                    # Date
                    if not current_subsection['date'] and line and not line.startswith('-'):
                        if any(month in line for month in ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']) or '20' in line:
                            current_subsection['date'] = line
                    # Bullet points
                    elif line.startswith('- ') or line.startswith('• '):
                        current_subsection['bullets'].append(line[2:].strip())

            # Skills parsing (various formats)
            if current_section == 'skills':
                # Handle "Category: skill1, skill2" format
                if ':' in line:
                    category, skills = line.split(':', 1)
                    sections['skills'].append({
                        'category': category.strip().replace('**', ''),
                        'items': skills.strip()
                    })
                # Handle bullet points
                elif line.startswith('- ') or line.startswith('• '):
                    skill_text = line[2:].strip()
                    if ':' in skill_text:
                        category, skills = skill_text.split(':', 1)
                        sections['skills'].append({
                            'category': category.strip().replace('**', ''),
                            'items': skills.strip()
                        })
                    else:
                        sections['skills'].append({
                            'category': '',
                            'items': skill_text
                        })

            # Summary text
            if current_section == 'summary' and not line.startswith('#'):
                sections['summary'] += ' ' + line

            # Certifications
            if current_section == 'certifications':
                if line.startswith('- ') or line.startswith('• '):
                    sections['certifications'].append(line[2:].strip())
                elif line and not line.startswith('#'):
                    sections['certifications'].append(line)

        # Add last subsection if exists
        if current_subsection and current_section:
            sections[current_section].append(current_subsection)

        return sections

    def _build_hybrid_layout(self, sections):
        """
        Build single-column layout with strategic formatting.

        ABANDONS TABLE APPROACH - Tables cannot reliably span pages in ReportLab.
        Uses single-column with visual hierarchy instead.
        This is the professional, reliable solution used by actual resume generators.
        """
        story = []

        # Header section
        story.append(Paragraph(sections['name'], self.styles['ModernName']))

        if sections['title']:
            story.append(Paragraph(sections['title'], self.styles['ModernTitle']))

        # Contact Information (horizontal, compact)
        if sections['contact']:
            import re
            contact_parts = sections['contact'].split('|')

            # Process each contact part separately to make links clickable
            clickable_parts = []
            for part in contact_parts:
                part = part.strip()

                # Email - make clickable
                if '@' in part and '.' in part:
                    part = f'<link href="mailto:{part}" color="#0066cc"><u>{part}</u></link>'
                # LinkedIn - handle both full URLs and keywords
                elif 'linkedin' in part.lower():
                    if 'linkedin.com' in part.lower():
                        # Full URL provided
                        url = part if part.startswith('http') else f'https://{part}'
                        display_text = part.replace('http://', '').replace('https://', '')
                        part = f'<link href="{url}" color="#0066cc"><u>{display_text}</u></link>'
                    else:
                        # Just keyword "LinkedIn" - style it but don't make clickable
                        part = f'<font color="#0066cc">{part}</font>'
                # GitHub - handle both full URLs and keywords
                elif 'github' in part.lower():
                    if 'github.com' in part.lower():
                        # Full URL provided
                        url = part if part.startswith('http') else f'https://{part}'
                        display_text = part.replace('http://', '').replace('https://', '')
                        part = f'<link href="{url}" color="#0066cc"><u>{display_text}</u></link>'
                    else:
                        # Just keyword "GitHub" - style it but don't make clickable
                        part = f'<font color="#0066cc">{part}</font>'
                # Portfolio - handle both full URLs and keywords
                elif 'portfolio' in part.lower():
                    if any(domain in part.lower() for domain in ['.com', '.io', '.net', '.dev', 'http']):
                        # Full URL provided
                        url = part if part.startswith('http') else f'https://{part}'
                        display_text = part.replace('http://', '').replace('https://', '')
                        part = f'<link href="{url}" color="#0066cc"><u>{display_text}</u></link>'
                    else:
                        # Just keyword "Portfolio" - style it but don't make clickable
                        part = f'<font color="#0066cc">{part}</font>'
                # Other URLs - make clickable (must have domain to be valid)
                elif 'http://' in part or 'https://' in part or ('.com' in part.lower() and '/' in part) or ('.io' in part.lower() and '/' in part) or ('.net' in part.lower() and '/' in part):
                    url = part if part.startswith('http') else f'https://{part}'
                    display_text = part.replace('http://', '').replace('https://', '')
                    part = f'<link href="{url}" color="#0066cc"><u>{display_text}</u></link>'

                clickable_parts.append(part)

            contact_text = ' • '.join(clickable_parts)
            story.append(Paragraph(contact_text, self.styles['ModernContact']))

        story.append(Spacer(1, 12))

        # Professional Summary
        if sections['summary']:
            story.append(Paragraph('<b>PROFESSIONAL SUMMARY</b>', self.styles['ModernSectionHeader']))
            story.append(Paragraph(sections['summary'].strip(), self.styles['ModernSummary']))
            story.append(Spacer(1, 10))

        # Technical Skills (compact horizontal layout)
        if sections['skills']:
            story.append(Paragraph('<b>TECHNICAL SKILLS</b>', self.styles['ModernSectionHeader']))
            for skill_group in sections['skills']:
                if skill_group['category']:
                    story.append(
                        Paragraph(f"<b>{skill_group['category']}:</b> {skill_group['items']}",
                                self.styles['ModernSkills'])
                    )
                else:
                    story.append(Paragraph(skill_group['items'], self.styles['ModernSkills']))
            story.append(Spacer(1, 10))

        # Professional Experience
        if sections['experience']:
            story.append(Paragraph('<b>PROFESSIONAL EXPERIENCE</b>', self.styles['ModernSectionHeader']))

            for job in sections['experience']:
                # Job title
                story.append(Paragraph(job['title'], self.styles['ModernJobTitle']))

                # Company and location
                company_text = job['company']
                if job['location']:
                    company_text += f", {job['location']}"
                story.append(Paragraph(company_text, self.styles['ModernCompany']))

                # Date
                if job['date']:
                    story.append(Paragraph(job['date'], self.styles['ModernDate']))

                # Bullet points
                for bullet in job['bullets']:
                    story.append(Paragraph(f"• {bullet}", self.styles['ModernBullet']))

                story.append(Spacer(1, 10))

        # Education Section
        if sections['education']:
            story.append(Paragraph('<b>EDUCATION</b>', self.styles['ModernSectionHeader']))

            for edu in sections['education']:
                story.append(Paragraph(edu['degree'], self.styles['ModernJobTitle']))
                story.append(Paragraph(edu['school'], self.styles['ModernCompany']))
                if edu['date']:
                    story.append(Paragraph(edu['date'], self.styles['ModernDate']))
                for detail in edu['bullets']:
                    story.append(Paragraph(f"• {detail}", self.styles['ModernBullet']))
                story.append(Spacer(1, 8))

        # Certifications
        if sections['certifications']:
            story.append(Paragraph('<b>CERTIFICATIONS</b>', self.styles['ModernSectionHeader']))
            for cert in sections['certifications']:
                story.append(Paragraph(f"• {cert}", self.styles['ModernSkills']))
            story.append(Spacer(1, 8))

        # Projects Section
        if sections['projects']:
            story.append(Paragraph('<b>KEY PROJECTS</b>', self.styles['ModernSectionHeader']))

            for project in sections['projects']:
                story.append(Paragraph(project['title'], self.styles['ModernJobTitle']))
                if project['date']:
                    story.append(Paragraph(project['date'], self.styles['ModernDate']))
                for bullet in project['bullets']:
                    story.append(Paragraph(f"• {bullet}", self.styles['ModernBullet']))
                story.append(Spacer(1, 8))

        # Publications Section
        if sections['publications']:
            story.append(Paragraph('<b>PUBLICATIONS</b>', self.styles['ModernSectionHeader']))

            for publication in sections['publications']:
                story.append(Paragraph(publication['title'], self.styles['ModernJobTitle']))
                if publication['date']:
                    story.append(Paragraph(publication['date'], self.styles['ModernDate']))
                for bullet in publication['bullets']:
                    story.append(Paragraph(f"• {bullet}", self.styles['ModernBullet']))
                story.append(Spacer(1, 8))

        return story

    def markdown_to_pdf(self, markdown_content, output_path):
        """Wrapper method for compatibility with EnhancedPDFGenerator"""
        return self.generate(markdown_content, output_path)


def test_modern_template():
    """Test the modern two-column template with extensive content"""
    sample_markdown = """# Sarah Johnson
sarah.johnson@email.com | (555) 123-4567 | linkedin.com/in/sarahjohnson | github.com/sjohnson | San Francisco, CA

Senior Full-Stack Engineer

## PROFESSIONAL SUMMARY
Innovative Senior Full-Stack Engineer with 7+ years of experience building scalable web applications and leading development teams. Expertise in React, Node.js, and cloud technologies. Proven track record of delivering high-impact features that increased user engagement by 45% and reduced operational costs by 30%.

## TECHNICAL SKILLS
**Programming Languages:** JavaScript, TypeScript, Python, Java, SQL
**Frontend Technologies:** React, Redux, Vue.js, Angular, HTML5, CSS3, Sass
**Backend Technologies:** Node.js, Express, Django, Spring Boot, GraphQL, REST APIs
**Databases:** PostgreSQL, MongoDB, Redis, MySQL, Elasticsearch
**Cloud & DevOps:** AWS (EC2, S3, Lambda), Docker, Kubernetes, Jenkins, GitLab CI/CD
**Tools & Practices:** Git, Agile/Scrum, TDD, Microservices, System Design

## PROFESSIONAL EXPERIENCE

### Senior Full-Stack Engineer
TechCorp Solutions, San Francisco, CA
June 2020 - Present
- Led development of microservices architecture serving 2M+ daily active users
- Reduced API response time by 60% through database query optimization and caching strategies
- Mentored team of 5 junior developers and established code review best practices
- Implemented real-time collaboration features using WebSockets and Redis pub/sub
- Architected and deployed containerized applications on AWS EKS with 99.9% uptime

### Full-Stack Developer
InnovateTech Inc., San Jose, CA
March 2018 - May 2020
- Built RESTful APIs and GraphQL endpoints for e-commerce platform processing $10M+ in transactions
- Developed responsive React components following atomic design principles
- Integrated third-party payment systems (Stripe, PayPal) with custom fraud detection
- Improved application performance by 40% through code splitting and lazy loading
- Created automated testing suites achieving 85% code coverage

### Junior Full-Stack Developer
StartupXYZ, Mountain View, CA
July 2016 - February 2018
- Developed features for SaaS platform using React and Node.js
- Participated in full software development lifecycle from planning to deployment
- Collaborated with UX designers to implement pixel-perfect responsive designs
- Wrote comprehensive documentation for internal APIs and components
- Contributed to open-source projects and internal tooling improvements

### Web Development Intern
Digital Agency Co., Palo Alto, CA
January 2016 - June 2016
- Assisted in building client websites using modern web technologies
- Learned best practices for version control and collaborative development
- Participated in daily standup meetings and sprint planning sessions
- Developed responsive email templates and landing pages

### Freelance Web Developer
Self-Employed, Remote
September 2015 - December 2015
- Created custom WordPress themes and plugins for small businesses
- Managed client relationships and project timelines independently
- Delivered 10+ projects on time and within budget
- Provided ongoing maintenance and support for client websites

## EDUCATION

### Bachelor of Science in Computer Science
University of California, Berkeley
May 2016
- GPA: 3.8/4.0
- Dean's List: Fall 2014, Spring 2015, Fall 2015
- Relevant Coursework: Data Structures, Algorithms, Web Development, Database Systems

## CERTIFICATIONS
- AWS Certified Solutions Architect - Associate (2021)
- MongoDB Certified Developer (2020)
- Google Cloud Professional Cloud Developer (2019)

## KEY PROJECTS

### Open Source Contribution - ReactFlow
January 2021 - Present
- Contributing to popular React library for building node-based UIs
- Implemented new features and fixed critical bugs
- Improved documentation and created example applications

### Personal Finance Tracker
June 2020
- Built full-stack application for personal budget management
- Implemented data visualization using D3.js and Chart.js
- Deployed on AWS with automated CI/CD pipeline
"""

    generator = ModernProfessionalTemplate()
    output_path = '/tmp/test_modern_template_extended.pdf'
    result = generator.generate(sample_markdown, output_path)
    print(f"PDF generated successfully: {result}")
    return result


if __name__ == "__main__":
    test_modern_template()