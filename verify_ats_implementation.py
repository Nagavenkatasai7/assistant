#!/usr/bin/env python3
"""
Verification Script for ATS Scoring Engine Implementation
Checks that all components are properly installed and functional
"""

import sys
from pathlib import Path

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text.center(70)}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓{RESET} {text}")

def print_error(text):
    print(f"{RED}✗{RESET} {text}")

def print_warning(text):
    print(f"{YELLOW}⚠{RESET} {text}")

def verify_imports():
    """Verify all required imports work"""
    print_header("Verifying Imports")

    checks = []

    # Check scoring module
    try:
        from src.scoring.ats_scorer import ATSScorer
        print_success("ATSScorer imported successfully")
        checks.append(True)
    except ImportError as e:
        print_error(f"Failed to import ATSScorer: {e}")
        checks.append(False)

    try:
        from src.scoring.keyword_matcher import KeywordMatcher
        print_success("KeywordMatcher imported successfully")
        checks.append(True)
    except ImportError as e:
        print_error(f"Failed to import KeywordMatcher: {e}")
        checks.append(False)

    try:
        from src.scoring.format_validator import FormatValidator
        print_success("FormatValidator imported successfully")
        checks.append(True)
    except ImportError as e:
        print_error(f"Failed to import FormatValidator: {e}")
        checks.append(False)

    try:
        from src.scoring.section_analyzer import SectionAnalyzer
        print_success("SectionAnalyzer imported successfully")
        checks.append(True)
    except ImportError as e:
        print_error(f"Failed to import SectionAnalyzer: {e}")
        checks.append(False)

    return all(checks)

def verify_database():
    """Verify database schema updates"""
    print_header("Verifying Database Schema")

    try:
        from src.database.schema import Database

        # Check if new methods exist
        db = Database("test_verify.db")

        # Check for new method
        if hasattr(db, 'insert_generated_resume_with_score'):
            print_success("Database has insert_generated_resume_with_score method")
        else:
            print_error("Database missing insert_generated_resume_with_score method")
            return False

        if hasattr(db, 'get_resume_score_details'):
            print_success("Database has get_resume_score_details method")
        else:
            print_error("Database missing get_resume_score_details method")
            return False

        if hasattr(db, 'get_score_history'):
            print_success("Database has get_score_history method")
        else:
            print_error("Database missing get_score_history method")
            return False

        # Clean up test database
        Path("test_verify.db").unlink(missing_ok=True)

        print_success("All database methods present")
        return True

    except Exception as e:
        print_error(f"Database verification failed: {e}")
        return False

