# API SETUP GUIDE - Academic Command Center

**Version**: 1.0.0
**Last Updated**: November 12, 2025

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [Required APIs](#required-apis)
3. [Optional APIs](#optional-apis)
4. [Step-by-Step Setup](#step-by-step-setup)
5. [Cost Estimates](#cost-estimates)
6. [Troubleshooting](#troubleshooting)

---

## OVERVIEW

Academic Command Center uses AI APIs for intelligent features. You need API keys from third-party providers. This guide shows you how to obtain and configure these keys.

### Why API Keys?

- **Essay Parsing**: Extract requirements from assignment instructions
- **Task Generation**: Break essays into actionable subtasks
- **Grammar Checking**: Analyze writing quality
- **Research Assistance**: (Phase 6 feature)

### Security

- All API keys encrypted with AES-256
- Keys stored in `database/acc_main.db` (encrypted)
- Master encryption key: `config/encryption.key`
- **BACKUP encryption.key** - if lost, keys cannot be recovered

---

## REQUIRED APIs

These APIs are essential for core functionality:

### 1. Google Gemini ⭐ **REQUIRED**

**Used for**: Essay parsing, assignment analysis

**How to get**:
1. Go to: https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Get API Key"
4. Click "Create API key in new project"
5. Copy the key (starts with `AIza...`)

**Cost**: FREE for typical usage
- Free tier: 60 requests/minute
- Paid: $0.00025 per 1K tokens (~$0.01 per essay)

**Quota**: 60 requests/minute free tier

---

### 2. Groq ⭐ **REQUIRED**

**Used for**: Task generation, fast AI processing

**How to get**:
1. Go to: https://console.groq.com/
2. Sign up for free account
3. Go to "API Keys" section
4. Click "Create API Key"
5. Name it "Academic Command Center"
6. Copy the key (starts with `gsk_...`)

**Cost**: FREE for typical usage
- Free tier: 30 requests/minute
- Very fast inference (tokens/second)
- Cost: ~$0.0001 per 1K tokens (~$0.005 per essay)

**Models Available**:
- `llama-3.1-70b-versatile` (recommended)
- `llama-3.1-8b-instant` (faster, less accurate)

---

## OPTIONAL APIs

These enhance functionality but aren't required:

### 3. DeepSeek (Grammar Checking)

**Used for**: Advanced grammar and style checking

**How to get**:
1. Go to: https://platform.deepseek.com/
2. Create account
3. Go to API Keys
4. Click "Create New Key"
5. Copy the key (starts with `sk-...`)

**Cost**: Very affordable
- $0.00014 per 1K input tokens
- $0.00028 per 1K output tokens
- ~$0.02-$0.03 per essay grammar check

**Free Credits**: New accounts get $5 free credits

---

### 4. OpenRouter (Claude Access)

**Used for**: Complex reasoning, advanced analysis

**How to get**:
1. Go to: https://openrouter.ai/
2. Sign up with email
3. Go to Keys: https://openrouter.ai/keys
4. Click "Create Key"
5. Name it "ACC"
6. Copy the key (starts with `sk-or-...`)

**Cost**: Pay-per-use
- Claude Sonnet: ~$0.003 per 1K tokens
- Claude Haiku: ~$0.00025 per 1K tokens
- ~$0.10-$0.30 per essay (if used extensively)

**Credits**: Add credits via credit card ($5 minimum)

**Models Available**:
- `anthropic/claude-3.5-sonnet` (best quality)
- `anthropic/claude-3-haiku` (faster, cheaper)

---

### 5. Cohere (Semantic Search)

**Used for**: Material search, semantic analysis

**How to get**:
1. Go to: https://dashboard.cohere.com/
2. Sign up for free account
3. Go to API Keys
4. Copy default key or create new one

**Cost**: FREE for typical usage
- Free tier: 100 requests/minute
- Paid: $0.0002 per 1K tokens
- ~$0.01 per essay

**Free Trial**: Generous free tier for development

---

### 6. Canvas LMS (Grade Sync)

**Used for**: Assignment and grade synchronization

**How to get**:
1. Log into your school's Canvas
2. Click your profile picture (top left)
3. Go to **Account** → **Settings**
4. Scroll to "Approved Integrations"
5. Click **+ New Access Token**
6. Purpose: "Academic Command Center"
7. Expiration: (choose date or leave blank)
8. Click **Generate Token**
9. **IMPORTANT**: Copy token immediately (shown only once!)

**Canvas URL**: Your school's Canvas URL
- Example: `https://canvas.university.edu`
- Example: `https://ubc.instructure.com`
- Don't include `/login` or trailing `/`

**Token Format**: Long string (64+ characters)

**Security**: Token has full account access - keep secure!

**Expiration**: Set expiration date or regenerate periodically

---

## STEP-BY-STEP SETUP

### Step 1: Launch Application

1. Double-click `startlearn.bat`
2. Application opens to Dashboard

### Step 2: Navigate to Settings

1. Click **⚙️ Settings** in left sidebar
2. Click **API Keys** tab

### Step 3: Add Google Gemini (Required)

1. Click **+ Add API Key** button
2. Provider: Select **Google Gemini**
3. API Key: Paste your Gemini key
4. Click **Save**
5. Click **Verify** to test connection
6. ✅ Should show "Verified successfully"

### Step 4: Add Groq (Required)

1. Click **+ Add API Key** button
2. Provider: Select **Groq**
3. API Key: Paste your Groq key
4. Click **Save**
5. Click **Verify** to test connection
6. ✅ Should show "Verified successfully"

### Step 5: Add Optional APIs

Repeat for each optional API:
1. Click **+ Add API Key**
2. Select provider
3. Paste key
4. Save and verify

### Step 6: Configure Canvas (Optional)

1. Click **Canvas Settings** tab
2. Canvas URL: Enter your school's Canvas URL
3. API Token: Paste Canvas access token
4. Click **Save**
5. Click **Test Connection**
6. ✅ Should show "Connected to Canvas"

### Step 7: Verify Everything Works

1. Go to **📝 Essays**
2. Click **+ New Essay**
3. Paste sample assignment text
4. If parsing works, API keys are configured correctly!

---

## COST ESTIMATES

### Typical Essay (1,500 words, 5 sources)

| API | Usage | Cost | Notes |
|-----|-------|------|-------|
| **Gemini** | Essay parsing | $0.01 | Required |
| **Groq** | Task generation | $0.005 | Required |
| **DeepSeek** | Grammar check | $0.02 | Optional |
| **OpenRouter** | Advanced analysis | $0.10 | Optional |
| **Cohere** | Material search | $0.01 | Optional |
| **TOTAL** | Per essay | **$0.02-$0.15** | |

### Monthly Estimates

**Light Use** (5 essays/month):
- Required only: $0.10/month
- All features: $0.75/month

**Medium Use** (10 essays/month):
- Required only: $0.20/month
- All features: $1.50/month

**Heavy Use** (20 essays/month):
- Required only: $0.40/month
- All features: $3.00/month

**Semester** (~50 essays):
- Required only: ~$1.00
- All features: ~$7.50

### Free Tiers

Most providers offer free tiers:
- **Gemini**: 60 req/min free
- **Groq**: 30 req/min free
- **DeepSeek**: $5 free credits
- **Cohere**: 100 req/min free

**You can likely use ACC for FREE for typical semester workload!**

---

## TROUBLESHOOTING

### Verification Fails

**Problem**: "Failed to verify API key"

**Solutions**:
1. Check internet connection
2. Verify key copied correctly (no extra spaces)
3. Check key hasn't expired
4. Try regenerating key on provider's website
5. Wait a few minutes (new keys take time to activate)

**Check**: Try key in provider's playground/console first

---

### API Rate Limits

**Problem**: "Rate limit exceeded"

**What it means**: Too many requests too fast

**Solutions**:
1. Wait a few minutes
2. Upgrade to paid tier (higher limits)
3. Use fewer AI features simultaneously
4. Spread out requests

**Free Tier Limits**:
- Gemini: 60 req/min
- Groq: 30 req/min
- DeepSeek: 60 req/min

---

### Invalid API Key Format

**Problem**: "Invalid API key format"

**Check format**:
- Gemini: `AIza...` (39 characters)
- Groq: `gsk_...` (56+ characters)
- DeepSeek: `sk-...` (48+ characters)
- OpenRouter: `sk-or-...` (64+ characters)
- Cohere: varies (32+ characters)

**Solutions**:
1. Re-copy key from provider
2. Check for extra spaces/newlines
3. Ensure entire key copied (not truncated)

---

### Canvas Connection Fails

**Problem**: "Failed to connect to Canvas"

**Solutions**:
1. Check Canvas URL is correct
   - Include `https://`
   - No trailing `/`
   - No `/login` suffix
2. Verify access token is valid
3. Check token hasn't expired
4. Ensure token has necessary permissions
5. Try regenerating token

**Test**: Access Canvas URL in browser while logged in

---

### Encrypted Keys Lost

**Problem**: "Cannot decrypt API keys"

**Cause**: `config/encryption.key` was deleted or changed

**Solution**: Unfortunately, encrypted keys cannot be recovered

**What to do**:
1. Re-enter all API keys in Settings
2. Keys will be re-encrypted with new master key
3. **BACKUP** new `encryption.key` file

**Prevention**: Backup `config/encryption.key` regularly!

---

### Out of Credits

**Problem**: "Insufficient credits" (OpenRouter, DeepSeek)

**Solutions**:
1. Add credits to account
2. Switch to free-tier providers
3. Use features less frequently

**OpenRouter**: Minimum $5 credit purchase
**DeepSeek**: Can add credits via various methods

---

## API KEY MANAGEMENT

### Best Practices

1. **Use Free Tiers**: Start with free tier providers
2. **Monitor Usage**: Check provider dashboards regularly
3. **Set Budgets**: Set spending limits on paid APIs
4. **Rotate Keys**: Regenerate keys every few months
5. **Backup Encryption Key**: Save `config/encryption.key` securely

### Security Tips

1. **Never Share Keys**: API keys are like passwords
2. **Don't Commit to Git**: Never commit keys to repositories
3. **Use Separate Keys**: Different key per application
4. **Revoke if Compromised**: Immediately revoke exposed keys
5. **Backup Safely**: Encrypted backup of `encryption.key`

### Key Rotation

**When to rotate**:
- Every 3-6 months (routine)
- If key might be compromised
- When uninstalling application
- Before sharing computer

**How to rotate**:
1. Generate new key on provider's site
2. Update in ACC Settings
3. Revoke old key on provider's site

---

## RECOMMENDED SETUP

### Minimum Setup (FREE)

✅ **Google Gemini** (required)
✅ **Groq** (required)

**Total Cost**: $0/month for typical use
**Features**: Essay parsing, task generation

---

### Standard Setup ($1-3/month)

✅ **Google Gemini**
✅ **Groq**
✅ **DeepSeek** (grammar checking)
✅ **Canvas** (grade sync)

**Total Cost**: $1-3/month
**Features**: All core features + grammar

---

### Premium Setup ($3-10/month)

✅ **Google Gemini**
✅ **Groq**
✅ **DeepSeek**
✅ **OpenRouter (Claude)**
✅ **Cohere**
✅ **Canvas**

**Total Cost**: $3-10/month
**Features**: Everything + advanced AI

---

## GETTING HELP

**API Provider Support**:
- Gemini: https://ai.google.dev/support
- Groq: https://console.groq.com/docs
- DeepSeek: https://platform.deepseek.com/docs
- OpenRouter: https://openrouter.ai/docs
- Cohere: https://docs.cohere.com/

**ACC Support**:
- Check `logs/app.log` for errors
- See TROUBLESHOOTING_GUIDE.md
- Email: support@academiccommandcenter.com

---

**Good luck with your API setup!** 🔑

