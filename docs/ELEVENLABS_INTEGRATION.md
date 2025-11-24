# ElevenLabs TTS Integration with LiveKit

**Status:** Ready for Production **Last Updated:** 2025-11-16

This guide shows how to integrate ElevenLabs TTS with your LiveKit voice agent
for superior voice quality and natural-sounding speech.

---

## 📋 Prerequisites

1. **ElevenLabs Account**

   - Sign up at [elevenlabs.io](https://elevenlabs.io)
   - Get API key from
     [Settings → API Keys](https://elevenlabs.io/app/settings/api-keys)

2. **LiveKit Setup**

   - LiveKit server running (self-hosted or cloud)
   - LiveKit credentials configured

3. **Python Environment**
   - Python 3.8+
   - Virtual environment activated

---

## 🚀 Quick Start

### 1. Install ElevenLabs Plugin

```bash
# Install the ElevenLabs plugin for LiveKit
pip install livekit-plugins-elevenlabs

# Or add to your requirements.txt
echo "livekit-plugins-elevenlabs>=0.6.0" >> backend/requirements.txt
pip install -r backend/requirements.txt
```

### 2. Set API Key

**Option A: Environment Variable (Development)**

```bash
# Add to your .env file
echo "ELEVENLABS_API_KEY=sk_your_api_key_here" >> .env
```

**Option B: AWS SSM Parameter Store (Production)**

```bash
# Use the env_to_ssm.py script to add to SSM
python3 scripts/env_to_ssm.py \
  --env-file .env \
  --prefix /foundry/prod \
  --format bash > put_prod_params.sh

chmod +x put_prod_params.sh
./put_prod_params.sh
```

### 3. Update Voice Agent Worker

Replace `openai.TTS()` with `elevenlabs.TTS()` in your voice agent:

```python
from livekit.plugins import elevenlabs

# In your entrypoint function:
session = AgentSession(
    vad=silero.VAD.load(),
    stt=deepgram.STT(),
    llm=openai.LLM(model="gpt-4o-mini"),
    tts=elevenlabs.TTS(
        model_id="eleven_turbo_v2_5",  # Fastest model for real-time
        voice="Rachel",                # Professional female voice
    ),
)
```

---

## 🎙️ Voice Selection Guide

ElevenLabs provides high-quality pre-made voices. Choose based on your use case:

### **Professional / Business Assistant**

| Voice      | Gender | Description                  | Best For                     |
| ---------- | ------ | ---------------------------- | ---------------------------- |
| **Rachel** | Female | Calm, professional, friendly | Customer service, assistants |
| **Josh**   | Male   | Deep, authoritative          | Executive assistant, news    |
| **Antoni** | Male   | Well-rounded, versatile      | General purpose, tutorials   |

### **Friendly / Casual**

| Voice     | Gender | Description              | Best For                     |
| --------- | ------ | ------------------------ | ---------------------------- |
| **Bella** | Female | Soft, warm, approachable | Support, education           |
| **Elli**  | Female | Energetic, enthusiastic  | Marketing, demos             |
| **Sam**   | Male   | Dynamic, engaging        | Presentations, entertainment |

### **Technical / Authoritative**

| Voice      | Gender | Description           | Best For                    |
| ---------- | ------ | --------------------- | --------------------------- |
| **Adam**   | Male   | Deep, confident       | Technical content, reports  |
| **Arnold** | Male   | Crisp, clear, precise | Instructions, documentation |

**💡 Tip:** Test different voices at
[elevenlabs.io/voice-lab](https://elevenlabs.io/voice-lab)

---

## ⚙️ Configuration Options

### **Model Selection**

```python
# FASTEST - Lowest latency, English only (recommended for real-time)
model_id="eleven_turbo_v2_5"

# FAST - Low latency, English only
model_id="eleven_turbo_v2"

# BEST QUALITY - Supports 29 languages (higher latency)
model_id="eleven_multilingual_v2"
```

### **Voice Quality Tuning**

```python
tts=elevenlabs.TTS(
    model_id="eleven_turbo_v2_5",
    voice="Rachel",

    # Stability: 0-1 (higher = more consistent, lower = more expressive)
    stability=0.5,

    # Similarity Boost: 0-1 (higher = closer to original voice)
    similarity_boost=0.75,

    # Latency Optimization: 0-4 (higher = lower latency, may affect quality)
    optimize_streaming_latency=4,
)
```

### **Recommended Settings by Use Case**

**Customer Service / Support:**

```python
tts=elevenlabs.TTS(
    model_id="eleven_turbo_v2_5",
    voice="Rachel",
    stability=0.7,              # More consistent
    similarity_boost=0.8,       # Stay close to voice
    optimize_streaming_latency=3,
)
```

**Creative / Storytelling:**

```python
tts=elevenlabs.TTS(
    model_id="eleven_multilingual_v2",  # Best quality
    voice="Bella",
    stability=0.3,              # More expressive
    similarity_boost=0.6,       # Allow variation
    optimize_streaming_latency=1,
)
```

**Technical / Professional:**

```python
tts=elevenlabs.TTS(
    model_id="eleven_turbo_v2_5",
    voice="Adam",
    stability=0.8,              # Very consistent
    similarity_boost=0.9,       # Precise voice matching
    optimize_streaming_latency=4,
)
```

---

## 🔧 Advanced Features

### **SSML Support**

Use SSML tags for fine-grained control over pronunciation, pauses, emphasis:

```python
tts=elevenlabs.TTS(
    model_id="eleven_turbo_v2_5",
    voice="Rachel",
    enable_ssml_parsing=True,  # Enable SSML support
)

# In your agent instructions or responses:
# <speak>
#   <prosody rate="slow">This will be spoken slowly.</prosody>
#   <break time="500ms"/>
#   <emphasis level="strong">This is important!</emphasis>
# </speak>
```

### **Word-Level Timestamps**

Useful for lip sync, captions, or analytics:

```python
# The plugin automatically provides word-level timestamps
# Access them via the TTS stream events
```

### **Voice Cloning (Professional Plan)**

If you have a professional ElevenLabs plan, you can use custom cloned voices:

```python
tts=elevenlabs.TTS(
    model_id="eleven_turbo_v2_5",
    voice="your_custom_voice_id",  # From ElevenLabs dashboard
)
```

---

## 📊 Cost Estimation

ElevenLabs pricing is based on characters generated:

| Plan        | Characters/month | Cost | Use Case         |
| ----------- | ---------------- | ---- | ---------------- |
| **Free**    | 10,000           | $0   | Testing, demos   |
| **Starter** | 30,000           | $5   | Small projects   |
| **Creator** | 100,000          | $22  | Production apps  |
| **Pro**     | 500,000          | $99  | High-volume apps |

**💡 Estimation:**

- Average voice agent call: ~500 words
- Average word length: 5 characters
- **Per call:** ~2,500 characters
- **100 calls/day:** ~250,000 chars/month = **Creator plan**

Monitor usage at [elevenlabs.io/usage](https://elevenlabs.io/usage)

---

## 🧪 Testing

### Local Testing

1. **Set environment variables:**

   ```bash
   export ELEVENLABS_API_KEY="sk_..."
   export LIVEKIT_URL="ws://localhost:7880"
   export LIVEKIT_API_KEY="devkey"
   export LIVEKIT_API_SECRET="secret"
   ```

2. **Run the voice agent worker:**

   ```bash
   python backend/voice_agent_worker_elevenlabs.py dev
   ```

3. **Test in your UI:**
   - Navigate to `/chat` (playground)
   - Click "Start Voice Chat"
   - Speak and listen to the ElevenLabs TTS response

### Production Testing

```bash
# Deploy to ECS and test
# The worker will automatically use SSM parameters
```

---

## 🚨 Troubleshooting

### **API Key Not Found**

```
❌ ELEVENLABS_API_KEY environment variable not set!
```

**Fix:**

- Ensure `.env` file has `ELEVENLABS_API_KEY=sk_...`
- For production, verify SSM parameter exists:
  `/foundry/prod/ELEVENLABS_API_KEY`

### **Voice Not Available**

```
Error: Voice 'XYZ' not found
```

**Fix:**

- Check available voices at
  [elevenlabs.io/voice-library](https://elevenlabs.io/voice-library)
- Use voice name exactly as shown (case-sensitive)

### **High Latency**

**Fix:**

- Use `model_id="eleven_turbo_v2_5"` (fastest)
- Increase `optimize_streaming_latency` to 4
- Check your internet connection to ElevenLabs API

### **Quota Exceeded**

```
Error: Character limit exceeded for current billing period
```

**Fix:**

- Upgrade plan at [elevenlabs.io/pricing](https://elevenlabs.io/pricing)
- Monitor usage at [elevenlabs.io/usage](https://elevenlabs.io/usage)

---

## 🔄 Migration from OpenAI TTS

**Before (OpenAI):**

```python
from livekit.plugins import openai

tts=openai.TTS(voice="alloy")
```

**After (ElevenLabs):**

```python
from livekit.plugins import elevenlabs

tts=elevenlabs.TTS(
    model_id="eleven_turbo_v2_5",
    voice="Rachel",
)
```

**Key Differences:**

- **Quality:** ElevenLabs voices are more natural and expressive
- **Latency:** Similar with `eleven_turbo_v2_5`, slightly higher with
  multilingual models
- **Cost:** ElevenLabs charges per character, OpenAI per request
- **Voice Options:** ElevenLabs has more diverse voice library
- **Customization:** ElevenLabs offers voice cloning (Pro plan)

---

## 📚 Resources

- **ElevenLabs Documentation:** https://elevenlabs.io/docs
- **LiveKit Agents Guide:** https://docs.livekit.io/agents/
- **Voice Library:** https://elevenlabs.io/voice-library
- **API Reference:** https://elevenlabs.io/docs/api-reference
- **Pricing:** https://elevenlabs.io/pricing

---

## ✅ Production Checklist

- [ ] ElevenLabs API key added to `.env` (dev) and SSM (prod)
- [ ] Voice agent worker updated to use `elevenlabs.TTS()`
- [ ] Voice selection tested and finalized
- [ ] Model optimized for latency (`eleven_turbo_v2_5`)
- [ ] Cost monitoring set up (track monthly usage)
- [ ] Fallback plan if quota exceeded (switch to OpenAI TTS)
- [ ] Error handling for API failures
- [ ] Tested in production environment

---

**Generated by:** Claude Code **Last Updated:** 2025-11-16 **Version:** 1.0
