# Technical Architecture & Design Patterns

## 🏗️ System Design

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                    JARVIS ASSISTANT                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   VOICE IN   │  │     LLM      │  │  VOICE OUT   │   │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤   │
│  │ • Listener   │  │ • Groq       │  │ • Speaker    │   │
│  │ • Recognizer │  │ • LangChain  │  │ • pyttsx3    │   │
│  │ • Error      │  │ • Validation │  │ • TTS Engine │   │
│  │   Handling   │  │              │  │              │   │
│  └──────────────┘  └──────────────┘  └──────────────┘   │
│         ↑                  ↑                  ↑            │
│         └──────────────────┼──────────────────┘            │
│                            │                              │
│         ┌──────────────────▼───────────────────┐          │
│         │     ASSISTANT (Orchestrator)        │          │
│         ├────────────────────────────────────┤          │
│         │ • Wake Word Detection                │          │
│         │ • Command Processing                 │          │
│         │ • Session Management                 │          │
│         │ • Error Recovery                     │          │
│         └────────────────────────────────────┘          │
│                            ↑                              │
│         ┌──────────────────┴───────────────────┐          │
│         │   SETTINGS & CONFIG                 │          │
│         ├────────────────────────────────────┤          │
│         │ • Environment Variables              │          │
│         │ • Logging Configuration              │          │
│         │ • Model Parameters                   │          │
│         └────────────────────────────────────┘          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Design Patterns Used

### 1. **Singleton Pattern** (VoiceListener, VoiceSpeaker, GroqClient)
```python
# Single instance reused throughout application
self.listener = VoiceListener()  # Created once
self.speaker = VoiceSpeaker()    # Single speaker
self.llm = GroqClient()          # Single LLM connection
```

**Benefits:**
- Resource efficiency (single microphone/speaker)
- Consistent state management
- Easy configuration

### 2. **Facade Pattern** (JarvisAssistant)
```python
class JarvisAssistant:
    # Hides complexity of multiple subsystems
    # Simple interface: run()
    
    def __init__(self):
        self.listener  # Complex voice recognition
        self.speaker   # Complex TTS
        self.llm       # Complex LLM integration
```

**Benefits:**
- Simplified interface for complexity
- Easy to test individual components
- Clear separation of concerns

### 3. **Configuration Management** (Settings Pattern)
```python
# Centralized settings with defaults
class Settings:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    WAKE_WORD = os.getenv("WAKE_WORD", "Rise")
```

**Benefits:**
- Single source of truth
- Easy configuration changes
- Default fallbacks

---

## 🔄 Event Flow Diagram

```
START
  ↓
[Initialize Components]
  ↓ Success
Validate Groq API ← Logs info + state
  ↓ Valid
Speak "Jarvis online"
  ↓
┌─────────────────────────────────────────────┐
│ MAIN EVENT LOOP                             │
│ ┌──────────────────────────────────────┐   │
│ │ STANDBY MODE                         │   │
│ │  wait_for_wake_word("Rise")          │   │
│ │  [Listening in background]           │   │
│ └──────────────────────────────────────┘   │
│  ↓ Match found                              │
│ ┌──────────────────────────────────────┐   │
│ │ ACTIVE MODE                          │   │
│ │ ┌────────────────────────────────┐  │   │
│ │ │ Listen for Command             │  │   │
│ │ │ listen_command()               │  │   │
│ │ └────────────────────────────────┘  │   │
│ │  ↓ Command received                  │   │
│ │ ┌────────────────────────────────┐  │   │
│ │ │ Process Command                │  │   │
│ │ │ process_command(cmd)           │  │   │
│ │ └────────────────────────────────┘  │   │
│ │  ↓                                   │   │
│ │ [Check for Exit Commands?]           │   │
│ │  ↙ Yes              ↖ No             │   │
│ │ Exit to          Get LLM Response    │   │
│ │ Standby              ↓               │   │
│ │                  llm.get_response()  │   │
│ │                      ↓               │   │
│ │                  Speak Response      │   │
│ │                  speaker.speak()     │   │
│ │                      ↓               │   │
│ │                  Return to listening │   │
│ └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
  ↑
  └─ LOOP (Ctrl+C to exit)
```

---

## 🔌 Module Responsibilities

### `main.py`
- Entry point
- Validates configuration
- Initializes assistant
- Handles top-level exceptions

### `config/settings.py`
- Environment variable management
- Configuration validation
- Default values
- Settings export

### `utils.py`
- Logging setup
- Logger creation
- Console + file handlers
- Consistent formatting

### `voice/listener.py`
- Microphone initialization
- Speech-to-text conversion
- Ambient noise calibration
- Retry logic
- Error handling
  - NoSpeechError
  - UnknownValueError
  - RequestError
  - TimeoutError

### `voice/speaker.py`
- TTS engine initialization
- Text-to-speech conversion
- Voice configuration
- Rate/volume adjustment
- Error handling

### `llm/groq_client.py`
- Groq API integration
- LLM initialization
- Message formatting
- Response generation
- API validation
- Error handling

### `agent/assistant.py`
- Component orchestration
- Event loop management
- Session state tracking
- Wake word detection
- Command processing
- Exit command detection
- Cleanup on shutdown

---

## 🛡️ Error Handling Strategy

### Layered Error Handling

