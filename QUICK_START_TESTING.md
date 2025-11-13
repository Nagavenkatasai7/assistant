# Quick Start Guide - Production Testing

## ATS Resume Generator - 5-Minute Quick Start

---

## Before You Start

**Required:**
```bash
✅ Profile.pdf exists
✅ KIMI_API_KEY set in .env
✅ TAVILY_API_KEY set in .env
✅ Python 3.9+
✅ All packages installed (pip install -r requirements.txt)
```

**Check Environment:**
```bash
./run_production_tests.sh
```

---

## Option 1: Quick Test (15 minutes)

**Best for:** Initial validation

```bash
# Run automated quick tests
./run_production_tests.sh
# Select: 1

# Tests run:
# ✅ Kimi K2 initialization
# ✅ Tavily initialization
# ✅ ATS scorer accuracy
# ✅ Resume structure validation
# ✅ ATS score validation

# Expected: All tests PASS
```

---

## Option 2: Full Test (2 hours)

**Best for:** Complete validation

```bash
# Run full automated test suite
./run_production_tests.sh
# Select: 2

# Tests all:
# - Unit tests (30 min)
# - Integration tests (30 min)
# - Functional tests (45 min)
# - Performance tests (15 min)

# Expected: 100% pass rate
```

---

## Option 3: Manual Test (1 hour)

**Best for:** Understanding the system

### Step 1: Test Kimi K2 (5 min)
```bash
python -c "
from src.clients.kimi_client import KimiK2Client
client = KimiK2Client()
result = client.chat_completion(
    messages=[{'role': 'user', 'content': 'Say hello'}],
    timeout=30.0
)
print('✅ Kimi K2 works!' if result['success'] else '❌ Failed')
"
```

### Step 2: Test Tavily (5 min)
```bash
python -c "
from src.clients.tavily_client import TavilyClient
client = TavilyClient()
result = client.research_company('Google', focus_areas=['culture'])
print('✅ Tavily works!' if result['success'] else '❌ Failed')
print(f'Research length: {len(result.get(\"summary\", \"\"))} chars')
"
```

### Step 3: Generate Test Resume (45 min)
```python
# Run in Python shell
from src.parsers.profile_parser import ProfileParser
from src.analyzers.job_analyzer import JobAnalyzer
from src.generators.resume_generator import ResumeGenerator
from src.generators.pdf_generator_enhanced import EnhancedPDFGenerator
from src.scoring.ats_scorer_enhanced import EnhancedATSScorer
from src.clients.tavily_client import TavilyClient

# 1. Parse profile
parser = ProfileParser()
profile = parser.get_profile_summary()
print(f"✅ Profile parsed: {len(profile)} chars")

# 2. Analyze job
job_desc = "Software Engineer at Google. Skills: Python, Docker, AWS."
analyzer = JobAnalyzer()
job_analysis = analyzer.analyze_job_description(job_desc, "Google")
print(f"✅ Job analyzed: {len(job_analysis.get('keywords', []))} keywords")

# 3. Research company
tavily = TavilyClient()
research = tavily.research_company("Google", focus_areas=['culture', 'tech'])
print(f"✅ Research: {len(research.get('summary', ''))} chars")

# 4. Generate resume
generator = ResumeGenerator()
resume_result = generator.generate_resume(
    profile,
    job_analysis,
    {'research': research.get('summary', ''),
     'key_insights': research.get('key_insights', []),
     'sources': research.get('sources', [])}
)
print(f"✅ Resume generated: {len(resume_result['content'])} chars")

# 5. Score resume
scorer = EnhancedATSScorer()
score = scorer.score_resume(
    resume_result['content'],
    job_analysis.get('keywords', []),
    job_analysis.get('required_skills', []),
    'pdf',
    'modern'
)
print(f"✅ ATS Score: {score['score']:.1f}/100 (Target: 90+)")

# 6. Generate PDF
pdf_gen = EnhancedPDFGenerator()
pdf_gen.set_template('modern')
pdf_gen.markdown_to_pdf(resume_result['content'], 'test_resume.pdf')
print("✅ PDF generated: test_resume.pdf")

# 7. Verify
print("\n" + "="*60)
print("MANUAL VERIFICATION REQUIRED:")
print("="*60)
print("1. Open test_resume.pdf")
print("2. Check all sections present")
print("3. Click LinkedIn link (should open browser)")
print("4. Click GitHub link (should open browser)")
print("5. Click Portfolio link (should open browser)")
print("6. Verify ATS score >= 90")
```

### Step 4: Manual Validation Checklist
```
[ ] PDF opens successfully
[ ] All sections present:
    [ ] Header with name, email, phone
    [ ] LinkedIn link (clickable)
    [ ] GitHub link (clickable)
    [ ] Portfolio link (clickable)
    [ ] Professional Summary
    [ ] Technical Skills
    [ ] Professional Experience
    [ ] Education
[ ] ATS Score >= 90
[ ] Resume content looks professional
[ ] Company research incorporated (mentions Google culture)
```

---

## Critical Validations (MUST DO)

### 1. ATS Score Check
```bash
# Generate and score resume
python tests/test_production_readiness.py::TestProductionReadiness::test_ats_score_validation -v

# Expected: Score >= 90
```

