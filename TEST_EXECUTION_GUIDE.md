# Test Execution Guide
## Step-by-Step Instructions for Production Readiness Testing

**Document Version**: 1.0
**Last Updated**: 2025-11-12
**Estimated Time**: 16-20 hours (4-5 days)

---

## Quick Start

### Prerequisites Checklist

Before starting any tests, verify:

```bash
# 1. Check API Keys
echo "Kimi API Key: ${KIMI_API_KEY:0:10}... [${#KIMI_API_KEY} chars]"
echo "Tavily API Key: ${TAVILY_API_KEY:0:10}... [${#TAVILY_API_KEY} chars]"

# 2. Check Profile.pdf
ls -lh Profile.pdf

# 3. Check database
sqlite3 resume_generator.db "SELECT COUNT(*) FROM generated_resumes;"

# 4. Check Python environment
python --version  # Should be 3.9+
pip list | grep -E "streamlit|anthropic|tavily"

# 5. Check disk space
df -h . | tail -1
```

**Expected Output:**
- ✅ Both API keys present and non-empty
- ✅ Profile.pdf exists (size > 100KB)
- ✅ Database accessible
- ✅ Python 3.9+
- ✅ All packages installed
- ✅ >1GB free disk space

---

## Day 1: Unit Tests + Integration Tests (8 hours)

### Morning Session (4 hours): Unit Tests

#### Step 1: Kimi K2 Client Tests (30 min)

**Test ID**: UT-KIMI-001 to UT-KIMI-004

**Execute:**
```bash
cd /path/to/assistant
python -m pytest tests/test_production_readiness.py::TestProductionReadiness::test_kimi_client_initialization -v
python -m pytest tests/test_production_readiness.py::TestProductionReadiness::test_kimi_chat_completion -v
```

**Expected Results:**
- ✅ Client initializes successfully
- ✅ Chat completion returns valid response
- ✅ Token usage tracked
- ✅ Response time < 30s

**If Tests Fail:**
1. Check KIMI_API_KEY is valid
2. Check network connectivity to api.moonshot.cn
3. Check API rate limits
4. See Troubleshooting section

**Log Results:**
```
[ ] UT-KIMI-001: PASS / FAIL
    - Notes: _________________________________
    - Duration: ______s

[ ] UT-KIMI-002: PASS / FAIL
    - Token usage: ______
    - Duration: ______s
```

---

#### Step 2: Tavily Client Tests (30 min)

**Test ID**: UT-TAVILY-001 to UT-TAVILY-003

**Execute:**
```bash
python -m pytest tests/test_production_readiness.py::TestProductionReadiness::test_tavily_client_initialization -v
python -m pytest tests/test_production_readiness.py::TestProductionReadiness::test_tavily_search_functionality -v
python -m pytest tests/test_production_readiness.py::TestProductionReadiness::test_tavily_company_research -v
```

**CRITICAL CHECK**: Verify Tavily API is actually being called!

**Expected Results:**
- ✅ Client initializes successfully
- ✅ Search returns results
- ✅ Company research returns summary and insights
- ✅ Sources included

**Validation Checklist:**
```
[ ] Tavily API key valid
[ ] Search returns 3+ results
[ ] Company research summary length > 100 chars
[ ] Key insights list not empty
[ ] Sources list contains URLs
[ ] Response time < 5s
```

**If Tests Fail:**
1. Check TAVILY_API_KEY is valid
2. Check network connectivity
3. Check API quota (Tavily dashboard)
4. See Troubleshooting section

---

#### Step 3: ATS Scorer Tests (30 min)

**Test ID**: UT-ATS-001 to UT-ATS-002

**Execute:**
```bash
python -m pytest tests/test_production_readiness.py::TestProductionReadiness::test_ats_scorer_initialization -v
python -m pytest tests/test_production_readiness.py::TestProductionReadiness::test_ats_scorer_accuracy -v
```

