#!/usr/bin/env python3
"""
Jarvis AI Assistant - Main Entry Point

A production-level voice assistant that:
- Listens for wake word ("Rise")
- Processes user commands via Groq LLM
- Responds with natural language via text-to-speech

Usage:
    python main.py

Requirements:
    - python-dotenv (for environment variables)
    - SpeechRecognition (for voice input)
    - pyttsx3 (for voice output)
    - langchain-groq (for LLM integration)
"""

import sys
import logging
from agent.assistant import JarvisAssistant
from config.settings import settings
from utils import setup_logger

logger = setup_logger(__name__)


def main():
    """Main entry point"""
    try:
        # Validate settings
        settings.validate()
        logger.info("✓ Settings validated")
        
        # Initialize and run assistant
        jarvis = JarvisAssistant()
        jarvis.run()
        
    except ValueError as e:
        logger.error(f"❌ Configuration Error: {e}")
        logger.error("Please ensure GROQ_API_KEY is set in .env file")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("\n⏹️ Assistant terminated by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
