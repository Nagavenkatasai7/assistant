"""
Tavily AI Search Client
AI-powered search providing reliable, real-time web data optimized for AI agents
"""
import os
import time
from tavily import TavilyClient as TavilySDK
from typing import Dict, Any, List, Optional


class TavilyClient:
    """
    Client for Tavily AI Search API

    Features:
    - AI-optimized search results
    - Real-time web data with citations
    - Content extraction and scraping
    - Domain filtering for reliable sources
    - LLM-ready formatted output
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Tavily client

        Args:
            api_key: Tavily API key (or set TAVILY_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('TAVILY_API_KEY')
        if not self.api_key:
            raise ValueError("Tavily API key not provided")

        self.client = TavilySDK(api_key=self.api_key)

    def search(
        self,
        query: str,
        search_depth: str = "advanced",
        max_results: int = 5,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        include_answer: bool = True,
        include_raw_content: bool = False
    ) -> Dict[str, Any]:
        """
        Perform AI-powered web search

        Args:
            query: Search query
            search_depth: "basic" or "advanced" (more thorough)
            max_results: Maximum number of results to return
            include_domains: List of domains to focus on
            exclude_domains: List of domains to exclude
            include_answer: Include AI-generated answer summary
            include_raw_content: Include full raw content from pages

        Returns:
            Dictionary with search results and metadata
        """
        start_time = time.time()

        try:
            response = self.client.search(
                query=query,
                search_depth=search_depth,
                max_results=max_results,
                include_domains=include_domains,
                exclude_domains=exclude_domains,
                include_answer=include_answer,
                include_raw_content=include_raw_content
            )

            duration = time.time() - start_time

            return {
                "query": query,
                "answer": response.get("answer", ""),
                "results": response.get("results", []),
                "images": response.get("images", []),
                "duration": duration,
                "success": True
            }

        except Exception as e:
            return {
                "query": query,
                "answer": "",
                "results": [],
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time
            }

    def research_company(
        self,
        company_name: str,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Research a company for resume optimization

        Args:
            company_name: Name of the company to research
            focus_areas: Specific aspects to focus on (e.g., culture, values, tech stack)

        Returns:
            Dictionary with company research data
        """
        # Build comprehensive search query
        if focus_areas:
            focus_str = ", ".join(focus_areas)
            query = f"{company_name} company {focus_str}"
        else:
            query = f"{company_name} company culture values mission technology stack recent news"

        # Focus on reliable professional sources
        include_domains = [
            "linkedin.com",
            "glassdoor.com",
            "techcrunch.com",
            "crunchbase.com"
        ]

        result = self.search(
            query=query,
            search_depth="advanced",
            max_results=10,
            include_domains=include_domains,
            include_answer=True,
            include_raw_content=False
        )

        if not result["success"]:
            return result

        # Format company research data
        research = {
            "company_name": company_name,
            "summary": result["answer"],
            "key_insights": self._extract_insights(result["results"]),
            "sources": [
                {
                    "title": r["title"],
                    "url": r["url"],
                    "snippet": r.get("content", "")[:200]
                }
                for r in result["results"][:5]
            ],
            "success": True
        }

        return research

    def analyze_job_market(
        self,
        job_title: str,
        location: Optional[str] = None,
        industry: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze job market trends for a specific role

        Args:
            job_title: Target job title
            location: Geographic location (optional)
            industry: Industry sector (optional)

        Returns:
            Dictionary with job market analysis
        """
        # Build search query
        query_parts = [job_title, "job market trends"]
        if location:
            query_parts.append(location)
        if industry:
            query_parts.append(industry)

        query = " ".join(query_parts)

        result = self.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_answer=True
        )

        if not result["success"]:
            return result

        return {
            "job_title": job_title,
            "location": location,
            "industry": industry,
            "market_analysis": result["answer"],
            "trends": self._extract_trends(result["results"]),
            "sources": result["results"][:3],
            "success": True
        }

    def get_context(
        self,
        query: str,
        max_results: int = 5
    ) -> str:
        """
        Get search context optimized for RAG/LLM workflows

        This is a convenience method that returns formatted text
        suitable for including in LLM prompts.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            Formatted string with search results
        """
        try:
            context = self.client.get_search_context(
                query=query,
                max_results=max_results
            )
            return context
        except Exception as e:
            return f"Error retrieving search context: {str(e)}"

    def _extract_insights(self, results: List[Dict]) -> List[str]:
        """Extract key insights from search results"""
        insights = []

        for result in results[:5]:
            content = result.get("content", "")
            if content:
                # Extract first meaningful sentence
                sentences = content.split(". ")
                if sentences:
                    insights.append(sentences[0].strip())

        return insights

    def _extract_trends(self, results: List[Dict]) -> List[str]:
        """Extract trend information from job market results"""
        trends = []

        for result in results[:3]:
            content = result.get("content", "")
            # Look for keywords indicating trends
            trend_keywords = ["growing", "increasing", "demand", "popular", "emerging"]

            sentences = content.split(". ")
            for sentence in sentences:
                if any(keyword in sentence.lower() for keyword in trend_keywords):
                    trends.append(sentence.strip())
                    break

        return trends

    def get_client_info(self) -> Dict[str, Any]:
        """
        Get information about Tavily service

        Returns:
            Dictionary with service specifications
        """
        return {
            "service": "Tavily AI Search",
            "description": "AI-powered search for reliable, real-time web data",
            "capabilities": [
                "Web search",
                "Content extraction",
                "Domain filtering",
                "AI-generated summaries",
                "RAG optimization",
                "Citation tracking"
            ],
            "use_cases": [
                "Company research",
                "Job market analysis",
                "Competitive intelligence",
                "Content enrichment"
            ]
        }


# Convenience function for quick access
def create_tavily_client(api_key: Optional[str] = None) -> TavilyClient:
    """Create and return a Tavily client instance"""
    return TavilyClient(api_key=api_key)