**Expected Results:**
- ✅ Scorer initializes successfully
- ✅ High-quality resume scores >= 70
- ✅ Score calculation consistent
- ✅ Processing time < 1s

**Validation Checklist:**
```
[ ] Score range: 0-100
[ ] Grade assigned correctly
[ ] Color coding correct (green/yellow/red)
[ ] Top suggestions provided
[ ] Pass probability calculated
```

---

#### Step 4: Resume Structure Validation (30 min)

**Test ID**: FT-STRUCT-001

**Execute:**
```bash
python -m pytest tests/test_production_readiness.py::TestProductionReadiness::test_resume_structure_validation -v
```

**CRITICAL VALIDATION**: This test ensures EVERY resume has ALL required sections.

**Expected Results:**
- ✅ Header with email
- ✅ Header with phone
- ✅ Header with LinkedIn (clickable)
- ✅ Header with GitHub (clickable)
- ✅ Header with Portfolio (clickable)
- ✅ Professional Summary section
- ✅ Technical Skills section
- ✅ Professional Experience section
- ✅ Education section (MANDATORY)

**Manual Verification:**
Open generated resume and check:
```
[ ] Name present
[ ] Email format valid
[ ] Phone: +1 571-546-6207
[ ] LinkedIn URL present
[ ] GitHub URL present
[ ] Portfolio URL present
[ ] All sections have content (not just headers)
```

---

### Afternoon Session (4 hours): Integration Tests

#### Step 5: End-to-End Flow (90 min)

**Test ID**: IT-E2E-001

**Execute:**
```bash
python -m pytest tests/test_production_readiness.py::TestProductionReadiness::test_end_to_end_resume_generation -v --tb=short
```

**This is the MOST IMPORTANT test!** It tests the complete workflow:

```
Input → Parse Profile → Analyze Job → Research Company → Generate Resume → Score Resume → Generate PDF
```

**Expected Flow:**
1. Profile parsing: 2-5s
2. Job analysis: 5-10s
3. Company research (Tavily): 3-5s
4. Resume generation (Kimi K2): 20-30s
5. ATS scoring: 0.5-1s
6. PDF generation: 2-4s
7. **Total: 40-60s**

**Validation Checklist:**
```
[ ] Profile parsed successfully
[ ] Job analysis contains keywords
[ ] Company research returned (summary, insights, sources)
[ ] Resume content generated
[ ] All required sections present in resume
[ ] ATS score >= 85
[ ] PDF file created
[ ] PDF file size > 0
[ ] Total time < 120s
```

**If Test Fails:**
Identify which step failed:
- Profile parsing → Check Profile.pdf
- Job analysis → Check Kimi K2 API
- Company research → Check Tavily API
- Resume generation → Check Kimi K2 API and prompt
- Scoring → Check ATS scorer
- PDF generation → Check ReportLab

---

#### Step 6: Tavily Integration Verification (90 min)

**Test ID**: IT-TAVILY-001

**CRITICAL TEST**: This proves Tavily is actually being used!

**Execute:**
```bash
python -m pytest tests/test_production_readiness.py::TestProductionReadiness::test_tavily_integration_verification -v
```

**What This Test Does:**
1. Generates Resume A: WITH Tavily research
2. Generates Resume B: WITHOUT Tavily research
3. Compares the two resumes

**Expected Results:**
- ✅ Resume A and Resume B are DIFFERENT
- ✅ Resume A is longer than Resume B
- ✅ Resume A mentions company-specific details
- ✅ Research summary has content
- ✅ Key insights returned
- ✅ Sources included

**Critical Validation:**

Open both generated resumes and manually verify:

```markdown
Resume A (WITH Tavily):
- Professional summary mentions company culture/values
- Experience bullets tailored to company
- Skills emphasize company tech stack
- Overall tone fits company culture

Resume B (WITHOUT Tavily):
- More generic content
- Less company-specific tailoring
- Standard experience bullets
```

