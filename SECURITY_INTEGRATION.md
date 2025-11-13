# Security Integration Guide

Quick guide for integrating security features into the Ultra ATS Resume Generator application.

## Quick Start

### 1. Import Security Module

```python
# In app.py - add these imports
from src.security import get_app_security, ValidationError
from src.security.security_logger import get_security_logger
```

### 2. Initialize Security

```python
# At the start of your main() function or in initialize_components()
security = get_app_security()
security_logger = get_security_logger()
```

### 3. Add Input Validation

```python
# Before resume generation (around line 207 in app.py)
if st.button("🚀 Generate ATS-Optimized Resume", type="primary"):
    # Validate inputs
    is_valid, error_msg = security.validate_resume_generation_inputs(
        job_description=job_description,
        company_name=company_name,
        job_url=job_url,
        target_score=target_score
    )

    if not is_valid:
        st.error(f"Validation Error: {error_msg}")
        return

    # Check rate limits
    allowed, error_msg, reset_time = security.check_rate_limit()

    if not allowed:
        st.error(error_msg)
        st.info(f"Please try again in {reset_time} seconds")
        return

    # Continue with resume generation...
```

### 4. Display Rate Limit Info

```python
# In sidebar (around line 97)
with st.sidebar:
    st.header("⚙️ Settings")

    # Add security status
    security.display_rate_limit_info()
    security.display_security_status()

    # ... rest of sidebar code
```

### 5. File Upload Validation

```python
# When handling file uploads (around line 109)
uploaded_profile = st.file_uploader("Upload Profile PDF", type=["pdf"])

if uploaded_profile:
    # Validate file
    is_valid, error_msg = security.validate_file_upload(uploaded_profile)

    if not is_valid:
        st.error(f"File validation failed: {error_msg}")
        return

    # Save file
    with open("Profile.pdf", "wb") as f:
        f.write(uploaded_profile.read())

    st.success("✓ Profile uploaded and validated successfully!")
```

### 6. Pass User Identifier to Generators

```python
# When calling generators
user_id = security.get_user_identifier()

# Resume generation
resume_result = resume_generator.generate_resume(
    profile_text,
    job_analysis,
    company_research,
    user_identifier=user_id  # Add this
)

# Job analysis
job_analysis = job_analyzer.analyze_job_description(
    job_description,
    company_name,
    user_identifier=user_id  # Add this
)
```

## Complete Integration Example

Here's a complete example of securing the resume generation button:

```python
if st.button("🚀 Generate ATS-Optimized Resume", type="primary", use_container_width=True):
    # Step 1: Get security instance
    security = get_app_security()
    user_id = security.get_user_identifier()

    # Step 2: Validate inputs
    is_valid, error_msg = security.validate_resume_generation_inputs(
        job_description=job_description,
        company_name=company_name,
        job_url=job_url,
        target_score=target_score
    )

    if not is_valid:
        st.error(f"❌ Validation Error: {error_msg}")
        st.info("Please review your input and try again.")
        return

    # Step 3: Check rate limits
    allowed, error_msg, reset_time = security.check_rate_limit()

    if not allowed:
        st.error(f"⏱️ Rate Limit Exceeded: {error_msg}")

        # Show remaining quota
        quota_info = security.get_rate_limit_info()
        st.info(
            f"Hourly quota: {quota_info['hourly_remaining']}/{quota_info['hourly_max']}\n"
            f"Daily quota: {quota_info['daily_remaining']}/{quota_info['daily_max']}"
        )

        if reset_time:
            st.warning(f"Please wait {reset_time} seconds before trying again.")

        return

    # Step 4: Show quota before generation
    quota_info = security.get_rate_limit_info()
    st.info(
        f"📊 Remaining quota: {quota_info['hourly_remaining']} resumes this hour, "
        f"{quota_info['daily_remaining']} today"
    )

    # Step 5: Proceed with generation
    with st.spinner("Generating your ATS-optimized resume..."):
        try:
            # ... existing resume generation code ...

            # Pass user_id to all API calls
            profile_text = profile_parser.get_profile_summary()

            job_analysis = job_analyzer.analyze_job_description(
                job_description,
                company_name,
                user_identifier=user_id
            )

            resume_result = resume_generator.generate_resume(
                profile_text,
                job_analysis,
                company_research,
                user_identifier=user_id
            )

            # ... rest of generation code ...

            st.success("✅ Resume generated successfully!")

            # Show updated quota
            quota_info = security.get_rate_limit_info()
            st.caption(
                f"Remaining: {quota_info['hourly_remaining']} resumes this hour"
            )

        except ValidationError as e:
            st.error(f"Security error: {str(e)}")
        except Exception as e:
            st.error(f"Error: {str(e)}")
```

## Testing the Integration

### 1. Test Input Validation

Try these test cases:

