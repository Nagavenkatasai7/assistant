"""
Core resume generator using Kimi K2 API with ATS knowledge
"""
import os
import json
import time
from dotenv import load_dotenv
from openai import OpenAI
from openai import APITimeoutError, RateLimitError, APIConnectionError
from pathlib import Path
import sys

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import security modules
from src.security.prompt_sanitizer import PromptSanitizer
from src.security.secrets_manager import SecretsManager
from src.security.security_logger import get_security_logger, SecurityEventType
from config import APIConfig, SecurityConfig

# Import Kimi client
from src.clients.kimi_client import KimiK2Client

# Import ATS scoring
try:
    from scoring.ats_scorer import ATSScorer
except ImportError:
    from src.scoring.ats_scorer import ATSScorer

load_dotenv()

class ResumeGenerator:
    def __init__(self, ats_knowledge_path="ats_knowledge_base.md"):
        # Initialize security components
        self.secrets_manager = SecretsManager()
        self.security_logger = get_security_logger()
        self.prompt_sanitizer = PromptSanitizer()

        # Get API key securely
        try:
            api_key = self.secrets_manager.get_kimi_api_key()
            self.client = KimiK2Client(api_key=api_key)
        except ValueError as e:
            self.security_logger.log_event(
                SecurityEventType.SECRET_MISSING,
                "Kimi API key not found",
                severity="CRITICAL"
            )
            raise

        self.ats_knowledge = self._load_ats_knowledge(ats_knowledge_path)

        # Initialize ATS scorer
        self.ats_scorer = ATSScorer()

    def _load_ats_knowledge(self, knowledge_path):
        """Load ATS knowledge base"""
        try:
            with open(knowledge_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Warning: Could not load ATS knowledge: {e}")
            return ""

    def generate_resume(self, profile_text, job_analysis, company_research=None, user_identifier=None):
        """
        Generate ATS-optimized resume using Claude with security controls

        Args:
            profile_text: Raw text from Profile.pdf
            job_analysis: Analyzed job description (from JobAnalyzer)
            company_research: Optional company research from Perplexity
            user_identifier: User/IP identifier for logging

        Returns:
            dict with 'content' (markdown/text resume) and 'ats_tips' (optimization notes)
        """

        start_time = time.time()

        # Sanitize inputs before building prompt
        if SecurityConfig.ENABLE_PROMPT_SANITIZATION:
            profile_text = self.prompt_sanitizer.sanitize_input(profile_text, max_length=20000)

            # Detect potential injection attempts
            is_suspicious, patterns = self.prompt_sanitizer.detect_injection_attempt(profile_text)
            if is_suspicious:
                self.security_logger.log_prompt_injection_attempt(
                    user_identifier=user_identifier,
                    patterns_detected=patterns,
                    input_type="profile_text",
                    input_sample=profile_text[:200]
                )

                if SecurityConfig.BLOCK_SUSPICIOUS_REQUESTS:
                    return {
                        "content": "",
                        "success": False,
                        "error": "Request blocked due to suspicious content. Please review your input."
                    }

            if company_research:
                company_research_str = str(company_research)
                company_research_str = self.prompt_sanitizer.sanitize_input(company_research_str, max_length=10000)

        # Build the prompt
        prompt = self._build_resume_prompt(profile_text, job_analysis, company_research)

        # P1-2 FIX: Add exponential backoff retry logic for API timeouts
        max_retries = 3
        retry_delay = 1.0  # Start with 1 second
        last_error = None

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    print(f"Retry attempt {attempt + 1}/{max_retries} after {retry_delay:.1f}s delay...")
                    time.sleep(retry_delay)
                else:
                    print("Generating ATS-optimized resume with Kimi K2...")

                # Use configuration for API settings with Kimi K2
                result = self.client.chat_completion(
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=APIConfig.KIMI_TEMPERATURE,
                    max_tokens=APIConfig.KIMI_MAX_TOKENS,
                    timeout=SecurityConfig.API_TIMEOUT_SECONDS
                )

                # Check if API call was successful
                if not result['success']:
                    raise Exception(result.get('error', 'Unknown error'))

                # P1-2 FIX: API call succeeded, break out of retry loop
                response_text = result['content']

                # Calculate duration and tokens
                duration_ms = int(result['duration'] * 1000)
                tokens_used = result['usage']['total_tokens']

                # Estimate cost (Kimi pricing: ~$0.002/1K tokens for input+output)
                cost_estimate = (tokens_used / 1000) * 0.002

                # Log successful API call
                self.security_logger.log_api_call(
                    api_name="kimi_k2",
                    success=True,
                    user_identifier=user_identifier,
                    tokens_used=tokens_used,
                    cost_estimate=cost_estimate,
                    duration_ms=duration_ms
                )

                # Validate response for security
                is_safe, warning = self.prompt_sanitizer.validate_response(response_text)
                if not is_safe:
                    self.security_logger.log_event(
                        SecurityEventType.SUSPICIOUS_ACTIVITY,
                        f"Resume generation response validation warning: {warning}",
                        user_identifier=user_identifier,
                        severity="WARNING"
                    )

                # Clean up the response - remove any optimization notes or commentary
                cleaned_text = self._clean_resume_output(response_text)

                # Score the resume for ATS compatibility
                print("Scoring resume for ATS compatibility...")
                score_result = self._score_resume_content(cleaned_text, job_analysis)

                return {
                    "content": cleaned_text,
                    "success": True,
                    "tokens_used": tokens_used,
                    "cost_estimate": cost_estimate,
                    "ats_score": score_result
                }

            except (APITimeoutError, RateLimitError, APIConnectionError) as e:
                # P1-2 FIX: Retryable errors - continue to next attempt with exponential backoff
                last_error = e
                error_type = type(e).__name__
                print(f"Retryable error ({error_type}): {str(e)}")

                if attempt < max_retries - 1:
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    # Max retries exhausted
                    error_msg = f"API call failed after {max_retries} attempts: {str(e)}"
                    print(f"Error generating resume: {error_msg}")

                    self.security_logger.log_api_call(
                        api_name="kimi_k2",
                        success=False,
                        user_identifier=user_identifier,
                        error=error_msg
                    )

                    return {
                        "content": "",
                        "success": False,
                        "error": error_msg
                    }

            except Exception as e:
                # P1-2 FIX: Non-retryable errors - fail immediately
                error_msg = str(e)
                print(f"Error generating resume: {error_msg}")

                self.security_logger.log_api_call(
                    api_name="kimi_k2",
                    success=False,
                    user_identifier=user_identifier,
                    error=error_msg
                )

                return {
                    "content": "",
                    "success": False,
                    "error": error_msg
                }

    def _clean_resume_output(self, text):
        """Remove any optimization notes or commentary from the resume"""
        import re

        # Common patterns to remove
        patterns_to_remove = [
            r'\n\s*#+\s*Resume Optimization Notes.*$',
            r'\n\s*#+\s*ATS Optimization.*$',
            r'\n\s*#+\s*Notes.*$',
            r'\n\s*#+\s*Tips.*$',
            r'\n\s*---+\s*\n\s*\*\*.*Optimization.*$',
            r'\n\s*\*\*Note:.*$',
            r'\n\s*\*\*Tip:.*$',
        ]

        cleaned = text
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', cleaned, flags=re.MULTILINE | re.DOTALL)

        # Remove everything after common divider patterns if they appear before notes
        divider_patterns = [
            r'\n\s*---+\s*\n\s*#+\s*(Resume|ATS|Optimization)',
            r'\n\s*---+\s*\n\s*\*\*(Resume|ATS|Optimization)',
        ]

        for pattern in divider_patterns:
            match = re.search(pattern, cleaned, re.MULTILINE | re.IGNORECASE)
            if match:
                cleaned = cleaned[:match.start()].rstrip()
                break

        return cleaned.strip()

    def _build_resume_prompt(self, profile_text, job_analysis, company_research=None):
        """Build comprehensive prompt for Claude"""

        import re

        # Extract URLs from profile text for contact line
        # Use correct URLs as fallbacks
        linkedin_url = "https://www.linkedin.com/in/naga-venkata-sai-chennu/"
        github_url = "https://github.com/Nagavenkatasai7"
        portfolio_url = "https://nagavenkatasai7.github.io/portfolio/"

        # Try to extract LinkedIn URL from profile, fallback to default
        linkedin_match = re.search(r'(https?://)?(www\.)?linkedin\.com/in/[A-Za-z0-9-]+/?', profile_text, re.IGNORECASE)
        if linkedin_match:
            extracted_url = linkedin_match.group(0)
            if not extracted_url.startswith('http'):
                linkedin_url = f'https://{extracted_url}'
            else:
                linkedin_url = extracted_url
            # Ensure trailing slash and www
            if not linkedin_url.startswith('https://www.'):
                linkedin_url = linkedin_url.replace('https://', 'https://www.')
            if not linkedin_url.endswith('/'):
                linkedin_url += '/'

        # Try to extract GitHub URL from profile, fallback to default
        github_match = re.search(r'(https?://)?github\.com/[A-Za-z0-9-]+/?', profile_text, re.IGNORECASE)
        if github_match:
            extracted_url = github_match.group(0)
            if not extracted_url.startswith('http'):
                github_url = f'https://{extracted_url}'
            else:
                github_url = extracted_url
            if not github_url.endswith('/'):
                github_url += '/'

        # Try to extract Portfolio URL from profile, fallback to default
        portfolio_match = re.search(r'(https?://)?[a-zA-Z0-9-]+\.github\.io/[^\s|]*', profile_text)
        if portfolio_match:
            extracted_url = portfolio_match.group(0)
            # Fix incorrect username in portfolio
            if 'nagavenkatasai.github.io' in extracted_url.lower():
                portfolio_url = "https://nagavenkatasai7.github.io/portfolio/"
            else:
                if not extracted_url.startswith('http'):
                    portfolio_url = f'https://{extracted_url}'
                else:
                    portfolio_url = extracted_url
                if not portfolio_url.endswith('/'):
                    portfolio_url += '/'

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
   - Use standard section headers: "PROFESSIONAL SUMMARY", "EXPERIENCE", "EDUCATION", "SKILLS", "CERTIFICATIONS", "PUBLICATIONS"
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
[Email] | [Phone] | {linkedin_url or "LinkedIn"} | {github_url or "GitHub"} | {portfolio_url or "Portfolio"} | [Location]

**IMPORTANT for contact line formatting:**
- For LinkedIn: {'Use ' + linkedin_url if linkedin_url else "Just write 'LinkedIn' (URL not found in profile)"}
- For GitHub: {'Use ' + github_url if github_url else "Just write 'GitHub' (URL not found in profile)"}
- For Portfolio: {'Use ' + portfolio_url if portfolio_url else "Just write 'Portfolio' (URL not found in profile)"}
- For Email: Use the actual email address
- For Phone: Use +1 571-546-6207 (this is the correct number to always use)
- Format: email | phone | LinkedIn/URL | GitHub/URL | Portfolio/URL | location
- Example: nchennu@gmu.edu | +1 571-546-6207 | {linkedin_url or "linkedin.com/in/profile"} | {github_url or "github.com/username"} | {portfolio_url or "portfolio-site.com"} | Fairfax, VA

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

### [Degree] | [University] | [Location]
*[Graduation Date or Expected Graduation Date]*
- [GPA if strong, relevant coursework, honors, awards]
- [Research, thesis, or notable academic projects]
- [Leadership roles in student organizations if relevant]

## CERTIFICATIONS
[If applicable]

## PROJECTS (if relevant)
[Notable projects matching the job requirements]

## PUBLICATIONS (if applicable)
### [Publication Title]
*[Publication Date]*
- [Brief description or key points about the publication]
- [Impact, citations, or relevance to the role]

---

**IMPORTANT**:
- **ALWAYS include the EDUCATION section** - this is mandatory for all resumes
- **ALWAYS include the PUBLICATIONS section** if the candidate has any research papers or publications
- Ensure EVERY required skill from the job description appears somewhere in the resume
- Use exact terminology from the job posting
- Prioritize content that matches the job description
- Make the resume achievement-oriented with quantifiable results
- Optimize for both ATS parsing AND human readability
- Keep to 1-2 pages maximum
- Be truthful - enhance and optimize the candidate's real experience, don't fabricate

**OUTPUT REQUIREMENTS**:
- Generate ONLY the resume content in the format specified above
- Do NOT include any optimization notes, tips, or commentary
- Do NOT add any explanatory text before or after the resume
- Do NOT include sections like "Resume Optimization Notes" or "ATS Tips"
- Output should be pure resume content only, starting with the candidate name

Generate the ATS-optimized resume now (resume content only, no additional notes):"""

        return prompt

    def _score_resume_content(self, resume_content, job_analysis):
        """
        Score resume content for ATS compatibility.

        Args:
            resume_content: Generated resume text
            job_analysis: Job analysis dict with keywords and skills

        Returns:
            Dict with comprehensive scoring results
        """
        try:
            # Extract keywords and skills from job analysis
            job_keywords = job_analysis.get('keywords', [])
            required_skills = job_analysis.get('required_skills', [])

            # Score the resume
            score_result = self.ats_scorer.score_resume(
                resume_content=resume_content,
                job_keywords=job_keywords,
                required_skills=required_skills,
                file_format='pdf'
            )

            # Print score summary
            print(f"\nATS Score: {score_result['score']}/100 ({score_result['grade']}) - {score_result['color'].upper()}")
            print(f"Pass Probability: {score_result['pass_probability']:.1f}%")
            print(f"Processing Time: {score_result['processing_time']:.3f}s")

            if score_result.get('top_suggestions'):
                print("\nTop Improvement Suggestions:")
                for i, suggestion in enumerate(score_result['top_suggestions'][:3], 1):
                    print(f"  {i}. {suggestion}")

            return score_result

        except Exception as e:
            print(f"Warning: Could not score resume: {e}")
            # Return minimal score data if scoring fails
            return {
                'score': 0,
                'grade': 'N/A',
                'color': 'red',
                'summary': 'Scoring unavailable',
                'top_suggestions': [],
                'pass_probability': 0,
                'processing_time': 0
            }

    def generate_resume_with_retry(
        self,
        profile_text,
        job_analysis,
        company_research=None,
        user_identifier=None,
        min_score=80,
        max_retries=2
    ):
        """
        Generate resume with automatic retry if score is too low.

        Args:
            profile_text: Raw text from Profile.pdf
            job_analysis: Analyzed job description
            company_research: Optional company research
            user_identifier: User/IP for logging
            min_score: Minimum acceptable ATS score (default: 80)
            max_retries: Maximum number of regeneration attempts (default: 2)

        Returns:
            dict with resume content, score, and retry info
        """
        attempts = []

        for attempt in range(max_retries + 1):
            print(f"\n{'='*60}")
            print(f"Resume Generation Attempt {attempt + 1}/{max_retries + 1}")
            print(f"{'='*60}\n")

            result = self.generate_resume(
                profile_text,
                job_analysis,
                company_research,
                user_identifier
            )

            if not result['success']:
                attempts.append({
                    'attempt': attempt + 1,
                    'success': False,
                    'error': result.get('error', 'Unknown error')
                })
                continue

            # Get ATS score
            ats_score_data = result.get('ats_score', {})
            score = ats_score_data.get('score', 0)

            attempts.append({
                'attempt': attempt + 1,
                'success': True,
                'score': score,
                'grade': ats_score_data.get('grade'),
                'suggestions': ats_score_data.get('top_suggestions', [])
            })

            # Check if score meets minimum threshold
            if score >= min_score:
                print(f"\n✓ Resume meets quality threshold (Score: {score}/{min_score})")
                result['attempts'] = attempts
                result['final_attempt'] = attempt + 1
                return result

            # If not last attempt, prepare for retry
            if attempt < max_retries:
                print(f"\n⚠ Score {score} below threshold {min_score}. Regenerating...")
                print(f"Suggestions for improvement:")
                for suggestion in ats_score_data.get('top_suggestions', [])[:3]:
                    print(f"  - {suggestion}")

                # Add improvement instructions to job analysis for next attempt
                job_analysis['improvement_notes'] = {
                    'previous_score': score,
                    'top_issues': ats_score_data.get('top_suggestions', [])[:5]
                }
            else:
                print(f"\n⚠ Maximum retries reached. Final score: {score}/{min_score}")
                result['attempts'] = attempts
                result['final_attempt'] = attempt + 1
                return result

        # Should not reach here, but return last result as fallback
        return result

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
