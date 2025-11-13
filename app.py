"""
Ultra ATS Resume Generator - Streamlit Application
"""
# Fix SQLite3 version for Streamlit Cloud
# This must come before any imports that might use sqlite3
import sys
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules['pysqlite3']
except (ImportError, KeyError):
    # pysqlite3 not available, fall back to built-in sqlite3
    pass

import logging
import warnings

# Suppress Tornado WebSocket warnings (harmless connection close messages)
logging.getLogger('tornado.access').setLevel(logging.ERROR)
logging.getLogger('tornado.application').setLevel(logging.ERROR)
logging.getLogger('tornado.general').setLevel(logging.ERROR)
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', module='tornado')

import streamlit as st
import os
from pathlib import Path
from datetime import datetime
import json

# Import custom modules
# from src.database import Database  # Replaced with optimized database
from src.parsers import ProfileParser
from src.analyzers import JobAnalyzer
from src.clients.tavily_client import TavilyClient
from src.generators import ResumeGenerator
from src.generators.pdf_generator import PDFGenerator
from src.generators.pdf_generator_enhanced import EnhancedPDFGenerator  # New enhanced generator
from src.generators.coverletter_generator import CoverLetterGenerator
from src.generators.coverletter_pdf_generator import CoverLetterPDFGenerator
from src.generators.docx_generator import DOCXGenerator

# Security modules
from src.security.input_validator import InputValidator
from src.security.rate_limiter import RateLimiter
from src.security.prompt_sanitizer import PromptSanitizer
from src.security.secrets_manager import SecretsManager
from src.security.security_logger import SecurityLogger

# ATS Scoring
from src.scoring.ats_scorer import ATSScorer
from src.scoring.ats_scorer_enhanced import EnhancedATSScorer  # New enhanced scorer