```
┌─────────────────────────────────┐
│ GLOBAL EXCEPTION HANDLER        │
│ (Try-catch at main.py level)    │
└────────────────┬────────────────┘
                 ↓
┌─────────────────────────────────┐
│ ASSISTANT LEVEL                 │
│ (Try-catch in main loop)         │
└────────────────┬────────────────┘
                 ↓
┌─────────────────────────────────┐
│ COMPONENT LEVEL                 │
│ (Try-catch in each method)       │
└─────────────────────────────────┘
```

### Exception Types

| Exception | Layer | Handling |
|-----------|-------|----------|
| `sr.UnknownValueError` | Listener | Log warning, retry |
| `sr.RequestError` | Listener | Log error, fallback |
| `sr.WaitTimeoutError` | Listener | Log warning, continue |
| `ValueError` (API key) | LLM | Exit with error message |
| `Exception` (API call) | LLM | Log error, speak fallback |
| `KeyboardInterrupt` | Main | Graceful shutdown |

---

## 📊 State Management

### JarvisAssistant State Variables

```python
class JarvisAssistant:
    is_active: bool              # Currently in active session
    last_wake_time: float        # Timestamp of last wake
    wake_word: str               # Current wake word
    listener: VoiceListener      # Input component
    speaker: VoiceSpeaker        # Output component
    llm: GroqClient             # LLM component
```

### State Transitions

```
Initialized (False)
    ↓
Standby (is_active=False)
    ↓
Waiting for Wake Word
    ↓
Wake Word Detected ← [last_wake_time updated]
    ↓
Active (is_active=True)
    ↓
Listening for Command
    ↓
Exit Command Detected?
    ├─ Yes → Standby (is_active=False)
    └─ No  → Process & Loop
```

---

## ⚡ Performance Characteristics

### Timing Breakdown

```
User Says "Rise"
    ↓ 0.2s - Audio buffer
    ↓ 0.3s - Speech recognition API
Result: ~0.5s to recognize

Command → LLM
    ↓ 0.1s - Send request
    ↓ 0.8s - LLM inference (Groq is fast!)
    ↓ 0.1s - Receive response
Result: ~1s for response

Response → Speech
    ↓ (N * 0.02s) - Generate audio (N = words)
    ↓ N*0.03s - Play audio
Result: ~1-2s depending on response length

Total: ~2-3.5s end-to-end
```

### Resource Usage

| Resource | Usage |
|----------|-------|
| **CPU** | ~5-10% peak (mostly during TTS) |
| **Memory** | ~150-200 MB (models + runtime) |
| **Disk** | ~500 MB (dependencies) |
| **Network** | ~10-50 KB per request |

---

## 🔐 Security Considerations

### API Key Management
```
✓ Never hardcoded
✓ Loaded from .env (git-ignored)
✓ Validated at startup
✗ Never logged
✗ Never in error messages
```

### Microphone Access
```
✓ Requested system-level permission
✓ Only used during listening
✓ Cleaned up on exit
```

### Input Validation
```
✓ Check for empty strings
✓ Validate API responses
✓ Handle malformed input
```

---

## 🧪 Testing Strategy

### Unit Testing (Could add)
```python
def test_listener_empty_command():
    listener = VoiceListener()
    assert listener.listen() is None  # Empty audio

def test_speaker_empty_text():
    speaker = VoiceSpeaker()
    assert speaker.speak("") == False
```

### Integration Testing (Could add)
```python
def test_full_flow():
    assistant = JarvisAssistant()
    # Would need to mock speech input
    # Verify LLM calls work end-to-end
```

### Manual Testing Checklist
- [ ] Wake word detection works
- [ ] Multiple commands in sequence work
- [ ] Exit commands work
- [ ] Error recovery works
- [ ] Logging is comprehensive
- [ ] API connection fails gracefully

---

## 📈 Scalability Enhancements

### Potential Improvements

1. **Multi-threaded Listening**
   ```python
   # Listen while processing
   listen_thread = Thread(target=continuous_listen)
   ```

2. **Command Queuing**
   ```python
   from queue import Queue
   command_queue = Queue()  # Buffer multiple commands
   ```

3. **Context Storage**
   ```python
   # Store conversation history
   conversation_db = {
       "timestamp": message,
       ...
   }
   ```

4. **Skill System**
   ```python
   # Plugin architecture
   class Skill:
       def can_handle(self, command): pass
       def execute(self, command): pass
   ```

5. **Monitoring/Metrics**
   ```python
   # Track performance
   metrics = {
       "commands_processed": 0,
       "avg_response_time": 0,
       "error_rate": 0
   }
   ```

---

## 🔍 Logging Strategy

### Log Levels

```
DEBUG: Detailed diagnostic info
    - Parameter values
    - Function entry/exit
    - Internal state changes

INFO: General informational messages (DEFAULT)
    - Component initialization
    - User actions (wake word detected)
    - Normal flow progress

WARNING: Warning messages (potential issues)
    - Timeouts
    - Failed recognition
    - API rate limits

ERROR: Error messages (problems)
    - API failures
    - Initialization errors
    - Unexpected exceptions
```

### Log Output Channels

```
Console Output
    ├─ Real-time feedback
    ├─ Emoji indicators for UX
    └─ Color coding (if terminal supports)

File Output
    ├─ Timestamped logs
    ├─ Complete history
    └─ logs/jarvis_YYYYMMDD_HHMMSS.log
```

---

**Architecture Last Updated**: 2024