**Document Evidence:**
```
Tavily Research Summary:
_____________________________________________
_____________________________________________

Evidence in Resume A:
_____________________________________________
_____________________________________________

Length Difference: _______ chars
Conclusion: Tavily IS / IS NOT being used
```

---

#### Step 7: Error Handling (60 min)

**Test ID**: IT-ERROR-001

**Execute:**
```bash
python -m pytest tests/test_production_readiness.py::TestProductionReadiness::test_error_handling_integration -v
```

**Scenarios Tested:**
1. Short job description (edge case)
2. No company research (Tavily unavailable)
3. API timeouts
4. Database errors

**Expected Results:**
- ✅ System handles errors gracefully
- ✅ User sees clear error messages
- ✅ No crashes or exceptions
- ✅ Retry logic works for transient errors

---

## Day 2: Functional Tests (8 hours)

### Morning Session (4 hours): Core Functionality

#### Step 8: ATS Score Validation (90 min)

**Test ID**: FT-ATS-001

**TARGET**: 90%+ ATS score for all resumes

**Execute:**
```bash
python -m pytest tests/test_production_readiness.py::TestProductionReadiness::test_ats_score_validation -v
```

**Test Multiple Job Types:**

1. **Technical Role (Google Software Engineer)**
```bash
# Generate resume for Google SWE job
# Expected ATS Score: 90-100
```

2. **Business Role (Microsoft Product Manager)**
```bash
# Generate resume for Microsoft PM job
# Expected ATS Score: 90-100
```

3. **Data Role (Amazon Data Scientist)**
```bash
# Generate resume for Amazon DS job
# Expected ATS Score: 90-100
```

**Score Breakdown Analysis:**

For each resume, document:
```
Job: ____________________
Company: ____________________

ATS Score: _____/100
Grade: _____
Color: _____
Pass Probability: _____%

Category Scores:
- Content (40 pts): _____
  - Keyword match: _____/15
  - Keyword density: _____/10
  - Quantifiable results: _____/5
  - Action verbs: _____/5
  - Skills section: _____/5

- Format (30 pts): _____
  - No tables/columns: _____
  - Clean formatting: _____
  - Standard headers: _____

- Structure (20 pts): _____
  - Required sections: _____
  - Contact info: _____
  - Dates formatted: _____

- Compatibility (10 pts): _____
  - File format: _____
  - File size: _____

Top Suggestions:
1. _________________________________
2. _________________________________
3. _________________________________

Conclusion: PASS / FAIL (Target: >= 90)
```

**If Score < 90:**
1. Review top suggestions
2. Regenerate resume with improvements
3. Re-score
4. Document improvements made

---

#### Step 9: Link Functionality (60 min)

**Test ID**: FT-LINK-001

**CRITICAL REQUIREMENT**: All links must be clickable!

**Execute:**
```bash
python -m pytest tests/test_production_readiness.py::TestProductionReadiness::test_link_functionality_validation -v
```

**Manual Verification Steps:**

1. **Generate test resume**
2. **Open PDF in Adobe Reader / Preview**
3. **Click each link:**

```
Link Functionality Checklist:

[ ] LinkedIn link present in header
[ ] LinkedIn link is clickable (cursor changes to hand)
[ ] LinkedIn link opens correct profile URL
[ ] GitHub link present in header
[ ] GitHub link is clickable
[ ] GitHub link opens correct profile URL
[ ] Portfolio link present in header
[ ] Portfolio link is clickable
[ ] Portfolio link opens correct website

Evidence:
- Screenshot of PDF header: _____________
- Link destinations verified: YES / NO
- All links functional: YES / NO
```

**Test Multiple PDF Viewers:**
```
[ ] Adobe Acrobat Reader: Links work
[ ] macOS Preview: Links work
[ ] Chrome PDF viewer: Links work
[ ] Firefox PDF viewer: Links work
```

**If Links NOT Clickable:**
This is a PRODUCTION BLOCKER. Document:
1. Which PDF viewer used
2. Whether links are present in text
3. Whether links have underlines
4. Whether cursor changes when hovering
5. ReportLab version: `pip show reportlab`

