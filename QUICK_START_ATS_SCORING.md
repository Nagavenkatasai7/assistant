# Quick Start Guide - ATS Scoring Engine

## 5-Minute Setup

### 1. Verify Installation

```bash
cd /Users/nagavenkatasaichennu/Library/Mobile\ Documents/com~apple~CloudDocs/Downloads/new_assistant/assistant
python3 -c "from src.scoring.ats_scorer import ATSScorer; print('✅ Installation verified!')"
```

### 2. Run Demo (Optional)

```bash
python3 demo_ats_scorer.py
```

### 3. Run Tests (Optional)

```bash
python3 tests/test_ats_scorer.py
```

---

## Basic Usage

### Score a Resume

```python
from src.scoring.ats_scorer import ATSScorer

# Initialize
scorer = ATSScorer()

# Your resume text
resume = """
John Doe
john@email.com | 555-1234 | San Francisco, CA

PROFESSIONAL SUMMARY
Senior Engineer with 8+ years in Python, AWS, and Docker.

TECHNICAL SKILLS
Python, JavaScript, AWS, Docker, Kubernetes, React

EXPERIENCE
Senior Engineer | TechCorp | 2020-Present
- Developed 10+ microservices
- Led team of 5 engineers
- Reduced costs by 30%

EDUCATION
BS Computer Science | Stanford | 2017
"""

# Job keywords
keywords = ['Python', 'AWS', 'Docker', 'Kubernetes', 'React']

# Score it!
result = scorer.score_resume(
    resume_content=resume,
    job_keywords=keywords,
    file_format='pdf'
)

# Print results
print(f"Score: {result['score']}/100")
print(f"Grade: {result['grade']}")
print(f"Color: {result['color']}")
print(f"Pass Probability: {result['pass_probability']}%")

# Get suggestions
for suggestion in result['top_suggestions'][:3]:
    print(f"- {suggestion}")
```

---

## Integration with Resume Generator

### Automatic Scoring

```python
from src.generators.resume_generator import ResumeGenerator

generator = ResumeGenerator()

# Generate and score automatically
result = generator.generate_resume(
    profile_text=profile_text,
    job_analysis=job_analysis
)

# Access score
score = result['ats_score']['score']
grade = result['ats_score']['grade']
print(f"Generated resume scored {score}/100 ({grade})")
```

### With Retry Logic

```python
# Auto-retry if score < 80
result = generator.generate_resume_with_retry(
    profile_text=profile_text,
    job_analysis=job_analysis,
    min_score=80,      # Minimum acceptable score
    max_retries=2      # Maximum retry attempts
)

print(f"Final Score: {result['ats_score']['score']}")
print(f"Attempts: {result['final_attempt']}")
```

---

## Database Integration

### Store Score with Resume

```python
from src.database.schema import Database

db = Database()

# Store resume with complete score data
resume_id = db.insert_generated_resume_with_score(
    job_description_id=job_id,
    resume_content=resume_text,
    file_path="/path/to/resume.pdf",
    score_data=result  # Full score dict from scorer
)
```

### Retrieve Score Details

```python
# Get detailed score info
score_details = db.get_resume_score_details(resume_id)

print(f"Score: {score_details['ats_score']}")
print(f"Grade: {score_details['ats_grade']}")
print(f"Color: {score_details['ats_color']}")
print(f"Pass Probability: {score_details['pass_probability']}%")
```

### Score History

```python
# Get score history for a job
history = db.get_score_history(job_description_id=job_id, limit=10)

for record in history:
    print(f"{record['created_at']}: {record['ats_score']} ({record['ats_grade']})")
```

---

## Understanding Results

### Score Ranges

| Score | Grade | Color | Meaning | Pass Probability |
|-------|-------|-------|---------|------------------|
| 90-100 | A+, A | 🟢 Green | Excellent | 90-95% |
| 80-89 | A-, B+ | 🟢 Green | Very Good | 85-90% |
| 70-79 | B, B- | 🟡 Yellow | Good | 70-85% |
| 60-69 | C+, C | 🟡 Yellow | Acceptable | 50-70% |
| 0-59 | D, F | 🔴 Red | Needs Work | 25-50% |

### Category Breakdown

```python
result['category_scores']
# Returns:
{
    'content': {
        'score': 35,
        'max': 40,
        'checks': {
            'keyword_match': {...},
            'keyword_density': {...},
            'quantifiable_results': {...},
            'action_verbs': {...},
            'skills_section': {...}
        }
    },
    'format': {...},
    'structure': {...},
    'compatibility': {...}
}
```

---

