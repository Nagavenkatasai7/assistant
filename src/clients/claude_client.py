"""
Claude Sonnet 4.5 Client
Anthropic's balanced model for fast, high-quality resume generation
"""
import os
import time
from anthropic import Anthropic
from typing import Dict, Any, Optional


class ClaudeOpusClient:
    """
    Client for Claude Sonnet 4.5 API

    Features:
    - 200K token context window
    - Balanced reasoning and speed
    - Fast generation speed
    - Extended thinking mode for complex tasks
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claude Sonnet client

        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("Anthropic API key not provided")

        # Initialize Anthropic client
        self.client = Anthropic(api_key=self.api_key)

        # Model configuration - Claude Sonnet 4.5
        self.model = "claude-sonnet-4-5-20250929"  # Claude Sonnet 4.5 model
        self.default_temperature = 0.7
        self.default_max_tokens = 8192

    def chat_completion(
        self,
        messages: list[Dict[str, str]],
        temperature: float = None,
        max_tokens: int = None,
        timeout: float = 120.0
    ) -> Dict[str, Any]:
        """
        Create a chat completion using Claude Sonnet 4.5

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
            # Separate system message if present
            system_message = None
            api_messages = []

            for msg in messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                else:
                    api_messages.append({
                        "role": msg['role'],
                        "content": msg['content']
                    })

            # Create message with Anthropic API
            kwargs = {
                "model": self.model,
                "messages": api_messages,
                "temperature": temperature or self.default_temperature,
                "max_tokens": max_tokens or self.default_max_tokens,
                "timeout": timeout
            }

            if system_message:
                kwargs["system"] = system_message

            response = self.client.messages.create(**kwargs)

            # Extract response data
            duration = time.time() - start_time

            result = {
                "content": response.content[0].text,
                "finish_reason": response.stop_reason,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                "model": response.model,
                "duration": duration,
                "success": True
            }

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
        temperature: float = 0.7,
        max_tokens: int = 8192,
        timeout: float = 120.0
    ) -> Dict[str, Any]:
        """
        Generate resume content using Claude Opus 4.1

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
        Get information about the Claude Opus 4.1 model

        Returns:
            Dictionary with model specifications
        """
        return {
            "model": self.model,
            "provider": "Anthropic",
            "model_type": "Claude Opus 4.1",
            "context_window": 200000,  # 200K context window
            "max_output_tokens": self.default_max_tokens,
            "capabilities": [
                "Advanced reasoning and analysis",
                "Fast generation speed",
                "Extended thinking mode",
                "Code generation and review",
                "Long context understanding (200K)",
                "Multi-turn dialogue",
                "Tool use and agentic workflows"
            ],
            "api_type": "Anthropic Messages API"
        }


# Convenience function for quick access
def create_claude_client(api_key: Optional[str] = None) -> ClaudeOpusClient:
    """Create and return a Claude Opus client instance"""
    return ClaudeOpusClient(api_key=api_key)
