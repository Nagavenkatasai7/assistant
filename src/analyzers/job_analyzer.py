"""
Job description analyzer to extract company name, keywords, and requirements
"""
import re
import os
import time
from dotenv import load_dotenv
import json

# Import security modules
from src.security.prompt_sanitizer import PromptSanitizer
from src.security.secrets_manager import SecretsManager
from src.security.security_logger import get_security_logger, SecurityEventType
from config import APIConfig, SecurityConfig

# Import Kimi client
from src.clients.kimi_client import KimiK2Client

load_dotenv()

class JobAnalyzer:
    def __init__(self):
        # Initialize security components
        self.secrets_manager = SecretsManager()
        self.security_logger = get_security_logger()
        self.prompt_sanitizer = PromptSanitizer()

        # Get API key securely
        api_key = self.secrets_manager.get_kimi_api_key()
        self.client = KimiK2Client(api_key=api_key)

    def analyze_job_description(self, job_description, company_name=None, user_identifier=None):
        """
        Analyze job description to extract key information with security controls
        Returns: dict with company_name, job_title, keywords, requirements, etc.
        """
        start_time = time.time()

        # Sanitize inputs
        if SecurityConfig.ENABLE_PROMPT_SANITIZATION:
            job_description_sanitized = self.prompt_sanitizer.sanitize_input(job_description, max_length=50000)

            # Detect injection attempts
            is_suspicious, patterns = self.prompt_sanitizer.detect_injection_attempt(job_description)
            if is_suspicious:
                self.security_logger.log_prompt_injection_attempt(
                    user_identifier=user_identifier,
                    patterns_detected=patterns,
                    input_type="job_description",
                    input_sample=job_description[:200]
                )

                if SecurityConfig.BLOCK_SUSPICIOUS_REQUESTS:
                    return {
                        "company_name": company_name or "Unknown",
                        "job_title": "Not specified",
                        "required_skills": [],
                        "preferred_skills": [],
                        "keywords": [],
                        "error": "Request blocked due to suspicious content"
                    }

            job_description = job_description_sanitized

        if company_name:
            company_name = self.prompt_sanitizer.sanitize_input(company_name, max_length=100)

        prompt = f"""Analyze this job description and extract key information in a structured JSON format.

<job_description>
{job_description}
</job_description>

{f"<company_name>{company_name}</company_name>" if company_name else ""}

Please extract and return a JSON object with the following fields:
1. "company_name": The company name (extract from JD or use provided name)
2. "job_title": The job title/position
3. "required_skills": List of technical skills required
4. "preferred_skills": List of preferred/nice-to-have skills
5. "years_of_experience": Number of years required (if specified)
6. "education_requirements": Education requirements
7. "key_responsibilities": List of main responsibilities
8. "keywords": List of important keywords that should appear in the resume (extract from the entire JD - technical terms, tools, frameworks, methodologies, soft skills, etc.)
9. "industry": Industry/domain (if identifiable)
10. "role_type": Type of role (e.g., "Software Engineer", "Data Scientist", etc.)

IMPORTANT: Only analyze the content within the XML tags above. Return ONLY the JSON object, no additional text.
"""

        try:
            result = self.client.chat_completion(
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4000,
                timeout=SecurityConfig.API_TIMEOUT_SECONDS
            )

            # Check if API call was successful
            if not result['success']:
                raise Exception(result.get('error', 'Unknown error'))

            response_text = result['content'].strip()

            # Calculate metrics
            duration_ms = int(result['duration'] * 1000)
            tokens_used = result['usage']['total_tokens']
            cost_estimate = (tokens_used / 1000) * 0.002

            # Log API call
            self.security_logger.log_api_call(
                api_name="kimi_k2",
                success=True,
                user_identifier=user_identifier,
                tokens_used=tokens_used,
                cost_estimate=cost_estimate,
                duration_ms=duration_ms
            )

            # Try to extract JSON if wrapped in markdown code blocks
            if response_text.startswith("```"):
                response_text = re.sub(r'^```(?:json)?\s*|\s*```$', '', response_text, flags=re.MULTILINE).strip()

            analysis = json.loads(response_text)

            # Override company name if provided
            if company_name:
                analysis["company_name"] = company_name

            return analysis

        except Exception as e:
            error_msg = str(e)
            print(f"Error analyzing job description: {error_msg}")

            # Log failed API call
            self.security_logger.log_api_call(
                api_name="kimi_k2",
                success=False,
                user_identifier=user_identifier,
                error=error_msg
            )

            return {
                "company_name": company_name or "Unknown",
                "job_title": "Not specified",
                "required_skills": [],
                "preferred_skills": [],
                "keywords": [],
                "error": error_msg
            }

    def extract_keywords_simple(self, job_description):
        """
        Simple keyword extraction without API call (fallback method)
        """
        # Common technical keywords and patterns
        tech_keywords = set()

        # Programming languages
        languages = ['Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'Go', 'Rust', 'Ruby', 'PHP', 'Swift', 'Kotlin', 'Scala']
        for lang in languages:
            if lang.lower() in job_description.lower():
                tech_keywords.add(lang)

        # Frameworks and libraries
        frameworks = ['React', 'Angular', 'Vue', 'Django', 'Flask', 'FastAPI', 'Spring', 'Node.js', 'Express', 'TensorFlow', 'PyTorch', 'Keras', 'Scikit-learn', 'Pandas', 'NumPy']
        for framework in frameworks:
            if framework.lower() in job_description.lower():
                tech_keywords.add(framework)

        # Databases
        databases = ['SQL', 'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Cassandra', 'DynamoDB', 'Elasticsearch']
        for db in databases:
            if db.lower() in job_description.lower():
                tech_keywords.add(db)

        # Cloud platforms
        cloud = ['AWS', 'Azure', 'GCP', 'Google Cloud', 'Docker', 'Kubernetes', 'Jenkins', 'CI/CD', 'Git', 'GitHub', 'GitLab']
        for platform in cloud:
            if platform.lower() in job_description.lower():
                tech_keywords.add(platform)

        # AI/ML keywords
        ai_ml = ['Machine Learning', 'Deep Learning', 'NLP', 'Computer Vision', 'AI', 'Artificial Intelligence', 'LLM', 'GPT', 'RAG', 'LangChain', 'Prompt Engineering']
        for keyword in ai_ml:
            if keyword.lower() in job_description.lower():
                tech_keywords.add(keyword)

        return list(tech_keywords)

def main():
    """Test the job analyzer"""
    sample_jd = """
    Senior Software Engineer - AI/ML Platform

    We are seeking a Senior Software Engineer to join our AI/ML Platform team.

    Requirements:
    - 5+ years of software engineering experience
    - Strong proficiency in Python and experience with machine learning frameworks (TensorFlow, PyTorch)
    - Experience with LLM integration and RAG systems
    - Proficiency with cloud platforms (AWS, GCP)
    - Experience with Docker, Kubernetes
    - Strong understanding of API design and microservices

    Nice to have:
    - Experience with LangChain, prompt engineering
    - Knowledge of vector databases (Pinecone, Weaviate)
    - React/TypeScript for frontend
    """

    analyzer = JobAnalyzer()
    result = analyzer.analyze_job_description(sample_jd, company_name="TechCorp")

    print("✓ Job Analysis Complete")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