### 2. Link Functionality Check
```bash
# Generate PDF with links
python tests/test_production_readiness.py::TestProductionReadiness::test_link_functionality_validation -v

# Manual: Open PDF, click all links
```

### 3. Tavily Integration Check
```bash
# Verify Tavily is actually used
python tests/test_production_readiness.py::TestProductionReadiness::test_tavily_integration_verification -v

# Expected: Resumes WITH and WITHOUT Tavily differ
```

### 4. End-to-End Check
```bash
# Full workflow test
python tests/test_production_readiness.py::TestProductionReadiness::test_end_to_end_resume_generation -v

# Expected: Complete in < 60s, all steps pass
```

---

## Production Readiness Checklist

**Quick Validation (5 minutes):**
```
[ ] Kimi K2 API responds
[ ] Tavily API responds
[ ] Database accessible
[ ] Profile.pdf readable
[ ] Test resume generates
```

**Critical Validation (30 minutes):**
```
[ ] ATS score >= 90
[ ] All resume sections present
[ ] LinkedIn link clickable
[ ] GitHub link clickable
[ ] Portfolio link clickable
[ ] Tavily research incorporated
[ ] Generation time < 60s
```

**Production Sign-Off:**
```
[ ] All unit tests pass (100%)
[ ] All integration tests pass (100%)
[ ] All functional tests pass (100%)
[ ] 0 P0 (blocker) bugs
[ ] 0 P1 (critical) bugs
[ ] <3 P2 (high) bugs
[ ] Performance benchmarks met
[ ] Cost per resume < $0.05
```

---

## Troubleshooting

### Issue: Tests won't run
```bash
# Check Python
python --version  # Should be 3.9+

# Check packages
pip install -r requirements.txt

# Check API keys
echo $KIMI_API_KEY
echo $TAVILY_API_KEY
```

### Issue: Kimi K2 timeout
```bash
# Increase timeout in config.py
API_TIMEOUT_SECONDS = 180
```

### Issue: Tavily returns empty
```bash
# Check API key validity
curl -X POST https://api.tavily.com/search \
  -H "Authorization: Bearer $TAVILY_API_KEY" \
  -d '{"query": "test"}'
```

### Issue: ATS score < 90
```
1. Check score breakdown
2. Review top_suggestions
3. Add missing keywords
4. Verify all sections present
5. Regenerate resume
```

### Issue: Links not clickable
```
1. Check ReportLab version: pip show reportlab
2. Try different PDF viewer
3. Check URL extraction in resume_generator.py
4. Verify EnhancedPDFGenerator link code
```

---

## Test Results Location

```
test_results/
├── quick_tests_<timestamp>.txt      # Quick test results
├── full_tests_<timestamp>.txt       # Full test results
└── test_summary_<timestamp>.txt     # Summary report

test_output/
├── test_resume.pdf                  # Generated test resume
└── test_links.pdf                   # Link functionality test
```

---

## Next Steps After Testing

**If All Tests Pass:**
1. ✅ Review generated PDFs manually
2. ✅ Verify ATS scores >= 90
3. ✅ Check links are clickable
4. ✅ Sign production readiness document
5. ✅ Deploy to production

**If Tests Fail:**
1. ❌ Review test output
2. ❌ Document bugs in BUG_TRACKING_TEMPLATE.md
3. ❌ Fix bugs in priority order (P0 → P1 → P2)
4. ❌ Re-run tests
5. ❌ Iterate until 100% pass rate

---

## Quick Commands Reference

```bash
# Run all tests
python -m pytest tests/test_production_readiness.py -v

# Run specific test
python -m pytest tests/test_production_readiness.py::TestProductionReadiness::test_ats_score_validation -v

# Run with coverage
pytest tests/test_production_readiness.py --cov=src --cov-report=html

# Check database
sqlite3 resume_generator.db "SELECT * FROM generated_resumes LIMIT 5;"

# Clear test artifacts
rm -rf test_output/* test_results/*

# Make script executable
chmod +x run_production_tests.sh
```

---

## Documentation Files

- **TESTING_SUMMARY.md** - Executive overview (this is your main guide)
- **PRODUCTION_READINESS_TEST_PLAN.md** - Detailed 80-page test plan
- **TEST_EXECUTION_GUIDE.md** - Step-by-step instructions
- **BUG_TRACKING_TEMPLATE.md** - Bug documentation
- **tests/test_production_readiness.py** - Automated test suite
- **run_production_tests.sh** - Test runner script

---

## Time Requirements

| Test Type | Duration |
|-----------|----------|
| Quick Test | 15 minutes |
| Full Automated | 2 hours |
| Manual Test | 1 hour |
| Full Test Plan | 4-5 days |

---

## Success Metrics

**Pass Criteria:**
- Test pass rate: 100%
- ATS score: >= 90
- Generation time: < 60s
- Bug count: 0 P0, 0 P1, <3 P2

**Production Ready:**
- All tests pass ✅
- All bugs fixed ✅
- Manual verification complete ✅
- Performance meets SLA ✅
- Sign-off obtained ✅

---

## Getting Help

1. Check **troubleshooting** section above
2. Review **PRODUCTION_READINESS_TEST_PLAN.md** for details
3. Check **test logs** in `test_results/`
4. Review **error messages** carefully
5. Document **bugs** using BUG_TRACKING_TEMPLATE.md

---

**Start Here:** `./run_production_tests.sh`

**Good luck!** 🚀
