# 🚀 Quick Deploy to Streamlit Cloud (5 Minutes)

## Step-by-Step (Super Simple!)

### 1. Sign Up (1 minute)
- Go to: https://streamlit.io/cloud
- Click "Continue with GitHub"
- Authorize Streamlit

### 2. Create New App (2 minutes)
- Click "New app"
- **Repository**: `Nagavenkatasai7/assistant`
- **Branch**: `main`
- **Main file**: `app.py`
- Click "Advanced settings"

### 3. Add API Keys (2 minutes)
In the "Secrets" section, paste:

```toml
ANTHROPIC_API_KEY = "your-anthropic-key-here"
PERPLEXITY_API_KEY = "your-perplexity-key-here"
```

**Replace with your actual keys!**

### 4. Deploy!
- Click "Deploy"
- Wait 2-3 minutes
- Done! Your app is live! 🎉

---

## Your App URL
`https://[your-chosen-name].streamlit.app`

Example: `https://resume-generator-venkat.streamlit.app`

---

## ⚠️ Important: Handle Profile.pdf

**Option 1: Allow Upload in UI** (Recommended)
Users upload their own Profile.pdf - most flexible!

**Option 2: Hardcode Profile**
Add Profile.pdf to repository (but it becomes public!)

Choose option 1 for best security.

---

## 🎯 That's It!

Your Ultra ATS Resume Generator is now live on the internet!

**Full guide**: See `DEPLOYMENT_GUIDE.md` for detailed instructions.

---

## 📱 Share Your App

Once deployed:
- Add to LinkedIn profile
- Share on Twitter/X
- Add to your portfolio website
- Put in GitHub README

**Your app link**: `https://[your-app].streamlit.app`
