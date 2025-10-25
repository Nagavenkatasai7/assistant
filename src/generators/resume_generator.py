"""
Core resume generator using Claude API with ATS knowledge
"""
import os
import json
from dotenv import load_dotenv
import anthropic
from pathlib import Path

load_dotenv()

class ResumeGenerator:
    def __init__(self, ats_knowledge_path="ats_knowledge_base.md"):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.ats_knowledge = self._load_ats_knowledge(ats_knowledge_path)

    def _load_ats_knowledge(self, knowledge_path):
        """Load ATS knowledge base"""
        try:
            with open(knowledge_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Warning: Could not load ATS knowledge: {e}")
            return ""

    def generate_resume(self, profile_text, job_analysis, company_research=None):
        """
        Generate ATS-optimized resume using Claude

        Args:
            profile_text: Raw text from Profile.pdf
            job_analysis: Analyzed job description (from JobAnalyzer)
            company_research: Optional company research from Perplexity

        Returns:
            dict with 'content' (markdown/text resume) and 'ats_tips' (optimization notes)
        """

        # Build the prompt
        prompt = self._build_resume_prompt(profile_text, job_analysis, company_research)

        try:
            print("Generating ATS-optimized resume with Claude...")

            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=16000,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = message.content[0].text

            # Parse the response
            # Expected format: Resume content followed by ATS optimization notes

            return {
                "content": response_text,
                "success": True
            }

        except Exception as e:
            print(f"Error generating resume: {e}")
            return {
                "content": "",
                "success": False,
                "error": str(e)
            }

    def _build_resume_prompt(self, profile_text, job_analysis, company_research=None):
        """Build comprehensive prompt for Claude"""

        company_name = job_analysis.get("company_name", "the company")
        job_title = job_analysis.get("job_title", "the position")
        keywords = job_analysis.get("keywords", [])
        required_skills = job_analysis.get("required_skills", [])

        # Build company research section
        company_section = ""
        if company_research:
            company_section = f"""
## Company Research
{company_research.get('research', '')}
"""

        prompt = f"""You are an expert ATS (Applicant Tracking System) resume writer with deep knowledge of how ATS systems parse, rank, and score resumes.

# Your Task
Create a highly ATS-optimized resume for {company_name} - {job_title} position that will score 90+ in ATS systems while remaining compelling to human recruiters.

# ATS Optimization Knowledge Base
{self.ats_knowledge[:20000]}

# Candidate Profile
{profile_text}

# Target Job Analysis
Company: {company_name}
Job Title: {job_title}
Required Skills: {', '.join(required_skills) if required_skills else 'See job description'}
Key Keywords: {', '.join(keywords[:30]) if keywords else 'Extract from job description'}

Full Job Analysis:
{json.dumps(job_analysis, indent=2)}

{company_section}

# Resume Generation Instructions

## Critical ATS Requirements:
1. **File Format**: Generate plain text/markdown that can easily be converted to PDF
2. **Formatting**:
   - Use simple, clean formatting
   - NO tables, text boxes, columns, or graphics
   - Use standard section headers: "PROFESSIONAL SUMMARY", "EXPERIENCE", "EDUCATION", "SKILLS", "CERTIFICATIONS"
   - Use simple bullet points (-)
   - Standard fonts only in final PDF (Arial, Calibri, or similar)

3. **Keyword Optimization**:
   - Naturally integrate ALL keywords from the job description
   - Include exact phrases from the job posting where relevant
   - Place critical keywords in: Professional Summary, Skills section, and Experience descriptions
   - Mirror the job description language and terminology
   - Include both acronyms and full terms (e.g., "AI/ML" and "Artificial Intelligence/Machine Learning")

4. **Content Strategy**:
   - Lead with a strong Professional Summary (3-4 lines) that mirrors the job requirements
   - Quantify achievements with specific metrics (%, $, numbers)
   - Use strong action verbs relevant to the role
   - Tailor experience descriptions to emphasize relevant projects and responsibilities
   - Ensure Skills section is comprehensive and matches required/preferred skills
   - Optimize for the specific job title - include it prominently if candidate has that exact title

5. **ATS Scoring Optimization**:
   - Target 90%+ keyword match with job description
   - Ensure all required skills are explicitly mentioned
   - Include industry-specific terminology
   - Add relevant certifications and education
   - Use consistent date formatting (MM/YYYY)
   - Include location information

## Output Format:
Provide the resume in clean, well-structured markdown format that follows this structure:

# [CANDIDATE NAME]
[Email] | [Phone] | LinkedIn | GitHub | Portfolio | [Location]

**IMPORTANT for contact line formatting:**
- For LinkedIn: Just write "LinkedIn" (not the full URL)
- For GitHub: Just write "GitHub" (not the full URL)
- For Portfolio: Just write "Portfolio" (not the full URL)
- For Email: Use the actual email address
- For Phone: Use +1 571-546-6207 (this is the correct number to always use)
- Format: email | phone | LinkedIn | GitHub | Portfolio | location
- Example: nchennu@gmu.edu | +1 571-546-6207 | LinkedIn | GitHub | Portfolio | Fairfax, VA

## PROFESSIONAL SUMMARY
[3-4 line summary optimized for the role]

## TECHNICAL SKILLS
[Organized by category, include all relevant keywords]

## PROFESSIONAL EXPERIENCE

### [Job Title] | [Company] | [Location]
*[Start Date] - [End Date]*
- [Achievement-focused bullet point with metrics]
- [Tailored to match job requirements]

## EDUCATION
[Degree] | [University] | [Date]

## CERTIFICATIONS
[If applicable]

## PROJECTS (if relevant)
[Notable projects matching the job requirements]

---

**IMPORTANT**:
- Ensure EVERY required skill from the job description appears somewhere in the resume
- Use exact terminology from the job posting
- Prioritize content that matches the job description
- Make the resume achievement-oriented with quantifiable results
- Optimize for both ATS parsing AND human readability
- Keep to 1-2 pages maximum
- Be truthful - enhance and optimize the candidate's real experience, don't fabricate

Generate the ATS-optimized resume now:"""

        return prompt

def main():
    """Test resume generator"""
    # Sample data
    profile_text = "Sample profile content..."
    job_analysis = {
        "company_name": "TechCorp",
        "job_title": "Senior AI Engineer",
        "required_skills": ["Python", "Machine Learning", "LLM", "RAG"],
        "keywords": ["Python", "AI", "Machine Learning", "LLM", "RAG", "LangChain"]
    }

    generator = ResumeGenerator()
    result = generator.generate_resume(profile_text, job_analysis)

    if result['success']:
        print("✓ Resume generated successfully")
        print(f"\nContent length: {len(result['content'])} characters")
        print("\nFirst 500 characters:")
        print(result['content'][:500])
    else:
        print(f"✗ Resume generation failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    main()