## Common Issues & Solutions

### Issue: Low Keyword Match Score

```python
# Check what's missing
missing = result['category_scores']['content']['checks']['keyword_match']['details']['missing_keywords']
print(f"Add these keywords: {', '.join(missing[:5])}")
```

**Solution**: Add missing keywords naturally throughout resume.

### Issue: High Keyword Density

```python
density = result['category_scores']['content']['checks']['keyword_density']['details']['keyword_density']
if density > 6:
    print(f"Reduce keyword density from {density}% to 2-4%")
```

**Solution**: Remove duplicate keywords and use synonyms.

### Issue: Missing Sections

```python
missing = result['category_scores']['structure']['missing_sections']
print(f"Add these sections: {', '.join(missing)}")
```

**Solution**: Add EXPERIENCE, EDUCATION, or SKILLS sections.

### Issue: Format Problems

```python
issues = result['category_scores']['format']['issues']
for issue in issues:
    print(f"Fix: {issue}")
```

**Solution**: Remove tables, images, special characters.

---

## Performance Tips

### Quick Check (Fast Validation)

```python
# For real-time feedback during editing
quick_result = scorer.quick_check(resume_text)

print(f"Quick Score: {quick_result['score']}/100")
print(f"Passed: {quick_result['passed']}")
# Processing time: <0.05 seconds
```

### Batch Processing

```python
resumes = [resume1, resume2, resume3]
keywords = ['Python', 'AWS', 'Docker']

results = []
for resume in resumes:
    result = scorer.score_resume(resume, keywords)
    results.append(result)

# Total time: ~0.003s per resume
```

---

## API Reference (Key Methods)

### ATSScorer.score_resume()

```python
def score_resume(
    resume_content: str,           # Resume text
    job_keywords: List[str] = None,  # Job keywords
    required_skills: List[str] = None,  # Required skills
    file_format: str = "pdf",      # File format
    file_size_bytes: int = None    # File size
) -> Dict
```

**Returns**: Complete scoring dictionary with score, grade, color, suggestions, etc.

### ATSScorer.quick_check()

```python
def quick_check(resume_content: str) -> Dict
```

**Returns**: Fast validation with basic score and pass/fail status.

---

## Example Output

```json
{
  "score": 87.5,
  "grade": "B+",
  "color": "green",
  "summary": "Very Good! Your resume is well-optimized for ATS systems...",
  "pass_probability": 85.2,
  "processing_time": 0.002,
  "top_suggestions": [
    "Add 3 more quantifiable metrics",
    "Include missing keywords: Docker, Kubernetes",
    "Use consistent date formatting (MM/YYYY)"
  ],
  "category_scores": {
    "content": {"score": 35, "max": 40},
    "format": {"score": 28, "max": 30},
    "structure": {"score": 17, "max": 20},
    "compatibility": {"score": 8, "max": 10}
  }
}
```

---

## Tips for High Scores

### Content (40 pts)
- ✅ Match 90%+ of job keywords
- ✅ Maintain 2-4% keyword density
- ✅ Include 8+ quantifiable metrics (%, $, numbers)
- ✅ Use 10+ strong action verbs
- ✅ Create skills section with 15-20 skills

### Format (30 pts)
- ✅ No tables or multi-column layouts
- ✅ No images, logos, or graphics
- ✅ No headers/footers with critical info
- ✅ Use standard fonts (Arial, Calibri)
- ✅ Simple bullet points (-, •)
- ✅ Standard section headers

### Structure (20 pts)
- ✅ Include email, phone, location
- ✅ Add LinkedIn profile
- ✅ Format experience with dates and bullets
- ✅ Include education with degree and date
- ✅ Use consistent date format (MM/YYYY)

### Compatibility (10 pts)
- ✅ Use DOCX or PDF format
- ✅ Keep file size under 1MB
- ✅ Avoid special characters (★, •, →)

---

## Getting Help

1. **Documentation**: Read `/src/scoring/README.md`
2. **Tests**: Check `/tests/test_ats_scorer.py` for examples
3. **Demo**: Run `demo_ats_scorer.py` for interactive examples
4. **Code Comments**: All functions have detailed docstrings

---

## Next Steps

1. ✅ Verify installation works
2. ✅ Run demo to see examples
3. ✅ Integrate into your workflow
4. ✅ Test with real resumes
5. ✅ Monitor score improvements

---

**Need more details?** See:
- Full documentation: `/src/scoring/README.md`
- Implementation summary: `ATS_SCORING_IMPLEMENTATION_SUMMARY.md`
- Test suite: `/tests/test_ats_scorer.py`
