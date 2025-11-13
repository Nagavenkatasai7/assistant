"""
Demo Script for ATS Scoring Engine
Demonstrates comprehensive scoring capabilities with example resumes
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from scoring.ats_scorer import ATSScorer


def print_score_report(result):
    """Print a formatted score report"""
    print("\n" + "="*70)
    print("ATS SCORE REPORT")
    print("="*70)

    # Overall score
    print(f"\n📊 OVERALL SCORE: {result['score']:.1f}/100 ({result['grade']})")

    # Color indicator
    color_emoji = {
        'green': '🟢',
        'yellow': '🟡',
        'red': '🔴'
    }
    print(f"   Status: {color_emoji.get(result['color'], '⚪')} {result['color'].upper()}")
    print(f"   Pass Probability: {result['pass_probability']:.1f}%")
    print(f"   Processing Time: {result['processing_time']:.3f}s")

    # Category breakdown
    print(f"\n📋 CATEGORY BREAKDOWN:")
    print("-" * 70)

    categories = result['category_scores']
    for cat_name, cat_data in categories.items():
        score = cat_data['score']
        max_score = cat_data['max']
        percentage = (score / max_score * 100) if max_score > 0 else 0

        bar_length = int(percentage / 2)  # 50 chars max
        bar = '█' * bar_length + '░' * (50 - bar_length)

        print(f"\n{cat_name.upper():15} {score:5.1f}/{max_score:5.1f} [{bar}] {percentage:5.1f}%")

    # Summary
    print(f"\n💬 SUMMARY:")
    print(f"   {result['summary']}")

    # Top suggestions
    if result['top_suggestions']:
        print(f"\n💡 TOP IMPROVEMENT SUGGESTIONS:")
        for i, suggestion in enumerate(result['top_suggestions'], 1):
            print(f"   {i}. {suggestion}")

    print("\n" + "="*70 + "\n")


def demo_excellent_resume():
    """Demo with an excellent, well-optimized resume"""
    print("\n" + "🌟" * 35)
    print("DEMO 1: EXCELLENT ATS-OPTIMIZED RESUME")
    print("🌟" * 35)

    resume = """
    John Doe
    john.doe@email.com | +1-555-123-4567 | LinkedIn | GitHub | San Francisco, CA

    PROFESSIONAL SUMMARY
    Senior Software Engineer with 8+ years of experience in Python, JavaScript, and AWS.
    Expert in building scalable web applications, RESTful APIs, and microservices architecture.
    Proven track record of leading teams and delivering high-impact projects.

    TECHNICAL SKILLS
    Languages: Python, JavaScript, TypeScript, Java, SQL, Go
    Frameworks: React, Node.js, Django, Flask, Spring Boot, Express
    Cloud & DevOps: AWS, Docker, Kubernetes, Terraform, Jenkins, CircleCI
    Databases: PostgreSQL, MongoDB, Redis, MySQL, DynamoDB
    Tools: Git, JIRA, Confluence, Datadog, New Relic

    PROFESSIONAL EXPERIENCE

    Senior Software Engineer | TechCorp Inc | San Francisco, CA
    01/2020 - Present
    - Developed and deployed 15+ microservices using Python and AWS, improving system scalability by 300%
    - Led team of 5 engineers to deliver $2M revenue-generating product ahead of schedule
    - Implemented CI/CD pipeline reducing deployment time from 2 hours to 15 minutes (87% improvement)
    - Optimized database queries achieving 40% performance improvement and reducing costs by $30K annually
    - Architected RESTful APIs serving 1M+ daily requests with 99.9% uptime
    - Mentored 3 junior developers, accelerating their productivity by 50%

    Software Engineer | StartupCo | San Francisco, CA
    06/2017 - 12/2019
    - Built real-time data processing system handling 100K events/second using Kafka and Python
    - Reduced infrastructure costs by $50,000 annually through optimization and rightsizing
    - Collaborated with cross-functional teams to deliver 20+ features in agile sprints
    - Implemented automated testing suite increasing code coverage from 40% to 85%
    - Designed and implemented authentication system supporting 10K+ concurrent users

    EDUCATION
    Bachelor of Science in Computer Science | Stanford University | 2017
    GPA: 3.8/4.0 | Dean's List

    CERTIFICATIONS
    AWS Certified Solutions Architect - Professional
    Certified Kubernetes Administrator (CKA)
    """

    job_keywords = [
        'Python', 'JavaScript', 'AWS', 'Docker', 'Kubernetes', 'React', 'Node.js',
        'PostgreSQL', 'CI/CD', 'RESTful APIs', 'Microservices', 'Agile', 'Leadership'
    ]

    scorer = ATSScorer()
    result = scorer.score_resume(
        resume_content=resume,
        job_keywords=job_keywords,
        required_skills=['Python', 'JavaScript', 'AWS', 'Docker'],
        file_format='pdf'
    )

    print_score_report(result)


def demo_poor_resume():
    """Demo with a poorly formatted resume"""
    print("\n" + "⚠️ " * 35)
    print("DEMO 2: POORLY FORMATTED RESUME")
    print("⚠️ " * 35)

    resume = """
    Bob Smith
    Software Developer

    I am a software developer looking for opportunities.

    Work History:
    - Worked at Company A
    - Did programming
    - Made websites

    Education: College
    """

    job_keywords = [
        'Python', 'JavaScript', 'AWS', 'Docker', 'Kubernetes', 'React'
    ]

    scorer = ATSScorer()
    result = scorer.score_resume(
        resume_content=resume,
        job_keywords=job_keywords,
        required_skills=['Python', 'AWS'],
        file_format='pdf'
    )

    print_score_report(result)


def demo_good_resume():
    """Demo with a good resume that needs minor improvements"""
    print("\n" + "👍 " * 35)
    print("DEMO 3: GOOD RESUME WITH ROOM FOR IMPROVEMENT")
    print("👍 " * 35)

    resume = """
    Alice Johnson
    alice.johnson@email.com | 555-987-6543 | Seattle, WA | LinkedIn

    PROFESSIONAL SUMMARY
    Software Engineer with 5 years of experience in web development and cloud technologies.
    Skilled in Python, JavaScript, and AWS.

    TECHNICAL SKILLS
    Languages: Python, JavaScript, SQL
    Technologies: React, Node.js, AWS, Docker
    Databases: PostgreSQL, MongoDB

    EXPERIENCE

    Software Engineer | CloudTech Solutions | Seattle, WA
    03/2019 - Present
    - Developed web applications using React and Node.js
    - Worked with AWS services for deployment
    - Collaborated with team on various projects
    - Participated in code reviews and agile ceremonies

    Junior Developer | WebStart Inc | Seattle, WA
    06/2018 - 02/2019
    - Built features for company website
    - Fixed bugs and improved performance
    - Learned new technologies

    EDUCATION
    Bachelor of Science in Computer Science | University of Washington | 2018
    """

    job_keywords = [
        'Python', 'JavaScript', 'AWS', 'Docker', 'React', 'Node.js',
        'PostgreSQL', 'Microservices', 'CI/CD', 'Kubernetes', 'API'
    ]

    scorer = ATSScorer()
    result = scorer.score_resume(
        resume_content=resume,
        job_keywords=job_keywords,
        required_skills=['Python', 'JavaScript', 'AWS', 'Docker', 'React'],
        file_format='pdf'
    )

    print_score_report(result)


def demo_quick_check():
    """Demo quick check functionality"""
    print("\n" + "⚡ " * 35)
    print("DEMO 4: QUICK CHECK (Fast Validation)")
    print("⚡ " * 35)

    resume = """
    jane.doe@email.com | 555-1234 | New York, NY

    EXPERIENCE
    Senior Engineer at Tech Company

    EDUCATION
    MS Computer Science, MIT

    SKILLS
    Python, Java, AWS, Docker, Kubernetes
    """

    scorer = ATSScorer()
    result = scorer.quick_check(resume)

    print("\n" + "="*70)
    print("QUICK CHECK RESULTS")
    print("="*70)
    print(f"\n📊 Score: {result['score']}/100")
    print(f"   Color: {result['color'].upper()}")
    print(f"   Passed: {'✓' if result['passed'] else '✗'}")
    print(f"   Processing Time: {result['processing_time']:.3f}s")
    print("\n" + "="*70 + "\n")


def demo_comparison():
    """Compare multiple resumes"""
    print("\n" + "📊 " * 35)
    print("DEMO 5: RESUME COMPARISON")
    print("📊 " * 35)

    resumes = {
        'Excellent': """
            John Doe | john@email.com | 555-1234 | LinkedIn | San Francisco, CA

            PROFESSIONAL SUMMARY
            Senior Engineer with 8+ years in Python, AWS, and Kubernetes. Led teams delivering $2M+ products.

            TECHNICAL SKILLS
            Python, JavaScript, AWS, Docker, Kubernetes, React, PostgreSQL, CI/CD, Terraform

            EXPERIENCE
            Senior Engineer | TechCorp | 01/2020 - Present
            - Developed 15+ microservices improving scalability by 300%
            - Led team of 5 engineers
            - Reduced deployment time by 87%

            EDUCATION
            BS Computer Science | Stanford | 2017
        """,
        'Good': """
            Jane Smith | jane@email.com | 555-5678 | Boston, MA

            SUMMARY
            Software Engineer with 4 years experience in web development.

            SKILLS
            Python, JavaScript, React, AWS, Docker

            EXPERIENCE
            Engineer | WebCo | 2019 - Present
            - Built web applications
            - Worked with cloud services

            EDUCATION
            BS Computer Science | MIT | 2019
        """,
        'Poor': """
            Bob Jones
            Developer

            Experience: Worked at companies
            Education: Graduated college
        """
    }

    job_keywords = ['Python', 'AWS', 'Docker', 'Kubernetes', 'React', 'PostgreSQL']
    scorer = ATSScorer()

    results = {}
    for name, resume in resumes.items():
        result = scorer.score_resume(resume, job_keywords, file_format='pdf')
        results[name] = result

    print("\n" + "="*70)
    print("COMPARISON RESULTS")
    print("="*70)
    print(f"\n{'Resume':<15} {'Score':<10} {'Grade':<8} {'Color':<10} {'Pass %':<10}")
    print("-" * 70)

    for name, result in results.items():
        print(f"{name:<15} {result['score']:>7.1f}  {result['grade']:<8} {result['color']:<10} {result['pass_probability']:>6.1f}%")

    print("\n" + "="*70 + "\n")


def main():
    """Run all demos"""
    print("\n")
    print("╔" + "═"*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "         ATS SCORING ENGINE - COMPREHENSIVE DEMO         ".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "═"*68 + "╝")

    try:
        # Run demos
        demo_excellent_resume()
        input("Press Enter to continue to next demo...")

        demo_poor_resume()
        input("Press Enter to continue to next demo...")

        demo_good_resume()
        input("Press Enter to continue to next demo...")

        demo_quick_check()
        input("Press Enter to continue to final demo...")

        demo_comparison()

        print("\n" + "✓ " * 35)
        print("ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("✓ " * 35 + "\n")

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nError running demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
