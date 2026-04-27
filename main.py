#!/usr/bin/env python3
"""Jarvis AI Assistant — Main Entry Point"""

# ── Suppress ALSA / Jack noise before any audio lib loads ──────────────────── #
import os
import ctypes

# CFUNCTYPE signature for snd_lib_error_handler_t
_ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(
    None,
    ctypes.c_char_p, ctypes.c_int,
    ctypes.c_char_p, ctypes.c_int,
    ctypes.c_char_p,
)
# Must stay alive at module level — if GC'd, ALSA calls a freed pointer → segfault
_noop_handler = _ERROR_HANDLER_FUNC(lambda *args: None)

def _suppress_alsa_errors() -> None:
    """Silence ALSA C-level noise via a no-op error handler."""
    try:
        asound = ctypes.cdll.LoadLibrary("libasound.so.2")
        asound.snd_lib_error_set_handler(_noop_handler)
    except Exception:
        pass
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
