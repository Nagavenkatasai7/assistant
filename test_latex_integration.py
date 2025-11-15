"""
End-to-end test for LaTeX resume generation pipeline
"""
from pathlib import Path
from src.generators.latex_data_transformer import LaTeXDataTransformer, create_sample_resume_data
from src.generators.latex_generator import LaTeXGenerator
from src.generators.latex_compiler import auto_select_compiler, compile_with_retry


def test_complete_pipeline():
    """Test the complete LaTeX generation pipeline"""

    print("="*80)
    print("TESTING LATEX RESUME GENERATION PIPELINE")
    print("="*80)

    # Step 1: Create sample data
    print("\n[1/5] Creating sample resume data...")
    raw_data = create_sample_resume_data()
    print(f"✓ Created data with {len(raw_data['projects'])} projects")

    # Step 2: Transform data
    print("\n[2/5] Transforming data for LaTeX...")
    transformer = LaTeXDataTransformer()

    try:
        latex_data = transformer.transform(raw_data)
        print(f"✓ Transformed data")
        print(f"  - Name: {latex_data['header']['name']}")
        print(f"  - Projects: {len(latex_data['projects'])}")
        print(f"  - Skills categories: {list(latex_data['skills'].keys())}")
    except Exception as e:
        print(f"✗ Transformation failed: {e}")
        return False

    # Step 3: Validate
    print("\n[3/5] Validating transformed data...")
    errors = transformer.validate_output(latex_data)
    if errors:
        print(f"✗ Validation failed: {errors}")
        return False
    print(f"✓ Data validation passed")

    # Step 4: Generate LaTeX
    print("\n[4/5] Rendering LaTeX template...")
    try:
        generator = LaTeXGenerator()
        latex_content = generator.render_resume(latex_data)
        print(f"✓ Generated LaTeX ({len(latex_content)} characters)")

        # Save .tex file
        output_dir = Path(__file__).parent / 'test_output'
        output_dir.mkdir(exist_ok=True)

        tex_path = generator.save_tex_file(latex_content, str(output_dir / 'sample_resume.tex'))
        print(f"✓ Saved: {tex_path}")

    except Exception as e:
        print(f"✗ LaTeX generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Step 5: Compile to PDF
    print("\n[5/5] Compiling LaTeX to PDF...")
    try:
        pdf_path, error = compile_with_retry(str(tex_path))

        if error:
            print(f"✗ Compilation failed: {error}")
            print("\nNote: If Docker/pdflatex not installed, this is expected.")
            print("You can manually compile with: pdflatex sample_resume.tex")
            return False

        print(f"✓ PDF generated: {pdf_path}")

        # Verify PDF size
        pdf_size = Path(pdf_path).stat().st_size
        print(f"  PDF size: {pdf_size:,} bytes")

        if pdf_size < 5000:
            print(f"⚠ Warning: PDF seems too small, may have issues")

    except Exception as e:
        print(f"✗ Compilation error: {e}")
        print("\nIf Docker/pdflatex not installed:")
        print(f"  1. Install Docker: https://docs.docker.com/get-docker/")
        print(f"  2. Or install LaTeX: https://www.latex-project.org/get/")
        print(f"  3. Or manually compile: pdflatex {tex_path}")
        return False

    # Success summary
    print("\n" + "="*80)
    print("✓ END-TO-END TEST PASSED!")
    print("="*80)
    print(f"\nGenerated files:")
    print(f"  LaTeX source: {tex_path}")
    print(f"  PDF output:   {pdf_path}")
    print(f"\nNext steps:")
    print(f"  1. Open {pdf_path} to verify output")
    print(f"  2. Compare with original template styling")
    print(f"  3. Integrate with app.py for production use")

    return True


def test_with_custom_data():
    """Test with your own resume data"""
    print("\n" + "="*80)
    print("TEST WITH CUSTOM DATA")
    print("="*80)

    # Example: Replace with actual AI-generated data structure
    custom_data = {
        'header': {
            'name': 'Your Name Here',
            'location': 'City, State',
            'email': 'your.email@example.com',
            'linkedin': 'linkedin.com/in/yourprofile',
            'github': 'github.com/yourusername'
        },
        'summary': 'Your professional summary here...',
        'skills': {
            'ai_ml': ['Python', 'TensorFlow', 'GPT-4'],
            'product_dev': ['FastAPI', 'Docker'],
            'programming': ['Python', 'SQL', 'Git']
        },
        'education': [
            {
                'institution': 'Your University',
                'degree': 'Master of Science in CS',
                'dates': '2024 - 2026',
                'gpa': '4.0/4.0'
            }
        ],
        'projects': [
            {
                'title': 'Your Project Name',
                'dates': 'Jan 2025 - Present',
                'technologies': 'Python, AI, etc.',
                'bullets': [
                    'Achievement 1 with metrics',
                    'Achievement 2 with impact',
                    'Achievement 3 with results'
                ]
            }
        ],
        'additional': {
            'open_source': 'Your contributions',
            'research': 'Your publications',
            'hackathons': 'Your awards'
        }
    }

    transformer = LaTeXDataTransformer()

    try:
        latex_data = transformer.transform(custom_data)
        generator = LaTeXGenerator()
        latex_content = generator.render_resume(latex_data)

        output_dir = Path(__file__).parent / 'test_output'
        tex_path = generator.save_tex_file(latex_content, str(output_dir / 'custom_resume.tex'))

        print(f"✓ Generated custom resume: {tex_path}")
        print(f"  Compile with: pdflatex {tex_path}")

        return True

    except Exception as e:
        print(f"✗ Custom data test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # Run tests
    success = test_complete_pipeline()

    if success:
        print("\n" + "="*80)
        print("Would you like to test with custom data? (Uncomment below)")
        print("="*80)
        # test_with_custom_data()
