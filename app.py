"""
Ultra ATS Resume Generator - Streamlit Application
"""
import streamlit as st
import os
from pathlib import Path
from datetime import datetime
import json

# Import custom modules
from src.database import Database
from src.parsers import ProfileParser
from src.analyzers import JobAnalyzer
from src.utils import PerplexityClient
from src.generators import ResumeGenerator
from src.generators.pdf_generator import PDFGenerator

# Page configuration
st.set_page_config(
    page_title="Ultra ATS Resume Generator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'generated_resume' not in st.session_state:
    st.session_state.generated_resume = None
if 'job_analysis' not in st.session_state:
    st.session_state.job_analysis = None
if 'company_research' not in st.session_state:
    st.session_state.company_research = None

def initialize_components():
    """Initialize all components"""
    db = Database()
    profile_parser = ProfileParser()
    job_analyzer = JobAnalyzer()
    perplexity_client = PerplexityClient()
    resume_generator = ResumeGenerator()
    pdf_generator = PDFGenerator()

    return db, profile_parser, job_analyzer, perplexity_client, resume_generator, pdf_generator

def main():
    # Header
    st.markdown('<div class="main-header">📄 Ultra ATS Resume Generator</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Generate ATS-optimized resumes with 90+ scores using AI</div>', unsafe_allow_html=True)

    # Initialize components
    db, profile_parser, job_analyzer, perplexity_client, resume_generator, pdf_generator = initialize_components()

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        # Check for Profile.pdf
        if Path("Profile.pdf").exists():
            st.success("✓ Profile.pdf found")
        else:
            st.error("✗ Profile.pdf not found")
            st.info("Please add your Profile.pdf to the project directory")

        # Check API keys
        if os.getenv("ANTHROPIC_API_KEY"):
            st.success("✓ Anthropic API key configured")
        else:
            st.error("✗ Anthropic API key missing")

        if os.getenv("PERPLEXITY_API_KEY"):
            st.success("✓ Perplexity API key configured (optional)")
        else:
            st.info("ℹ Perplexity API key not set (optional)")

        st.divider()

        # Previous resumes
        st.header("📚 Previous Resumes")
        previous_resumes = db.get_all_resumes()

        if previous_resumes:
            st.write(f"Total resumes generated: {len(previous_resumes)}")
            for resume in previous_resumes[:5]:
                with st.expander(f"{resume['company_name']} - {resume['job_title'][:30]}..."):
                    st.write(f"**Created:** {resume['created_at']}")
                    st.write(f"**ATS Score:** {resume['ats_score'] or 'N/A'}")
                    if resume['file_path'] and Path(resume['file_path']).exists():
                        with open(resume['file_path'], 'rb') as f:
                            st.download_button(
                                "Download",
                                f.read(),
                                file_name=Path(resume['file_path']).name,
                                mime="application/pdf"
                            )
        else:
            st.info("No resumes generated yet")

    # Main content
    tab1, tab2, tab3 = st.tabs(["🎯 Generate Resume", "📊 Job Analysis", "ℹ️ About"])

    with tab1:
        st.header("Generate ATS-Optimized Resume")

        # Input fields
        col1, col2 = st.columns([2, 1])

        with col1:
            company_name = st.text_input(
                "Company Name *",
                placeholder="e.g., Google, Microsoft, Amazon",
                help="Enter the company name for the job"
            )

        with col2:
            job_url = st.text_input(
                "Job URL (optional)",
                placeholder="https://...",
                help="Optional: URL to the job posting"
            )

        job_description = st.text_area(
            "Job Description *",
            height=300,
            placeholder="Paste the complete job description here...",
            help="Paste the full job description including requirements, responsibilities, and qualifications"
        )

        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            use_perplexity = st.checkbox(
                "Use Perplexity for company research",
                value=bool(os.getenv("PERPLEXITY_API_KEY")),
                disabled=not os.getenv("PERPLEXITY_API_KEY"),
                help="Enhance resume with company-specific insights"
            )

        with col2:
            target_score = st.slider(
                "Target ATS Score",
                min_value=85,
                max_value=100,
                value=90,
                help="Target ATS compatibility score"
            )

        # Generate button
        if st.button("🚀 Generate ATS-Optimized Resume", type="primary", use_container_width=True):
            if not company_name or not job_description:
                st.error("Please provide both company name and job description")
            elif not Path("Profile.pdf").exists():
                st.error("Profile.pdf not found. Please add it to the project directory.")
            else:
                # Show progress
                with st.spinner("Generating your ATS-optimized resume..."):
                    try:
                        # Step 1: Parse profile
                        progress_bar = st.progress(0)
                        st.info("📄 Parsing your profile...")
                        profile_text = profile_parser.get_profile_summary()
                        progress_bar.progress(20)

                        # Step 2: Analyze job description
                        st.info("🔍 Analyzing job description...")
                        job_analysis = job_analyzer.analyze_job_description(
                            job_description,
                            company_name
                        )
                        st.session_state.job_analysis = job_analysis
                        progress_bar.progress(40)

                        # Step 3: Company research (if enabled)
                        company_research = None
                        if use_perplexity:
                            st.info("🔬 Researching company...")
                            company_research = perplexity_client.research_company(
                                company_name,
                                job_analysis.get('job_title')
                            )
                            st.session_state.company_research = company_research
                        progress_bar.progress(60)

                        # Step 4: Check for duplicates
                        st.info("🔎 Checking for existing resumes...")
                        job_id = db.insert_job_description(
                            company_name,
                            job_description,
                            job_analysis.get('job_title'),
                            job_url,
                            json.dumps(job_analysis.get('keywords', []))
                        )

                        existing_resume = db.check_resume_exists(job_id)
                        if existing_resume:
                            st.warning(f"⚠️ Resume already exists for this job (created {existing_resume['created_at']})")
                            use_existing = st.checkbox("Use existing resume", value=False)
                            if not use_existing:
                                st.info("Generating new resume...")
                            else:
                                st.success("Using existing resume")
                                progress_bar.progress(100)
                                st.balloons()
                                return

                        progress_bar.progress(70)

                        # Step 5: Generate resume
                        st.info("✨ Generating ATS-optimized resume with Claude...")
                        resume_result = resume_generator.generate_resume(
                            profile_text,
                            job_analysis,
                            company_research
                        )

                        if not resume_result['success']:
                            st.error(f"Resume generation failed: {resume_result.get('error', 'Unknown error')}")
                            return

                        progress_bar.progress(90)

                        # Step 6: Generate PDF
                        st.info("📝 Creating PDF...")
                        output_dir = Path("generated_resumes")
                        output_dir.mkdir(exist_ok=True)

                        # Create filename: Venkat_CompanyName.pdf
                        safe_company_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).strip()
                        pdf_filename = f"Venkat_{safe_company_name}.pdf"
                        pdf_path = output_dir / pdf_filename

                        pdf_generator.markdown_to_pdf(resume_result['content'], str(pdf_path))
                        progress_bar.progress(95)

                        # Step 7: Save to database
                        db.insert_generated_resume(
                            job_id,
                            resume_result['content'],
                            str(pdf_path),
                            target_score
                        )

                        progress_bar.progress(100)

                        # Success!
                        st.success("✅ ATS-Optimized Resume Generated Successfully!")
                        st.balloons()

                        # Store in session
                        st.session_state.generated_resume = {
                            'content': resume_result['content'],
                            'pdf_path': str(pdf_path),
                            'company_name': company_name
                        }

                    except Exception as e:
                        st.error(f"Error generating resume: {e}")
                        import traceback
                        st.code(traceback.format_exc())

        # Display generated resume
        if st.session_state.generated_resume:
            st.divider()
            st.subheader("📄 Generated Resume")

            col1, col2 = st.columns([3, 1])

            with col1:
                with st.expander("📝 Resume Content (Markdown)", expanded=True):
                    st.markdown(st.session_state.generated_resume['content'])

            with col2:
                st.metric("Target ATS Score", f"{target_score}+")

                # Download button
                pdf_path = st.session_state.generated_resume['pdf_path']
                if Path(pdf_path).exists():
                    with open(pdf_path, 'rb') as f:
                        st.download_button(
                            "⬇️ Download PDF",
                            f.read(),
                            file_name=Path(pdf_path).name,
                            mime="application/pdf",
                            use_container_width=True
                        )

                # Copy to clipboard
                if st.button("📋 Copy Markdown", use_container_width=True):
                    st.code(st.session_state.generated_resume['content'])

    with tab2:
        st.header("📊 Job Analysis")

        if st.session_state.job_analysis:
            analysis = st.session_state.job_analysis

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Job Details")
                st.write(f"**Company:** {analysis.get('company_name', 'N/A')}")
                st.write(f"**Title:** {analysis.get('job_title', 'N/A')}")
                st.write(f"**Industry:** {analysis.get('industry', 'N/A')}")
                st.write(f"**Experience:** {analysis.get('years_of_experience', 'N/A')}")

            with col2:
                st.subheader("Education & Skills")
                st.write(f"**Education:** {analysis.get('education_requirements', 'N/A')}")

            # Keywords
            st.subheader("🔑 Key Keywords")
            keywords = analysis.get('keywords', [])
            if keywords:
                # Display as tags
                keyword_html = " ".join([f'<span style="background-color: #e1f5ff; padding: 5px 10px; margin: 3px; border-radius: 5px; display: inline-block;">{kw}</span>' for kw in keywords[:20]])
                st.markdown(keyword_html, unsafe_allow_html=True)
            else:
                st.info("No keywords extracted")

            # Skills
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Required Skills")
                required_skills = analysis.get('required_skills', [])
                if required_skills:
                    for skill in required_skills:
                        st.write(f"• {skill}")
                else:
                    st.info("No required skills listed")

            with col2:
                st.subheader("Preferred Skills")
                preferred_skills = analysis.get('preferred_skills', [])
                if preferred_skills:
                    for skill in preferred_skills:
                        st.write(f"• {skill}")
                else:
                    st.info("No preferred skills listed")

            # Responsibilities
            st.subheader("Key Responsibilities")
            responsibilities = analysis.get('key_responsibilities', [])
            if responsibilities:
                for resp in responsibilities:
                    st.write(f"• {resp}")
            else:
                st.info("No responsibilities listed")

        else:
            st.info("Generate a resume to see job analysis")

    with tab3:
        st.header("About Ultra ATS Resume Generator")

        st.markdown("""
        ### 🎯 What is this?

        The **Ultra ATS Resume Generator** is an AI-powered tool that creates highly optimized resumes designed to score 90+ in Applicant Tracking Systems (ATS).

        ### ✨ Key Features

        - **ATS Optimization**: Trained on comprehensive ATS knowledge from industry sources
        - **AI-Powered**: Uses Claude (Anthropic) for intelligent resume generation
        - **Company Research**: Optional Perplexity integration for company-specific insights
        - **Duplicate Detection**: Prevents regenerating resumes for the same job
        - **Database Storage**: Keeps history of all generated resumes
        - **PDF Export**: Creates ATS-friendly PDF format

        ### 🔧 How it Works

        1. **Parse Profile**: Extracts your information from Profile.pdf
        2. **Analyze Job**: Uses Claude to extract keywords, skills, and requirements
        3. **Research Company**: (Optional) Gathers company insights via Perplexity
        4. **Generate Resume**: Creates tailored, ATS-optimized resume with Claude
        5. **Export PDF**: Generates clean, ATS-friendly PDF format

        ### 📋 ATS Optimization Includes

        - ✅ Keyword optimization from job description
        - ✅ ATS-friendly formatting (no tables, columns, or graphics)
        - ✅ Standard section headers
        - ✅ Achievement-focused bullet points
        - ✅ Quantifiable metrics
        - ✅ Industry-specific terminology
        - ✅ Skills matching

        ### 🔑 API Keys Required

        - **Anthropic API** (Required): For resume generation and analysis
        - **Perplexity API** (Optional): For company research

        ### 📚 Knowledge Base

        Built on insights from 7 authoritative ATS sources including Jobscan, industry reports, and best practices guides.

        ---

        **Version**: 1.0.0 | **Author**: AI-Powered Resume Solutions
        """)

if __name__ == "__main__":
    main()
