"""LLM module — Groq API integration via langchain-groq."""

from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage

from config.settings import settings
from utils import setup_logger

logger = setup_logger(__name__)

_SYSTEM_PROMPT = """\
You are Jarvis, an advanced AI assistant modelled after the iconic J.A.R.V.I.S. from Iron Man.
You are highly intelligent, composed, and subtly witty. You address the user respectfully.

IMPORTANT — you are speaking aloud via text-to-speech:
- Keep answers concise and conversational (2-4 sentences unless asked for detail).
- Avoid bullet points, markdown, code blocks, or special characters in your responses.
- Speak naturally as if talking, not writing.
- If you don't know something, say so honestly and briefly.
"""


class GroqClient:
    """Handles communication with the Groq LLM API."""

    def __init__(self) -> None:
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set")

        self.model = settings.MODEL_NAME
        self.llm = ChatGroq(
            model=self.model,
            api_key=settings.GROQ_API_KEY,
            temperature=0.7,
            max_tokens=512,   # concise for voice
        )
        logger.info(f"✓ Groq LLM ready  [model: {self.model}]")

    def get_response(self, query: str) -> str:
        """
        Send *query* to the LLM and return the text response.
        Raises on API failure so the caller can handle it.
        """
        if not query or not query.strip():
            return "I didn't catch that. Could you please repeat your question?"

        logger.info(f"📤 → Groq: '{query[:120]}'")

        messages = [
            SystemMessage(content=_SYSTEM_PROMPT),
            HumanMessage(content=query),
        ]
        response = self.llm.invoke(messages)
        result = response.content.strip()

        logger.info(f"📥 ← Groq: '{result[:120]}'")
        return result

