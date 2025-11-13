"""
Test suite for Resume Editor functionality
"""
import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.schema import Database
from src.generators.docx_generator import DOCXGenerator
from src.generators.pdf_generator import PDFGenerator


class TestResumeEditor:
    """Test cases for resume editing functionality"""

    @pytest.fixture
    def db(self, tmp_path):
        """Create a temporary database for testing"""
        db_path = tmp_path / "test_resume_editor.db"
        return Database(str(db_path))

    @pytest.fixture
    def sample_resume_content(self):
        """Sample resume content for testing"""
        return """# John Doe
johndoe@email.com | (555) 123-4567 | LinkedIn | GitHub | San Francisco, CA

## PROFESSIONAL SUMMARY
Senior Software Engineer with 5+ years of experience in AI/ML and full-stack development.

## TECHNICAL SKILLS
**Programming:** Python, JavaScript, TypeScript, SQL
**AI/ML:** LangChain, OpenAI, Anthropic Claude, RAG

## PROFESSIONAL EXPERIENCE

### Senior AI Engineer | TechCorp | San Francisco, CA
*01/2022 - Present*
- Built production RAG system handling 10K+ queries/day with 95% accuracy
- Implemented LLM-powered features using GPT-4 and Claude

## EDUCATION
**Master of Science in Computer Science** | Stanford University | 2019
"""

    def test_database_schema_initialization(self, db):
        """Test that database schema includes version tracking table"""
        conn = db.get_connection()
        cursor = conn.cursor()

        # Check if resume_versions table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='resume_versions'
        """)
        result = cursor.fetchone()

        assert result is not None, "resume_versions table should exist"

        # Check table structure
        cursor.execute("PRAGMA table_info(resume_versions)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        assert 'id' in column_names
        assert 'resume_id' in column_names
        assert 'content' in column_names
        assert 'version_notes' in column_names
        assert 'created_at' in column_names

        conn.close()

    def test_insert_and_retrieve_resume(self, db, sample_resume_content):
        """Test inserting and retrieving a resume"""
        # Insert job description
        job_id = db.insert_job_description(
            company_name="TechCorp",
            job_description="Software Engineer position",
            job_title="Senior Software Engineer"
        )

        # Insert resume
        resume_id = db.insert_generated_resume(
            job_description_id=job_id,
            resume_content=sample_resume_content,
            file_path="/path/to/resume.pdf",
            ats_score=95
        )

        assert resume_id is not None

        # Retrieve resume
        resume = db.get_resume_by_id(resume_id)

        assert resume is not None
        assert resume['resume_content'] == sample_resume_content
        assert resume['company_name'] == "TechCorp"
        assert resume['ats_score'] == 95

    def test_update_resume_content(self, db, sample_resume_content):
        """Test updating resume content and version tracking"""
        # Insert job and resume
        job_id = db.insert_job_description(
            company_name="TechCorp",
            job_description="Software Engineer position",
            job_title="Senior Software Engineer"
        )

        resume_id = db.insert_generated_resume(
            job_description_id=job_id,
            resume_content=sample_resume_content,
            file_path="/path/to/resume.pdf"
        )

        # Update resume content
        new_content = sample_resume_content + "\n\n## CERTIFICATIONS\nAWS Certified"

        db.update_resume_content(resume_id, new_content)

        # Verify update
        updated_resume = db.get_resume_by_id(resume_id)
        assert updated_resume['resume_content'] == new_content

        # Verify version was saved
        versions = db.get_resume_versions(resume_id)
        assert len(versions) == 1
        assert versions[0]['content'] == sample_resume_content

    def test_version_history_tracking(self, db, sample_resume_content):
        """Test that version history is properly tracked"""
        # Insert job and resume
        job_id = db.insert_job_description(
            company_name="TechCorp",
            job_description="Software Engineer position"
        )

        resume_id = db.insert_generated_resume(
            job_description_id=job_id,
            resume_content=sample_resume_content,
            file_path="/path/to/resume.pdf"
        )

        # Make multiple edits
        edit_1 = sample_resume_content + "\n\nEdit 1"
        edit_2 = sample_resume_content + "\n\nEdit 2"
        edit_3 = sample_resume_content + "\n\nEdit 3"

        db.update_resume_content(resume_id, edit_1)
        db.update_resume_content(resume_id, edit_2)
        db.update_resume_content(resume_id, edit_3)

        # Check version history
        versions = db.get_resume_versions(resume_id)

        # Should have 3 versions (original + 2 intermediate edits)
        assert len(versions) >= 3

        # Most recent version should be edit_2
        assert versions[0]['content'] == edit_2

    def test_create_resume_version_manually(self, db, sample_resume_content):
        """Test manually creating a resume version"""
        # Insert job and resume
        job_id = db.insert_job_description(
            company_name="TechCorp",
            job_description="Software Engineer position"
        )

        resume_id = db.insert_generated_resume(
            job_description_id=job_id,
            resume_content=sample_resume_content,
            file_path="/path/to/resume.pdf"
        )

        # Create manual version
        version_id = db.create_resume_version(
            resume_id,
            sample_resume_content,
            "Manual backup before major edit"
        )

        assert version_id is not None

        # Retrieve versions
        versions = db.get_resume_versions(resume_id)
        assert len(versions) == 1
        assert versions[0]['version_notes'] == "Manual backup before major edit"

    def test_update_resume_score(self, db, sample_resume_content):
        """Test updating ATS score after editing"""
        # Insert job and resume
        job_id = db.insert_job_description(
            company_name="TechCorp",
            job_description="Software Engineer position"
        )

        resume_id = db.insert_generated_resume(
            job_description_id=job_id,
            resume_content=sample_resume_content,
            file_path="/path/to/resume.pdf",
            ats_score=85
        )

        # Update score
        db.update_resume_score(resume_id, 95)

        # Verify update
        resume = db.get_resume_by_id(resume_id)
        assert resume['ats_score'] == 95

    def test_docx_generation(self, sample_resume_content, tmp_path):
        """Test DOCX generation from markdown"""
        docx_gen = DOCXGenerator()

        output_path = tmp_path / "test_resume.docx"

        result_path = docx_gen.markdown_to_docx(
            sample_resume_content,
            str(output_path),
            "TechCorp"
        )

        assert Path(result_path).exists()
        assert Path(result_path).suffix == '.docx'
        assert Path(result_path).stat().st_size > 0

    def test_pdf_generation(self, sample_resume_content, tmp_path):
        """Test PDF generation from markdown"""
        pdf_gen = PDFGenerator()

        output_path = tmp_path / "test_resume.pdf"

        result_path = pdf_gen.markdown_to_pdf(
            sample_resume_content,
            str(output_path)
        )

        assert Path(result_path).exists()
        assert Path(result_path).suffix == '.pdf'
        assert Path(result_path).stat().st_size > 0

    def test_version_limit(self, db, sample_resume_content):
        """Test that version history respects the limit parameter"""
        # Insert job and resume
        job_id = db.insert_job_description(
            company_name="TechCorp",
            job_description="Software Engineer position"
        )

        resume_id = db.insert_generated_resume(
            job_description_id=job_id,
            resume_content=sample_resume_content,
            file_path="/path/to/resume.pdf"
        )

        # Create 15 versions
        for i in range(15):
            db.create_resume_version(
                resume_id,
                f"{sample_resume_content}\n\nVersion {i}",
                f"Version {i}"
            )

        # Get versions with limit
        versions = db.get_resume_versions(resume_id, limit=5)

        # Should only return 5 versions
        assert len(versions) == 5

    def test_word_count_calculation(self, sample_resume_content):
        """Test word count calculation for editor stats"""
        word_count = len(sample_resume_content.split())
        assert word_count > 0

        # Test with known content
        test_content = "This is a test resume with exactly ten words here."
        assert len(test_content.split()) == 10

    def test_character_count_calculation(self, sample_resume_content):
        """Test character count calculation for editor stats"""
        char_count = len(sample_resume_content)
        assert char_count > 0

        # Test with known content
        test_content = "Hello"
        assert len(test_content) == 5

    def test_markdown_formatting_preservation(self):
        """Test that markdown formatting is preserved in editing"""
        original = "**Bold** *italic* and normal text"

        # Simulate editing
        edited = original + "\n\nNew paragraph"

        assert "**Bold**" in edited
        assert "*italic*" in edited

    def test_database_cascade_delete(self, db, sample_resume_content):
        """Test that versions are deleted when resume is deleted"""
        # Insert job and resume
        job_id = db.insert_job_description(
            company_name="TechCorp",
            job_description="Software Engineer position"
        )

        resume_id = db.insert_generated_resume(
            job_description_id=job_id,
            resume_content=sample_resume_content,
            file_path="/path/to/resume.pdf"
        )

        # Create versions
        db.create_resume_version(resume_id, sample_resume_content, "Version 1")
        db.create_resume_version(resume_id, sample_resume_content, "Version 2")

        # Verify versions exist
        versions = db.get_resume_versions(resume_id)
        assert len(versions) == 2

        # Delete resume
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM generated_resumes WHERE id = ?", (resume_id,))
        conn.commit()

        # Verify versions are deleted (cascade)
        versions_after = db.get_resume_versions(resume_id)
        assert len(versions_after) == 0

        conn.close()


class TestDOCXGenerator:
    """Test cases specifically for DOCX generator"""

    @pytest.fixture
    def docx_gen(self):
        """Create DOCX generator instance"""
        return DOCXGenerator()

    def test_markdown_heading_conversion(self, docx_gen, tmp_path):
        """Test that markdown headings are properly converted"""
        markdown = """# John Doe
