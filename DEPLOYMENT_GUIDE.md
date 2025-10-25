# 🚀 Streamlit Cloud Deployment Guide

## Ultra ATS Resume Generator - Deploy to Streamlit Cloud

### 📋 Prerequisites

Before deploying, ensure you have:

- ✅ GitHub repository with your code (Done! https://github.com/Nagavenkatasai7/assistant)
- ✅ Streamlit Cloud account (free at https://streamlit.io/cloud)
- ✅ Anthropic API key
- ✅ Perplexity API key (optional)

---

## 🎯 Step-by-Step Deployment

### Step 1: Sign Up for Streamlit Cloud

1. **Go to Streamlit Cloud**
   - Visit: https://streamlit.io/cloud
   - Click "Sign up" or "Get started"

2. **Connect GitHub Account**
   - Click "Continue with GitHub"
   - Authorize Streamlit Cloud to access your repositories
   - Grant permissions to read your public repositories

### Step 2: Create New App

1. **Click "New app"** in the Streamlit Cloud dashboard

2. **Select Repository Settings**
   - **Repository**: `Nagavenkatasai7/assistant`
   - **Branch**: `main`
   - **Main file path**: `app.py`

3. **Advanced Settings (Optional)**
   - **App URL**: Choose a custom subdomain (e.g., `resume-generator-venkat`)
   - Your app will be at: `https://resume-generator-venkat.streamlit.app`

### Step 3: Configure Secrets (CRITICAL!)

**⚠️ IMPORTANT: Your app won't work without API keys!**

1. **Click "Advanced settings"** before deploying

2. **Go to "Secrets" section**

3. **Add your API keys** in TOML format:

```toml
# Streamlit Secrets
# Add these in the Secrets section

ANTHROPIC_API_KEY = "sk-ant-api03-your-key-here"

PERPLEXITY_API_KEY = "pplx-your-key-here"

# Optional settings
APP_TITLE = "Ultra ATS Resume Generator"
MIN_ATS_SCORE = 90
```

**⚠️ Replace with your actual API keys:**
- Get Anthropic API key from: https://console.anthropic.com
- Get Perplexity API key from: https://www.perplexity.ai/api

4. **Click "Save"**

### Step 4: Add Profile.pdf (Important!)

Since `Profile.pdf` is in `.gitignore`, you need to upload it:

**Option A: Upload via Streamlit Secrets (Recommended)**

1. In the "Secrets" section, add a file upload option
2. Or modify app to allow profile upload through UI

**Option B: Temporarily Add to Repository**

```bash
# In your local repository
git rm --cached Profile.pdf  # Remove from gitignore tracking
git add -f Profile.pdf        # Force add
git commit -m "Add Profile.pdf for deployment"
git push
```

⚠️ **Security Note**: This makes your profile public. Consider option C instead.

**Option C: Modify App for Profile Upload (Best for Cloud)**

The app can be modified to allow users to upload their own Profile.pdf through the UI. This is the most secure option for cloud deployment.

### Step 5: Deploy!

1. **Click "Deploy"** button

2. **Wait for deployment** (2-5 minutes)
   - Streamlit will:
     - Install dependencies from `requirements.txt`
     - Set up the environment
     - Start your app

3. **Watch the logs** for any errors

### Step 6: Verify Deployment

Once deployed, your app will be live at:
- **URL**: `https://[your-app-name].streamlit.app`
- Example: `https://resume-generator-venkat.streamlit.app`

**Test the following:**
- ✅ App loads successfully
- ✅ No API key errors
- ✅ Can enter job description
- ✅ Can generate resume
- ✅ Can download PDF
- ✅ Company research works (if Perplexity enabled)

---

## 🔧 Post-Deployment Configuration

### Update Secrets

If you need to update API keys:

1. Go to your app in Streamlit Cloud
2. Click "Settings" (⚙️)
3. Click "Secrets"
4. Update the values
5. App will automatically restart

### View Logs

If something goes wrong:

1. Click "Manage app"
2. Click "Logs" tab
3. See real-time logs and errors

### Restart App

If app is stuck:

1. Go to "Manage app"
2. Click "Reboot app"

---

## 🐛 Troubleshooting

### Error: "ANTHROPIC_API_KEY not found"

**Solution:**
1. Go to app Settings → Secrets
2. Add your Anthropic API key
3. Make sure the format is correct (TOML)
4. Save and reboot app

### Error: "Profile.pdf not found"

**Solutions:**

**Option 1: Modify app.py to allow profile upload**

Add this to your app.py:

```python
# In the sidebar or main area
uploaded_profile = st.file_uploader("Upload your Profile.pdf", type=["pdf"])

if uploaded_profile:
    # Save temporarily
    with open("Profile.pdf", "wb") as f:
        f.write(uploaded_profile.read())
```

**Option 2: Use environment variable for profile path**

Store profile in secrets as base64 and decode at runtime.

### Error: "Module not found"

**Solution:**
1. Check `requirements.txt` includes all dependencies
2. Add missing package to requirements.txt
3. Commit and push changes
4. App will auto-redeploy

### Error: "Port already in use"

**Solution:**
- This doesn't apply to Streamlit Cloud
- Remove port specifications from config.toml
- Streamlit Cloud manages ports automatically

### App is Slow

**Solutions:**
1. **Use caching** for ATS knowledge:
   ```python
   @st.cache_data
   def load_ats_knowledge():
       return knowledge
   ```

2. **Optimize Claude API calls**:
   - Cache job analysis results
   - Use smaller context when possible

3. **Upgrade Streamlit Cloud tier** (if on free tier)

---

## 💡 Optimization Tips

### 1. Add Caching

Update `app.py` to cache expensive operations:

```python
import streamlit as st

@st.cache_data
def load_ats_knowledge():
    with open("ats_knowledge_base.md", 'r') as f:
        return f.read()

@st.cache_resource
def initialize_components():
    # Cache component initialization
    return db, profile_parser, job_analyzer, etc.
```

### 2. Reduce Build Size

Optimize `requirements.txt`:
- Remove unused dependencies
- Use specific versions
- Consider lighter alternatives

### 3. Add Usage Analytics

Track usage with Streamlit Analytics:

```python
# In app.py
from streamlit_analytics import track

with track():
    # Your app code
    pass
```

### 4. Add Custom Domain (Paid Feature)

1. Go to app Settings
2. Click "Custom domain"
3. Add your domain (e.g., `resume.nagavenkatasai.com`)
4. Update DNS records

---

## 🎨 Enhance Your Deployed App

### Add App Metadata

Create `streamlit_app.py` header:

```python
# Add to top of app.py
st.set_page_config(
    page_title="Ultra ATS Resume Generator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/Nagavenkatasai7/assistant',
        'Report a bug': 'https://github.com/Nagavenkatasai7/assistant/issues',
        'About': "# Ultra ATS Resume Generator\nBuilt with Claude AI & Streamlit"
    }
)
```

### Add Footer

```python
# At bottom of app
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p>Built with ❤️ using <a href='https://www.anthropic.com/'>Claude</a> & <a href='https://streamlit.io/'>Streamlit</a></p>
    <p><a href='https://github.com/Nagavenkatasai7/assistant'>View on GitHub</a> | <a href='https://nagavenkatasai7.github.io/portfolio/'>Portfolio</a></p>
</div>
""", unsafe_allow_html=True)
```

---

## 📊 Monitor Your App

### View Analytics

Streamlit Cloud provides:
- **Viewer count**: How many people use your app
- **Resource usage**: CPU, memory usage
- **Error rate**: Track application errors
- **Response time**: App performance

Access in: App Settings → Analytics

### Set Up Alerts

1. Go to Settings → Notifications
2. Enable email alerts for:
   - App crashes
   - High error rates
   - Deployment failures

---

## 🔄 Update Your Deployed App

### Automatic Updates

Streamlit Cloud auto-deploys when you push to GitHub:

```bash
# Make changes locally
git add .
git commit -m "Update feature X"
git push

# App automatically redeploys in ~2 minutes
```

### Manual Reboot

If auto-deploy doesn't trigger:

1. Go to Streamlit Cloud dashboard
2. Click "Reboot app"

---

## 💰 Pricing & Limits

### Free Tier (Community)
- ✅ Unlimited public apps
- ✅ 1 GB RAM per app
- ✅ 1 CPU core
- ✅ Community support
- ❌ No custom domain
- ❌ Limited resources

### Paid Tier (Teams/Enterprise)
- ✅ Private apps
- ✅ More resources (up to 32 GB RAM)
- ✅ Custom domains
- ✅ Priority support
- ✅ SSO/SAML
- ✅ Advanced analytics

For your use case, **Free Tier is sufficient**!

---

## 🎯 Quick Deployment Checklist

Before deploying, verify:

- [ ] GitHub repository is public or connected
- [ ] `requirements.txt` is complete and correct
- [ ] `app.py` is in the root directory
- [ ] `.streamlit/config.toml` doesn't have port conflicts
- [ ] API keys are ready to add to Secrets
- [ ] `.gitignore` protects sensitive files
- [ ] README.md is clear and helpful
- [ ] Profile.pdf handling is decided (upload or hardcoded)

**Ready to Deploy?**

1. Go to https://streamlit.io/cloud
2. Click "New app"
3. Select your repository
4. Add secrets
5. Deploy!

---

## 📞 Support

**Streamlit Cloud Issues:**
- Docs: https://docs.streamlit.io/streamlit-community-cloud
- Forum: https://discuss.streamlit.io/
- Support: support@streamlit.io

**App Issues:**
- GitHub: https://github.com/Nagavenkatasai7/assistant/issues
- Email: nchennu@gmu.edu

---

## 🎉 Success!

Once deployed, share your app:
- **Direct link**: `https://[your-app].streamlit.app`
- **On LinkedIn**: "Check out my AI resume generator!"
- **On GitHub README**: Add the live demo link
- **On Portfolio**: Add to your projects

**Your app is now live and helping people optimize their resumes! 🚀**
