# Claude API Setup Guide

The Benchmark Intelligence Agent uses Claude AI for intelligent benchmark extraction, consolidation, and classification. This guide explains how to set up Claude API access across different environments.

## 🌐 Supported Environments

The agent automatically detects and adapts to:
- ✅ **Ambient Code Platform**
- ✅ **Claude Code**
- ✅ **Cursor**
- ✅ **Standard Anthropic API**
- ✅ **Vertex AI** (with limitations)

---

## 🔑 Getting an API Key

### Option 1: Anthropic API (Recommended)

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to **Settings** → **API Keys**
4. Click **Create Key**
5. Copy the key (starts with `sk-ant-...`)

**Pricing**: Pay-as-you-go, ~$3 per million tokens for Claude Sonnet

### Option 2: Vertex AI

If you're using Google Cloud's Vertex AI:
1. Set up Vertex AI access in Google Cloud Console
2. Get your Vertex AI key
3. Note: Some features may have different authentication

---

## ⚙️ Configuration by Environment

### Ambient Code Platform

**Method 1: Workspace Environment Variables** (Recommended)
1. Open your Ambient workspace
2. Go to **Workspace Settings** → **Environment Variables**
3. Add: `ANTHROPIC_API_KEY` = `sk-ant-your-key-here`
4. Save and restart your session

**Method 2: Project Configuration**
```bash
# Add to agents/benchmark_intelligence/config/auth.yaml
huggingface:
  token: ${HF_TOKEN}

claude:
  api_key: ${ANTHROPIC_API_KEY}  # Or hardcode (not recommended)
```

### Claude Code

**Terminal Setup:**
```bash
# Add to ~/.bashrc or ~/.zshrc
export ANTHROPIC_API_KEY='sk-ant-your-key-here'

# Or set for current session only
export ANTHROPIC_API_KEY='sk-ant-your-key-here'
```

**Verify:**
```bash
echo $ANTHROPIC_API_KEY
```

### Cursor

**Option 1: Workspace Settings**
1. Open Cursor Settings (Cmd/Ctrl + ,)
2. Search for "Environment Variables"
3. Add `ANTHROPIC_API_KEY`

**Option 2: Terminal**
```bash
export ANTHROPIC_API_KEY='sk-ant-your-key-here'
```

### Standard Python Environment

```bash
# Linux/macOS
export ANTHROPIC_API_KEY='sk-ant-your-key-here'

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY='sk-ant-your-key-here'

# Windows (CMD)
set ANTHROPIC_API_KEY=sk-ant-your-key-here
```

---

## ✅ Verification

Test that Claude API is accessible:

```python
python -c "
from agents.benchmark_intelligence.tools._claude_client import call_claude, detect_environment
import os

print('Environment:', detect_environment().value)
print('API Key Set:', bool(os.getenv('ANTHROPIC_API_KEY')))
print('Key Prefix:', os.getenv('ANTHROPIC_API_KEY', '')[:10] + '...')

try:
    response = call_claude('Hello, respond with just: Working!')
    print('✅ Claude API is working!')
    print('Response:', response)
except Exception as e:
    print('❌ Error:', e)
"
```

---

## 🐛 Troubleshooting

### Error: "ANTHROPIC_API_KEY not found"

**Solutions:**
1. Check environment variable is set: `echo $ANTHROPIC_API_KEY`
2. Restart your terminal/IDE after setting the variable
3. For Ambient: check Workspace Settings → Environment Variables
4. Verify the key is not quoted incorrectly

### Error: "authentication_error" or "401"

**Causes:**
- ❌ Invalid API key
- ❌ Expired API key
- ❌ Wrong key format for environment

**Solutions:**
1. Verify key starts with `sk-ant-` (for standard Anthropic)
2. Check key is copied correctly (no extra spaces)
3. Generate a new key if expired
4. For Vertex AI, ensure correct authentication method

### Error: "rate_limit_error" or "429"

**Solutions:**
1. Wait a few minutes before retrying
2. Reduce `models_per_lab` in config (currently set to 5)
3. Add delays between API calls
4. Upgrade Anthropic API tier if needed

### Error: "Invalid API key format"

This warning appears when the key doesn't match the expected format:

- **Standard Anthropic**: Should start with `sk-ant-`
- **Vertex AI**: Should start with `vertex-`
- **Unknown format**: May still work but is untested

**Solution**: Use a standard Anthropic API key from console.anthropic.com

---

## 📊 Usage Limits

The agent makes Claude API calls for:
- **Benchmark extraction**: ~1-2 calls per model
- **Consolidation**: ~1 call per batch of 50 benchmarks
- **Classification**: ~1 call per unique benchmark

**Estimated costs** (5 models per lab × 16 labs = 80 models):
- Extraction: 80 calls × ~2K tokens = ~$0.50
- Consolidation: ~2 calls × ~4K tokens = ~$0.05
- Classification: ~50 calls × ~1K tokens = ~$0.10

**Total: ~$0.65 per run** (monthly with caching: <$1)

---

## 🔒 Security Best Practices

1. **Never commit API keys to git**
   - Use environment variables
   - Add `auth.yaml` to `.gitignore` (already done)

2. **Use read-only keys when possible**
   - Create separate keys for different environments
   - Rotate keys periodically

3. **For production use**:
   - Use workspace/platform-managed secrets
   - Enable API key restrictions in Anthropic Console
   - Monitor usage in Anthropic Dashboard

---

## 🚀 Quick Start

**Ambient Code:**
```bash
# 1. Set API key in Workspace Settings
# 2. Run the agent
python -m agents.benchmark_intelligence.main
```

**Claude Code / Cursor:**
```bash
# 1. Set environment variable
export ANTHROPIC_API_KEY='sk-ant-your-key-here'

# 2. Run the agent
python -m agents.benchmark_intelligence.main
```

**Verify it's working:**
- Check logs for "Claude environment: anthropic_api"
- Should see "Calling Claude API" messages
- Benchmarks should be extracted successfully

---

## 📚 Additional Resources

- [Anthropic API Documentation](https://docs.anthropic.com/)
- [API Key Management](https://console.anthropic.com/settings/keys)
- [Pricing Calculator](https://www.anthropic.com/pricing)
- [Rate Limits](https://docs.anthropic.com/claude/reference/rate-limits)

---

**Need help?** Check the logs with `--verbose` flag:
```bash
python -m agents.benchmark_intelligence.main --verbose
```