---

### Afternoon Session (4 hours): Templates & Edge Cases

#### Step 10: Template Validation (60 min)

**Test ID**: FT-TEMPLATE-001

**Test All 3 Templates:**

1. **Modern Template**
```bash
# Generate with template='modern'
# Expected: Two-column layout, ATS score 95-100
```

2. **Harvard Template**
```bash
# Generate with template='harvard'
# Expected: Traditional format, ATS score 98-100
```

3. **Original Template**
```bash
# Generate with template='original'
# Expected: Simple format, ATS score 85-90
```

**Template Comparison Matrix:**

| Feature | Modern | Harvard | Original |
|---------|--------|---------|----------|
| Layout | Two-column | Single-column | Single-column |
| ATS Score | 95-100 | 98-100 | 85-90 |
| Links Clickable | YES/NO | YES/NO | YES/NO |
| All Sections | YES/NO | YES/NO | YES/NO |
| File Size | ___KB | ___KB | ___KB |
| Generation Time | ___s | ___s | ___s |

**Recommendation**: Which template is best for production?
```
Recommended Template: _______________
Reason: _________________________________
```

---

#### Step 11: Edge Cases (60 min)

**Test Edge Cases:**

1. **Very Long Job Description (5000+ words)**
```
Expected: Resume still generated
ATS Score: Should not degrade
```

2. **Very Short Job Description (50 words)**
```
Expected: Graceful handling
Warning shown: YES / NO
```

3. **Job Description with Special Characters**
```
Expected: Characters handled correctly
Resume generated: YES / NO
```

4. **Multiple Concurrent Requests (5 users)**
```
Expected: All resumes generated
No database locks: YES / NO
```

---

## Day 3: Production Readiness Tests (6 hours)

### Morning Session (3 hours): Load & Performance

#### Step 12: Load Testing (120 min)

**Test ID**: PR-LOAD-001

**Scenarios:**

**Scenario 1: Sequential Load (20 resumes)**
```bash
# Generate 20 resumes one after another
# Monitor: Response time, memory, errors
```

Expected Results:
```
[ ] All 20 resumes generated successfully
[ ] Average response time: _____s
[ ] Response time degradation < 20%
[ ] Memory usage stable (no leaks)
[ ] No database errors
```

**Scenario 2: Concurrent Load (5 users)**
```bash
# Simulate 5 concurrent resume generations
# Use threading or multiprocessing
```

Expected Results:
```
[ ] All 5 resumes completed
[ ] No race conditions
[ ] No database locks
[ ] Average time: _____s (acceptable: <75s)
```

**Scenario 3: Database Connection Pool**
```bash
# Generate 15 resumes in rapid succession
# Pool size: 10 connections
```

Expected Results:
```
[ ] Connection pool handles load
[ ] No connection exhaustion
[ ] All queries complete
```

---

#### Step 13: Performance Benchmarks (60 min)

**Test ID**: PR-PERF-001

**Benchmark Each Component:**

```bash
python -m pytest tests/test_production_readiness.py::TestProductionReadiness::test_performance_benchmarks -v
```

**Record Results:**

| Component | Target | Actual | Status |
|-----------|--------|--------|--------|
| Profile Parsing | <5s | ___s | PASS/FAIL |
| Job Analysis | <10s | ___s | PASS/FAIL |
| Tavily Research | <5s | ___s | PASS/FAIL |
| Resume Generation | <30s | ___s | PASS/FAIL |
| ATS Scoring | <1s | ___s | PASS/FAIL |
| PDF Generation | <5s | ___s | PASS/FAIL |
| **Total E2E** | **<60s** | **___s** | **PASS/FAIL** |

**Performance Optimization Notes:**
```
Bottlenecks identified:
1. _________________________________
2. _________________________________

Optimization opportunities:
1. _________________________________
2. _________________________________
```

---

### Afternoon Session (3 hours): Cost & Error Recovery

