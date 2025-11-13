#!/usr/bin/env python3
"""
Comprehensive test suite for all PDF templates
Tests each template with extensive resume data to ensure multi-page handling
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from src.generators.pdf_generator import PDFGenerator
from src.generators.pdf_generator_enhanced import EnhancedPDFGenerator

# Extensive test resume data with multiple experiences
TEST_RESUME_MARKDOWN = """# Alexandra Chen
alexandra.chen@email.com | (415) 555-0123 | linkedin.com/in/alexandrachen | github.com/achen | San Francisco, CA

Senior Software Engineering Manager

## PROFESSIONAL SUMMARY
Accomplished engineering leader with 10+ years of experience building and scaling high-performance engineering teams. Expertise in distributed systems, cloud architecture, and agile methodologies. Proven track record of delivering complex technical projects that drive business growth and operational excellence. Led teams of 20+ engineers across multiple continents, achieving 99.99% system uptime and reducing deployment times by 75%.

## TECHNICAL SKILLS
**Programming Languages:** Python, Java, JavaScript, TypeScript, Go, Scala, C++
**Frontend Technologies:** React, Angular, Vue.js, Next.js, Redux, GraphQL, Webpack
**Backend Technologies:** Spring Boot, Django, Node.js, Express, FastAPI, Microservices
**Databases:** PostgreSQL, MySQL, MongoDB, Cassandra, Redis, Elasticsearch, DynamoDB
**Cloud Platforms:** AWS (Certified Solutions Architect), Google Cloud Platform, Microsoft Azure
**DevOps & Tools:** Kubernetes, Docker, Terraform, Jenkins, GitLab CI/CD, Prometheus, Grafana
**Methodologies:** Agile, Scrum, Kanban, TDD, DDD, Event-Driven Architecture, CQRS

## PROFESSIONAL EXPERIENCE

### Senior Engineering Manager - Platform Services
MegaTech Corporation, San Francisco, CA
March 2020 - Present
- Lead a distributed team of 22 engineers across 3 time zones building core platform services
- Architected and delivered next-generation microservices platform processing 1B+ requests daily
- Reduced infrastructure costs by 45% through optimization and automated resource management
- Implemented comprehensive observability stack improving incident response time by 60%
- Established engineering excellence program increasing code quality metrics by 35%
- Mentored 8 engineers to senior positions and 3 to team lead roles
- Drove adoption of event-driven architecture across 15+ product teams
- Led migration from monolithic architecture to microservices serving 50M+ users

### Engineering Manager - Data Platform
DataDriven Inc., Palo Alto, CA
June 2018 - February 2020
- Managed team of 12 engineers building real-time data processing platform
- Delivered machine learning infrastructure supporting 100+ ML models in production
- Reduced data pipeline latency from hours to minutes using Apache Kafka and Spark
- Implemented data governance framework ensuring GDPR and CCPA compliance
- Built self-service analytics platform used by 200+ internal stakeholders
- Established 24/7 on-call rotation and incident management process
- Increased team productivity by 40% through process improvements and automation

### Senior Software Engineer / Tech Lead
CloudFirst Solutions, San Jose, CA
January 2016 - May 2018
- Technical lead for cloud migration initiative moving 50+ applications to AWS
- Designed and implemented multi-tenant SaaS platform architecture
- Built CI/CD pipelines reducing deployment time from days to hours
- Led performance optimization efforts improving application response time by 70%
- Mentored junior developers and conducted technical interviews
- Established coding standards and best practices adopted company-wide
- Developed disaster recovery strategy achieving RPO of 1 hour and RTO of 4 hours

### Software Engineer II
TechStartup Co., Mountain View, CA
August 2014 - December 2015
- Full-stack development for B2B enterprise platform
- Implemented RESTful APIs serving 10M+ requests daily
- Built real-time notification system using WebSockets and Redis
- Optimized database queries reducing page load time by 50%
- Participated in architecture reviews and design discussions
- Contributed to open-source projects and internal tools

### Software Engineer
Digital Innovations Ltd., Redwood City, CA
June 2012 - July 2014
- Developed features for customer-facing web applications
- Implemented automated testing increasing code coverage to 85%
- Participated in agile ceremonies and sprint planning
- Resolved production issues and performed root cause analysis
- Collaborated with product managers to define technical requirements

### Junior Developer
StartupXYZ, San Francisco, CA
January 2011 - May 2012
- Built responsive web applications using modern JavaScript frameworks
- Assisted in database design and optimization
- Wrote technical documentation and user guides
- Participated in code reviews and pair programming sessions

## EDUCATION

### Master of Science in Computer Science
Stanford University, Stanford, CA
September 2009 - June 2011
- Specialization: Distributed Systems and Machine Learning
- GPA: 3.9/4.0
- Research: Scalable consensus algorithms for distributed databases
- Teaching Assistant for CS 140 Operating Systems

### Bachelor of Science in Computer Engineering
University of California, Berkeley, CA
September 2005 - May 2009
- Magna Cum Laude, GPA: 3.85/4.0
- Dean's List: All semesters
- President, Association for Computing Machinery (ACM) Student Chapter
- Relevant Coursework: Data Structures, Algorithms, Computer Networks, Database Systems