```python
# Test 1: Too short job description
job_description = "Short"
# Should show: "Job description must be at least 100 characters"

# Test 2: SQL injection attempt
job_description = "Valid job desc... '; DROP TABLE users; --"
# Should show: "Job description contains invalid characters"

# Test 3: XSS attempt
company_name = "Company<script>alert('xss')</script>"
# Should show: "Company name contains invalid characters"

# Test 4: Path traversal
company_name = "../../../etc/passwd"
# Should show: "Company name contains invalid characters"
```

### 2. Test Rate Limiting

```python
# Generate 3 resumes quickly
# Should work for first 3, then show rate limit error

# Check quota display
# Should show "0 resumes remaining this burst period"
```

### 3. Test Security Logging

```bash
# Check logs after testing
cat logs/security.log | grep validation_failed
cat logs/security.log | grep rate_limit_exceeded
cat logs/security.log | grep prompt_injection
cat logs/api_usage.log | jq '.cost_estimate'
```

## Configuration for Production

### 1. Apply Production Settings

```python
# In config.py or at app startup
from config import SecurityConfig

# Apply strict production settings
SecurityConfig.apply_production_settings()

# This sets:
# - MAX_RESUMES_PER_HOUR = 5 (reduced from 10)
# - MAX_RESUMES_PER_10MIN = 2 (reduced from 3)
# - MAX_RESUMES_PER_DAY = 20 (reduced from 50)
# - ENABLE_PROMPT_SANITIZATION = True
# - BLOCK_SUSPICIOUS_REQUESTS = True
# - LOG_SENSITIVE_DATA = False
```

### 2. Environment Variables

Create `.env` file:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxx

# Optional
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxx

# Security (optional)
PRODUCTION_MODE=true
DEBUG_MODE=false
MAX_RESUMES_PER_HOUR=5
```

### 3. Validate on Startup

```python
# At app startup
from src.security import SecretsManager

secrets = SecretsManager()

# Validate all required secrets
all_valid, missing = secrets.validate_all_secrets()

if not all_valid:
    st.error(f"❌ Missing required secrets: {', '.join(missing)}")
    st.stop()

# Verify key formats
format_results = secrets.verify_secrets_format()

for key, is_valid in format_results.items():
    if is_valid is False:
        st.warning(f"⚠️ {key} has invalid format")
```

## Monitoring and Alerts

### 1. Set Up Log Monitoring

```bash
# Monitor security events in real-time
tail -f logs/security.log

# Monitor API costs
tail -f logs/api_usage.log | jq '.metadata.cost_estimate'

# Check for suspicious activity
grep "SUSPICIOUS" logs/security.log
grep "prompt_injection" logs/security.log
```

### 2. Cost Alerts

```python
# Add to your monitoring script
from src.security.security_logger import get_security_logger

logger = get_security_logger()

# Get API usage stats
stats = logger.get_api_usage_stats(hours=24)

if stats['estimated_cost'] > 10.0:  # $10 threshold
    send_alert(f"High API costs: ${stats['estimated_cost']}")
```

### 3. Security Dashboard

```python
# Add to sidebar for admin view
if st.sidebar.checkbox("Show Security Dashboard (Admin)"):
    st.header("🔒 Security Dashboard")

    # Rate limit status
    quota_info = security.get_rate_limit_info()
    col1, col2 = st.columns(2)

    with col1:
        st.metric("Hourly Quota", f"{quota_info['hourly_remaining']}/{quota_info['hourly_max']}")

    with col2:
        st.metric("Daily Quota", f"{quota_info['daily_remaining']}/{quota_info['daily_max']}")

    # Recent security events
    st.subheader("Recent Security Events")
    # Read from logs/security.log and display

    # API usage
    st.subheader("API Usage (24h)")
    # Show cost and token stats
```

## Troubleshooting

### Issue: Imports not working

```python
# Make sure to add parent directory to path
import sys
from pathlib import Path

parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))
```

### Issue: Logs not being created

```bash
# Create logs directory
mkdir -p logs

# Check permissions
chmod 755 logs
```

### Issue: Rate limits too strict

```python
# Adjust in config.py for development
SecurityConfig.apply_development_settings()

# Or manually
SecurityConfig.MAX_RESUMES_PER_HOUR = 20
SecurityConfig.MAX_RESUMES_PER_10MIN = 5
```

### Issue: False positives on injection detection

```python
# Review detected patterns
is_suspicious, patterns = sanitizer.detect_injection_attempt(text)

if is_suspicious:
    print(f"Detected patterns: {patterns}")

    # If false positive, you can disable blocking but keep logging
    SecurityConfig.BLOCK_SUSPICIOUS_REQUESTS = False
    SecurityConfig.LOG_INJECTION_ATTEMPTS = True
```

## Next Steps

1. ✅ Complete integration into app.py
2. ✅ Test all security features
3. ✅ Review security logs
4. ✅ Adjust rate limits for your use case
5. ✅ Set up monitoring and alerts
6. ✅ Create backup strategy for logs
7. ✅ Document any custom security rules

## Support

For issues or questions:
- Check `SECURITY.md` for detailed documentation
- Review `tests/test_security.py` for examples
- Check logs in `logs/` directory
- Run tests: `python tests/test_security.py`
