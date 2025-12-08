# Setting Up Google Gemini for WhatsApp AI Assistant

## Overview

Your WhatsApp AI Assistant now supports **Google Gemini** as the AI provider! Gemini is:
- **Free to use** with generous quota (15 requests/minute, 1 million tokens/minute on free tier)
- **Fast and reliable** - Gemini 1.5 Flash is optimized for low latency
- **Easy to set up** - No credit card required for API key
- **Multimodal capable** - Can handle images in the future

## Quick Setup (5 Minutes)

### Step 1: Get Your Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click **"Get API Key"**
3. Click **"Create API key in new project"** (or select existing project)
4. Copy the API key (starts with `AIza...`)

**That's it!** No credit card needed.

### Step 2: Add API Key to .env

Open your `.env` file and add your API key:

```bash
# Gemini API (Google)
GEMINI_API_KEY=AIzaSyD...your_actual_key_here
GEMINI_MODEL=gemini-1.5-flash

# AI Provider Selection
AI_PROVIDER=gemini
```

### Step 3: Install Gemini Package

```bash
cd /Users/nurlasyraffie/Downloads/Workspace/whatsapp-ai-assistant
source venv/bin/activate
pip install google-generativeai==0.8.3
```

### Step 4: Restart Server

```bash
# Stop current server (Ctrl+C)
python main.py
```

**Done!** Your system is now using Gemini for AI responses.

---

## AI Provider Options

Your MVP supports **3 AI providers**:

### Option 1: Gemini (Recommended for MVP)
```bash
AI_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-1.5-flash
```

**Pros:**
- Free with generous limits
- Fast responses (optimized for chat)
- Easy to get API key
- No credit card required

**Cons:**
- Slightly less capable than Claude Opus

### Option 2: Anthropic Claude
```bash
AI_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-api03-...
AI_MODEL=claude-3-sonnet-20240229
```

**Pros:**
- Very high quality responses
- Excellent instruction following
- Good for complex queries

**Cons:**
- Requires API access (may have waitlist)
- Paid service ($3/million input tokens)

### Option 3: Mock (For Testing)
```bash
AI_PROVIDER=mock
```

**Pros:**
- No API key needed
- Instant responses
- Free
- Good for testing system without external dependencies

**Cons:**
- Generic responses
- Limited intelligence
- Only uses property context

---

## Switching Providers

You can switch AI providers anytime by changing `.env`:

```bash
# Edit .env
nano .env

# Change AI_PROVIDER to: gemini, anthropic, or mock
AI_PROVIDER=gemini

# Restart server
# Ctrl+C then python main.py
```

---

## Gemini Models Available

### gemini-1.5-flash (Recommended - Default)
- **Best for:** Chat applications, real-time responses
- **Speed:** Very fast (~1-2 seconds)
- **Cost:** Free tier: 15 RPM, 1M TPM
- **Context window:** 1 million tokens
- **Use case:** MVP, testing, production chat

### gemini-1.5-pro
- **Best for:** Complex reasoning, long context
- **Speed:** Slower (~3-5 seconds)
- **Cost:** Free tier: 2 RPM, 32K TPM
- **Context window:** 2 million tokens
- **Use case:** Complex property matching, detailed analysis

### gemini-1.0-pro
- **Best for:** General purpose (older model)
- **Speed:** Fast
- **Cost:** Free tier: 60 RPM
- **Context window:** 30K tokens
- **Use case:** Legacy support

**For WhatsApp chat, use `gemini-1.5-flash` for best performance.**

---

## Testing Gemini Integration

### Test 1: Check Configuration

```bash
cd /Users/nurlasyraffie/Downloads/Workspace/whatsapp-ai-assistant
source venv/bin/activate
python -c "from execution.config import settings; print(f'AI Provider: {settings.ai_provider}')"
```

Should output: `AI Provider: gemini`

### Test 2: Test AI Response