#### Step 14: Cost Monitoring (30 min)

**Test ID**: PR-COST-001

**Calculate Costs:**

Generate 10 resumes and calculate total cost:

```
Cost Per Resume:
- Kimi K2 API: ~_______ tokens × $0.002/1K = $_______
- Tavily API: ~$0.01-0.05 per search = $_______
- Total: $_______

Cost for 100 Resumes:
- Estimated: $_______ × 100 = $_______

Monthly Cost (1000 resumes):
- Estimated: $_______ × 1000 = $_______
```

**Cost Validation:**
```
[ ] Token usage logged correctly
[ ] Cost estimates reasonable
[ ] No unexpected charges
[ ] Cost tracking in database
```

---

#### Step 15: Error Recovery (90 min)

**Test ID**: PR-ERROR-001

**Test Scenarios:**

**1. API Timeout**
```bash
# Mock Kimi K2 timeout
# Expected: Retry with exponential backoff
# Max retries: 3
```

Results:
```
[ ] Timeout detected
[ ] Retry 1: _____s delay
[ ] Retry 2: _____s delay
[ ] Retry 3: _____s delay
[ ] Eventually succeeded / Failed gracefully
```

**2. API Rate Limit**
```bash
# Trigger rate limit
# Expected: Clear error message
```

Results:
```
[ ] Rate limit detected
[ ] User notified with clear message
[ ] Retry time displayed
[ ] No crash
```

**3. Database Lock**
```bash
# Simulate concurrent write
# Expected: Transaction retry
```

Results:
```
[ ] Lock detected
[ ] Retry logic executed
[ ] Transaction eventually completed
```

**4. Low Disk Space**
```bash
# Mock low disk space
# Expected: Error before operation
```

Results:
```
[ ] Disk space check executed
[ ] Error caught before PDF generation
[ ] User notified
```

---

## Day 4: Bug Fixing & Regression (8 hours)

### Bug Review & Prioritization (2 hours)

**Review All Test Results:**

```
Total Tests Run: _______
Tests Passed: _______
Tests Failed: _______
Pass Rate: _______%

Critical Bugs (P0 - Blocker):
1. _________________________________
2. _________________________________

High Priority Bugs (P1 - Critical):
1. _________________________________
2. _________________________________

Medium Priority Bugs (P2 - High):
1. _________________________________
2. _________________________________
```

**Prioritization:**
1. Fix all P0 bugs first (production blockers)
2. Fix all P1 bugs (critical functionality)
3. Fix P2 bugs if time permits

---

### Bug Fixing Iteration (4 hours)

For each bug:

**1. Document Bug**
```
Bug ID: BUG-___
Severity: P0 / P1 / P2
Test Case: _______
Description: _________________________________

Steps to Reproduce:
1. _________________________________
2. _________________________________
3. _________________________________

Expected: _________________________________
Actual: _________________________________
```

**2. Fix Bug**
```
Root Cause: _________________________________
Fix Applied: _________________________________
Code Changed: _________________________________
```

**3. Verify Fix**
```bash
# Re-run failing test
python -m pytest tests/test_production_readiness.py::<TestName> -v
```

**4. Regression Test**
```bash
# Run full suite to ensure no new bugs
python -m pytest tests/test_production_readiness.py -v
```

---

### Final Regression Suite (2 hours)

**Run ALL Tests One Final Time:**

```bash
python -m pytest tests/test_production_readiness.py -v --tb=short > test_results_final.txt 2>&1
```

**Final Results:**
```
Total Tests: _______
Passed: _______
Failed: _______
Skipped: _______

Pass Rate: _______%

P0 Bugs: _______ (Target: 0)
P1 Bugs: _______ (Target: 0)
P2 Bugs: _______ (Target: <3)
```

---

## Production Readiness Decision

### Go / No-Go Criteria

**Functional Requirements:**
```
[ ] All resumes achieve 90%+ ATS score
[ ] 100% resume structure completeness
[ ] LinkedIn, GitHub, Portfolio links clickable
[ ] Tavily integration verified (actively used)
[ ] All templates work correctly
[ ] Education section always present
```

