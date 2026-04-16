# Additional Documentation

## 🎓 GETTING STARTED GUIDE

### Step-by-Step Setup

#### 1. Environment Setup
```bash
# Navigate to project
cd /home/mobcoder-id-282/Desktop/jarvis

# Create virtual environment (recommended)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

#### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 3. Configure API Key
```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your Groq API key
nano .env  # or use your favorite editor
```

**Get Groq API Key:**
1. Visit https://console.groq.com
2. Sign up or log in
3. Create API key
4. Copy key to `.env` file

#### 4. Test Installation
```bash
# Test speech recognition
python -m speech_recognition

# Test pyttsx3
python -c "import pyttsx3; engine = pyttsx3.init(); engine.say('Hello'); engine.runAndWait()"
```

#### 5. Run Jarvis
```bash
python main.py
```

---

## 🔧 Configuration Details

### .env Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | N/A | **REQUIRED** - Groq API key |
| `WAKE_WORD` | Rise | Wake word to activate assistant |
| `MODEL_NAME` | llama3-70b-8192 | LLM model name |
| `TIMEOUT` | 10 | Seconds before speech recognition times out |
| `RETRY_ATTEMPTS` | 3 | Number of retry attempts for wake word |
| `VOICE_RATE` | 150 | Speech rate in words per minute |
| `VOICE_VOLUME` | 1.0 | Speaking volume (0.0-1.0) |
| `LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |

---

## 🐛 DEBUG MODE

### Enable Detailed Logging
Update `.env`:
```env
LOG_LEVEL=DEBUG
```

Then run:
```bash
python main.py 2>&1 | tee debug.log
```

### Check Microphone
```bash
python -m speech_recognition
```

### Test Each Component

**Test Voice Listener:**
```python
from voice.listener import VoiceListener
listener = VoiceListener()
text = listener.listen()
print(f"Heard: {text}")
```

**Test Voice Speaker:**
```python
from voice.speaker import VoiceSpeaker
speaker = VoiceSpeaker()
speaker.speak("Hello! This is Jarvis.")
```

**Test Groq LLM:**
```python
from llm.groq_client import GroqClient
llm = GroqClient()
response = llm.get_response("What is Python?")
print(response)
```

---

## 📊 System Architecture Flow

```
┌─────────────────────────────────────────────────────────┐
│                 JARVIS MAIN LOOP                        │
└─────────────────────────────────────────────────────────┘
                        ↓
         ┌──────────────────────────────┐
         │  Standby Mode (Listening)    │
         │  Waiting for "Rise"          │
         └──────────────────────────────┘
                        ↓
                  Wake Word Detected?
                   ↙          ↖
                Yes            No → Back to Standby
                ↓
    ┌────────────────────────────┐
    │  Active Mode                │
    │  Listening for Command      │
    └────────────────────────────┘
                ↓
        Speech Recognized?
         ↙              ↖
       Yes              No → Ask again
        ↓
    ┌────────────────────────────┐
    │  Check for Exit Command     │
    │  (stop/exit/quit/bye)       │
    └────────────────────────────┘
         ↙             ↖
       Yes            No → Continue
        ↓               ↓
    Return to       ┌──────────────────┐
    Standby         │ Send to Groq LLM │
                    └──────────────────┘
                            ↓
                    ┌──────────────────┐
                    │ Get Response     │
                    └──────────────────┘
                            ↓
                    ┌──────────────────┐
                    │ Speak Response   │
                    └──────────────────┘
                            ↓
                    Listen for Next Command
```

---

## 🚀 Performance Optimization

### Reduce Latency
1. **Increase wake word timeout:**
   ```env
   TIMEOUT=5  # Instead of 10
   ```

2. **Reduce retry attempts:**
   ```env
   RETRY_ATTEMPTS=1  # Skip retries
   ```

3. **Faster speech rate:**
   ```env
   VOICE_RATE=200  # Faster speech
   ```

### Improve Wake Word Accuracy
1. Speak clearly and close to mic
2. Reduce background noise
3. Calibrate microphone: Delete mic index
   ```python
   # In listener.py, delete this if it exists:
   mic = sr.Microphone()  # Recreates index
   ```

---

## 🔐 Security Notes

- **API Key Safety**: Never commit `.env` to git
- **Logs**: Check `logs/` directory for sensitive data
- **Microphone**: Runs with system-level audio access

### .gitignore (Already included)
```
.env
__pycache__/
*.pyc
logs/
venv/
*.log
```

---

## 🌐 API Costs

### Groq API
- **Free tier**: Generally sufficient for personal use
- **Cost**: Small inference costs (~$0.0005 per 1M tokens)
- **Monitor at**: https://console.groq.com

### Google Speech Recognition
- **Free tier**: Included with SpeechRecognition library
- **Rate limit**: ~100-200 requests/day for anonymous use
- **Recommendation**: Implement API key for higher limits

---

## 🎯 Common Customizations

### Change Wake Word
```env
WAKE_WORD=Jarvis  # or any single word
```

### Add Multiple Wake Words
Modify `voice/listener.py`:
```python
wake_words = ["Rise", "Jarvis", "Hey"]
if any(word in recognized_text.lower() for word in wake_words):
    return True
```

### Change Voice Gender
```python
# In voice/speaker.py, change voice_id parameter
speaker = VoiceSpeaker(voice_id=1)  # 0=default, 1=alternative
```

### Custom System Prompt
```python
# In llm/groq_client.py, modify SYSTEM_PROMPT
SYSTEM_PROMPT = """Your custom prompt here"""
```

---

## 📈 Scaling Considerations

### For Production:
1. **Add error recovery**: Implement retry with exponential backoff
2. **Add monitoring**: Track API usage and errors
3. **Add queuing**: Buffer commands during high load
4. **Add multi-turn context**: Maintain conversation history
5. **Add skill system**: Plugin architecture for extensibility

### Example: Add Context Memory
```python
class JarvisAssistant:
    def __init__(self):
        self.conversation_history = []
    
    def remember(self, user_msg, assistant_response):
        self.conversation_history.append({
            "user": user_msg,
            "assistant": assistant_response
        })
```

---

## 📚 Additional Resources

- [SpeechRecognition Docs](https://github.com/Uberi/speech_recognition)
- [pyttsx3 Docs](https://pyttsx3.readthedocs.io/)
- [LangChain Docs](https://python.langchain.com/)
- [Groq API Docs](https://console.groq.com/docs)

---

## ❓ FAQ

**Q: How do I change the LLM model?**
A: Edit `.env`:
```env
MODEL_NAME=gemma-7b-it  # or another Groq model
```

**Q: Can I run this without internet?**
A: Partially - speech recognition and LLM require internet. Voice output works offline.

**Q: How do I make it start at boot?**
A: Create a systemd service or cron job that runs `python /path/to/main.py`

**Q: Can I use a different speech recognition?**
A: Yes, modify `voice/listener.py` to use Whisper, AssemblyAI, etc.

---

**Last Updated**: 2024