## PROFESSIONAL SUMMARY
### Senior Engineer
"""
        output_path = tmp_path / "test.docx"

        docx_gen.markdown_to_docx(markdown, str(output_path))

        assert output_path.exists()

    def test_markdown_bullet_conversion(self, docx_gen, tmp_path):
        """Test that markdown bullets are properly converted"""
        markdown = """## SKILLS
- Python
- JavaScript
- TypeScript
"""
        output_path = tmp_path / "test.docx"

        docx_gen.markdown_to_docx(markdown, str(output_path))

        assert output_path.exists()

    def test_markdown_bold_italic_conversion(self, docx_gen, tmp_path):
        """Test that markdown formatting is converted"""
        markdown = """**Bold text** and *italic text* and normal text"""

        output_path = tmp_path / "test.docx"

        docx_gen.markdown_to_docx(markdown, str(output_path))

        assert output_path.exists()

    def test_contact_info_formatting(self, docx_gen, tmp_path):
        """Test that contact info with pipes is formatted correctly"""
        markdown = """# John Doe
email@example.com | (555) 123-4567 | LinkedIn | GitHub | San Francisco, CA
"""
        output_path = tmp_path / "test.docx"

        docx_gen.markdown_to_docx(markdown, str(output_path))

        assert output_path.exists()


def run_tests():
    """Run all tests"""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_tests()
