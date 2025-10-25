# 🚀 Quick Start Guide

## Ultra ATS Resume Generator

### ⚡ 3-Step Launch

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Keys**
   - Your API keys are already in `.env`
   - Anthropic: ✓ Configured
   - Perplexity: ✓ Configured

3. **Launch Application**
   ```bash
   streamlit run app.py
   ```

### 📋 How to Use

1. **Open the app** in your browser (opens automatically)

2. **Enter job details**:
   - Company name (e.g., "Google")
   - Paste full job description
   - (Optional) Job URL

3. **Configure settings**:
   - ✓ Enable company research (Perplexity)
   - Set target ATS score (default: 90)

4. **Generate**:
   - Click "Generate ATS-Optimized Resume"
   - Wait ~30-60 seconds
   - Download as PDF: `Venkat_CompanyName.pdf`

### 📊 What Happens Behind the Scenes

```
Your Profile.pdf
     ↓
  Parse & Extract
     ↓
Job Description → Analyze with Claude → Extract Keywords & Requirements
     ↓                                           ↓
Company Research (Perplexity) ← ← ← ← ← ← ← ← ←
     ↓
Generate Resume with Claude
     ↓
  (Profile + Job Analysis + ATS Knowledge + Company Info)
     ↓
Convert to ATS-friendly PDF
     ↓
Save to Database
     ↓
Download: Venkat_CompanyName.pdf
```

### 🎯 ATS Optimization Features

Your resume will be optimized for:

- ✅ **90%+ keyword match** with job description
- ✅ **ATS-friendly formatting** (no tables/columns)
- ✅ **Standard section headers** (ATS recognizes them)
- ✅ **Quantifiable achievements** (numbers, %, $)
- ✅ **Industry-specific keywords** from job posting
- ✅ **Skills alignment** (required & preferred)
- ✅ **Company-specific insights** (if research enabled)

### 📁 Generated Files

- **PDF Resume**: `generated_resumes/Venkat_CompanyName.pdf`
- **Database**: `resume_generator.db` (history of all resumes)
- **Logs**: Console output shows progress

### 🔍 View Previous Resumes

Check the sidebar in the app to see:
- All previously generated resumes
- Download them again
- See creation dates and ATS scores

### ⚙️ Troubleshooting

**App won't start?**
```bash
python3 test_system.py  # Run diagnostics
```

**Missing Profile.pdf?**
- Add it to the project root directory
- It should be named exactly `Profile.pdf`

**API errors?**
- Check `.env` file has valid API keys
- Verify keys at:
  - Anthropic: https://console.anthropic.com
  - Perplexity: https://www.perplexity.ai/api

**No resume generated?**
- Check console for errors
- Verify job description is complete
- Ensure company name is provided

### 💡 Pro Tips

1. **Paste complete job descriptions** - more details = better optimization
2. **Use company research** - adds company-specific insights
3. **Try different companies** - each resume is tailored
4. **Check "Previous Resumes"** - avoid regenerating
5. **Review markdown output** - see what was optimized

### 📱 Next Steps

- **Deploy to Streamlit Cloud**: See README.md
- **Customize**: Edit prompt in `src/generators/resume_generator.py`
- **Add templates**: Modify PDF layout in `src/generators/pdf_generator.py`
- **Enhance analysis**: Update `src/analyzers/job_analyzer.py`

---

**Ready to generate your first ATS-optimized resume?**

```bash
streamlit run app.py
```

🎉 Good luck with your job applications!