**Technical Requirements:**
```
[ ] Kimi K2 API working (with retry)
[ ] Tavily API working (with error handling)
[ ] Database operations successful
[ ] Connection pooling works
[ ] PDF links clickable
[ ] ATS scoring accurate
```

**Performance Requirements:**
```
[ ] End-to-end < 60s
[ ] ATS scoring < 1s
[ ] Handles 5 concurrent users
[ ] No memory leaks
```

**Quality Requirements:**
```
[ ] 100% unit test pass rate
[ ] 100% integration test pass rate
[ ] 100% functional test pass rate
[ ] 100% production test pass rate
[ ] 0 P0 bugs
[ ] 0 P1 bugs
[ ] <3 P2 bugs
```

### Final Decision

```
Production Readiness: [ ] APPROVED  [ ] REJECTED

Decision Date: _______________
Approved By: _______________

Comments:
_________________________________________
_________________________________________
_________________________________________

Next Steps:
_________________________________________
_________________________________________
_________________________________________
```

---

## Troubleshooting

### Common Issues

**Issue 1: Kimi K2 API Timeout**
```
Symptoms: Request takes >120s, timeout error
Solutions:
1. Check network connectivity: ping api.moonshot.cn
2. Check API status: Visit Moonshot dashboard
3. Increase timeout: Set timeout=180 in config
4. Check rate limits
```

**Issue 2: Tavily Returns Empty Results**
```
Symptoms: research_result['success'] = False
Solutions:
1. Check API key: echo $TAVILY_API_KEY
2. Check quota: Visit Tavily dashboard
3. Test with simple query: "Google company"
4. Check network: curl https://api.tavily.com
```

**Issue 3: ATS Score < 90**
```
Symptoms: Generated resumes score 80-89
Solutions:
1. Review top_suggestions from scorer
2. Check keyword match percentage
3. Verify all sections present
4. Check job description has enough keywords
5. Regenerate resume with improvements
```

**Issue 4: Links Not Clickable in PDF**
```
Symptoms: Links visible but not clickable
Solutions:
1. Check ReportLab version: pip show reportlab
2. Verify URL extraction in resume_generator.py
3. Check PDF annotations with PyPDF2
4. Test with different PDF viewers
5. Check EnhancedPDFGenerator link embedding code
```

**Issue 5: Database Lock Errors**
```
Symptoms: "database is locked" error
Solutions:
1. Check concurrent access
2. Verify connection pool size
3. Add retry logic with exponential backoff
4. Check for long-running transactions
```

---

## Test Data & Artifacts

### Save Test Artifacts

After testing, save:
```
test_results/
├── test_results_final.txt
├── test_resumes/
│   ├── resume_google_swe.pdf
│   ├── resume_microsoft_pm.pdf
│   └── resume_amazon_ds.pdf
├── ats_scores/
│   ├── google_swe_score.json
│   ├── microsoft_pm_score.json
│   └── amazon_ds_score.json
├── performance_benchmarks.txt
├── cost_analysis.txt
└── bug_report.md
```

---

## Appendix: Quick Commands

**Run all tests:**
```bash
python -m pytest tests/test_production_readiness.py -v
```

**Run specific test:**
```bash
python -m pytest tests/test_production_readiness.py::TestProductionReadiness::test_end_to_end_resume_generation -v
```

**Run with verbose output:**
```bash
python -m pytest tests/test_production_readiness.py -v --tb=short
```

**Generate coverage report:**
```bash
pytest tests/test_production_readiness.py --cov=src --cov-report=html
```

**Check database:**
```bash
sqlite3 resume_generator.db "SELECT * FROM generated_resumes ORDER BY created_at DESC LIMIT 5;"
```

---

**End of Test Execution Guide**

**Next Steps**: Follow this guide step-by-step, document all results, and make the production readiness decision based on the criteria above.
