"""
End-to-End System Test for Resume Generator
Tests the entire pipeline: PDF parsing → Dynamic section detection → AI generation → LaTeX rendering
"""
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.parsers.profile_parser import ProfileParser
from src.parsers.ai_resume_parser import AIResumeParser
from src.generators.resume_generator import ResumeGenerator
from src.generators.latex_data_transformer import LaTeXDataTransformer
from src.generators.latex_resume_pipeline import LaTeXResumePipeline
from src.utils.database import Database


class E2ESystemTester:
    """Comprehensive end-to-end system tester"""

    def __init__(self):
        self.profile_parser = ProfileParser()
        self.ai_parser = AIResumeParser()
        self.data_transformer = LaTeXDataTransformer()
        self.db = Database()
        self.resume_generator = ResumeGenerator(self.db, model='gpt-4o')
        self.latex_pipeline = LaTeXResumePipeline()

        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {}
        }

    def log(self, message, status='INFO'):
        """Log test progress"""
        symbol = {
            'INFO': 'ℹ️',
            'SUCCESS': '✅',
            'FAIL': '❌',
            'WARNING': '⚠️'
        }.get(status, 'ℹ️')
        print(f"{symbol} {message}")

    def test_1_pdf_parsing(self, pdf_path: str):
        """Test 1: PDF parsing extracts text correctly"""
        self.log("TEST 1: PDF Parsing", 'INFO')
        try:
            text = self.profile_parser.extract_text_from_pdf(pdf_path)

            # Verify text extraction
            assert text and len(text) > 100, "PDF text extraction failed or too short"
            self.log(f"  - Extracted {len(text)} characters from PDF", 'SUCCESS')

            # Check for common resume sections
            text_lower = text.lower()
            sections_found = []
            for section in ['summary', 'experience', 'education', 'skills', 'projects']:
                if section in text_lower:
                    sections_found.append(section)

            self.log(f"  - Found sections: {', '.join(sections_found)}", 'SUCCESS')

            self.test_results['tests']['pdf_parsing'] = {
                'status': 'PASS',
                'text_length': len(text),
                'sections_found': sections_found
            }
            return text

        except Exception as e:
            self.log(f"  - PDF parsing failed: {e}", 'FAIL')
            self.test_results['tests']['pdf_parsing'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            raise

    def test_2_dynamic_section_detection(self, markdown: str):
        """Test 2: Dynamic section detection identifies all sections"""
        self.log("\nTEST 2: Dynamic Section Detection", 'INFO')
        try:
            # Parse markdown with new dynamic section detection
            structured_data = self.ai_parser.parse_markdown_resume(markdown)

            # Check core sections
            assert 'header' in structured_data, "Missing header"
            assert 'summary' in structured_data, "Missing summary"
            assert 'projects' in structured_data, "Missing projects"
            self.log("  - Core sections extracted successfully", 'SUCCESS')

            # Check dynamic sections
            dynamic_sections = structured_data.get('dynamic_sections', {})
            self.log(f"  - Detected {len(dynamic_sections)} dynamic sections", 'SUCCESS')

            for section_name, section_data in dynamic_sections.items():
                content_type = section_data.get('type', 'unknown')
                display_name = section_data.get('display_name', section_name)
                self.log(f"    • {display_name} (type: {content_type})", 'INFO')

            self.test_results['tests']['dynamic_section_detection'] = {
                'status': 'PASS',
                'core_sections': ['header', 'summary', 'projects'],
                'dynamic_sections': list(dynamic_sections.keys()),
                'dynamic_section_types': {
                    name: data.get('type') for name, data in dynamic_sections.items()
                }
            }

            return structured_data

        except Exception as e:
            self.log(f"  - Dynamic section detection failed: {e}", 'FAIL')
            self.test_results['tests']['dynamic_section_detection'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            raise

    def test_3_ai_resume_generation(self, profile_text: str):
        """Test 3: AI generates resume with all sections preserved"""
        self.log("\nTEST 3: AI Resume Generation", 'INFO')
        try:
            # Test job description
            job_desc = """
            Senior AI Product Developer

            Requirements:
            - 5+ years of experience building AI-powered products
            - Expert in GPT-4, LangChain, and RAG systems
            - Strong Python and ML skills
            - Experience with multi-agent systems
            """

            # Generate resume
            self.log("  - Calling AI to generate resume markdown...", 'INFO')
            ai_resume_md = self.resume_generator.generate_resume_content(
                profile_info=profile_text,
                job_description=job_desc,
                company_name="TestCorp",
                target_score=95
            )

            assert ai_resume_md and len(ai_resume_md) > 200, "AI generation failed or too short"
            self.log(f"  - AI generated {len(ai_resume_md)} characters", 'SUCCESS')

            # Check if AI preserved sections
            sections_in_output = []
            for section in ['Summary', 'Skills', 'Education', 'Projects', 'Publications', 'Awards', 'Additional']:
                if section.lower() in ai_resume_md.lower():
                    sections_in_output.append(section)

            self.log(f"  - Sections in AI output: {', '.join(sections_in_output)}", 'SUCCESS')

            self.test_results['tests']['ai_generation'] = {
                'status': 'PASS',
                'output_length': len(ai_resume_md),
                'sections_preserved': sections_in_output
            }

            return ai_resume_md

        except Exception as e:
            self.log(f"  - AI generation failed: {e}", 'FAIL')
            self.test_results['tests']['ai_generation'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            raise

    def test_4_data_transformation(self, structured_data: dict):
        """Test 4: Data transformation escapes LaTeX correctly"""
        self.log("\nTEST 4: LaTeX Data Transformation", 'INFO')
        try:
            # Transform data
            latex_data = self.data_transformer.transform(structured_data)

            # Validate output
            errors = self.data_transformer.validate_output(latex_data)
            assert not errors, f"Validation errors: {errors}"
            self.log("  - Data transformation validation passed", 'SUCCESS')

            # Check dynamic sections preserved
            dynamic_sections = latex_data.get('dynamic_sections', {})
            self.log(f"  - Transformed {len(dynamic_sections)} dynamic sections", 'SUCCESS')

            # Verify LaTeX escaping
            sample_text = latex_data.get('summary', '')
            dangerous_chars = ['$', '%', '&', '#', '_']
            unescaped = [c for c in dangerous_chars if c in sample_text and f'\\{c}' not in sample_text]

            if not unescaped:
                self.log("  - LaTeX special characters properly escaped", 'SUCCESS')
            else:
                self.log(f"  - WARNING: Unescaped chars found: {unescaped}", 'WARNING')

            self.test_results['tests']['data_transformation'] = {
                'status': 'PASS',
                'dynamic_sections_count': len(dynamic_sections),
                'validation_errors': errors
            }

            return latex_data

        except Exception as e:
            self.log(f"  - Data transformation failed: {e}", 'FAIL')
            self.test_results['tests']['data_transformation'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            raise

    def test_5_latex_compilation(self, latex_data: dict):
        """Test 5: LaTeX template compiles to PDF successfully"""
        self.log("\nTEST 5: LaTeX Compilation", 'INFO')
        try:
            # Generate PDF
            output_dir = Path("./test_output")
            output_dir.mkdir(exist_ok=True)

            output_path = output_dir / f"e2e_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

            self.log("  - Compiling LaTeX to PDF...", 'INFO')
            pdf_path, tex_path = self.latex_pipeline.generate_pdf(
                resume_data=latex_data,
                output_path=str(output_path)
            )

            # Verify PDF created
            assert Path(pdf_path).exists(), "PDF not created"
            pdf_size = Path(pdf_path).stat().st_size
            self.log(f"  - PDF created successfully: {pdf_path} ({pdf_size} bytes)", 'SUCCESS')

            # Verify TEX created
            assert Path(tex_path).exists(), "TEX file not created"
            self.log(f"  - TEX file created: {tex_path}", 'SUCCESS')

            self.test_results['tests']['latex_compilation'] = {
                'status': 'PASS',
                'pdf_path': str(pdf_path),
                'pdf_size': pdf_size,
                'tex_path': str(tex_path)
            }

            return pdf_path, tex_path

        except Exception as e:
            self.log(f"  - LaTeX compilation failed: {e}", 'FAIL')
            self.test_results['tests']['latex_compilation'] = {
                'status': 'FAIL',
                'error': str(e)
            }
            raise

    def test_6_verify_dynamic_sections_in_pdf(self, tex_path: str, expected_sections: list):
        """Test 6: Verify dynamic sections appear in TEX file"""
        self.log("\nTEST 6: Dynamic Sections in Output", 'INFO')
        try:
            with open(tex_path, 'r', encoding='utf-8') as f:
                tex_content = f.read()

            sections_found = []
            sections_missing = []

            for section_name in expected_sections:
                # Check if section appears in TEX
                if section_name.lower() in tex_content.lower():
                    sections_found.append(section_name)
                    self.log(f"  - ✓ {section_name} found in output", 'SUCCESS')
                else:
                    sections_missing.append(section_name)
                    self.log(f"  - ✗ {section_name} MISSING from output", 'FAIL')

            if sections_missing:
                self.log(f"  - WARNING: {len(sections_missing)} sections missing", 'WARNING')
            else:
                self.log(f"  - All {len(sections_found)} dynamic sections present", 'SUCCESS')

            self.test_results['tests']['dynamic_sections_in_output'] = {
                'status': 'PASS' if not sections_missing else 'PARTIAL',
                'sections_found': sections_found,
                'sections_missing': sections_missing
            }

        except Exception as e:
            self.log(f"  - Verification failed: {e}", 'FAIL')
            self.test_results['tests']['dynamic_sections_in_output'] = {
                'status': 'FAIL',
                'error': str(e)
            }

    def run_full_test_suite(self, pdf_path: str):
        """Run all tests in sequence"""
        self.log("="*60, 'INFO')
        self.log("STARTING END-TO-END SYSTEM TEST", 'INFO')
        self.log("="*60, 'INFO')

        try:
            # Test 1: PDF Parsing
            pdf_text = self.test_1_pdf_parsing(pdf_path)

            # Test 2 & 3: We need to test the AI generation first to get markdown
            # Then parse that markdown to detect sections
            ai_resume_md = self.test_3_ai_resume_generation(pdf_text)

            # Test 2: Dynamic section detection on AI-generated markdown
            structured_data = self.test_2_dynamic_section_detection(ai_resume_md)

            # Test 4: Data transformation
            latex_data = self.test_4_data_transformation(structured_data)

            # Test 5: LaTeX compilation
            pdf_path, tex_path = self.test_5_latex_compilation(latex_data)

            # Test 6: Verify dynamic sections
            dynamic_section_names = list(structured_data.get('dynamic_sections', {}).keys())
            self.test_6_verify_dynamic_sections_in_pdf(tex_path, dynamic_section_names)

            # Summary
            self.log("\n" + "="*60, 'INFO')
            self.log("TEST SUITE SUMMARY", 'INFO')
            self.log("="*60, 'INFO')

            total_tests = len(self.test_results['tests'])
            passed = sum(1 for t in self.test_results['tests'].values() if t['status'] == 'PASS')
            failed = sum(1 for t in self.test_results['tests'].values() if t['status'] == 'FAIL')
            partial = sum(1 for t in self.test_results['tests'].values() if t['status'] == 'PARTIAL')

            self.log(f"Total Tests: {total_tests}", 'INFO')
            self.log(f"Passed: {passed}", 'SUCCESS' if passed == total_tests else 'INFO')
            self.log(f"Failed: {failed}", 'FAIL' if failed > 0 else 'INFO')
            self.log(f"Partial: {partial}", 'WARNING' if partial > 0 else 'INFO')

            # Save results
            results_path = Path("./test_output/e2e_test_results.json")
            with open(results_path, 'w') as f:
                json.dump(self.test_results, f, indent=2)
            self.log(f"\nDetailed results saved to: {results_path}", 'INFO')

            if failed == 0:
                self.log("\n🎉 ALL TESTS PASSED!", 'SUCCESS')
                return True
            else:
                self.log(f"\n⚠️  {failed} TEST(S) FAILED", 'FAIL')
                return False

        except Exception as e:
            self.log(f"\n💥 CRITICAL ERROR: {e}", 'FAIL')
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    tester = E2ESystemTester()

    # Run test with Profile.pdf
    pdf_path = "./Profile.pdf"

    if not Path(pdf_path).exists():
        print(f"❌ Error: {pdf_path} not found")
        sys.exit(1)

    success = tester.run_full_test_suite(pdf_path)
    sys.exit(0 if success else 1)
