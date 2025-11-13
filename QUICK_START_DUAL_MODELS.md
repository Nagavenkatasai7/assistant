# Quick Start: Dual Model Support

## What Changed?

You now have **TWO AI models** to choose from for resume generation:

1. **Claude Opus 4.1** - Fast and efficient (NEW!)
2. **Kimi K2** - Deep reasoning and high quality (Original)

## How to Use

### 1. Start the App
```bash
streamlit run app.py
```

### 2. Check API Keys (Sidebar)
- ✅ Kimi K2 API key configured
- ✅ Claude Opus 4.1 API key configured (or ⚠️ optional)
- ✅ Tavily API key configured

### 3. Select Your Model
In the main interface, you'll see:

```
🤖 AI Model Selection

Claude Opus 4.1 (Fast)        |  Kimi K2 (High Quality)
Speed: Very Fast              |  Speed: Moderate
Quality: Excellent            |  Quality: Superior
Best for: Quick iterations    |  Best for: Important jobs

( ) ⚡ Claude Opus 4.1 (Fast)
(•) 🎯 Kimi K2 (High Quality - Default)
```

**Default:** Claude Opus 4.1 (Fast) as requested

### 4. Generate Resume
- Fill in job details
- Click "Generate ATS-Optimized Resume"
- Wait for generation
- Success message will show: "✅ ATS-Optimized Resume Generated Successfully using Claude Opus 4.1!"

## When to Use Each Model

### Use Claude Opus 4.1 When:
- ⚡ You need fast results
- 🔄 You're iterating on multiple versions
- 💰 Cost is not a primary concern
- 📝 Most standard resume generation tasks

### Use Kimi K2 When:
- 🎯 Applying to important positions
- 🧠 Need deep analysis and reasoning
- 💎 Quality is the top priority
- 💰 You want lower costs

## API Key Setup

If you don't have Claude API key yet:

1. **Option A:** Use Kimi K2 only (app will auto-fallback)
2. **Option B:** Get Anthropic API key:
   - Visit: https://console.anthropic.com/
   - Sign up and get API key
   - Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-your-key`

## Troubleshooting

### "Claude API key not configured"
- This is just a warning (optional)
- App will automatically use Kimi K2
- No action needed unless you want Claude

### "Warning: Anthropic API key not found, falling back to Kimi K2"
- App detected you selected Claude but key is missing
- Automatically switched to Kimi K2
- Your resume will still be generated

### Both Models Available
- Both API keys configured? Great!
- Switch between them anytime
- No restart needed

## Features That Work With Both Models

✅ All existing features work with both models:
- ATS optimization
- Company research (Tavily)
- Cover letter generation
- PDF/DOCX export
- Resume editing
- Version history
- Security features

## Quick Test

Run this to verify everything works:
```bash
python3 test_model_integration.py
```

Expected output:
```
✓ ResumeGenerator imported successfully
✓ Kimi K2 initialized: kimi_k2
✓ Claude initialized: claude_opus_4
✓ Integration test completed successfully!
```

## Summary

- 🎉 You now have 2 model options
- ⚡ Claude Opus 4.1 is the default (fast)
- 🎯 Kimi K2 is available for high-quality needs
- 🔄 Switch between them anytime
- 🛡️ Auto-fallback if Claude key missing
- ✅ All features work with both models

Ready to generate resumes with your choice of AI model!