```bash
# Replace with your actual conversation_id from database
python execution/ai_router.py <conversation-id> "Hi! I'm looking for a 3-bedroom condo in Marina Bay"
```

Should generate intelligent response using Gemini.

### Test 3: Full End-to-End

1. Send WhatsApp message to your connected number
2. Check logs: `tail -f logs/app.log`
3. Look for: `Using AI provider: gemini`
4. Verify response received on WhatsApp

---

## Gemini-Specific Features

### Temperature Control

Adjust response randomness in `.env`:

```bash
AI_TEMPERATURE=0.7  # Default: balanced (0.0-1.0)
AI_TEMPERATURE=0.3  # More focused, deterministic
AI_TEMPERATURE=0.9  # More creative, varied
```

### Max Tokens

Control response length:

```bash
AI_MAX_TOKENS=1024  # Default: ~750 words
AI_MAX_TOKENS=512   # Shorter responses
AI_MAX_TOKENS=2048  # Longer, detailed responses
```

---

## Troubleshooting

### Error: "GEMINI_API_KEY not set"

**Fix:**
```bash
# Check .env has the key
cat .env | grep GEMINI_API_KEY

# Add if missing
echo "GEMINI_API_KEY=your_key_here" >> .env

# Restart server
```

### Error: "google.generativeai not found"

**Fix:**
```bash
source venv/bin/activate
pip install google-generativeai==0.8.3
```

### Error: "API key not valid"

**Fix:**
1. Verify key starts with `AIza`
2. Check for extra spaces in `.env`
3. Get new key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### Responses too slow

**Fix:**
```bash
# Switch to faster model
GEMINI_MODEL=gemini-1.5-flash

# Or use mock for instant responses
AI_PROVIDER=mock
```

### Rate limit exceeded

**Symptoms:** Error after 15 messages/minute

**Fix:**
- Wait 1 minute
- Upgrade to paid tier for higher limits
- Use Claude (has higher free tier)

---

## Cost Comparison

### Gemini Free Tier
- **15 requests/minute**
- **1 million tokens/minute**
- **1,500 requests/day**
- **Cost:** $0

Perfect for MVP with <1000 messages/day.

### Gemini Paid (if you scale)
- **gemini-1.5-flash:** $0.075 per 1M input tokens, $0.30 per 1M output tokens
- **Example:** 10,000 messages/month = ~$5-10/month

### Claude for Comparison
- **Sonnet:** $3 per 1M input tokens, $15 per 1M output tokens
- **Example:** 10,000 messages/month = ~$30-50/month

**Gemini is 5-10x cheaper than Claude.**

---

## Production Recommendations

### For MVP (< 1000 messages/day)
```bash
AI_PROVIDER=gemini
GEMINI_MODEL=gemini-1.5-flash
# Use free tier
```

### For Scaling (1000-10,000 messages/day)
```bash
AI_PROVIDER=gemini
GEMINI_MODEL=gemini-1.5-flash
# Upgrade to paid tier ($5-10/month)
```

### For Enterprise (10,000+ messages/day)
```bash
AI_PROVIDER=gemini
GEMINI_MODEL=gemini-1.5-flash
# Or consider Claude for better quality
# Set up load balancing between providers
```

---

## Next Steps

1. **Get API key** (5 minutes): https://makers uite.google.com/app/apikey
2. **Add to .env** and restart server
3. **Test with WhatsApp message**
4. **Monitor usage** in [Google Cloud Console](https://console.cloud.google.com)
5. **Adjust settings** (temperature, max tokens) based on responses

---

## Additional Resources

- **Google AI Studio:** https://makersuite.google.com
- **Gemini API Docs:** https://ai.google.dev/docs
- **Pricing:** https://ai.google.dev/pricing
- **Rate Limits:** https://ai.google.dev/docs/rate_limits

---

**Gemini is now the default AI provider for your WhatsApp AI Assistant MVP!** 🚀

It's free, fast, and perfect for getting your MVP running without any costs. You can always switch to Claude later if you need higher quality responses.
