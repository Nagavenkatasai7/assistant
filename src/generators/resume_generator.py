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

# Import AI clients
from src.clients.kimi_client import KimiK2Client
from src.clients.claude_client import ClaudeOpusClient

# Import ATS scoring
try:
    from scoring.ats_scorer import ATSScorer
except ImportError:
    from src.scoring.ats_scorer import ATSScorer

# Import voice analyzer for personalization
from src.utils.voice_analyzer import VoiceAnalyzer

load_dotenv()

class ResumeGenerator:
    def __init__(self, ats_knowledge_path="ats_knowledge_base_comprehensive.md", model="kimi-k2"):
        """
        Initialize ResumeGenerator with model selection

        Args:
            ats_knowledge_path: Path to ATS knowledge base file
            model: Model to use - "claude-sonnet-4.5" (default) or "kimi-k2"
        """
        # Initialize security components
        self.secrets_manager = SecretsManager()
        self.security_logger = get_security_logger()
        self.prompt_sanitizer = PromptSanitizer()

        # Store model selection
        self.model = model

        # Initialize appropriate client based on model selection
        try:
            print(f"[DEBUG] ResumeGenerator initializing with model: {model}")
            if model == "claude-sonnet-4.5" or model == "claude-opus-4":
                # Use Claude Sonnet 4.5 (or legacy opus-4)
                api_key = self.secrets_manager.get_anthropic_api_key()
                if not api_key:
                    # Fallback to Kimi if Claude key not available
                    print("❌ Warning: Anthropic API key not found, falling back to Kimi K2")
                    self.model = "kimi-k2"
                    api_key = self.secrets_manager.get_kimi_api_key()
                    self.client = KimiK2Client(api_key=api_key)
                    self.api_name = "kimi_k2"
                else:
                    print(f"✅ Initializing ClaudeOpusClient (Sonnet 4.5) with API key: {api_key[:10]}...")
                    self.client = ClaudeOpusClient(api_key=api_key)
                    self.api_name = "claude_sonnet_4_5"
                    print(f"✅ Claude client initialized. Model: {self.client.model}")
            else:
                # Use Kimi K2 (default)
                print(f"[DEBUG] Using Kimi K2 (model parameter was: {model})")
                api_key = self.secrets_manager.get_kimi_api_key()
                self.client = KimiK2Client(api_key=api_key)
                self.api_name = "kimi_k2"
        except ValueError as e:
            self.security_logger.log_event(
                SecurityEventType.SECRET_MISSING,
                f"API key not found for model {model}",
                severity="CRITICAL"
            )
            raise

        self.ats_knowledge = self._load_ats_knowledge(ats_knowledge_path)

        # Initialize ATS scorer
        self.ats_scorer = ATSScorer()

        # Initialize voice analyzer for personalization
        self.voice_analyzer = VoiceAnalyzer()

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
                    model_name = "Claude Sonnet 4.5" if self.model in ["claude-sonnet-4.5", "claude-opus-4"] else "Kimi K2"
                    print(f"Generating ATS-optimized resume with {model_name}...")

                # Use configuration for API settings based on selected model
                if self.model in ["claude-sonnet-4.5", "claude-opus-4"]:
                    result = self.client.chat_completion(
                        messages=[
                            {"role": "user", "content": prompt}
                        ],
                        temperature=APIConfig.CLAUDE_TEMPERATURE,
                        max_tokens=APIConfig.CLAUDE_MAX_TOKENS,
                        timeout=SecurityConfig.API_TIMEOUT_SECONDS
                    )
                else:
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

                # Estimate cost based on model
                # Kimi pricing: ~$0.002/1K tokens, Claude Sonnet 4.5: ~$0.003/1K input + $0.015/1K output (average ~$0.009/1K)
                if self.model in ["claude-sonnet-4.5", "claude-opus-4"]:
                    cost_estimate = (tokens_used / 1000) * 0.009
                else:
                    cost_estimate = (tokens_used / 1000) * 0.002

                # Log successful API call
                self.security_logger.log_api_call(
                    api_name=self.api_name,
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
                        api_name=self.api_name,
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
                    api_name=self.api_name,
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

        # Analyze candidate's voice for personalization (Fix #1 & #5)
        print("Analyzing candidate's voice and personality...")
        voice_analysis = self.voice_analyzer.analyze_profile_voice(profile_text)
        personalization_instructions = self.voice_analyzer.generate_personalization_instructions(voice_analysis)
        structure_variation = self.voice_analyzer.generate_structure_variation(voice_analysis, job_analysis)

        print(f"✓ Voice analysis complete: {voice_analysis['dominant_tone']} tone, {voice_analysis['formality_level']} formality")

        # Build company research section with strategic alignment instructions
        company_section = ""
        if company_research:
            company_section = f"""
## Company Research - USE THIS TO DEMONSTRATE GENUINE INTEREST
{company_research.get('research', '')}

**CRITICAL INSTRUCTIONS FOR STRATEGIC COMPANY ALIGNMENT:**

You MUST use the company research above to demonstrate genuine interest in {company_name} specifically. Generic resumes get rejected - show you actually care about THIS company.

**MANDATORY INTEGRATIONS:**

1. **Professional Summary MUST Include Company-Specific Elements:**
   - Mention {company_name} by name in the summary
   - Reference company's mission/values from research (use exact phrases if found)
   - Show alignment between your experience and company's goals
   - Express genuine enthusiasm for THIS specific opportunity

   Example Framework:
   "[Your expertise] passionate about {company_name}'s mission of [mission from research].
   [X] years building [relevant experience] using [technologies that match company stack].
   Excited to bring expertise in [your strength] to {company_name}'s [specific product/team from research].
   Proven track record of [achievement relevant to company's known challenges/goals]."

2. **Reference Company Products/Services in Experience Bullets:**
   - Find opportunities to mention company's known products
   - Draw parallels between your past work and company's tech stack
   - Show understanding of company's technical challenges

   Examples:
   - "Built API rate limiting system (relevant to {company_name}'s high-traffic infrastructure handling [scale from research])"
   - "Experience with microservices architecture similar to {company_name}'s known tech stack"
   - "Developed real-time notification system comparable to {company_name}'s [Product] feature"

3. **Mirror Company Values Throughout Resume:**
   - Extract 2-3 key values from research (e.g., "innovation", "customer obsession", "collaboration")
   - Incorporate these exact values naturally into bullet points

   If research shows company values "customer obsession":
   - ✅ "Customer-focused approach: reduced user-reported bugs by 60% through proactive testing"
   - ✅ "Prioritized customer experience in every decision, increasing NPS from 42 to 68"

   If research shows company values "innovation":
   - ✅ "Pioneered novel approach to [problem], now adopted across engineering org"
   - ✅ "Innovated solutions for [challenge] using cutting-edge [technology]"

4. **Align Technical Skills with Company's Known Stack:**
   - If research reveals specific technologies company uses, prominently feature matching experience
   - Mention migration/transition experience to company's stack if applicable

   Example: Research shows {company_name} uses React, TypeScript, PostgreSQL, AWS:
   - List these FIRST in your technical skills section
   - Mention experience: "Migrated system from MySQL to PostgreSQL (matching {company_name}'s database stack)"

5. **Show Product Knowledge & Research:**
   - Reference specific company products naturally (don't force it)
   - Demonstrate understanding of company's market position
   - Show awareness of company's recent initiatives/news from research

   Examples:
   - "Built recommendation engine using collaborative filtering similar to {company_name}'s [Product] approach"
   - "Experience scaling systems to [X]M users aligns with {company_name}'s growth to [scale from research]"

6. **Address Company's Known Challenges (if mentioned in research):**
   - If research reveals company is scaling rapidly: emphasize scalability experience
   - If company is expanding globally: highlight cross-cultural/international experience
   - If company recently launched product: emphasize fast-paced/startup experience

**INTEGRATION CHECKLIST:**
- [ ] Company name mentioned in Professional Summary
- [ ] Company mission/values referenced in summary or bullets
- [ ] At least 1-2 experience bullets reference company products or tech stack
- [ ] Technical skills section prioritizes technologies matching company's stack
- [ ] Language and tone match company culture (formal/casual based on research)
- [ ] Show understanding of company's market position or challenges

**AUTHENTICITY WARNING:**
- Only reference products/technologies you've actually worked with
- Don't fabricate knowledge of company systems you don't have
- Be genuine - forced connections are obvious and backfire
- If research is limited, focus more on job requirements than company specifics

**IMPACT:**
Recruiters can tell when candidates have done their homework. Strategic alignment increases interview callback rate by up to 40% versus generic applications.
"""
        else:
            # Even without research, provide strategic customization guidance
            company_section = f"""
## Strategic Company Customization

**IMPORTANT:** While detailed company research is not available, you MUST still demonstrate genuine interest in {company_name} specifically.

**Minimum Required Customizations:**

1. **Professional Summary:**
   - Mention {company_name} by name
   - Express specific interest in the {job_title} role
   - Example: "Excited to bring [expertise] to {company_name}'s {job_title} team, leveraging [X] years of experience in [relevant domain]"

2. **Tailor to Job Description:**
   - Prioritize experiences that match the job requirements
   - Use terminology from the job posting
   - Show clear alignment between your background and role needs

3. **Technical Skills Alignment:**
   - List technologies from job requirements FIRST in skills section
   - Emphasize tools/frameworks mentioned in job description

**Note:** Generic resumes are easily identified. Even without deep company research, show you've crafted this resume specifically for this {job_title} position at {company_name}.
"""

        prompt = f"""You are an expert ATS (Applicant Tracking System) resume writer with deep knowledge of how ATS systems parse, rank, and score resumes.

# CRITICAL INSTRUCTION - READ CAREFULLY
You MUST use ONLY the information from the candidate's profile below. Do NOT invent skills, experiences, projects, or qualifications that are not explicitly mentioned in their profile. Do NOT hallucinate or fabricate content. Your role is to REFORMAT and OPTIMIZE what exists, not to create new content.

# Candidate Profile (USE THIS DATA ONLY)
{profile_text}

# Your Task
Create a highly ATS-optimized resume for {company_name} - {job_title} position that will score 90+ in ATS systems while remaining compelling to human recruiters.

IMPORTANT: Use ONLY the candidate's actual:
- Skills mentioned in their profile
- Projects they actually worked on
- Experience they actually have
- Education they actually completed
- Publications they actually authored

Do NOT add:
- Skills they don't have (e.g., if they don't mention "Neural Rendering" or "3D Reconstruction", DO NOT add these)
- Projects they didn't work on
- Technologies they didn't use
- Experience they don't have

# ATS Optimization Knowledge Base (Synthesized from 7+ Industry Sources)
This knowledge base contains proven strategies from industry-leading sources including Jobscan, ATS platform documentation, and 2025 best practices. Use this to guide resume optimization while keeping the candidate's actual information.

{self.ats_knowledge[:30000]}

# Target Job Analysis
Company: {company_name}
Job Title: {job_title}
Required Skills: {', '.join(required_skills) if required_skills else 'See job description'}
Key Keywords: {', '.join(keywords[:30]) if keywords else 'Extract from job description'}

Full Job Analysis:
{json.dumps(job_analysis, indent=2)}

{company_section}

# Resume Generation Instructions

{personalization_instructions}

{structure_variation}

## Critical ATS Requirements (Based on Analysis of 10+ Million Job Descriptions):

1. **Natural, Human-Readable Writing**:
   - Write in natural language that sounds authentic and personal to the candidate
   - Avoid robotic, keyword-stuffed language
   - Use the candidate's actual voice and experience
   - Balance ATS optimization with compelling storytelling
   - Make it easy for humans to read and understand (6-second recruiter scan test)

2. **File Format & Formatting**:
   - Generate clean markdown that converts to ATS-friendly PDF
   - NO tables, text boxes, columns, graphics, or images
   - Use standard section headers: "Summary", "Technical Skills", "Education", "Projects", "Publications"
   - Use simple bullet points (-)
   - Standard fonts only (Arial, Calibri, Charter)

3. **Smart Keyword Integration** (65-75% match rate is optimal - higher triggers keyword stuffing filters):
   - **CRITICAL RULE**: Only include keywords for skills/technologies the candidate ACTUALLY HAS
   - Use keywords that match the candidate's real experience naturally in context
   - Repeat core skills the candidate possesses 2-3 times naturally (Summary + Skills + Project descriptions)
   - Include exact terminology from job description ONLY if candidate has that skill
   - Mirror job description language for skills candidate genuinely possesses
   - Include acronyms + full terms where candidate used them (e.g., "AI/ML", "RAG Systems")
   - **DO NOT add skills the candidate doesn't have** - 76.4% of recruiters filter by skills, false claims are easily detected
   - Focus on the candidate's strongest, most relevant actual skills rather than keyword stuffing

4. **Content Strategy**:
   - Lead with a strong Professional Summary (3-4 lines) that mirrors the job requirements
   - Quantify achievements with specific metrics (%, $, numbers)
   - Use strong action verbs relevant to the role
   - Tailor experience descriptions to emphasize relevant projects and responsibilities
   - Ensure Skills section is comprehensive and matches required/preferred skills
   - **Job Title Prominence**: Include the exact job title "{job_title}" prominently in the Professional Summary or Skills section to match ATS searches

**🚨 MICROSOFT RECRUITER INSIGHT: USE STAR METHOD FOR STORYTELLING 🚨**

**THIS IS CRITICAL**: Generic bullet points get ignored. Microsoft recruiters specifically look for STAR format (Situation, Task, Action, Result) to understand the full context of your achievements.

**STAR METHOD FORMULA:**
- **S**ituation: Brief context - what was the challenge/environment?
- **T**ask: What needed to be done?
- **A**ction: What YOU specifically did (use "I" mentally, write in first-person implied)
- **R**esult: Quantified outcome and business impact

**IMPLEMENTATION:**

**❌ WEAK (Action + Result only):**
- "Developed machine learning model achieving 95% accuracy"
- "Led team of 5 engineers to deliver project on time"
- "Optimized database queries reducing latency by 40%"

**✅ STRONG (STAR Format - adds Situation/Task context):**
- "When legacy recommendation system struggled to scale beyond 10K users (S), redesigned architecture using collaborative filtering (T+A), achieving 95% accuracy while supporting 100K+ concurrent users and increasing click-through rate by 35% (R)"
- "Inherited stalled project with 3-month delay and team morale issues (S), restructured sprint planning and mentored 5 junior engineers in agile practices (T+A), delivering product 2 weeks ahead of revised deadline with 98% test coverage (R)"
- "Identified database as bottleneck causing customer support team to wait 8+ seconds per query (S), optimized queries and added intelligent caching (T+A), reducing latency by 40% and enabling support team to resolve tickets 2x faster, improving NPS from 42 to 68 (R)"

**KEY DIFFERENCES:**
1. **Context**: STAR bullets tell a mini-story - what was happening before you took action?
2. **Scope**: Readers understand the complexity and constraints you faced
3. **Impact**: Results are tied to business/user outcomes, not just technical metrics
4. **Memorability**: Stories stick in recruiters' minds; generic bullets blur together

**REQUIRED**: At least 60-70% of your experience bullets MUST use STAR format. This is what separates exceptional candidates from average ones.

**🚨 AVOID GENERIC ACTION VERBS - MICROSOFT'S #1 PET PEEVE 🚨**

**MICROSOFT RECRUITER QUOTE**: "Most experiential bullet points start with the same set of action verbs like led, handled, or managed—find creative ways to express your professional responsibilities to help you stand out."

**FORBIDDEN VERBS (These make you invisible):**
❌ Led
❌ Managed
❌ Handled
❌ Worked on
❌ Developed (overused)
❌ Responsible for
❌ Helped with
❌ Assisted with
❌ Involved in
❌ Participated in
❌ Contributed to

**These verbs are on EVERY resume. Using them makes you blend in with 500 other applicants.**

**✅ USE THESE CREATIVE, SPECIFIC ALTERNATIVES INSTEAD:**

**For Leadership/Influence:**
- Orchestrated, Spearheaded, Pioneered, Championed, Drove, Galvanized, Mobilized, Steered, Directed, Guided

**For Building/Creating:**
- Architected, Engineered, Designed, Crafted, Built, Constructed, Established, Launched, Implemented, Deployed

**For Improving/Optimizing:**
- Transformed, Streamlined, Revolutionized, Modernized, Overhauled, Refined, Enhanced, Elevated, Amplified, Accelerated

**For Analyzing/Problem-Solving:**
- Diagnosed, Investigated, Identified, Uncovered, Discovered, Resolved, Troubleshot, Debugged, Isolated, Pinpointed

**For Collaboration:**
- Partnered with, Coordinated with, Aligned with, Collaborated with, Synchronized, Integrated, Unified, Bridged

**For Impact/Results:**
- Achieved, Delivered, Generated, Produced, Yielded, Realized, Attained, Secured, Captured, Unlocked

**For Innovation:**
- Pioneered, Invented, Conceived, Innovated, Devised, Formulated, Designed, Created, Introduced, Originated

**IMPLEMENTATION EXAMPLES:**

❌ GENERIC: "Led development of new API feature"
✅ SPECIFIC: "Architected RESTful API serving 1M+ daily requests, reducing response time from 500ms to 80ms"

❌ GENERIC: "Managed team of engineers"
✅ SPECIFIC: "Mentored team of 5 junior engineers through hands-on code reviews, elevating their code quality scores from 3.2 to 4.5/5.0"

❌ GENERIC: "Worked on machine learning model"
✅ SPECIFIC: "Engineered ensemble learning pipeline combining 3 ML algorithms, boosting prediction accuracy from 66% to 89%"

**RULE**: If you can replace your verb with "worked on" and it means the same thing, your verb is too generic. Choose a verb that describes EXACTLY what you did.

**🚨 MANDATORY: ADD PERSONAL SECTION TO SHOW WHO YOU ARE 🚨**

**MICROSOFT RECRUITER INSIGHT**: "Microsoft's recruiters want to get to know you—not only your professional self, but what you're interested in, too, which has much to do with the company's cultural fit."

**THIS IS NON-NEGOTIABLE FOR INTERNATIONAL STUDENTS**: U.S. recruiters evaluate cultural fit heavily. A purely technical resume = instant rejection. You MUST show your personality and interests.

**REQUIRED SECTION** (Add after Publications/Projects, before end of resume):

## WHAT DRIVES ME / PERSONAL INTERESTS / BEYOND WORK

**Format Options** (Choose the one that fits candidate's voice):

**Option 1 - Passion Statement (2-3 sentences):**
Example: "Passionate about democratizing AI education in underserved communities—volunteer tutor teaching Python and ML fundamentals to 50+ high school students from low-income backgrounds. Fascinated by the intersection of AI and healthcare, exploring how LLMs can improve medical diagnosis accessibility in rural areas. Outside tech, avid trail runner (completed 3 half-marathons) and amateur photographer documenting cultural diversity in Northern Virginia."

**Option 2 - Interests List (bulleted):**
- Active open-source contributor: Maintain Python library for RAG optimization with 500+ GitHub stars
- Volunteer: Teach coding workshops to underrepresented minorities in tech through CodePath
- Personal projects: Building AI-powered sign language translator to improve accessibility for deaf community
- Continuous learner: Completed 5 advanced ML courses on Coursera, staying current with latest research from NeurIPS/ICML
- Outside work: Marathon runner, chess enthusiast (1800 ELO rating), and volunteer at local animal shelter

**Option 3 - What Drives Me (narrative):**
Example: "Driven by curiosity about how AI can solve real-world problems with social impact. My weekends involve exploring new ML research papers, contributing to open-source projects, and mentoring aspiring engineers from underrepresented backgrounds. When not coding, you'll find me at local tech meetups discussing the latest LLM advancements, hiking Virginia trails, or experimenting with home-cooked fusion cuisine combining Indian and American flavors."

**WHAT TO INCLUDE** (Choose 3-5 of these):
1. **Genuine Tech Interests**: What problems excite you? What do you research in free time?
2. **Community Involvement**: Volunteering, teaching, mentoring, open source contributions
3. **Continuous Learning**: Courses, conferences attended, research papers you follow
4. **Creative Pursuits**: Photography, music, writing, design, art
5. **Athletic/Wellness**: Sports, running, yoga, hiking, fitness
6. **Cultural Bridge**: How you blend your background with U.S. culture
7. **Side Projects**: Personal coding projects driven by passion, not career
8. **Hobbies**: Chess, gaming, cooking, reading, travel

**WHAT NOT TO INCLUDE:**
❌ Generic statements: "I like movies and travel" (everyone says this)
❌ Controversial topics: Politics, religion, polarizing social issues
❌ Overly personal: Family details, relationship status
❌ Negative statements: "When not working long hours..." (sounds burnt out)

**WHY THIS MATTERS:**
Microsoft recruiters specifically said international candidates who got interviews shared genuine interests and personality. This section:
- Shows you're a real person, not just a resume robot
- Demonstrates cultural fit and communication style
- Gives interviewers conversation starters
- Differentiates you from 500 identical technical resumes

**AUTHENTICITY IS KEY**: Don't fabricate interests. If you genuinely have limited interests outside work, focus on what truly drives you in tech—your curiosity, learning habits, and genuine passion for specific problems.

**PLACEMENT**: Add this section AFTER your main content (Experience/Projects/Publications) but BEFORE any "Additional Technical Contributions" or appendix-style sections. It should feel like a natural conclusion to "who you are."

**🚨 MAKE PROFESSIONAL SUMMARY CONVERSATIONAL, NOT ROBOTIC 🚨**

**MICROSOFT RECRUITER FEEDBACK**: Resumes that sound like AI wrote them get rejected. Your summary must sound human, authentic, and conversational while remaining professional.

**❌ ROBOTIC (Generic template language):**
"Results-driven software engineer with 3+ years of experience in full-stack development seeking to leverage expertise in cloud technologies to contribute to innovative solutions at Company X."

**Why it fails**: Could apply to 1000 people, uses buzzwords ("results-driven", "leverage"), no personality, sounds like template.

**✅ CONVERSATIONAL (Authentic voice):**
"Software engineer obsessed with building delightful user experiences that just work. Spent the last 3 years at fast-growing startups (Series B, 100K users) turning messy requirements into elegant React/Node.js solutions that customers love. Excited to bring this product-minded engineering approach to {company_name}'s mission of [specific mission from research]. Happiest when collaborating across time zones, mentoring junior devs, and shipping features that make users say 'wow.'"

**Why it works**: Specific details, personality ("obsessed", "delightful", "happiest when"), company-specific, authentic voice.

**CONVERSATIONAL TECHNIQUES:**

1. **Use Authentic Descriptors** (not corporate buzzwords):
   - ❌ "Results-driven" → ✅ "Impact-obsessed" or "Passionate about measurable outcomes"
   - ❌ "Team player" → ✅ "Thrive in collaborative environments" or "Energized by team success"
   - ❌ "Seeking to leverage" → ✅ "Excited to bring" or "Ready to apply"

2. **Add Specific Details** (not vague claims):
   - ❌ "Experience in AI/ML" → ✅ "Built production LLMs serving 50K daily users"
   - ❌ "Strong technical skills" → ✅ "Fluent in PyTorch, shipped 5 ML models to production"

3. **Show Enthusiasm Naturally**:
   - ❌ "Interested in role" → ✅ "Genuinely excited about {company_name}'s [specific product/mission]"
   - ❌ "Qualified candidate" → ✅ "Can't wait to tackle [specific challenge company faces]"

4. **Be Human, Not Corporate**:
   - ✅ Use words like: "love", "excited", "passionate", "obsessed with", "thrive on", "energized by"
   - ❌ Avoid: "synergize", "leverage", "utilize", "facilitate", "strategically"

5. **Tell Your Story** (what makes YOU different):
   - Include your journey: "From building chatbots in college dorm room to deploying enterprise AI at scale"
   - Mention your unique angle: "Combining background in psychology with ML expertise to build empathetic AI"
   - Share what drives you: "Fascinated by making complex AI accessible to non-technical users"

**FORMULA FOR CONVERSATIONAL SUMMARY:**

[What you're passionate about/obsessed with] + [Specific experience with metrics] + [Why THIS company specifically] + [What excites you most about the work] + [Unique strength or perspective]

Example:
"AI researcher captivated by the challenge of teaching machines to understand human emotion. Spent last 2 years at George Mason's R1 research lab pioneering novel LLM pre-training approaches, processing 500B+ tokens and publishing 5 peer-reviewed papers with 92-98% accuracy across domains. Drawn to {company_name}'s mission of [mission] and excited to bring fresh research perspective to production systems serving millions. Happiest when bridging cutting-edge research with real-world applications, especially in [domain relevant to company]."

**TONE GUIDELINES:**
- **Professional** but not stuffy
- **Enthusiastic** but not over-the-top
- **Confident** but not arrogant
- **Specific** not vague
- **Authentic** not templated

**TEST**: Read your summary out loud. If it sounds like you're reading a corporate press release, rewrite it. If it sounds like how you'd introduce yourself to a potential colleague at a coffee chat, you nailed it.

**🚨 ABSOLUTELY MANDATORY: SOFT SKILLS & CULTURAL FIT 🚨**

**THIS IS NON-NEGOTIABLE**: U.S. recruiters evaluate international candidates heavily on cultural fit and soft skills. If you don't include these, the resume will be REJECTED regardless of technical skills.

**REQUIRED: You MUST include AT LEAST 2-3 examples from EACH of the 5 categories below:**

1. **Communication & Presentation Skills** (MANDATORY - choose 2-3):
   - "Presented [technical topic] to [audience type - executives/stakeholders/cross-functional teams]"
   - "Documented [system/architecture/API] used by [X]+ developers across [teams/locations]"
   - "Led weekly knowledge-sharing sessions on [topic] for [team size/audience]"
   - "Delivered technical training to [non-technical stakeholders/clients/team members]"
   - "Facilitated sprint retrospectives and architecture discussions with distributed team"
   - "Wrote comprehensive technical blog posts that received [X] views from engineering community"

2. **Cross-Cultural & Remote Collaboration** (CRITICAL for international candidates):
   - "Collaborated with U.S.-based [team type] across [X]-hour time zone difference"
   - "Partnered with designers/engineers in [X] countries ([list countries]) to deliver [outcome]"
   - "Mentored [X] junior developers in remote-first environment, improving their [metric] by [Y]%"
   - "Facilitated async communication across distributed team of [X] members in [X] time zones"
   - "Successfully coordinated releases with global team spanning [X] continents"
   - "Participated in 24/7 on-call rotation supporting international customer base"

3. **Initiative & Proactive Problem-Solving** (Shows self-direction):
   - "Identified critical [issue/bottleneck] and proposed solution that [outcome/adoption]"
   - "Volunteered to [action] when [situation], resulting in [benefit]"
   - "Created internal [tool/documentation/process] that saved team [X] hours per week"
   - "Took ownership of [problem/technical debt] without being assigned, delivering [outcome]"
   - "Self-initiated [project/research/improvement] that became [adoption/impact]"
   - "Proactively researched and recommended [technology/approach], now team standard"

4. **Adaptability & Continuous Learning** (Critical for dynamic environments):
   - "Quickly adapted to [methodology/process] when joining team, becoming productive in [timeframe]"
   - "Learned [company's tech stack/codebase] ([size/complexity]) in [short timeframe]"
   - "Transitioned from [role A] to [role B] in [X] months while maintaining [standard]"
   - "Mastered [new technology/framework] in [timeframe] to meet critical project deadline"
   - "Successfully pivoted project approach when requirements changed, delivering on time"
   - "Self-taught [skill/technology] to fill team gap, now serving as subject matter expert"

5. **Teamwork & Collaboration** (Beyond individual contribution):
   - "Active participant in code reviews, providing constructive feedback that improved code quality by [metric]"
   - "Collaborated with [teams] to [outcome], ensuring alignment across [departments/functions]"
   - "Pair-programmed with [junior/senior] developers to [knowledge transfer/problem solve]"
   - "Contributed to team culture by [organizing events/mentoring/knowledge sharing]"
   - "Worked closely with [non-technical teams] to translate business requirements into technical solutions"

**Integration Strategy - WHERE to Include Soft Skills:**

1. **Professional Summary (1 soft skill descriptor):**
   - Example: "Collaborative problem-solver with proven track record..."
   - Example: "Self-directed engineer with strong cross-cultural communication skills..."
   - Example: "Adaptable technical leader experienced in global team environments..."

2. **Experience Bullets (30-40% should demonstrate soft skills):**
   - Don't just state WHAT you did - show HOW you worked with others
   - Mix technical accomplishments with collaboration/communication examples
   - Use phrases: "Collaborated with...", "Communicated [technical concepts] to...", "Led...", "Mentored...", "Facilitated..."

3. **Show Impact ON PEOPLE, not just systems:**
   - ❌ "Optimized database queries reducing latency by 40%"
   - ✅ "Optimized database queries reducing latency by 40%, enabling customer support team to resolve tickets 2x faster and improving user satisfaction score from 3.2 to 4.5/5.0"

**Cultural Fit Signals to Include:**
- Remote work proficiency: "Thrived in remote-first environment with async communication"
- Self-direction: "Self-directed learning of [technology] through online courses and hands-on projects"
- U.S. workplace norms: "Participated in daily standups, sprint planning, and retrospectives"
- Team collaboration: "Active contributor to team's code review culture and knowledge base"
- Communication style: "Clear, concise technical communication in English with global stakeholders"

**IMPORTANT**: Soft skills should feel natural and be demonstrated through concrete examples, NOT listed abstractly. Every soft skill claim must be backed by a specific example showing HOW you demonstrated it.

**⚠️ SOFT SKILLS CHECKLIST - VERIFY BEFORE SUBMITTING:**
You MUST include examples from ALL 5 categories:
- [ ] ✅ Communication & Presentation (2-3 examples)
- [ ] ✅ Cross-Cultural & Remote Collaboration (2-3 examples)
- [ ] ✅ Initiative & Proactive Problem-Solving (2-3 examples)
- [ ] ✅ Adaptability & Continuous Learning (2-3 examples)
- [ ] ✅ Teamwork & Collaboration (2-3 examples)

**Total Required: 10-15 soft skill examples distributed throughout the resume.**

5. **Human Recruiter Optimization (6-Second Scan)**:
   - **Top 1/3 Critical**: Most important info must be in the top third of page 1 (name, contact, summary, key skills)
   - **Job Title Matching**: Make it immediately clear you're qualified for "{job_title}" role
   - **Quantified Achievements**: Lead with numbers that pop (%, $, time saved, scale)
   - **Action Verbs**: Start bullets with powerful verbs: Achieved, Drove, Increased, Led, Built, Optimized, Delivered
   - **Scannable Format**: Short bullet points (1-2 lines max), clear headers, strategic white space
   - **Compelling Story**: Don't just list responsibilities - show progression, impact, and growth

6. **ATS Scoring Optimization** (Target 65-75% match rate - avoid over-optimization):
   - Target 65-75% keyword match with job description (higher scores often flagged as keyword stuffing)
   - Ensure all required skills are explicitly mentioned
   - Include industry-specific terminology
   - Add relevant certifications and education
   - Use consistent date formatting (MM/YYYY)
   - Include location information
   - **Balance**: Natural readability for humans > perfect ATS score

**🚨 ABSOLUTELY MANDATORY: U.S. CONTEXT TRANSLATION 🚨**

**THIS IS CRITICAL FOR INTERNATIONAL CANDIDATES**: U.S. recruiters have NEVER heard of companies/universities outside the U.S. You MUST provide context or your resume will be immediately discarded.

**REQUIRED FORMAT FOR ALL ORGANIZATIONS:**
Every job, internship, university, or organization MUST include context in parentheses:

**Format:** `[Job Title] | [Organization Name] ([CONTEXT]) | [Location]`

**CONTEXT TEMPLATES (Choose appropriate one):**

1. **For Companies/Startups:**
   - `(Series [A/B/C] [Industry], [X]K users, [team size]-person team)`
   - `([Industry] company, [market position], [scale indicator])`
   - Example: `Software Engineer | TechCorp (Series B SaaS, 100K users, 40-person team) | India`

2. **For Universities/Academic Institutions:**
   - `(Public/Private R1/R2 research university, [X]K students, top-[rank] [program] program)`
   - `([Type] university, [notable distinction], [size])`
   - Example: `Research Assistant | Indian Institute of Technology Delhi (Public R1 research university, 16K students, top-10 CS program in India) | New Delhi, India`
   - Example: `Graduate TA | George Mason University (Public R1 research university, 40K students, top-100 CS program) | Virginia, USA`

3. **For Research Labs/Organizations:**
   - `([Field] research institution, [affiliation], [notable work])`
   - Example: `Research Intern | CSIR Lab (National research institution, govt-funded, AI/ML focus) | India`

4. **For Service/Consulting Companies:**
   - `([Service type], [X] clients, [industry focus])`
   - Example: `Consultant | GlobalTech (IT consulting, 100+ enterprise clients, fintech focus) | India`

5. **For Product Companies:**
   - `([Product type], [market position/scale])`
   - Example: `Engineer | PaymentCo (Mobile payments, top-3 in Southeast Asia, 5M users) | Singapore`

**SCALE INDICATORS (Include at least ONE):**
- User base: "100K monthly users" / "1M+ transactions daily"
- Team size: "15-person team" / "60+ developers"
- Market position: "leading fintech in region" / "top e-commerce platform"
- Funding: "Series B, $10M ARR" (if known)
- Academic ranking: "top-50 CS program" / "R1 research institution"

**⚠️ U.S. CONTEXT CHECKLIST - VERIFY EVERY ORGANIZATION:**
For EACH job, project, or experience listed:
- [ ] ✅ Organization name followed by context in parentheses
- [ ] ✅ Context includes type (company/university/research)
- [ ] ✅ Context includes scale indicator (users/students/team size)
- [ ] ✅ Context includes market position or ranking (if applicable)

**Examples of CORRECT formatting:**

✅ `Research Assistant | George Mason University (Public R1 research university, 40K students, top-100 CS program) | Virginia, USA`

✅ `Software Engineer | Infosys (Global IT services, 300K employees, Fortune 500, serves 1500+ clients) | India`

✅ `ML Intern | AI Research Lab (University-affiliated research center, focus on computer vision) | Singapore`

❌ WRONG: `Research Assistant | George Mason University | Virginia, USA` (NO CONTEXT!)

❌ WRONG: `Software Engineer | Infosys | India` (NO CONTEXT!)

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

### [Job Title] | [Company/Organization Name] ([CONTEXT - See above for format!]) | [Location]
*[Start Date] - [End Date]*
- [Achievement-focused bullet point with metrics]
- [Tailored to match job requirements]

## EDUCATION

### [Degree] | [University Name] ([CONTEXT - See above!]) | [Location]
*[Graduation Date or Expected Graduation Date]*
- [GPA if strong, relevant coursework, honors, awards]
- [Research, thesis, or notable academic projects]
- [Leadership roles in student organizations if relevant]

## PROJECTS (if relevant)

### [Project Name]
*[Date Range]*
- [Description with technologies used]
- [Impact and outcomes with metrics]

## PUBLICATIONS (if applicable)

### [Publication Title]
*[Publication Date]*
- [Brief description or key points]
- [Impact, citations, or relevance]

## WHAT DRIVES ME / BEYOND WORK (MANDATORY - See instructions above)

[2-3 sentence personal statement OR bulleted list showing personality, interests, community involvement, and what makes you unique beyond technical skills. This is REQUIRED for cultural fit evaluation. Choose format based on candidate's voice - see examples above in "MANDATORY: ADD PERSONAL SECTION" for guidance.]

Examples:
- Active open-source contributor and volunteer coding instructor
- Continuous learner: Following latest AI research from NeurIPS/ICML, completed advanced ML coursework
- Outside tech: [Genuine hobbies that show well-rounded personality]

OR narrative format:
"[Passionate statement about what drives you in tech] + [Community involvement/learning habits] + [Authentic interests outside work that show cultural fit]"

## [ANY OTHER SECTIONS FROM CANDIDATE'S PROFILE]
**CRITICAL**: If the candidate's profile contains additional sections (Awards, Certifications, Additional Technical Contributions, Professional Memberships, Languages, etc.), you MUST INCLUDE THEM using the same markdown format:

### Section Name
- Bullet point format for lists
- Or paragraph format for text
- Maintain the structure from the original profile

**Examples of additional sections to preserve**:
- Awards & Honors
- Certifications
- Professional Memberships
- Additional Technical Contributions
- Volunteer Experience
- Languages
- Patents
- Conference Presentations
- Media Mentions
- Teaching Experience

---

**IMPORTANT**:
- **CRITICAL: DO NOT HALLUCINATE OR FABRICATE** - Use ONLY information from the candidate's actual profile above
- **CRITICAL: DO NOT INVENT SKILLS** - If the candidate doesn't mention a skill (like "Neural Rendering", "3D Reconstruction", "NeRF"), DO NOT add it
- **CRITICAL: DO NOT REWRITE PROJECT CONTENT** - Keep the candidate's actual project descriptions, just optimize the wording for ATS
- **CRITICAL: PRESERVE ALL SECTIONS** - If the candidate has Publications, Awards, Certifications, Additional Technical Contributions, or any other sections in their profile, INCLUDE THEM ALL in your output
- **CRITICAL: MAINTAIN SECTION ORDER** - Keep sections in a logical order: Summary → Skills → Education → Projects/Experience → Publications → Awards → Additional Technical Contributions → Other sections
- **ALWAYS include the EDUCATION section** - this is mandatory for all resumes
- Ensure required skills from job description that the CANDIDATE ACTUALLY HAS appear in the resume
- Use exact terminology from the job posting ONLY for skills the candidate actually possesses
- Prioritize content that matches the job description from the candidate's REAL experience
- Make the resume achievement-oriented with quantifiable results from their ACTUAL work
- Optimize for both ATS parsing AND human readability
- Keep to 1-2 pages maximum
- ENHANCE and OPTIMIZE the candidate's REAL experience - DO NOT fabricate new skills or projects

**OUTPUT REQUIREMENTS**:
- Generate ONLY the resume content in the format specified above
- Do NOT include any optimization notes, tips, or commentary
- Do NOT add any explanatory text before or after the resume
- Do NOT include sections like "Resume Optimization Notes" or "ATS Tips"
- Output should be pure resume content only, starting with the candidate name

---

# 🚨 MASTER VALIDATION CHECKLIST - VERIFY BEFORE GENERATING 🚨

**STOP! Before you generate the resume, verify you will include ALL of the following:**

## ✅ U.S. CONTEXT REQUIREMENTS (MANDATORY):
- [ ] EVERY organization (company/university/research lab) has context in parentheses
- [ ] Format: `[Job Title] | [Organization] ([CONTEXT]) | [Location]`
- [ ] Context includes: type + scale indicator + market position/ranking
- [ ] Example: `Research Assistant | George Mason University (Public R1 research university, 40K students, top-100 CS program) | Virginia, USA`

## ✅ SOFT SKILLS REQUIREMENTS (MANDATORY - ALL 5 CATEGORIES):
You MUST include 2-3 examples from EACH category:
- [ ] Communication & Presentation (2-3 examples)
- [ ] Cross-Cultural & Remote Collaboration (2-3 examples)
- [ ] Initiative & Proactive Problem-Solving (2-3 examples)
- [ ] Adaptability & Continuous Learning (2-3 examples)
- [ ] Teamwork & Collaboration (2-3 examples)
**Target: 10-15 total soft skill examples throughout the resume**

## ✅ COMPANY ALIGNMENT REQUIREMENTS:
- [ ] Company name "{company_name}" mentioned in Professional Summary
- [ ] At least 1-2 references to company products/values in bullets (if research available)
- [ ] Technical skills prioritize company's known tech stack

## ✅ BASIC RESUME REQUIREMENTS:
- [ ] Professional Summary is 3-4 lines and mentions the role
- [ ] All bullet points have metrics and quantified impact
- [ ] No fabricated skills or experiences - using only profile data
- [ ] Education section included
- [ ] All sections from profile preserved (Publications, Awards, etc.)

## ✅ MICROSOFT RECRUITER REQUIREMENTS (DIFFERENTIATION):
- [ ] 60-70% of bullets use STAR format (Situation + Task + Action + Result)
- [ ] NO generic action verbs (led, managed, handled, worked on, developed)
- [ ] Using creative, specific action verbs from provided list
- [ ] Professional Summary is CONVERSATIONAL, not robotic (no buzzwords)
- [ ] "WHAT DRIVES ME / BEYOND WORK" section included (MANDATORY)
- [ ] Personal section shows genuine interests and cultural fit

**IF ANY CHECKBOX ABOVE IS UNCHECKED, DO NOT GENERATE THE RESUME YET!**

Go back and ensure ALL requirements are met, especially:
1. U.S. Context in EVERY organization name
2. ALL 5 soft skill categories represented with 2-3 examples each
3. STAR format in 60-70% of bullets
4. NO generic action verbs
5. Personal section included with authentic interests

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
