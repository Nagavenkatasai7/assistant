#!/usr/bin/env python3
"""
Test script to verify LaTeX PDF generation with AI-parsed data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.parsers.ai_resume_parser import AIResumeParser
from src.generators.latex_resume_pipeline import LaTeXResumePipeline
from pathlib import Path


def test_ai_parser():
    """Test the AI resume parser with sample markdown"""

    sample_markdown = """
# John Doe
San Francisco, CA | john.doe@email.com | linkedin.com/in/johndoe | github.com/johndoe

## Professional Summary
Experienced AI/ML Engineer with 8+ years building production machine learning systems and LLM applications. Expert in developing RAG systems, fine-tuning models, and implementing scalable AI solutions. Strong product mindset with proven ability to translate business requirements into technical solutions.

## Technical Skills
**AI/ML & LLMs:** PyTorch, TensorFlow, Hugging Face Transformers, LangChain, Vector Databases (Pinecone, Weaviate), RAG Systems, Prompt Engineering, Fine-tuning, RLHF
**Product Development:** Agile/Scrum, Product Strategy, User Research, A/B Testing, Analytics, Cross-functional Leadership
**Programming & Tools:** Python, JavaScript, TypeScript, SQL, Docker, Kubernetes, AWS, GCP, Git, CI/CD, REST APIs

## Education
**Stanford University** | MS in Computer Science | 2018 – 2020
GPA: 3.9/4.0

**UC Berkeley** | BS in Computer Science | 2014 – 2018
GPA: 3.8/4.0

## Technical Projects

### **AI-Powered Customer Support System** (2024 – Present)
Technologies: Python, LangChain, GPT-4, Pinecone, FastAPI, React
- Developed RAG-based customer support system reducing response time by 75%
- Implemented semantic search across 100k+ documents with 95% accuracy
- Built custom prompt chains for complex multi-step customer queries
- Integrated with existing CRM systems serving 10,000+ daily users

### **Machine Learning Platform for E-commerce** (2023 – 2024)
Technologies: Python, TensorFlow, Kubernetes, Apache Spark, PostgreSQL
- Built recommendation engine increasing conversion rates by 35%
- Developed real-time fraud detection system processing 1M+ transactions/day
- Implemented A/B testing framework for ML model deployment
- Led team of 5 engineers in microservices architecture migration

### **Open Source LLM Fine-tuning Framework** (2023)
Technologies: PyTorch, Hugging Face, PEFT, LoRA, Distributed Training
GitHub: github.com/johndoe/llm-framework
- Created framework for efficient LLM fine-tuning with 80% less memory
- Implemented LoRA and QLoRA techniques for parameter-efficient training
- Achieved state-of-the-art results on multiple benchmark datasets
- 500+ GitHub stars and adopted by 20+ companies

## Additional Contributions
**Certifications:** AWS Certified Machine Learning Specialist, Google Cloud Professional ML Engineer
**Languages:** English (Native), Spanish (Professional)
"""

    parser = AIResumeParser()
    structured_data = parser.parse_markdown_resume(sample_markdown)

    print("=" * 60)
    print("AI RESUME PARSER TEST")
    print("=" * 60)

    print("\n1. HEADER DATA:")
    for key, value in structured_data['header'].items():
        print(f"   {key}: {value}")

    print("\n2. SUMMARY:")
    print(f"   {structured_data['summary'][:100]}...")

    print("\n3. SKILLS:")
    for category, skills in structured_data['skills'].items():
        print(f"   {category}: {', '.join(skills[:3])}...")

    print("\n4. EDUCATION:")
    for edu in structured_data['education']:
        print(f"   - {edu.get('institution')} | {edu.get('degree')} | {edu.get('dates')}")

    print("\n5. PROJECTS:")
    for i, proj in enumerate(structured_data['projects'][:3], 1):
        print(f"   Project {i}: {proj['title']}")
        print(f"   Dates: {proj['dates']}")
        print(f"   Tech: {proj.get('technologies', 'N/A')}")
        print(f"   Bullets: {len(proj.get('bullets', []))} items")
        print()

    return structured_data


def test_latex_generation(structured_data):
    """Test LaTeX PDF generation with structured data"""

    print("=" * 60)
    print("LATEX GENERATION TEST")
    print("=" * 60)

    pipeline = LaTeXResumePipeline()

    # Test with the structured data
    output_path = "test_output/test_resume_fixed"

    print(f"\nGenerating LaTeX resume...")
    tex_path, pdf_path, error = pipeline.generate_resume(
        resume_data=structured_data,
        output_path=output_path,
        compile_pdf=False  # Don't compile PDF in test
    )

    if error:
        print(f"❌ Error: {error}")
        return False

    print(f"✅ LaTeX generated: {tex_path}")

    # Check if the tex file was created
    if Path(tex_path).exists():
        # Read first few lines to verify
        with open(tex_path, 'r') as f:
            lines = f.readlines()[:20]

        print("\nFirst 20 lines of generated LaTeX:")
        print("-" * 40)
        for line in lines:
            print(line.rstrip())

        # Check for key content
        tex_content = Path(tex_path).read_text()
        checks = {
            'Name in header': 'John Doe' in tex_content,
            'Email in header': 'john.doe@email.com' in tex_content,
            'AI/ML skills': 'AI/ML' in tex_content or 'PyTorch' in tex_content,
            'Projects section': 'AI-Powered Customer Support System' in tex_content,
            'Education section': 'Stanford University' in tex_content
        }

        print("\n" + "-" * 40)
        print("Content Verification:")
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"  {status} {check}")

        all_passed = all(checks.values())
        if all_passed:
            print("\n🎉 All checks passed! LaTeX generation is working correctly.")
        else:
            print("\n⚠️ Some checks failed. Review the LaTeX output.")

        return all_passed
    else:
        print(f"❌ LaTeX file not created at {tex_path}")
        return False


def main():
    """Main test function"""
    print("\n" + "=" * 60)
    print("TESTING LATEX RESUME GENERATION FIX")
    print("=" * 60)

    # Ensure output directory exists
    Path("test_output").mkdir(exist_ok=True)

    # Test 1: AI Parser
    structured_data = test_ai_parser()

    # Test 2: LaTeX Generation
    success = test_latex_generation(structured_data)

    print("\n" + "=" * 60)
    if success:
        print("✅ FIX VERIFIED: LaTeX resume generation is working!")
        print("\nThe system now:")
        print("1. ✅ Parses AI-generated markdown resumes")
        print("2. ✅ Extracts structured data (skills, projects, etc.)")
        print("3. ✅ Maps data to correct LaTeX template fields")
        print("4. ✅ Generates complete LaTeX documents")
    else:
        print("❌ FIX INCOMPLETE: Review the errors above")
    print("=" * 60)


if __name__ == "__main__":
    main()