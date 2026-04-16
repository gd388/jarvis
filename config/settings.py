"""
Settings and configuration for the Jarvis Assistant.
Loads environment variables and provides sensible defaults.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings"""
    
    # API Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    
    # Assistant Configuration
    WAKE_WORD = os.getenv("WAKE_WORD", "Rise").lower()
    MODEL_NAME = os.getenv("MODEL_NAME", "llama3-70b-8192")
    TIMEOUT = int(os.getenv("TIMEOUT", "10"))
    RETRY_ATTEMPTS = int(os.getenv("RETRY_ATTEMPTS", "3"))
    
    # Voice Configuration
    VOICE_RATE = int(os.getenv("VOICE_RATE", "150"))
    VOICE_VOLUME = float(os.getenv("VOICE_VOLUME", "1.0"))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Wake word detection delay (seconds) - prevents re-triggering on assistant voice
    WAKE_WORD_COOLDOWN = 1.0
    
    @classmethod
    def validate(cls):
        """Validate that all required settings are present"""
        if not cls.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not set in environment variables")
        return True


# Export settings instance
settings = Settings()
