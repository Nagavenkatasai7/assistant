"""
Kimi K2 Thinking Model Client
OpenAI-compatible API wrapper for Moonshot AI's Kimi K2
"""
import os
import time
from openai import OpenAI
from typing import Dict, Any, Optional


class KimiK2Client:
    """
    Client for Kimi K2 Thinking Model API

    Features:
    - OpenAI-compatible API at platform.moonshot.ai
    - 128K token context window
    - Advanced reasoning with thinking traces
    - Optimized for coding, reasoning, and agentic tasks
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Kimi K2 client

        Args:
            api_key: Kimi API key (or set KIMI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('KIMI_API_KEY')
        if not self.api_key:
            raise ValueError("Kimi API key not provided")

        # Initialize OpenAI client pointing to Moonshot AI endpoint
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.moonshot.ai/v1"  # Use .ai domain, not .cn
        )

        # Model configuration - Kimi K2 Thinking (Full reasoning model)
        self.model = "kimi-k2-thinking"  # Full thinking model with deep reasoning
        self.default_temperature = 0.6
        self.default_max_tokens = 4096

    def chat_completion(
        self,
        messages: list[Dict[str, str]],
        temperature: float = None,
        max_tokens: int = None,
        timeout: float = 300.0
    ) -> Dict[str, Any]:
        """
        Create a chat completion using Kimi K2

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds

        Returns:
            Dictionary with response data
        """
        start_time = time.time()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or self.default_temperature,
                max_tokens=max_tokens or self.default_max_tokens,
                timeout=timeout
            )

            # Extract response data
            duration = time.time() - start_time

            result = {
                "content": response.choices[0].message.content,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model,
                "duration": duration,
                "success": True
            }

            # Extract reasoning if available (Kimi K2 may include thinking traces)
            if hasattr(response.choices[0].message, 'reasoning_content'):
                result['reasoning'] = response.choices[0].message.reasoning_content

            return result

        except Exception as e:
            return {
                "content": "",
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }

    def generate_resume(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.6,
        max_tokens: int = 4096,
        timeout: float = 300.0
    ) -> Dict[str, Any]:
        """
        Generate resume content using Kimi K2

        Args:
            system_prompt: System instructions for resume generation
            user_prompt: User request with profile and job details
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            timeout: Request timeout

        Returns:
            Dictionary with generated resume and metadata
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        return self.chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout
        )

    def analyze_job_description(
        self,
        job_description: str,
        timeout: float = 60.0
    ) -> Dict[str, Any]:
        """
        Analyze job description to extract keywords, skills, requirements

        Args:
            job_description: Raw job description text
            timeout: Request timeout

        Returns:
            Dictionary with analyzed job data
        """
        system_prompt = """You are an expert ATS (Applicant Tracking System) analyst.
Your task is to analyze job descriptions and extract structured information that helps
optimize resumes for ATS systems."""

        user_prompt = f"""Analyze this job description and provide:
1. Company name (if mentioned)
2. Job title
3. Required skills (technical and soft skills)
4. Preferred qualifications
5. Key responsibilities
6. Important keywords that ATS systems will look for
7. Experience level required

Job Description:
{job_description}

Provide the analysis in a structured format."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        return self.chat_completion(
            messages=messages,
            temperature=0.3,  # Lower temperature for more consistent extraction
            max_tokens=2048,
            timeout=timeout
        )

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the Kimi K2 Thinking model

        Returns:
            Dictionary with model specifications
        """
        return {
            "model": self.model,
            "provider": "Moonshot AI",
            "model_type": "Kimi K2 Thinking",
            "context_window": 256000,  # 256K context window
            "max_output_tokens": self.default_max_tokens,
            "capabilities": [
                "Advanced reasoning with thinking traces",
                "Code generation and debugging",
                "Tool use and agentic workflows",
                "Multi-turn dialogue",
                "Long context understanding (256K)",
                "1 trillion parameter MoE architecture"
            ],
            "api_type": "OpenAI-compatible"
        }


# Convenience function for quick access
def create_kimi_client(api_key: Optional[str] = None) -> KimiK2Client:
    """Create and return a Kimi K2 client instance"""
    return KimiK2Client(api_key=api_key)