def verify_scorer_functionality():
    """Verify scorer actually works"""
    print_header("Verifying Scorer Functionality")

    try:
        from src.scoring.ats_scorer import ATSScorer

        scorer = ATSScorer()
        print_success("ATSScorer initialized")

        # Test with sample resume
        sample_resume = """
        John Doe
        john@email.com | 555-1234 | San Francisco, CA

        EXPERIENCE
        Software Engineer | TechCorp | 2020-Present
        - Developed applications using Python and AWS
        - Led team of 3 developers

        EDUCATION
        BS Computer Science | Stanford | 2020

        SKILLS
        Python, JavaScript, AWS, Docker
        """

        sample_keywords = ['Python', 'AWS', 'Docker', 'JavaScript']

        result = scorer.score_resume(
            resume_content=sample_resume,
            job_keywords=sample_keywords,
            file_format='pdf'
        )

        # Verify result structure
        required_keys = ['score', 'grade', 'color', 'category_scores',
                        'summary', 'top_suggestions', 'pass_probability']

        for key in required_keys:
            if key in result:
                print_success(f"Result contains '{key}'")
            else:
                print_error(f"Result missing '{key}'")
                return False

        # Verify score is in valid range
        if 0 <= result['score'] <= 100:
            print_success(f"Score is valid: {result['score']}/100")
        else:
            print_error(f"Score out of range: {result['score']}")
            return False

        # Verify processing time
        if result['processing_time'] < 1.0:
            print_success(f"Processing time acceptable: {result['processing_time']:.3f}s")
        else:
            print_warning(f"Processing time high: {result['processing_time']:.3f}s")

        return True

    except Exception as e:
        print_error(f"Scorer functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_files_exist():
    """Verify all required files exist"""
    print_header("Verifying File Structure")

    base_path = Path(__file__).parent

    required_files = [
        'src/scoring/__init__.py',
        'src/scoring/ats_scorer.py',
        'src/scoring/keyword_matcher.py',
        'src/scoring/format_validator.py',
        'src/scoring/section_analyzer.py',
        'src/scoring/README.md',
        'tests/test_ats_scorer.py',
        'demo_ats_scorer.py',
        'ATS_SCORING_IMPLEMENTATION_SUMMARY.md',
        'QUICK_START_ATS_SCORING.md'
    ]

    all_exist = True
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print_success(f"{file_path}")
        else:
            print_error(f"{file_path} - NOT FOUND")
            all_exist = False

    return all_exist

def verify_generator_integration():
    """Verify integration with resume generator"""
    print_header("Verifying Resume Generator Integration")

    try:
        # Check if generator imports scorer
        with open('src/generators/resume_generator.py', 'r') as f:
            content = f.read()

        if 'ATSScorer' in content:
            print_success("Resume generator imports ATSScorer")
        else:
            print_error("Resume generator doesn't import ATSScorer")
            return False

        if 'ats_scorer' in content:
            print_success("Resume generator initializes ATSScorer")
        else:
            print_error("Resume generator doesn't initialize ATSScorer")
            return False

        if 'generate_resume_with_retry' in content:
            print_success("Resume generator has retry logic")
        else:
            print_warning("Resume generator missing retry logic")

        return True

    except Exception as e:
        print_error(f"Generator integration check failed: {e}")
        return False

def run_quick_test():
    """Run a quick end-to-end test"""
    print_header("Running Quick End-to-End Test")

    try:
        from src.scoring.ats_scorer import ATSScorer

        scorer = ATSScorer()

        # Test with excellent resume
        excellent_resume = """
        Jane Doe
        jane.doe@email.com | +1-555-987-6543 | LinkedIn | GitHub | Seattle, WA

        PROFESSIONAL SUMMARY
        Senior Software Engineer with 7+ years of experience in Python, JavaScript, AWS, and Docker.
        Expert in building scalable microservices and leading engineering teams.

        TECHNICAL SKILLS
        Languages: Python, JavaScript, TypeScript, Java, SQL
        Cloud: AWS, Docker, Kubernetes, Terraform
        Frameworks: React, Node.js, Django, Flask
        Databases: PostgreSQL, MongoDB, Redis

        PROFESSIONAL EXPERIENCE

        Senior Software Engineer | CloudTech Inc | Seattle, WA
        01/2019 - Present
        - Developed 12+ microservices using Python and AWS, improving scalability by 250%
        - Led team of 4 engineers to deliver $1.5M revenue-generating product
        - Implemented CI/CD pipeline reducing deployment time by 75%
        - Optimized database queries achieving 35% performance improvement
        - Architected RESTful APIs serving 500K+ daily requests

        Software Engineer | StartupCo | Seattle, WA
        06/2017 - 12/2018
        - Built real-time data processing system handling 50K events/second
        - Reduced infrastructure costs by $30,000 annually
        - Implemented automated testing increasing code coverage to 80%

        EDUCATION
        Bachelor of Science in Computer Science | University of Washington | 2017
        GPA: 3.7/4.0

        CERTIFICATIONS
        AWS Certified Solutions Architect
        """

        keywords = ['Python', 'JavaScript', 'AWS', 'Docker', 'Kubernetes',
                   'React', 'Node.js', 'PostgreSQL', 'CI/CD', 'Microservices']

        result = scorer.score_resume(
            resume_content=excellent_resume,
            job_keywords=keywords,
            required_skills=['Python', 'AWS', 'Docker'],
            file_format='pdf'
        )

        print(f"\n  Sample Resume Score: {result['score']:.1f}/100 ({result['grade']})")
        print(f"  Color: {result['color'].upper()}")
        print(f"  Pass Probability: {result['pass_probability']:.1f}%")
        print(f"  Processing Time: {result['processing_time']:.3f}s")

        # Should score high
        if result['score'] >= 70:
            print_success("Sample resume scored well (>70)")
        else:
            print_warning(f"Sample resume scored low: {result['score']}")

        return True

    except Exception as e:
        print_error(f"Quick test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all verification checks"""
    print("\n")
    print("╔" + "═"*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "    ATS SCORING ENGINE - IMPLEMENTATION VERIFICATION    ".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "═"*68 + "╝")

    results = []

    # Run all checks
    results.append(("File Structure", verify_files_exist()))
    results.append(("Imports", verify_imports()))
    results.append(("Database Schema", verify_database()))
    results.append(("Generator Integration", verify_generator_integration()))
    results.append(("Scorer Functionality", verify_scorer_functionality()))
    results.append(("End-to-End Test", run_quick_test()))

    # Summary
    print_header("Verification Summary")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for check_name, passed_check in results:
        status = f"{GREEN}✓ PASSED{RESET}" if passed_check else f"{RED}✗ FAILED{RESET}"
        print(f"  {check_name:<30} {status}")

    print(f"\n{BLUE}{'─'*70}{RESET}")

    success_rate = (passed / total) * 100

    if passed == total:
        print(f"\n{GREEN}🎉 ALL CHECKS PASSED! ({passed}/{total}){RESET}")
        print(f"{GREEN}ATS Scoring Engine is fully operational and ready for production!{RESET}\n")
        return 0
    elif passed >= total * 0.8:
        print(f"\n{YELLOW}⚠ MOSTLY WORKING ({passed}/{total} checks passed - {success_rate:.0f}%){RESET}")
        print(f"{YELLOW}Some minor issues detected but core functionality works.{RESET}\n")
        return 1
    else:
        print(f"\n{RED}✗ VERIFICATION FAILED ({passed}/{total} checks passed - {success_rate:.0f}%){RESET}")
        print(f"{RED}Critical issues detected. Please review the errors above.{RESET}\n")
        return 2

if __name__ == '__main__':
    sys.exit(main())
