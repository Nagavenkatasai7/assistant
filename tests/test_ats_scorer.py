"""
Comprehensive unit tests for ATS Scoring Engine
Tests all scoring components and validates accuracy
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from scoring.ats_scorer import ATSScorer
from scoring.keyword_matcher import KeywordMatcher
from scoring.format_validator import FormatValidator
from scoring.section_analyzer import SectionAnalyzer


class TestKeywordMatcher(unittest.TestCase):
    """Test keyword matching and density analysis"""

    def setUp(self):
        self.matcher = KeywordMatcher()

    def test_basic_keyword_matching(self):
        """Test basic keyword matching functionality"""
        resume_content = """
        Senior Software Engineer with expertise in Python, JavaScript, and AWS.
        Developed machine learning models using TensorFlow and PyTorch.
        """
        job_keywords = ['Python', 'JavaScript', 'AWS', 'Machine Learning', 'TensorFlow']

        result = self.matcher.analyze_keywords(resume_content, job_keywords)

        self.assertGreater(result['match_percentage'], 80)
        self.assertIn('python', [k.lower() for k in result['matched_keywords']])
        self.assertIn('javascript', [k.lower() for k in result['matched_keywords']])

    def test_keyword_density_calculation(self):
        """Test keyword density is calculated correctly"""
        # Small resume with known keywords
        resume_content = "Python developer Python expert Python specialist"  # 6 words, 3 keywords
        job_keywords = ['Python']

        result = self.matcher.analyze_keywords(resume_content, job_keywords)

        # 3 occurrences / 6 words = 50% density
        self.assertGreater(result['keyword_density'], 40)
        self.assertEqual(result['total_occurrences'], 3)

    def test_synonym_matching(self):
        """Test that synonyms are properly matched"""
        resume_content = "Expert in JS and JavaScript programming"
        job_keywords = ['JavaScript']

        result = self.matcher.analyze_keywords(resume_content, job_keywords)

        self.assertGreater(result['match_percentage'], 90)
        self.assertGreater(result['total_occurrences'], 1)

    def test_action_verbs_analysis(self):
        """Test action verb detection"""
        resume_content = """
        - Developed and implemented new features
        - Led team of 5 engineers
        - Achieved 30% performance improvement
        - Optimized database queries
        """

        result = self.matcher.analyze_action_verbs(resume_content)

        self.assertGreater(result['count'], 3)
        self.assertGreater(result['score'], 2)
        self.assertIn('developed', result['found_verbs'])
        self.assertIn('led', result['found_verbs'])

    def test_quantifiable_results_detection(self):
        """Test detection of metrics and numbers"""
        resume_content = """
        - Increased revenue by 25%
        - Reduced costs by $50,000
        - Managed team of 10+ engineers
        - Improved performance by 3x
        """

        result = self.matcher.analyze_quantifiable_results(resume_content)

        self.assertGreater(result['count'], 3)
        self.assertGreater(result['score'], 2)

    def test_empty_input_handling(self):
        """Test handling of empty inputs"""
        result = self.matcher.analyze_keywords("", [])

        self.assertEqual(result['match_percentage'], 0)
        self.assertEqual(result['matched_keywords'], [])


class TestFormatValidator(unittest.TestCase):
    """Test format validation for ATS compatibility"""

    def setUp(self):
        self.validator = FormatValidator()

    def test_clean_resume_format(self):
        """Test that clean, ATS-friendly format passes all checks"""
        clean_resume = """
        John Doe
        email@example.com | 555-1234 | LinkedIn | GitHub

        PROFESSIONAL SUMMARY
        Experienced software engineer with 5+ years in full-stack development.

        PROFESSIONAL EXPERIENCE
        Senior Engineer | Tech Corp | San Francisco, CA
        01/2020 - Present
        - Developed scalable applications
        - Led team of 3 developers

        EDUCATION
        Bachelor of Science in Computer Science | MIT | 2019

        TECHNICAL SKILLS
        Python, JavaScript, React, AWS, Docker
        """

        result = self.validator.validate_format(clean_resume, 'pdf')

        self.assertGreater(result['total_score'], 25)
        self.assertEqual(len(result['issues']), 0)

    def test_table_detection(self):
        """Test detection of tables in resume"""
        resume_with_table = """
        | Skill | Level |
        |-------|-------|
        | Python | Expert |
        """

        result = self.validator.validate_format(resume_with_table, 'pdf')

        self.assertLess(result['checks']['tables']['score'], 5)
        self.assertFalse(result['checks']['tables']['passed'])

    def test_special_characters_detection(self):
        """Test detection of problematic special characters"""
        resume_with_symbols = "Skills: Python ★ JavaScript ✓ AWS ◆"

        result = self.validator.validate_format(resume_with_symbols, 'pdf')

        self.assertFalse(result['checks']['special_characters']['passed'])
        self.assertGreater(len(result['checks']['special_characters']['found_chars']), 0)

    def test_section_headers_validation(self):
        """Test validation of standard section headers"""
        resume_with_sections = """
        PROFESSIONAL EXPERIENCE
        Software Engineer at Company

        EDUCATION
        BS in Computer Science

        TECHNICAL SKILLS
        Python, Java, SQL
        """

        result = self.validator.validate_format(resume_with_sections, 'pdf')

        self.assertTrue(result['checks']['section_headers']['passed'])
        self.assertEqual(result['checks']['section_headers']['score'], 5.0)

    def test_file_format_validation(self):
        """Test file format scoring"""
        # DOCX should score highest
        docx_result = self.validator.validate_file_format('docx', 500000)
        self.assertEqual(docx_result['checks']['file_format']['score'], 5.0)

        # PDF should score well
        pdf_result = self.validator.validate_file_format('pdf', 500000)
        self.assertEqual(pdf_result['checks']['file_format']['score'], 4.0)

        # Unsupported format should score poorly
        bad_result = self.validator.validate_file_format('jpg', 500000)
        self.assertEqual(bad_result['checks']['file_format']['score'], 0.0)

    def test_file_size_validation(self):
        """Test file size limits"""
        # Under 1MB should pass
        small_result = self.validator.validate_file_format('pdf', 500000)
        self.assertEqual(small_result['checks']['file_size']['score'], 3.0)

        # Over 2MB should fail
        large_result = self.validator.validate_file_format('pdf', 3000000)
        self.assertEqual(large_result['checks']['file_size']['score'], 0.0)


class TestSectionAnalyzer(unittest.TestCase):
    """Test resume section analysis"""

    def setUp(self):
        self.analyzer = SectionAnalyzer()

    def test_complete_contact_info(self):
        """Test detection of complete contact information"""
        resume = """
        John Doe
        john@example.com | 555-123-4567 | San Francisco, CA | LinkedIn
        """

        result = self.analyzer.analyze_sections(resume)

        self.assertTrue(result['checks']['contact_info']['complete'])
        self.assertEqual(result['checks']['contact_info']['score'], 5.0)

    def test_missing_contact_info(self):
        """Test detection of missing contact fields"""
        resume = "John Doe\nSoftware Engineer"

        result = self.analyzer.analyze_sections(resume)

        self.assertFalse(result['checks']['contact_info']['complete'])
        self.assertGreater(len(result['checks']['contact_info']['missing_fields']), 0)

    def test_experience_section_detection(self):
        """Test detection and validation of experience section"""
        resume = """
        PROFESSIONAL EXPERIENCE

        Senior Software Engineer | TechCorp | San Francisco, CA
        01/2020 - Present
        - Developed scalable web applications
        - Led team of 5 developers
        - Increased system performance by 40%

        Software Engineer | StartupCo | New York, NY
        06/2018 - 12/2019
        - Built RESTful APIs
        - Implemented CI/CD pipelines
        """

        result = self.analyzer.analyze_sections(resume)

        self.assertTrue(result['checks']['experience']['passed'])
        self.assertGreater(result['checks']['experience']['entry_count'], 1)
        self.assertGreater(result['checks']['experience']['bullet_count'], 4)

    def test_education_section_detection(self):
        """Test detection of education section"""
        resume = """
        EDUCATION

        Bachelor of Science in Computer Science | MIT | 2018
        GPA: 3.8/4.0
        """

        result = self.analyzer.analyze_sections(resume)

        self.assertTrue(result['checks']['education']['passed'])
        self.assertTrue(result['checks']['education']['has_degree'])

    def test_date_formatting_consistency(self):
        """Test date format consistency checking"""
        # Consistent dates
        consistent_resume = """
        Experience:
        01/2020 - 05/2023
        06/2018 - 12/2019
        """

        result = self.analyzer.analyze_sections(consistent_resume)
        self.assertTrue(result['checks']['date_formatting']['consistent'])

        # Inconsistent dates
        inconsistent_resume = """
        Experience:
        01/2020 - May 2023
        2018 - 2019
        """

        result2 = self.analyzer.analyze_sections(inconsistent_resume)
        self.assertFalse(result2['checks']['date_formatting']['consistent'])

    def test_skills_section_detection(self):
        """Test detection and analysis of skills section"""
        resume = """
        TECHNICAL SKILLS
        Languages: Python, JavaScript, Java, C++, SQL
        Frameworks: React, Node.js, Django, Spring Boot
        Tools: Docker, Kubernetes, AWS, Git, Jenkins
        """

        result = self.analyzer.analyze_sections(resume)

        skills_check = result['checks'].get('skills', {})
        self.assertGreater(skills_check.get('skill_count', 0), 10)


class TestATSScorer(unittest.TestCase):
    """Test main ATS scoring engine"""

    def setUp(self):
        self.scorer = ATSScorer()

    def test_perfect_resume_score(self):
        """Test scoring of a high-quality, ATS-optimized resume"""
        perfect_resume = """
        John Doe
        john.doe@email.com | 555-123-4567 | LinkedIn | GitHub | San Francisco, CA

        PROFESSIONAL SUMMARY
        Senior Software Engineer with 8+ years of experience in Python, JavaScript, and AWS.
        Expert in building scalable web applications and RESTful APIs. Led teams of 5+ engineers.

        TECHNICAL SKILLS
        Languages: Python, JavaScript, TypeScript, Java, SQL
        Frameworks: React, Node.js, Django, Flask, Spring Boot
        Cloud: AWS, Docker, Kubernetes, Terraform
        Databases: PostgreSQL, MongoDB, Redis
        Tools: Git, Jenkins, CircleCI, JIRA

        PROFESSIONAL EXPERIENCE

        Senior Software Engineer | TechCorp Inc | San Francisco, CA
        01/2020 - Present
        - Developed and deployed 15+ microservices using Python and AWS, improving system scalability by 300%
        - Led team of 5 engineers to deliver $2M revenue-generating product
        - Implemented CI/CD pipeline reducing deployment time by 50%
        - Optimized database queries achieving 40% performance improvement
        - Architected RESTful APIs serving 1M+ daily requests

        Software Engineer | StartupCo | San Francisco, CA
        06/2017 - 12/2019
        - Built real-time data processing system handling 100K events/second
        - Reduced infrastructure costs by $50,000 annually through optimization
        - Collaborated with cross-functional teams to deliver 20+ features
        - Mentored 3 junior developers

        EDUCATION
        Bachelor of Science in Computer Science | Stanford University | 2017
        GPA: 3.8/4.0

        CERTIFICATIONS
        AWS Certified Solutions Architect
        """

        job_keywords = [
            'Python', 'JavaScript', 'AWS', 'Docker', 'Kubernetes',
            'React', 'Node.js', 'PostgreSQL', 'CI/CD', 'RESTful APIs'
        ]

        result = self.scorer.score_resume(
            resume_content=perfect_resume,
            job_keywords=job_keywords,
            file_format='pdf'
        )

        # Should score very high
        self.assertGreater(result['score'], 75)
        self.assertEqual(result['color'], 'green')
        self.assertGreater(result['pass_probability'], 70)

    def test_poor_resume_score(self):
        """Test scoring of a poorly formatted resume"""
        poor_resume = """
        Bob Smith
        Software developer
        """

        job_keywords = [
            'Python', 'JavaScript', 'AWS', 'Docker', 'Kubernetes'
        ]

        result = self.scorer.score_resume(
            resume_content=poor_resume,
            job_keywords=job_keywords,
            file_format='pdf'
        )

        # Should score low
        self.assertLess(result['score'], 60)
        self.assertEqual(result['color'], 'red')
        self.assertGreater(len(result['top_suggestions']), 0)

    def test_category_scores_breakdown(self):
        """Test that all category scores are calculated"""
        resume = """
        John Doe
        john@email.com | 555-1234 | San Francisco, CA

        EXPERIENCE
        Software Engineer | Company | 2020-2023
        - Developed applications

        EDUCATION
        BS Computer Science | University | 2019

        SKILLS
        Python, JavaScript
        """

        result = self.scorer.score_resume(
            resume_content=resume,
            job_keywords=['Python', 'JavaScript'],
            file_format='pdf'
        )

        # Check all categories are present
        self.assertIn('content', result['category_scores'])
        self.assertIn('format', result['category_scores'])
        self.assertIn('structure', result['category_scores'])
        self.assertIn('compatibility', result['category_scores'])

        # Each category should have a score
        for category, data in result['category_scores'].items():
            self.assertIn('score', data)
            self.assertIn('max', data)
            self.assertGreater(data['max'], 0)

    def test_scoring_performance(self):
        """Test that scoring completes within performance requirements"""
        resume = "Test resume content" * 100
        job_keywords = ['Python', 'JavaScript', 'AWS']

        result = self.scorer.score_resume(
            resume_content=resume,
            job_keywords=job_keywords
        )

        # Should complete in less than 1 second
        self.assertLess(result['processing_time'], 1.0)

    def test_quick_check_functionality(self):
        """Test quick check provides fast results"""
        resume = """
        john@email.com | 555-1234
        EXPERIENCE: Software Engineer
        EDUCATION: BS Computer Science
        """

        result = self.scorer.quick_check(resume)

        self.assertIn('score', result)
        self.assertIn('color', result)
        self.assertIn('passed', result)
        self.assertTrue(result['quick_check'])
        self.assertLess(result['processing_time'], 0.5)

    def test_empty_resume_handling(self):
        """Test handling of empty or minimal resume"""
        result = self.scorer.score_resume(
            resume_content="",
            job_keywords=['Python']
        )

        self.assertEqual(result['score'], 0)
        self.assertEqual(result['color'], 'red')

    def test_suggestions_are_actionable(self):
        """Test that suggestions are specific and actionable"""
        resume = """
        John Doe
        Developer

        Experience:
        Worked on projects
        """

        result = self.scorer.score_resume(
            resume_content=resume,
            job_keywords=['Python', 'AWS', 'Docker']
        )

        # Should have specific suggestions
        self.assertGreater(len(result['top_suggestions']), 0)

        # Suggestions should be strings
        for suggestion in result['top_suggestions']:
            self.assertIsInstance(suggestion, str)
            self.assertGreater(len(suggestion), 10)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling"""

    def setUp(self):
        self.scorer = ATSScorer()

    def test_very_long_resume(self):
        """Test handling of very long resume"""
        long_resume = "Experience: " + " ".join(["Developed software"] * 1000)

        result = self.scorer.score_resume(
            resume_content=long_resume,
            job_keywords=['Python']
        )

        self.assertIsInstance(result['score'], (int, float))

    def test_special_characters_in_keywords(self):
        """Test handling of special characters in keywords"""
        resume = "Expert in C++, .NET, and React.js"
        keywords = ['C++', '.NET', 'React.js']

        matcher = KeywordMatcher()
        result = matcher.analyze_keywords(resume, keywords)

        self.assertGreater(result['match_percentage'], 50)

    def test_unicode_content(self):
        """Test handling of unicode characters"""
        resume = "Software Engineer with expertise in AI/ML 🚀"
        keywords = ['AI', 'ML']

        matcher = KeywordMatcher()
        result = matcher.analyze_keywords(resume, keywords)

        self.assertGreater(result['match_percentage'], 0)

    def test_none_inputs(self):
        """Test handling of None inputs gracefully"""
        result = self.scorer.score_resume(
            resume_content="Test resume",
            job_keywords=None
        )

        # Should not crash, should provide some score
        self.assertIsInstance(result['score'], (int, float))


def run_test_suite():
    """Run all tests and generate report"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestKeywordMatcher))
    suite.addTests(loader.loadTestsFromTestCase(TestFormatValidator))
    suite.addTests(loader.loadTestsFromTestCase(TestSectionAnalyzer))
    suite.addTests(loader.loadTestsFromTestCase(TestATSScorer))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success Rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print("="*70)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_test_suite()
    sys.exit(0 if success else 1)
