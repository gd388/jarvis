"""LLM module — Groq API integration (groq SDK)."""

from groq import Groq

from config.settings import settings
from utils import setup_logger

logger = setup_logger(__name__)

_SYSTEM_PROMPT = """\
You are Jarvis, an advanced AI voice assistant modelled after J.A.R.V.I.S. from Iron Man.
You are highly intelligent, composed, and subtly witty. Address the user as "sir".

CRITICAL RULES — you MUST follow every single one:
1. NEVER ask a question. NEVER. Not even to clarify. Just answer with your best guess.
2. NEVER say "Would you like", "Do you want", "Shall I", "Could you", "Can you specify",
   "Which one", "What kind", "Did you mean" — these are ALL FORBIDDEN.
3. Give exactly ONE short answer in 1-2 sentences. Be decisive.
4. If the request is unclear, pick the most likely interpretation and go with it.
5. Speak naturally for text-to-speech — no bullets, markdown, asterisks, or special characters.
6. If someone says something you don't understand, say "I'm not sure about that, sir" and STOP.
7. NEVER list options or suggestions. Just give one direct answer.
"""


class GroqClient:
    """Handles communication with the Groq API."""

    # Keep last N exchanges (user+assistant pairs) in memory
    _MAX_HISTORY = 50

    def __init__(self) -> None:
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set")

        self.model = settings.MODEL_NAME
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self._history: list[dict] = []   # rolling conversation history
        logger.info(f"✓ Groq LLM ready  [model: {self.model}]")

    def clear_history(self) -> None:
        """Wipe conversation history (called when returning to standby)."""
        self._history.clear()
        logger.debug("🗑️  Conversation history cleared")

    def get_response(self, query: str) -> str:
        """Send *query* to the LLM and return the text response."""
        if not query or not query.strip():
            return "I didn't catch that, sir."

        logger.info(f"📤 → Groq: '{query[:120]}'")

        self._history.append({"role": "user", "content": query})
        # Trim to last _MAX_HISTORY exchanges (each exchange = 2 messages)
        if len(self._history) > self._MAX_HISTORY * 2:
            self._history = self._history[-(self._MAX_HISTORY * 2):]

        messages = [{"role": "system", "content": _SYSTEM_PROMPT}] + self._history

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.4,
            max_tokens=120,
        )
        result = response.choices[0].message.content.strip()
        self._history.append({"role": "assistant", "content": result})

        logger.info(f"📥 ← Groq: '{result[:120]}'")
        return result


