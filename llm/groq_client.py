"""LLM module — Groq API integration via langchain-groq."""

from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage

from config.settings import settings
from utils import setup_logger

logger = setup_logger(__name__)

_SYSTEM_PROMPT = """\
You are Jarvis, an advanced AI assistant modelled after the iconic J.A.R.V.I.S. from Iron Man.
You are highly intelligent, composed, and subtly witty. You address the user as "sir".

RULES — follow these strictly:
- NEVER ask follow-up questions. Always give a direct, complete answer immediately.
- NEVER say "Would you like..." or "Do you want..." or "Shall I..." — just answer.
- Keep answers to 1-2 short sentences. Be direct and decisive.
- Speak naturally for text-to-speech — no bullet points, markdown, or special characters.
- If you don't know something, say so in one sentence.
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