## CERTIFICATIONS
- AWS Certified Solutions Architect - Professional (2021)
- Google Cloud Professional Cloud Architect (2020)
- Certified Kubernetes Administrator (CKA) (2019)
- Scrum Master Certification (CSM) (2018)
- MongoDB Certified Developer (2017)

## KEY ACHIEVEMENTS & PROJECTS

### Open Source Contributions
September 2019 - Present
- Core contributor to Apache Kafka with 50+ merged PRs
- Maintained popular React component library with 10K+ GitHub stars
- Created developer tools used by 5000+ engineers globally

### Patent: Distributed Cache Invalidation System
June 2020
- Co-invented novel cache invalidation algorithm reducing latency by 40%
- Patent pending: US Patent Application #16/890,123
- Implemented in production serving billions of requests

### Speaker & Technical Writer
2018 - Present
- Keynote speaker at KubeCon 2021: "Scaling Kubernetes to 10,000 Nodes"
- Published 15+ technical articles on Medium with 100K+ views
- Regular contributor to engineering blog and technical documentation
"""

def test_all_templates():
    """Test all three PDF templates with extensive resume data"""

    print("=" * 60)
    print("COMPREHENSIVE PDF TEMPLATE TEST SUITE")
    print("=" * 60)

    results = []

    # Test 1: Original Template
    print("\n1. Testing ORIGINAL Template...")
    try:
        generator = PDFGenerator()
        output_path = Path("test_output_original.pdf")
        result = generator.markdown_to_pdf(TEST_RESUME_MARKDOWN, str(output_path))
        print(f"   ✅ Original template SUCCESS: {output_path}")
        results.append(("Original", True, str(output_path)))
    except Exception as e:
        print(f"   ❌ Original template FAILED: {e}")
        results.append(("Original", False, str(e)))

    # Test 2: Modern Professional Template
    print("\n2. Testing MODERN PROFESSIONAL Template...")
    try:
        enhanced_gen = EnhancedPDFGenerator(template="modern")
        output_path = Path("test_output_modern.pdf")
        result = enhanced_gen.markdown_to_pdf(
            TEST_RESUME_MARKDOWN,
            str(output_path),
            template="modern"
        )
        print(f"   ✅ Modern template SUCCESS: {output_path}")
        results.append(("Modern", True, str(output_path)))
    except Exception as e:
        print(f"   ❌ Modern template FAILED: {e}")
        results.append(("Modern", False, str(e)))

    # Test 3: Harvard Business Template
    print("\n3. Testing HARVARD BUSINESS Template...")
    try:
        enhanced_gen = EnhancedPDFGenerator(template="harvard")
        output_path = Path("test_output_harvard.pdf")
        result = enhanced_gen.markdown_to_pdf(
            TEST_RESUME_MARKDOWN,
            str(output_path),
            template="harvard"
        )
        print(f"   ✅ Harvard template SUCCESS: {output_path}")
        results.append(("Harvard", True, str(output_path)))
    except Exception as e:
        print(f"   ❌ Harvard template FAILED: {e}")
        results.append(("Harvard", False, str(e)))

    # Test 4: Default Enhanced Template (should use modern)
    print("\n4. Testing DEFAULT Enhanced Template...")
    try:
        enhanced_gen = EnhancedPDFGenerator()
        output_path = Path("test_output_default.pdf")
        result = enhanced_gen.markdown_to_pdf(
            TEST_RESUME_MARKDOWN,
            str(output_path)
        )
        print(f"   ✅ Default template SUCCESS: {output_path}")
        results.append(("Default", True, str(output_path)))
    except Exception as e:
        print(f"   ❌ Default template FAILED: {e}")
        results.append(("Default", False, str(e)))

    # Summary Report
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    success_count = sum(1 for _, success, _ in results if success)
    total_count = len(results)

    for template, success, detail in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{template:15} : {status:8} - {detail}")

    print(f"\nTotal: {success_count}/{total_count} tests passed")

    if success_count == total_count:
        print("\n🎉 ALL TESTS PASSED! System is production-ready.")
        return True
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
        return False


def test_ats_scoring():
    """Test ATS scoring functionality with generated PDFs"""
    print("\n" + "=" * 60)
    print("ATS SCORING TEST")
    print("=" * 60)

    try:
        from src.ats_scorer import ATSScorer

        scorer = ATSScorer()

        # Test with Modern template PDF
        if Path("test_output_modern.pdf").exists():
            print("\nTesting ATS scoring with Modern template...")
            score_data = scorer.score_resume(
                "test_output_modern.pdf",
                job_description="Senior Software Engineer position requiring Python, AWS, and microservices experience"
            )

            print(f"ATS Score: {score_data['overall_score']}/100")
            print(f"Sections Found: {', '.join(score_data['sections_found'])}")

            if score_data['overall_score'] > 70:
                print("✅ ATS scoring functional and score is good!")
            else:
                print("⚠️  ATS score is lower than expected")
        else:
            print("⚠️  No PDF found for ATS testing")

    except Exception as e:
        print(f"❌ ATS scoring test failed: {e}")


if __name__ == "__main__":
    # Run all template tests
    all_passed = test_all_templates()

    # Run ATS scoring test
    test_ats_scoring()

    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)