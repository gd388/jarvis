"""
Settings and configuration for the Jarvis Assistant.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # API
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # LLM
    MODEL_NAME: str = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")

    # Wake word
    WAKE_WORD: str = os.getenv("WAKE_WORD", "Rise").lower()

    # Listener
    LISTEN_TIMEOUT: int = int(os.getenv("LISTEN_TIMEOUT", "5"))    # secs to wait for speech
    COMMAND_TIMEOUT: int = int(os.getenv("COMMAND_TIMEOUT", "8"))   # secs for a full command
    PHRASE_LIMIT: int = int(os.getenv("PHRASE_LIMIT", "10"))        # max phrase length secs
    COMMAND_RETRIES: int = int(os.getenv("COMMAND_RETRIES", "3"))   # retries before standby

    # Speaker
    VOICE_RATE: int = int(os.getenv("VOICE_RATE", "160"))
    VOICE_VOLUME: float = float(os.getenv("VOICE_VOLUME", "1.0"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> None:
        if not cls.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is not set in the .env file")


settings = Settings()
