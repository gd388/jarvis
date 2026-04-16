#!/usr/bin/env python3
"""Jarvis AI Assistant — Main Entry Point"""

# ── Suppress ALSA / Jack noise before any audio lib loads ──────────────────── #
import os
import ctypes

def _suppress_alsa_errors() -> None:
    """Redirect ALSA/Jack C-level stderr so noise never reaches the terminal."""
    try:
        asound = ctypes.cdll.LoadLibrary("libasound.so.2")
        asound.snd_lib_error_set_handler(None)   # silence ALSA C errors
    except Exception:
        pass
    # Also suppress via env var
    os.environ.setdefault("PYTHONWARNINGS", "ignore")

_suppress_alsa_errors()
# ─────────────────────────────────────────────────────────────────────────────  #

import sys
from agent.assistant import JarvisAssistant
from config.settings import settings
from utils import setup_logger

logger = setup_logger(__name__)


def main():
    try:
        settings.validate()
        logger.info("✓ Settings validated")
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
