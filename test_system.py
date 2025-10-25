"""
System test script to verify all components are working
"""
import os
from pathlib import Path

def test_environment():
    """Test environment setup"""
    print("🔍 Testing Environment...")

    checks = []

    # Check Python version
    import sys
    python_version = sys.version_info
    if python_version >= (3, 8):
        checks.append(("✓", f"Python {python_version.major}.{python_version.minor}"))
    else:
        checks.append(("✗", f"Python {python_version.major}.{python_version.minor} (need 3.8+)"))

    # Check API keys
    from dotenv import load_dotenv
    load_dotenv()

    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    perplexity_key = os.getenv("PERPLEXITY_API_KEY")

    if anthropic_key:
        checks.append(("✓", "Anthropic API key configured"))
    else:
        checks.append(("✗", "Anthropic API key missing"))

    if perplexity_key:
        checks.append(("✓", "Perplexity API key configured"))
    else:
        checks.append(("ℹ", "Perplexity API key not set (optional)"))

    # Check Profile.pdf
    if Path("Profile.pdf").exists():
        checks.append(("✓", "Profile.pdf found"))
    else:
        checks.append(("✗", "Profile.pdf not found"))

    # Check knowledge base
    if Path("ats_knowledge_base.md").exists():
        checks.append(("✓", "ATS knowledge base exists"))
    else:
        checks.append(("✗", "ATS knowledge base not found"))

    for status, message in checks:
        print(f"  {status} {message}")

    return all(status == "✓" or status == "ℹ" for status, _ in checks)

def test_imports():
    """Test all required imports"""
    print("\n📦 Testing Imports...")

    imports = [
        ("streamlit", "Streamlit"),
        ("anthropic", "Anthropic SDK"),
        ("pypdf", "PyPDF"),
        ("reportlab", "ReportLab"),
        ("requests", "Requests"),
        ("dotenv", "Python-dotenv"),
    ]

    all_good = True
    for module, name in imports:
        try:
            __import__(module)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} not installed")
            all_good = False

    return all_good

def test_components():
    """Test custom components"""
    print("\n🧩 Testing Components...")

    try:
        from src.database import Database
        print("  ✓ Database module")

        from src.parsers import ProfileParser
        print("  ✓ Profile parser")

        from src.analyzers import JobAnalyzer
        print("  ✓ Job analyzer")

        from src.utils import PerplexityClient
        print("  ✓ Perplexity client")

        from src.generators import ResumeGenerator
        print("  ✓ Resume generator")

        from src.generators.pdf_generator import PDFGenerator
        print("  ✓ PDF generator")

        return True
    except Exception as e:
        print(f"  ✗ Component import failed: {e}")
        return False

def test_database():
    """Test database initialization"""
    print("\n💾 Testing Database...")

    try:
        from src.database import Database
        db = Database("test_resume.db")
        print("  ✓ Database initialized")

        # Clean up
        if Path("test_resume.db").exists():
            Path("test_resume.db").unlink()
            print("  ✓ Test database cleaned up")

        return True
    except Exception as e:
        print(f"  ✗ Database test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 Ultra ATS Resume Generator - System Test")
    print("=" * 60)

    env_ok = test_environment()
    imports_ok = test_imports()
    components_ok = test_components()
    db_ok = test_database()

    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)

    all_tests = [
        ("Environment", env_ok),
        ("Imports", imports_ok),
        ("Components", components_ok),
        ("Database", db_ok)
    ]

    for test_name, result in all_tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")

    print("\n" + "=" * 60)

    if all(result for _, result in all_tests):
        print("🎉 All tests passed! System is ready.")
        print("\nTo start the application, run:")
        print("  streamlit run app.py")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  - Install missing packages: pip install -r requirements.txt")
        print("  - Add API keys to .env file")
        print("  - Add Profile.pdf to project directory")
        print("  - Run analyze_ats_knowledge.py to generate knowledge base")

    print("=" * 60)

if __name__ == "__main__":
    main()