# Optimized Database
from src.database.schema_optimized import Database as OptimizedDatabase
from src.database.pool import DatabasePool
from src.utils.file_cleanup import FileCleanupManager
from src.utils.disk_space import DiskSpaceValidator
from src.database.cache import get_global_cache
from src.database.migrations import MigrationManager

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

    /* Resume Editor Styling */
    .stTextArea textarea {
        font-family: 'Monaco', 'Courier New', monospace !important;
        font-size: 13px !important;
        line-height: 1.6 !important;
    }

    /* Save button prominence */
    .stButton > button[kind="primary"] {
        background-color: #4CAF50 !important;
    }

    /* Editor stats */
    .editor-stats {
        font-size: 0.9rem;
        color: #666;
        padding: 0.5rem;
        background-color: #f8f9fa;
        border-radius: 5px;
        margin-top: 0.5rem;
    }

    /* Version history */
    .version-item {
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-left: 3px solid #1f77b4;
        background-color: #f8f9fa;
    }

    /* Mobile responsive editor */
    @media (max-width: 768px) {
        .stTextArea textarea {
            font-size: 14px !important;
            line-height: 1.4 !important;
        }

        .stTabs [role="tablist"] {
            gap: 0.5rem !important;
        }
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
if 'generated_cover_letter' not in st.session_state:
    st.session_state.generated_cover_letter = None
if 'profile_text' not in st.session_state:
    st.session_state.profile_text = None
if 'current_job_id' not in st.session_state:
    st.session_state.current_job_id = None
if 'last_auto_save' not in st.session_state:
    st.session_state.last_auto_save = None
if 'resume_id' not in st.session_state:
    st.session_state.resume_id = None

@st.cache_resource
def initialize_database():
    """Initialize database with migrations and optimizations"""
    import os
    import sqlite3

    db_path = 'resume_generator.db'

    try:
        # Run migrations with validation (non-blocking - optional performance optimizations)
        try:
            migrator = MigrationManager(db_path, 'migrations')
            pending = migrator.get_pending_migrations()

            if pending:
                # Silently attempt migrations without showing UI messages
                print(f"Attempting to apply {len(pending)} optional database migrations...")
                success = migrator.migrate()
                if success:
                    print("✓ Database migrations applied successfully")
                else:
                    print("Note: Database migrations partially failed (optional optimizations)")
        except Exception as migration_error:
            # Migrations are optional - log but don't show warning to users
            print(f"Note: Could not apply database migrations: {migration_error} (optional optimizations)")

        # Initialize connection pool with corruption recovery
        try:
            pool = DatabasePool(db_path, pool_size=10)
        except (sqlite3.DatabaseError, sqlite3.OperationalError) as db_error:
            error_str = str(db_error).lower()
            is_corrupted = any(msg in error_str for msg in [
                "malformed", "corrupted", "file is not a database",
                "is encrypted", "disk image is"
            ])
            if is_corrupted:
                # Silently recover from database corruption
                print(f"Detected corrupted database. Recreating...")
                # Delete corrupted database files
                for ext in ['', '-shm', '-wal', '-journal']:
                    try:
                        file_path = db_path + ext
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            print(f"Removed corrupted file: {file_path}")
                    except Exception as e:
                        print(f"Warning: Could not remove {file_path}: {e}")

                # Try again with fresh database
                pool = DatabasePool(db_path, pool_size=10)
                print("✓ Database recreated successfully")
            else:
                raise

        # Initialize cache
        cache = get_global_cache()

        # Create optimized database instance
        db = OptimizedDatabase()

        # P1-3 FIX: Run file cleanup on startup to remove orphaned files
        try:
            import sqlite3
            conn = sqlite3.connect('resume_generator.db')
            cleanup_manager = FileCleanupManager(db_connection=conn, max_age_days=30)
            cleanup_results = cleanup_manager.run_full_cleanup(
                directories=["."],
                cleanup_old=False,  # Don't delete old files on startup, only orphaned
                cleanup_orphaned=True,
                cleanup_tests=True
            )
            if cleanup_results['total']['deleted_count'] > 0:
                print(f"Startup cleanup: Removed {cleanup_results['total']['deleted_count']} orphaned files, "
                      f"freed {cleanup_results['total']['freed_mb']:.2f} MB")
            conn.close()
        except Exception as e:
            print(f"Warning: Startup file cleanup failed: {e}")

        # P1-7 FIX: Initialize disk space validator
        disk_validator = DiskSpaceValidator(min_free_space_mb=100)

        return db, pool, cache, disk_validator
    except Exception as e:
        st.error(f"❌ Database initialization failed: {e}")
        import traceback
        st.code(traceback.format_exc())
        st.stop()
        return None, None, None

def initialize_components(db, model="kimi-k2"):
    """Initialize all components with model selection"""
    profile_parser = ProfileParser()
    job_analyzer = JobAnalyzer()
    tavily_client = TavilyClient()
    resume_generator = ResumeGenerator(model=model)
    pdf_generator = PDFGenerator()
    enhanced_pdf_generator = EnhancedPDFGenerator()  # New enhanced generator
    coverletter_generator = CoverLetterGenerator()
    coverletter_pdf_generator = CoverLetterPDFGenerator()
    docx_generator = DOCXGenerator()

    return profile_parser, job_analyzer, tavily_client, resume_generator, pdf_generator, enhanced_pdf_generator, coverletter_generator, coverletter_pdf_generator, docx_generator

def main():
    # Generate or retrieve session ID for rate limiting
    if 'session_id' not in st.session_state:
        import uuid
        st.session_state.session_id = str(uuid.uuid4())

    # Header
    st.markdown('<div class="main-header">📄 Ultra ATS Resume Generator</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Generate ATS-optimized resumes with 90+ scores using AI</div>', unsafe_allow_html=True)

    # Initialize security components
    try:
        validator = InputValidator()
        limiter = RateLimiter()
        sanitizer = PromptSanitizer()
        security_logger = SecurityLogger()
        ats_scorer = ATSScorer()
        enhanced_ats_scorer = EnhancedATSScorer()  # New enhanced scorer
    except Exception as e:
        st.error(f"❌ Security initialization failed: {e}")
        st.stop()

    # Initialize optimized database
    db, pool, cache, disk_validator = initialize_database()

    # Model selection - store in session state for persistence
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = "claude-opus-4"  # Default to Claude Opus 4.1 (Fast)

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        # Check for Profile.pdf or allow upload
        profile_exists = Path("Profile.pdf").exists()

        if profile_exists:
            st.success("✓ Profile.pdf found")
        else:
            st.warning("⚠️ Profile.pdf not found")
            st.info("Upload your profile PDF below:")

            uploaded_profile = st.file_uploader(
                "Upload Profile PDF",
                type=["pdf"],
                help="Upload your profile/resume PDF for parsing"
            )

            if uploaded_profile:
                # Validate file type
                if not uploaded_profile.name.lower().endswith('.pdf'):
                    st.error("✗ Please upload a PDF file")
                else:
                    # Validate file size (max 10MB)
                    file_size = uploaded_profile.size
                    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

                    if file_size > MAX_FILE_SIZE:
                        st.error(f"✗ File too large ({file_size / (1024*1024):.1f}MB). Maximum size: 10MB")
                    else:
                        try:
                            # SECURITY FIX: Path traversal protection - sanitize filename
                            safe_filename = os.path.basename("Profile.pdf")
                            # Ensure filename doesn't contain path traversal sequences
                            if '..' in safe_filename or '/' in safe_filename or '\\' in safe_filename:
                                st.error("✗ Invalid filename detected")
                            else:
                                # Save temporarily with explicit error handling
                                with open(safe_filename, "wb") as f:
                                    f.write(uploaded_profile.read())
                                st.success("✓ Profile uploaded successfully!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"✗ Error saving profile: {str(e)}")

        # Check API keys
        if os.getenv("KIMI_API_KEY"):
            st.success("✓ Kimi K2 API key configured")
        else:
            st.error("✗ Kimi K2 API key missing")

        if os.getenv("ANTHROPIC_API_KEY"):
            st.success("✓ Claude Opus 4.1 API key configured")
        else:
            st.warning("⚠️ Claude Opus 4.1 API key not configured (optional)")

        if os.getenv("TAVILY_API_KEY"):
            st.success("✓ Tavily API key configured")
        else:
            st.error("✗ Tavily API key missing")

        st.divider()

        # Auto-save status
        if st.session_state.last_auto_save:
            time_since_save = (datetime.now() - st.session_state.last_auto_save).total_seconds()
            if time_since_save < 60:
                st.success(f"✅ Auto-saved {int(time_since_save)}s ago")
            else:
                st.info(f"💾 Last saved {int(time_since_save/60)}m ago")

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
                                mime="application/pdf",
                                key=f"download_prev_{resume['id']}"
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
            max_chars=50000,  # Limit to prevent memory issues
            placeholder="Paste the complete job description here...",
            help="Paste the full job description including requirements, responsibilities, and qualifications"
        )

        # Input validation feedback - immediate client-side checks
        if job_description:
            char_count = len(job_description)
            word_count = len(job_description.split())

            # Show helpful statistics
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            with col_stat1:
                st.caption(f"📝 Characters: {char_count:,}/50,000")
            with col_stat2:
                st.caption(f"📄 Words: {word_count:,}")
            with col_stat3:
                # Warn if too short (likely incomplete)
                if word_count < 50:
                    st.caption("⚠️ Job description seems short")
                elif word_count > 2000:
                    st.caption("⚠️ Very long description")
                else:
                    st.caption("✅ Good length")

        # Template Selection Section
        st.subheader("📄 Select Resume Template")

        # Get available templates info
        templates_info = enhanced_pdf_generator.get_all_templates()

        col_t1, col_t2, col_t3 = st.columns(3)

        with col_t1:
            st.markdown("**🎯 Original Simple**")
            st.caption("Clean single-column format")
            st.info("ATS Score: 85-90%")
            st.caption("Best for: Entry to mid-level")

        with col_t2:
            st.markdown("**✨ Modern Professional**")
            st.caption("Two-column with sidebar")
            st.info("ATS Score: 95-100%")
            st.caption("Best for: Technical roles")

        with col_t3:
            st.markdown("**🏛️ Harvard Business**")
            st.caption("Traditional HBS format")
            st.info("ATS Score: 98-100%")
            st.caption("Best for: Business/Executive")

        # Template selection radio buttons
        selected_template = st.radio(
            "Choose Template:",
            options=['modern', 'harvard', 'original'],
            format_func=lambda x: {
                'original': '🎯 Original Simple',
                'modern': '✨ Modern Professional (Recommended)',
                'harvard': '🏛️ Harvard Business'
            }[x],
            index=0,  # Default to Modern
            horizontal=True,
            help="Select the resume template that best fits your target role"
        )

        st.divider()

        # Model Selection
        st.subheader("🤖 AI Model Selection")

        col_model1, col_model2 = st.columns(2)

        with col_model1:
            st.markdown("**Claude Opus 4.1 (Fast)**")
            st.caption("Anthropic's fast reasoning model")
            st.info("Speed: Very Fast | Quality: Excellent")
            st.caption("Best for: Quick iterations")

        with col_model2:
            st.markdown("**Kimi K2 (High Quality)**")
            st.caption("Moonshot AI's deep reasoning model")
            st.info("Speed: Moderate | Quality: Superior")
            st.caption("Best for: Important applications")

        # Model selection radio buttons
        selected_model = st.radio(
            "Choose AI Model:",
            options=['claude-opus-4', 'kimi-k2'],
            format_func=lambda x: {
                'claude-opus-4': '⚡ Claude Opus 4.1 (Fast)',
                'kimi-k2': '🎯 Kimi K2 (High Quality - Default)'
            }[x],
            index=0,  # Default to Claude Opus 4.1
            horizontal=True,
            help="Select the AI model for resume generation. Claude is faster, Kimi provides deeper analysis."
        )

        # Store selected model in session state
        st.session_state.selected_model = selected_model

        st.divider()

        # Options row
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            use_tavily = st.checkbox(
                "Use Tavily for company research",
                value=bool(os.getenv("TAVILY_API_KEY")),
                disabled=not os.getenv("TAVILY_API_KEY"),
                help="Enhance resume with company-specific insights"
            )

        with col2:
            target_score = st.slider(
                "Target ATS Score",
                min_value=85,
                max_value=100,
                value=100,  # Changed default to 100
                help="Target ATS compatibility score"
            )

        # Generate button
        if st.button("🚀 Generate ATS-Optimized Resume", type="primary", use_container_width=True):
            if not company_name or not job_description:
                st.error("Please provide both company name and job description")
            elif not Path("Profile.pdf").exists():
                st.error("Profile.pdf not found. Please add it to the project directory.")
            else:
                # Security: Validate all inputs
                is_valid, error_msg = validator.validate_all_inputs(
                    job_description=job_description,
                    company_name=company_name,
                    job_url=job_url if job_url else None,
                    target_score=target_score
                )

                if not is_valid:
                    st.error(f"❌ {error_msg}")
                    security_logger.log_security_event(
                        event_type="validation_failed",
                        severity="medium",
                        details={"error": error_msg, "company": company_name}
                    )
                    st.stop()

                # Security: Check rate limits
                user_id = st.session_state.session_id
                allowed, limit_msg, reset_time = limiter.check_all_limits(user_id)

                if not allowed:
                    st.error(f"🚫 {limit_msg}")
                    st.info(f"⏱️ Please wait {reset_time} seconds before trying again.")
                    st.sidebar.warning(f"Rate limit reached. Reset in {reset_time}s")
                    st.stop()

                # Show remaining quota in sidebar
                remaining_quota = limiter.get_remaining_quota(user_id, 'hourly')
                st.sidebar.success(f"✅ Remaining quota: {remaining_quota}/10 this hour")
                # Initialize components with selected model
                profile_parser, job_analyzer, tavily_client, resume_generator, pdf_generator, enhanced_pdf_generator, coverletter_generator, coverletter_pdf_generator, docx_generator = initialize_components(db, model=selected_model)

                # Show progress
                with st.spinner("Generating your ATS-optimized resume..."):
                    try:
                        # Step 1: Parse profile
                        progress_bar = st.progress(0)
                        st.info("📄 Parsing your profile...")
                        profile_text = profile_parser.get_profile_summary()
                        st.session_state.profile_text = profile_text  # Save for cover letter
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
                        if use_tavily:
                            st.info("🔬 Researching company...")
                            research_result = tavily_client.research_company(
                                company_name,
                                focus_areas=['culture', 'values', 'technology', 'recent news']
                            )
                            if research_result.get('success'):
                                company_research = {
                                    'research': research_result.get('summary', ''),
                                    'key_insights': research_result.get('key_insights', []),
                                    'sources': research_result.get('sources', [])
                                }
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
                        st.session_state.current_job_id = job_id  # Save for cover letter

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

                        # Use enhanced PDF generator with selected template
                        enhanced_pdf_generator.set_template(selected_template)
                        enhanced_pdf_generator.markdown_to_pdf(resume_result['content'], str(pdf_path))

                        # Store selected template in session state for later use
                        st.session_state.selected_template = selected_template
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
                        model_display = "Claude Opus 4.1" if selected_model == "claude-opus-4" else "Kimi K2"
                        st.success(f"✅ ATS-Optimized Resume Generated Successfully using {model_display}!")
                        st.balloons()

                        # Get the resume ID from database
                        existing_resume = db.check_resume_exists(job_id)
                        resume_id = existing_resume['id'] if existing_resume else None

                        # ENHANCED ATS SCORING
                        with st.spinner("📊 Analyzing ATS compatibility with enhanced scorer..."):
                            try:
                                # Use enhanced scorer with template awareness
                                score_result = enhanced_ats_scorer.score_resume(
                                    resume_content=resume_result['content'],
                                    job_keywords=job_analysis.get('keywords', []),
                                    required_skills=job_analysis.get('required_skills', []),
                                    file_format='pdf',
                                    template_type=selected_template  # Pass template type
                                )

                                # Display score with color coding
                                score = score_result['score']
                                grade = score_result['grade']
                                color = score_result['color']

                                if color == 'green':
                                    st.success(f"✅ **ATS Score: {score:.1f}/100** (Grade: {grade})")
                                elif color == 'yellow':
                                    st.warning(f"⚠️ **ATS Score: {score:.1f}/100** (Grade: {grade})")
                                else:
                                    st.error(f"❌ **ATS Score: {score:.1f}/100** (Grade: {grade})")

                                st.caption(f"📈 Pass Probability: {score_result['pass_probability']}%")

                                # Store real score
                                actual_ats_score = score

                                # Show improvement suggestions
                                if score_result['top_suggestions']:
                                    with st.expander("💡 Top Improvement Suggestions", expanded=(score < 80)):
                                        for i, suggestion in enumerate(score_result['top_suggestions'], 1):
                                            st.info(f"**{i}.** {suggestion}")

                                # Show detailed breakdown
                                with st.expander("📋 Detailed Score Breakdown"):
                                    checks = score_result.get('checks', {})

                                    col1, col2 = st.columns(2)

                                    with col1:
                                        st.markdown("### Content Quality")
                                        for check_name, check_data in checks.items():
                                            if check_name in ['keyword_match', 'keyword_density', 'quantifiable_results', 'action_verbs', 'skills_section']:
                                                status = "✅" if check_data['status'] == 'pass' else "⚠️"
                                                # Some checks don't have max score, handle gracefully
                                                if 'max' in check_data and 'score' in check_data:
                                                    st.write(f"{status} {check_data['message']} ({check_data['score']}/{check_data['max']})")
                                                else:
                                                    st.write(f"{status} {check_data.get('message', 'Check completed')}")

                                    with col2:
                                        st.markdown("### Format & Structure")
                                        for check_name, check_data in checks.items():
                                            if check_name not in ['keyword_match', 'keyword_density', 'quantifiable_results', 'action_verbs', 'skills_section']:
                                                status = "✅" if check_data['status'] == 'pass' else "⚠️"
                                                # Some checks don't have max score, handle gracefully
                                                if 'max' in check_data and 'score' in check_data:
                                                    st.write(f"{status} {check_data['message']} ({check_data['score']}/{check_data['max']})")
                                                else:
                                                    st.write(f"{status} {check_data.get('message', 'Check completed')}")

                            except Exception as e:
                                # Error handler for ATS scoring - ensure spinner clears properly
                                st.warning(f"⚠️ Could not score resume: {e}")
                                actual_ats_score = None

                        # Store in session
                        st.session_state.generated_resume = {
                            'id': resume_id,
                            'content': resume_result['content'],
                            'pdf_path': str(pdf_path),
                            'company_name': company_name,
                            'ats_score': actual_ats_score if actual_ats_score else target_score,
                            'score_breakdown': score_result if actual_ats_score else None
                        }
                        st.session_state.resume_id = resume_id

                    except Exception as e:
                        st.error(f"Error generating resume: {e}")
                        import traceback
                        st.code(traceback.format_exc())

        # Display generated resume
        # Defensive check: ensure generated_resume exists and is a dictionary
        if st.session_state.generated_resume and isinstance(st.session_state.generated_resume, dict):
            st.divider()
            st.subheader("📄 Generated Resume")

            col1, col2 = st.columns([3, 1])

            with col1:
                with st.expander("📝 Resume Content (Markdown)", expanded=True):
                    # Defensive check: ensure 'content' key exists
                    content = st.session_state.generated_resume.get('content', '')
                    if content:
                        st.markdown(content)
                    else:
                        st.warning("Resume content not available")

            with col2:
                st.metric("Target ATS Score", f"{target_score}+")

                # Download button - defensive check for pdf_path
                pdf_path = st.session_state.generated_resume.get('pdf_path', '')
                if Path(pdf_path).exists():
                    with open(pdf_path, 'rb') as f:
                        st.download_button(
                            "⬇️ Download PDF",
                            f.read(),
                            file_name=Path(pdf_path).name,
                            mime="application/pdf",
                            use_container_width=True,
                            key="download_generated_resume"
                        )

                # Copy to clipboard - defensive check
                if st.button("📋 Copy Markdown", use_container_width=True, key="copy_markdown_btn"):
                    content = st.session_state.generated_resume.get('content', '')
                    if content:
                        st.code(content)
                    else:
                        st.warning("No content available to copy")

            st.divider()

            # ======= RESUME EDITOR SECTION =======
            st.subheader("✏️ Edit Resume")
            st.markdown("Edit your resume in real-time. Changes are saved automatically and you can export to PDF or DOCX.")

            # Create tabs for edit and preview
            edit_tab, preview_tab = st.tabs(["📝 Edit Markdown", "👁️ Preview"])

            with edit_tab:
                # Initialize editor content - defensive checks
                resume_content = st.session_state.generated_resume.get('content', '')
                if 'editor_content' not in st.session_state:
                    st.session_state.editor_content = resume_content

                # Editable text area - use defensive get()
                edited_content = st.text_area(
                    "Edit your resume content below:",
                    value=resume_content if resume_content else "# No content available",
                    height=600,
                    key="resume_editor",
                    help="Edit the markdown content. Changes appear in Preview tab. Use Markdown formatting: **bold**, *italic*, ## headers, - bullets"
                )

                # Word and character count
                word_count = len(edited_content.split())
                char_count = len(edited_content)
                line_count = len(edited_content.split('\n'))

                st.markdown(
                    f'<div class="editor-stats">📊 <strong>{word_count}</strong> words | '
                    f'<strong>{char_count}</strong> characters | '
                    f'<strong>{line_count}</strong> lines</div>',
                    unsafe_allow_html=True
                )

                # Action buttons
                col1, col2, col3, col4 = st.columns([1.5, 1.5, 1.5, 1])

                with col1:
                    if st.button("💾 Save Changes", type="primary", use_container_width=True, key="save_resume_btn"):
                        try:
                            # Defensive check before updating
                            if not isinstance(st.session_state.generated_resume, dict):
                                st.error("Invalid resume state. Please regenerate the resume.")
                            else:
                                # Update session state
                                st.session_state.generated_resume['content'] = edited_content

                            # Update database - defensive check for resume_id
                            if st.session_state.get('resume_id'):
                                db.update_resume_content(
                                    st.session_state.resume_id,
                                    edited_content
                                )

                                # Regenerate PDF with edited content using selected template
                                pdf_path = st.session_state.generated_resume['pdf_path']
                                # Get the currently selected template (store in session state)
                                current_template = st.session_state.get('selected_template', 'modern')
                                enhanced_pdf_generator.set_template(current_template)
                                enhanced_pdf_generator.markdown_to_pdf(edited_content, pdf_path)

                                st.success("✅ Resume saved successfully!")
                                st.session_state.last_auto_save = datetime.now()

                            else:
                                st.error("Resume ID not found. Please regenerate the resume.")

                        except Exception as e:
                            st.error(f"Error saving resume: {e}")

                with col2:
                    if st.button("↩️ Undo Changes", use_container_width=True, key="undo_resume_btn"):
                        try:
                            # Defensive check for resume_id
                            if st.session_state.get('resume_id'):
                                # Get latest version from database
                                resume_data = db.get_resume_by_id(st.session_state.resume_id)
                                if resume_data and isinstance(st.session_state.generated_resume, dict):
                                    st.session_state.generated_resume['content'] = resume_data.get('resume_content', '')
                                    st.success("✅ Changes reverted to last saved version")
                                    st.rerun()
                                else:
                                    st.error("Could not load original resume from database")
                            else:
                                st.error("Resume ID not found")
                        except Exception as e:
                            st.error(f"Error reverting changes: {e}")

                with col3:
                    if st.button("🔄 Regenerate from Scratch", use_container_width=True, key="regenerate_resume_btn"):
                        # Clear session and trigger full regeneration
                        st.session_state.generated_resume = None
                        st.session_state.resume_id = None
                        st.info("Click 'Generate ATS-Optimized Resume' button above to regenerate")
                        st.rerun()

                with col4:
                    # Version history button
                    if st.button("📜", use_container_width=True, key="version_history_btn", help="View version history"):
                        st.session_state.show_versions = not st.session_state.get('show_versions', False)
                        st.rerun()

                # Show version history if toggled
                if st.session_state.get('show_versions', False):
                    st.markdown("### 📜 Version History")

                    if st.session_state.resume_id:
                        versions = db.get_resume_versions(st.session_state.resume_id)

                        if versions:
                            st.info(f"Found {len(versions)} previous versions")

                            for idx, version in enumerate(versions):
                                with st.expander(f"Version {len(versions)-idx} - {version['created_at']}", expanded=False):
                                    st.markdown(f"**Notes:** {version['version_notes']}")

                                    col_a, col_b = st.columns([3, 1])

                                    with col_a:
                                        st.text_area(
                                            "Content",
                                            value=version['content'][:500] + "..." if len(version['content']) > 500 else version['content'],
                                            height=150,
                                            key=f"version_content_{version['id']}",
                                            disabled=True
                                        )

                                    with col_b:
                                        if st.button("📥 Restore", key=f"restore_version_{version['id']}", use_container_width=True):
                                            st.session_state.generated_resume['content'] = version['content']
                                            st.success(f"✅ Restored version from {version['created_at']}")
                                            st.rerun()
                        else:
                            st.info("No version history available yet. Versions are created automatically when you save changes.")
                    else:
                        st.warning("Resume ID not found. Version history not available.")

                st.divider()

                # Export options
                st.markdown("### 📥 Export Options")

                col_exp1, col_exp2, col_exp3 = st.columns(3)

                with col_exp1:
                    # PDF export
                    pdf_path = st.session_state.generated_resume['pdf_path']
                    if Path(pdf_path).exists():
                        with open(pdf_path, 'rb') as f:
                            st.download_button(
                                "📄 Download PDF",
                                f.read(),
                                file_name=Path(pdf_path).name,
                                mime="application/pdf",
                                use_container_width=True,
                                key="export_pdf_btn"
                            )
                    else:
                        st.button("📄 Download PDF", disabled=True, use_container_width=True)

                with col_exp2:
                    # DOCX export
                    if st.button("📝 Generate DOCX", use_container_width=True, key="generate_docx_btn"):
                        try:
                            # Create DOCX file
                            output_dir = Path("generated_resumes")
                            output_dir.mkdir(exist_ok=True)

                            safe_company_name = "".join(c for c in st.session_state.generated_resume['company_name'] if c.isalnum() or c in (' ', '-', '_')).strip()
                            docx_filename = f"Venkat_{safe_company_name}.docx"
                            docx_path = output_dir / docx_filename

                            docx_generator.markdown_to_docx(
                                edited_content,
                                str(docx_path),
                                st.session_state.generated_resume['company_name']
                            )

                            st.success("✅ DOCX generated successfully!")

                            # Offer download
                            with open(docx_path, 'rb') as f:
                                st.download_button(
                                    "⬇️ Download DOCX",
                                    f.read(),
                                    file_name=docx_filename,
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    use_container_width=True,
                                    key="download_docx_btn"
                                )

                        except Exception as e:
                            st.error(f"Error generating DOCX: {e}")
                            st.exception(e)

                with col_exp3:
                    # Copy markdown
                    if st.button("📋 Copy Markdown", use_container_width=True, key="copy_edited_markdown_btn"):
                        st.code(edited_content, language="markdown")
                        st.info("Copy the markdown from the code block above")

            with preview_tab:
                # Live preview of edited content
                st.markdown("### 📄 Resume Preview")
                st.markdown(edited_content)

                # Show metrics
                st.divider()
                col_p1, col_p2, col_p3 = st.columns(3)

                with col_p1:
                    st.metric("Words", word_count)

                with col_p2:
                    st.metric("Characters", char_count)

                with col_p3:
                    if 'ats_score' in st.session_state.generated_resume:
                        st.metric("ATS Score", f"{st.session_state.generated_resume['ats_score']}+")
                    else:
                        st.metric("ATS Score", "N/A")

            st.divider()

            # Cover Letter Section
            st.subheader("✉️ Cover Letter (Optional)")

            col1, col2 = st.columns([2, 1])

            with col1:
                st.write("Generate a professional cover letter to complement your resume")

            with col2:
                if st.button("📝 Generate Cover Letter", type="secondary", use_container_width=True, key="generate_cover_letter_btn"):
                    if not st.session_state.profile_text or not st.session_state.job_analysis:
                        st.error("Missing required data. Please generate a resume first.")
                    else:
                        with st.spinner("Generating your professional cover letter..."):
                            try:
                                progress_bar = st.progress(0)

                                # Step 1: Generate cover letter
                                st.info("✨ Writing cover letter with Claude...")
                                coverletter_result = coverletter_generator.generate_cover_letter(
                                    st.session_state.profile_text,
                                    st.session_state.job_analysis,
                                    st.session_state.company_research,
                                    st.session_state.generated_resume['content']
                                )

                                if not coverletter_result['success']:
                                    st.error(f"Cover letter generation failed: {coverletter_result.get('error', 'Unknown error')}")
                                else:
                                    progress_bar.progress(50)

                                    # Step 2: Generate PDF
                                    st.info("📄 Creating cover letter PDF...")
                                    company_name = st.session_state.job_analysis.get('company_name', 'Company')
                                    job_title = st.session_state.job_analysis.get('job_title', 'Position')

                                    # P1-7 FIX: Validate disk space before PDF generation
                                    content_length = len(coverletter_result['content'])
                                    estimated_size = disk_validator.estimate_pdf_size(content_length)
                                    has_space, space_msg = disk_validator.has_sufficient_space(
                                        required_bytes=estimated_size,
                                        safety_margin_mb=50
                                    )
                                    if not has_space:
                                        st.error(f"❌ {space_msg}")
                                        st.stop()

                                    coverletter_pdf_path = coverletter_pdf_generator.generate_pdf(
                                        coverletter_result['content'],
                                        company_name,
                                        job_title
                                    )
                                    progress_bar.progress(75)

                                    # Step 3: Save to database
                                    if coverletter_pdf_path and st.session_state.current_job_id:
                                        resume_id = db.check_resume_exists(st.session_state.current_job_id)
                                        resume_id = resume_id['id'] if resume_id else None

                                        db.insert_generated_cover_letter(
                                            st.session_state.current_job_id,
                                            coverletter_result['content'],
                                            coverletter_pdf_path,
                                            resume_id
                                        )
                                    progress_bar.progress(100)

                                    # Success!
                                    st.success("✅ Cover Letter Generated Successfully!")

                                    # Store in session
                                    st.session_state.generated_cover_letter = {
                                        'content': coverletter_result['content'],
                                        'pdf_path': coverletter_pdf_path,
                                        'company_name': company_name
                                    }

                                    st.rerun()

                            except Exception as e:
                                st.error(f"Error generating cover letter: {e}")
                                import traceback
                                st.code(traceback.format_exc())

            # Display generated cover letter
            if st.session_state.generated_cover_letter:
                st.markdown("---")

                col1, col2 = st.columns([3, 1])

                with col1:
                    with st.expander("✉️ Cover Letter Content", expanded=True):
                        st.markdown(st.session_state.generated_cover_letter['content'])

                with col2:
                    # Download button
                    coverletter_pdf_path = st.session_state.generated_cover_letter['pdf_path']
                    if coverletter_pdf_path and Path(coverletter_pdf_path).exists():
                        with open(coverletter_pdf_path, 'rb') as f:
                            st.download_button(
                                "⬇️ Download Cover Letter PDF",
                                f.read(),
                                file_name=Path(coverletter_pdf_path).name,
                                mime="application/pdf",
                                use_container_width=True,
                                key="download_cover_letter_pdf"
                            )

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

        The **Ultra ATS Resume Generator** is an AI-powered tool that creates highly optimized resumes and cover letters designed to score 90+ in Applicant Tracking Systems (ATS).

        ### ✨ Key Features

        - **ATS Optimization**: Trained on comprehensive ATS knowledge from industry sources
        - **Dual AI Models**: Choose between Claude Opus 4.1 (fast) or Kimi K2 (high quality) for resume generation
        - **Cover Letter Generation**: Optional professional cover letters that complement your resume
        - **Company Research**: Optional Tavily AI integration for company-specific insights
        - **Duplicate Detection**: Prevents regenerating resumes for the same job
        - **Database Storage**: Keeps history of all generated resumes and cover letters
        - **PDF Export**: Creates ATS-friendly PDF format with clickable links

        ### 🔧 How it Works

        1. **Parse Profile**: Extracts your information from Profile.pdf
        2. **Analyze Job**: Uses AI to extract keywords, skills, and requirements
        3. **Research Company**: (Optional) Gathers company insights via Tavily AI
        4. **Generate Resume**: Creates tailored, ATS-optimized resume with your chosen AI model (Claude Opus 4.1 or Kimi K2)
        5. **Export PDF**: Generates clean, ATS-friendly PDF format
        6. **Generate Cover Letter**: (Optional) Creates professional cover letter complementing your resume

        ### 📋 ATS Optimization Includes

        - ✅ Keyword optimization from job description
        - ✅ ATS-friendly formatting (no tables, columns, or graphics)
        - ✅ Standard section headers
        - ✅ Achievement-focused bullet points
        - ✅ Quantifiable metrics
        - ✅ Industry-specific terminology
        - ✅ Skills matching

        ### 🔑 API Keys Required

        - **Kimi K2 API** (Required): For high-quality resume generation and analysis
        - **Claude Opus 4.1 API** (Optional): For fast resume generation
        - **Tavily API** (Required): For company research

        ### 📚 Knowledge Base

        Built on insights from 7 authoritative ATS sources including Jobscan, industry reports, and best practices guides.

        ---

        **Version**: 1.0.0 | **Author**: AI-Powered Resume Solutions
        """)

if __name__ == "__main__":
    main()
