# 📄 Ultra ATS Resume Generator

An AI-powered resume generator that creates ATS-optimized resumes with 90+ scores using Claude AI and comprehensive ATS knowledge.

## 🌟 Features

- **ATS Optimization**: Built on knowledge from 7 authoritative ATS sources
- **AI-Powered Generation**: Uses Claude Sonnet 4.5 for intelligent resume creation
- **Company Research**: Optional Perplexity integration for company insights
- **Duplicate Detection**: Smart checking to prevent redundant resume generation
- **Database Storage**: SQLite-based history of all generated resumes
- **PDF Export**: Clean, ATS-friendly PDF format with proper formatting
- **Interactive UI**: Beautiful Streamlit interface

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Anthropic API key (required)
- Perplexity API key (optional)
- Your profile in `Profile.pdf` format

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd resume-maker
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

4. Add your Profile.pdf to the project root

5. Run the application:
```bash
streamlit run app.py
```

## 📁 Project Structure

```
resume-maker/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variables template
├── Profile.pdf                # Your profile (required)
├── knowledge/                 # ATS knowledge PDFs (7 sources)
├── src/
│   ├── database/             # SQLite database schema
│   ├── parsers/              # Profile PDF parser
│   ├── analyzers/            # Job description analyzer
│   ├── generators/           # Resume & PDF generators
│   └── utils/                # Perplexity client & utilities
├── ats_knowledge_base.md     # Synthesized ATS knowledge
└── generated_resumes/        # Output directory for PDFs
```

## 🔧 Configuration

### Required Environment Variables

```bash
ANTHROPIC_API_KEY=your-anthropic-api-key
```

### Optional Environment Variables

```bash
PERPLEXITY_API_KEY=your-perplexity-api-key
APP_TITLE=Ultra ATS Resume Generator
MIN_ATS_SCORE=90
```

## 💡 How It Works

1. **Profile Parsing**: Extracts structured data from your Profile.pdf
2. **Job Analysis**: Claude analyzes the job description to extract:
   - Company name and job title
   - Required and preferred skills
   - Key keywords for ATS optimization
   - Responsibilities and requirements
3. **Company Research** (Optional): Perplexity gathers company insights
4. **Resume Generation**: Claude creates a tailored, ATS-optimized resume using:
   - Your profile data
   - Job analysis results
   - ATS knowledge base (synthesized from 7 sources)
   - Company research (if available)
5. **PDF Export**: Converts markdown to ATS-friendly PDF format
6. **Database Storage**: Saves resume with metadata for future reference

## 📊 ATS Optimization Techniques

The generator implements best practices from industry sources:

- ✅ **Keyword Matching**: Natural integration of job description keywords
- ✅ **Clean Formatting**: No tables, columns, or graphics that break ATS parsers
- ✅ **Standard Sections**: Recognized headers (Summary, Experience, Skills, Education)
- ✅ **Achievement Focus**: Quantifiable results and metrics
- ✅ **Skill Alignment**: Explicit mention of required and preferred skills
- ✅ **Industry Terminology**: Role-specific keywords and phrases
- ✅ **Consistent Formatting**: Standard date formats and clear structure

## 🎯 Usage

1. **Launch the app**: `streamlit run app.py`
2. **Enter job details**:
   - Company name (required)
   - Job description (required)
   - Job URL (optional)
3. **Configure options**:
   - Enable/disable company research
   - Set target ATS score (85-100)
4. **Generate**: Click "Generate ATS-Optimized Resume"
5. **Download**: Get your PDF as `Venkat_CompanyName.pdf`

## 📚 ATS Knowledge Sources

The knowledge base is built from:

1. Jobscan Report: Resume Skills Data for 24 Job Roles
2. Applicant Tracking Systems: Everything You Need to Know
3. Power Edit Your Resume (AI Resume Builder)
4. How to Use ChatGPT to Write a Resume
5. Best Resume Formats for 2025
6. How to Write a Resume for Today's Job Market
7. ATS Resume: How to Create a Resume That Gets You Noticed

## 🔒 Privacy & Security

- All processing happens locally or via secure APIs
- No data is stored externally except in your local SQLite database
- API keys are managed via environment variables
- Generated resumes are saved locally in `generated_resumes/`

## 📦 Deployment to Streamlit Cloud

1. Push your code to GitHub
2. Connect your repo to Streamlit Cloud
3. Configure secrets in the Streamlit Cloud dashboard:
   - `ANTHROPIC_API_KEY`
   - `PERPLEXITY_API_KEY` (optional)
4. Upload your Profile.pdf as a secret file
5. Deploy!

## 🛠️ Development

### Running Tests

```bash
# Test profile parser
python src/parsers/profile_parser.py

# Test job analyzer
python src/analyzers/job_analyzer.py

# Test PDF generator
python src/generators/pdf_generator.py

# Test resume generator
python src/generators/resume_generator.py
```

### Extracting ATS Knowledge

```bash
# Extract text from PDFs
python extract_ats_knowledge.py

# Analyze and synthesize knowledge
python analyze_ats_knowledge.py
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is for educational and personal use.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [Anthropic Claude](https://www.anthropic.com/)
- Enhanced with [Perplexity AI](https://www.perplexity.ai/)
- ATS knowledge from industry-leading sources

## 📞 Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Version**: 1.0.0
**Last Updated**: 2025-10-24

Made with ❤️ and AI
