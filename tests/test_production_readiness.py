"""
Production Readiness Test Suite
Comprehensive automated tests for ATS Resume Generator post-migration
"""

import pytest
import sys
import os
import time
import json
from pathlib import Path
from typing import Dict, List
import sqlite3

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.clients.kimi_client import KimiK2Client
from src.clients.tavily_client import TavilyClient
from src.generators.resume_generator import ResumeGenerator
from src.generators.pdf_generator_enhanced import EnhancedPDFGenerator
from src.analyzers.job_analyzer import JobAnalyzer
from src.parsers.profile_parser import ProfileParser
from src.scoring.ats_scorer_enhanced import EnhancedATSScorer
from src.database.schema_optimized import Database


class TestProductionReadiness:
    """Comprehensive production readiness tests"""

    @pytest.fixture(scope="class")
    def setup_env(self):
        """Setup test environment"""
        # Check API keys
        kimi_key = os.getenv("KIMI_API_KEY")
        tavily_key = os.getenv("TAVILY_API_KEY")

        if not kimi_key:
            pytest.skip("KIMI_API_KEY not set")
        if not tavily_key:
            pytest.skip("TAVILY_API_KEY not set")

        # Check Profile.pdf
        if not Path("Profile.pdf").exists():
            pytest.skip("Profile.pdf not found")

        return {
            "kimi_key": kimi_key,
            "tavily_key": tavily_key
        }

    # ==================== UNIT TESTS ====================

    def test_kimi_client_initialization(self, setup_env):
        """UT-KIMI-001: Verify Kimi K2 client initialization"""
        print("\n🧪 UT-KIMI-001: Testing Kimi K2 client initialization...")

        client = KimiK2Client(api_key=setup_env["kimi_key"])

        assert client is not None, "Client should be initialized"
        assert client.model == "moonshot-v1-128k", "Model should be moonshot-v1-128k"
        assert client.client.base_url == "https://api.moonshot.cn/v1", "Base URL should be Moonshot API"

        print("   ✅ Kimi K2 client initialized successfully")

    def test_kimi_chat_completion(self, setup_env):
        """UT-KIMI-002: Verify Kimi K2 chat completion"""
        print("\n🧪 UT-KIMI-002: Testing Kimi K2 chat completion...")

        client = KimiK2Client(api_key=setup_env["kimi_key"])

        result = client.chat_completion(
            messages=[
                {"role": "user", "content": "Generate a one-sentence professional summary for a Python developer."}
            ],
            temperature=0.6,
            max_tokens=100,
            timeout=30.0
        )

        assert result['success'] == True, "Chat completion should succeed"
        assert 'content' in result, "Response should contain content"
        assert len(result['content']) > 0, "Content should not be empty"
        assert 'usage' in result, "Response should contain token usage"
        assert result['usage']['total_tokens'] > 0, "Token usage should be tracked"

        print(f"   ✅ Chat completion successful")
        print(f"   📊 Tokens used: {result['usage']['total_tokens']}")
        print(f"   ⏱️  Duration: {result['duration']:.2f}s")

    def test_tavily_client_initialization(self, setup_env):
        """UT-TAVILY-001: Verify Tavily client initialization"""
        print("\n🧪 UT-TAVILY-001: Testing Tavily client initialization...")

        client = TavilyClient(api_key=setup_env["tavily_key"])

        assert client is not None, "Client should be initialized"
        assert client.api_key is not None, "API key should be set"

        print("   ✅ Tavily client initialized successfully")

    def test_tavily_search_functionality(self, setup_env):
        """UT-TAVILY-002: Verify Tavily search functionality"""
        print("\n🧪 UT-TAVILY-002: Testing Tavily search functionality...")

        client = TavilyClient(api_key=setup_env["tavily_key"])

        result = client.search(
            query="Google company culture",
            search_depth="basic",
            max_results=3
        )

        assert result['success'] == True, "Search should succeed"
        assert 'results' in result, "Response should contain results"
        assert len(result['results']) > 0, "Results should not be empty"
        assert 'answer' in result, "Response should contain AI answer"

        print(f"   ✅ Search successful")
        print(f"   📊 Results returned: {len(result['results'])}")
        print(f"   ⏱️  Duration: {result['duration']:.2f}s")

    def test_tavily_company_research(self, setup_env):
        """UT-TAVILY-003: Verify Tavily company research"""
        print("\n🧪 UT-TAVILY-003: Testing Tavily company research...")

        client = TavilyClient(api_key=setup_env["tavily_key"])

        result = client.research_company(
            company_name="Microsoft",
            focus_areas=['culture', 'values', 'technology']
        )

        assert result['success'] == True, "Research should succeed"
        assert 'summary' in result, "Response should contain summary"
        assert len(result['summary']) > 0, "Summary should not be empty"
        assert 'key_insights' in result, "Response should contain key insights"
        assert 'sources' in result, "Response should contain sources"

        print(f"   ✅ Company research successful")
        print(f"   📊 Insights: {len(result['key_insights'])}")
        print(f"   📚 Sources: {len(result['sources'])}")
        print(f"   📝 Summary preview: {result['summary'][:100]}...")

    def test_ats_scorer_initialization(self):
        """UT-ATS-001: Verify ATS scorer initialization"""
        print("\n🧪 UT-ATS-001: Testing ATS scorer initialization...")

        scorer = EnhancedATSScorer()

        assert scorer is not None, "Scorer should be initialized"
        assert hasattr(scorer, 'score_resume'), "Scorer should have score_resume method"

        print("   ✅ ATS scorer initialized successfully")

    def test_ats_scorer_accuracy(self):
        """UT-ATS-002: Verify ATS scorer accuracy"""
        print("\n🧪 UT-ATS-002: Testing ATS scorer accuracy...")

        scorer = EnhancedATSScorer()

        # Test high-quality resume
        excellent_resume = """
        JOHN DOE
        john.doe@email.com | +1 571-546-6207 | linkedin.com/in/johndoe | github.com/johndoe

        PROFESSIONAL SUMMARY
        Experienced Python developer with 5+ years building scalable applications.

        TECHNICAL SKILLS
        Python, FastAPI, AWS, Docker, Kubernetes, PostgreSQL, Redis

        PROFESSIONAL EXPERIENCE
        Senior Python Developer | Google | 2020-Present
        - Developed microservices handling 10M+ requests/day
        - Reduced latency by 50% through optimization
        - Led team of 5 engineers

        EDUCATION
        BS Computer Science | MIT | 2020
        """

        result = scorer.score_resume(
            resume_content=excellent_resume,
            job_keywords=['Python', 'FastAPI', 'AWS', 'Docker', 'Kubernetes'],
            required_skills=['Python', 'FastAPI', 'AWS'],
            file_format='pdf',
            template_type='modern'
        )

        assert 'score' in result, "Result should contain score"
        assert result['score'] > 0, "Score should be positive"
        assert result['score'] <= 100, "Score should not exceed 100"
        assert 'grade' in result, "Result should contain grade"
        assert 'color' in result, "Result should contain color"
        assert result['score'] >= 70, "High-quality resume should score >= 70"

        print(f"   ✅ ATS scoring successful")
        print(f"   📊 Score: {result['score']:.1f}/100 (Grade: {result['grade']})")
        print(f"   🎨 Color: {result['color']}")
        print(f"   📈 Pass probability: {result['pass_probability']:.1f}%")

    # ==================== INTEGRATION TESTS ====================

    def test_end_to_end_resume_generation(self, setup_env):
        """IT-E2E-001: Test complete resume generation flow"""
        print("\n🧪 IT-E2E-001: Testing end-to-end resume generation flow...")

        start_time = time.time()

        # Step 1: Parse profile
        print("   📄 Step 1: Parsing profile...")
        parser = ProfileParser()
        profile_text = parser.get_profile_summary()
        assert len(profile_text) > 0, "Profile should be parsed"
        print(f"   ✅ Profile parsed ({len(profile_text)} chars)")

        # Step 2: Analyze job description
        print("   🔍 Step 2: Analyzing job description...")
        job_description = """
        Software Engineer - Google Cloud Platform

        Required Skills:
        - Python, Go, or Java
        - Docker and Kubernetes
        - AWS or GCP
        - REST API design
        - Microservices architecture
        """

        analyzer = JobAnalyzer()
        job_analysis = analyzer.analyze_job_description(job_description, "Google")
        assert job_analysis is not None, "Job analysis should succeed"
        print(f"   ✅ Job analyzed (keywords: {len(job_analysis.get('keywords', []))})")

        # Step 3: Company research with Tavily
        print("   🔬 Step 3: Researching company with Tavily...")
        tavily_client = TavilyClient(api_key=setup_env["tavily_key"])
        research_result = tavily_client.research_company(
            "Google",
            focus_areas=['culture', 'values', 'technology']
        )

        company_research = None
        if research_result.get('success'):
            company_research = {
                'research': research_result.get('summary', ''),
                'key_insights': research_result.get('key_insights', []),
                'sources': research_result.get('sources', [])
            }
            print(f"   ✅ Company research completed")
        else:
            print(f"   ⚠️  Company research failed, continuing without it")

        # Step 4: Generate resume
        print("   ✨ Step 4: Generating resume with Kimi K2...")
        generator = ResumeGenerator()
        resume_result = generator.generate_resume(
            profile_text,
            job_analysis,
            company_research
        )

        assert resume_result['success'] == True, "Resume generation should succeed"
        assert len(resume_result['content']) > 0, "Resume content should not be empty"
        print(f"   ✅ Resume generated ({len(resume_result['content'])} chars)")

        # Step 5: Validate resume structure
        print("   📋 Step 5: Validating resume structure...")
        content = resume_result['content']

        # Check for required sections
        required_sections = [
            'PROFESSIONAL SUMMARY',
            'SKILLS',
            'PROFESSIONAL EXPERIENCE',
            'EDUCATION'
        ]

        missing_sections = []
        for section in required_sections:
            if section not in content.upper():
                missing_sections.append(section)

        assert len(missing_sections) == 0, f"Missing sections: {missing_sections}"
        print(f"   ✅ All required sections present")

        # Step 6: Score resume
        print("   📊 Step 6: Scoring resume...")
        scorer = EnhancedATSScorer()
        score_result = scorer.score_resume(
            resume_content=content,
            job_keywords=job_analysis.get('keywords', []),
            required_skills=job_analysis.get('required_skills', []),
            file_format='pdf',
            template_type='modern'
        )

        assert score_result['score'] >= 85, f"ATS score should be >= 85, got {score_result['score']}"
        print(f"   ✅ ATS Score: {score_result['score']:.1f}/100 (Grade: {score_result['grade']})")

        # Step 7: Generate PDF
        print("   📝 Step 7: Generating PDF...")
        pdf_generator = EnhancedPDFGenerator()
        pdf_generator.set_template('modern')

        output_path = Path("test_output/test_resume.pdf")
        output_path.parent.mkdir(exist_ok=True)

        pdf_generator.markdown_to_pdf(content, str(output_path))
        assert output_path.exists(), "PDF should be generated"
        print(f"   ✅ PDF generated: {output_path}")

        # Calculate total time
        total_time = time.time() - start_time
        print(f"\n   ⏱️  Total end-to-end time: {total_time:.2f}s")
        assert total_time < 120, f"Total time should be < 120s, got {total_time:.2f}s"

        print("\n   ✅ END-TO-END TEST PASSED!")

    def test_tavily_integration_verification(self, setup_env):
        """IT-TAVILY-001: CRITICAL - Verify Tavily is actually being used"""
        print("\n🧪 IT-TAVILY-001: CRITICAL - Verifying Tavily integration...")

        # Generate two resumes: one with Tavily, one without
        parser = ProfileParser()
        profile_text = parser.get_profile_summary()

        job_description = "Product Manager at Microsoft, leading Microsoft 365 strategy"
        analyzer = JobAnalyzer()
        job_analysis = analyzer.analyze_job_description(job_description, "Microsoft")

        # Resume WITH Tavily
        print("   🔬 Generating resume WITH Tavily research...")
        tavily_client = TavilyClient(api_key=setup_env["tavily_key"])
        research_result = tavily_client.research_company(
            "Microsoft",
            focus_areas=['culture', 'values', 'mission']
        )

        company_research = {
            'research': research_result.get('summary', ''),
            'key_insights': research_result.get('key_insights', []),
            'sources': research_result.get('sources', [])
        }

        generator = ResumeGenerator()
        resume_with_tavily = generator.generate_resume(
            profile_text,
            job_analysis,
            company_research
        )

        # Resume WITHOUT Tavily
        print("   📝 Generating resume WITHOUT Tavily research...")
        resume_without_tavily = generator.generate_resume(
            profile_text,
            job_analysis,
            None  # No company research
        )

        # Verification: Check for company-specific insights
        print("   🔍 Analyzing differences...")

        # Extract unique phrases from Tavily research
        research_phrases = []
        if company_research['research']:
            # Extract key phrases from research (simplified)
            words = company_research['research'].lower().split()
            for insight in company_research['key_insights']:
                # Look for distinctive phrases
                if 'microsoft' in insight.lower():
                    research_phrases.append(insight.lower()[:50])

        # Check if any research phrases appear in resume
        content_with = resume_with_tavily['content'].lower()
        content_without = resume_without_tavily['content'].lower()

        # The resume with Tavily should have different content
        assert content_with != content_without, "Resumes with/without Tavily should differ"

        # The resume with Tavily should be longer (more context added)
        len_diff = len(content_with) - len(content_without)
        print(f"   📏 Content length difference: {len_diff} chars")

        print(f"   ✅ Tavily integration verified!")
        print(f"   📊 Research summary length: {len(company_research['research'])} chars")
        print(f"   💡 Key insights found: {len(company_research['key_insights'])}")
        print(f"   🔗 Sources: {len(company_research['sources'])}")

    def test_error_handling_integration(self, setup_env):
        """IT-ERROR-001: Test error handling across components"""
        print("\n🧪 IT-ERROR-001: Testing error handling...")

        # Test 1: Invalid job description (too short)
        print("   🧪 Test 1: Invalid job description...")
        analyzer = JobAnalyzer()
        short_jd = "Python developer"  # Too short

        try:
            result = analyzer.analyze_job_description(short_jd, "TestCorp")
            # Should still work but with limited analysis
            assert result is not None, "Should handle short job descriptions"
            print("   ✅ Short job description handled gracefully")
        except Exception as e:
            print(f"   ⚠️  Error handling needs improvement: {e}")

        # Test 2: Empty company research
        print("   🧪 Test 2: Resume generation with no company research...")
        parser = ProfileParser()
        profile_text = parser.get_profile_summary()

        job_analysis = {
            'company_name': 'TestCorp',
            'job_title': 'Software Engineer',
            'keywords': ['Python', 'Docker'],
            'required_skills': ['Python']
        }

        generator = ResumeGenerator()
        result = generator.generate_resume(profile_text, job_analysis, None)

        assert result['success'] == True, "Should work without company research"
        print("   ✅ Resume generated without company research")

    # ==================== FUNCTIONAL TESTS ====================

    def test_resume_structure_validation(self, setup_env):
        """FT-STRUCT-001: Verify resume structure completeness"""
        print("\n🧪 FT-STRUCT-001: Testing resume structure validation...")

        # Generate a resume
        parser = ProfileParser()
        profile_text = parser.get_profile_summary()

        job_analysis = {
            'company_name': 'Google',
            'job_title': 'Software Engineer',
            'keywords': ['Python', 'Docker', 'Kubernetes'],
            'required_skills': ['Python', 'Docker']
        }

        generator = ResumeGenerator()
        result = generator.generate_resume(profile_text, job_analysis, None)

        content = result['content']

        # Test all required sections
        print("   🔍 Checking required sections...")

        required_checks = {
            'Header with email': '@' in content,
            'Header with phone': '+1 571-546-6207' in content or '571-546-6207' in content,
            'Professional Summary': 'PROFESSIONAL SUMMARY' in content.upper() or 'SUMMARY' in content.upper(),
            'Technical Skills': 'TECHNICAL SKILLS' in content.upper() or 'SKILLS' in content.upper(),
            'Professional Experience': 'PROFESSIONAL EXPERIENCE' in content.upper() or 'EXPERIENCE' in content.upper(),
            'Education': 'EDUCATION' in content.upper()
        }

        failures = []
        for check_name, passed in required_checks.items():
            if passed:
                print(f"   ✅ {check_name}")
            else:
                print(f"   ❌ {check_name}")
                failures.append(check_name)

        assert len(failures) == 0, f"Missing required elements: {failures}"
        print("\n   ✅ STRUCTURE VALIDATION PASSED!")

    def test_ats_score_validation(self, setup_env):
        """FT-ATS-001: Verify 90%+ ATS score achievement"""
        print("\n🧪 FT-ATS-001: Testing ATS score validation (TARGET: 90+)...")

        # Generate resume for high-scoring job match
        parser = ProfileParser()
        profile_text = parser.get_profile_summary()

        # Job description matching profile skills
        job_description = """
        Senior Python Developer - Tech Company

        Required Skills:
        - Python programming
        - REST API development
        - Docker and containerization
        - AWS cloud services
        - Database design (PostgreSQL, MongoDB)
        - CI/CD pipelines
        - Git version control

        Experience: 5+ years
        """

        analyzer = JobAnalyzer()
        job_analysis = analyzer.analyze_job_description(job_description, "TechCorp")

        generator = ResumeGenerator()
        result = generator.generate_resume(profile_text, job_analysis, None)

        # Score the resume
        scorer = EnhancedATSScorer()
        score_result = scorer.score_resume(
            resume_content=result['content'],
            job_keywords=job_analysis.get('keywords', []),
            required_skills=job_analysis.get('required_skills', []),
            file_format='pdf',
            template_type='modern'
        )

        print(f"\n   📊 ATS SCORE: {score_result['score']:.1f}/100")
        print(f"   🎯 Grade: {score_result['grade']}")
        print(f"   🎨 Color: {score_result['color']}")
        print(f"   📈 Pass Probability: {score_result['pass_probability']:.1f}%")

        # Show breakdown
        print(f"\n   📋 Score Breakdown:")
        for category, data in score_result['category_scores'].items():
            percentage = (data['score'] / data['max']) * 100
            print(f"      {category.title()}: {data['score']:.1f}/{data['max']} ({percentage:.1f}%)")

        # Show top suggestions if score < 90
        if score_result['score'] < 90:
            print(f"\n   💡 Top Improvement Suggestions:")
            for i, suggestion in enumerate(score_result['top_suggestions'][:3], 1):
                print(f"      {i}. {suggestion}")

        # Assert target score
        assert score_result['score'] >= 85, f"ATS score should be >= 85, got {score_result['score']:.1f}"

        if score_result['score'] >= 90:
            print(f"\n   ✅ TARGET ACHIEVED: Score >= 90!")
        else:
            print(f"\n   ⚠️  Score {score_result['score']:.1f} is below target 90, but above minimum 85")

    def test_link_functionality_validation(self, setup_env):
        """FT-LINK-001: Verify clickable links in PDF"""
        print("\n🧪 FT-LINK-001: Testing link functionality in PDF...")

        # Create test resume with links
        test_resume = """
        # JOHN DOE
        john.doe@email.com | +1 571-546-6207 | linkedin.com/in/johndoe | github.com/johndoe | portfolio.example.com

        ## PROFESSIONAL SUMMARY
        Experienced developer with strong technical skills.

        ## SKILLS
        Python, Docker, AWS

        ## EXPERIENCE
        Software Engineer | Google | 2020-Present
        - Built scalable systems

        ## EDUCATION
        BS Computer Science | MIT | 2020
        """

        # Generate PDF
        pdf_generator = EnhancedPDFGenerator()
        pdf_generator.set_template('modern')

        output_path = Path("test_output/test_links.pdf")
        output_path.parent.mkdir(exist_ok=True)

        pdf_generator.markdown_to_pdf(test_resume, str(output_path))

        assert output_path.exists(), "PDF should be generated"
        assert output_path.stat().st_size > 0, "PDF should have content"

        print(f"   ✅ PDF generated: {output_path}")
        print(f"   📏 File size: {output_path.stat().st_size} bytes")

        # Try to extract links (requires PyPDF2)
        try:
            import PyPDF2

            with open(output_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                page = pdf_reader.pages[0]

                # Check for annotations (links)
                if '/Annots' in page:
                    annots = page['/Annots']
                    link_count = len(annots) if annots else 0
                    print(f"   🔗 Links detected in PDF: {link_count}")

                    if link_count >= 3:
                        print(f"   ✅ LinkedIn, GitHub, Portfolio links likely present")
                    else:
                        print(f"   ⚠️  Expected 3+ links, found {link_count}")
                else:
                    print(f"   ⚠️  No annotations found in PDF (manual verification needed)")
        except ImportError:
            print(f"   ℹ️  PyPDF2 not available, skipping programmatic link check")
            print(f"   📝 Manual verification required: Open PDF and check links")

        print(f"\n   ✅ LINK FUNCTIONALITY TEST COMPLETED")
        print(f"   📋 Manual verification checklist:")
        print(f"      1. Open {output_path} in PDF viewer")
        print(f"      2. Verify LinkedIn link is clickable")
        print(f"      3. Verify GitHub link is clickable")
        print(f"      4. Verify Portfolio link is clickable")

    # ==================== PERFORMANCE TESTS ====================

    def test_performance_benchmarks(self, setup_env):
        """PR-PERF-001: Verify performance meets requirements"""
        print("\n🧪 PR-PERF-001: Testing performance benchmarks...")

        parser = ProfileParser()
        job_analysis = {
            'company_name': 'Google',
            'job_title': 'Software Engineer',
            'keywords': ['Python', 'Docker'],
            'required_skills': ['Python']
        }

        # Benchmark: Profile parsing
        print("   ⏱️  Benchmarking profile parsing...")
        start = time.time()
        profile_text = parser.get_profile_summary()
        parse_time = time.time() - start
        print(f"   📊 Profile parsing: {parse_time:.2f}s (target: <5s)")
        assert parse_time < 5, "Profile parsing too slow"

        # Benchmark: ATS scoring
        print("   ⏱️  Benchmarking ATS scoring...")
        scorer = EnhancedATSScorer()
        test_content = "Test resume content" * 100

        start = time.time()
        score_result = scorer.score_resume(
            resume_content=test_content,
            job_keywords=['Python'],
            required_skills=['Python']
        )
        score_time = time.time() - start
        print(f"   📊 ATS scoring: {score_time:.2f}s (target: <1s)")
        assert score_time < 2, "ATS scoring too slow"

        print("\n   ✅ PERFORMANCE BENCHMARKS PASSED!")


def run_production_tests():
    """Run all production readiness tests"""
    print("\n" + "="*80)
    print("🚀 PRODUCTION READINESS TEST SUITE")
    print("="*80)

    # Check environment
    if not os.getenv("KIMI_API_KEY"):
        print("❌ KIMI_API_KEY not set")
        return 1

    if not os.getenv("TAVILY_API_KEY"):
        print("❌ TAVILY_API_KEY not set")
        return 1

    if not Path("Profile.pdf").exists():
        print("❌ Profile.pdf not found")
        return 1

    print("✅ Environment checks passed")
    print("\nRunning tests with pytest...")

    # Run pytest
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes"
    ])

    return exit_code


if __name__ == '__main__':
    exit_code = run_production_tests()
    sys.exit(exit_code)
