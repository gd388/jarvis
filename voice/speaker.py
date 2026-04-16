"""Voice speaker — text-to-speech using gTTS + pygame (primary) or pyttsx3 (fallback)."""

import logging
import os
import tempfile
from typing import Optional

from config.settings import settings
from utils import setup_logger

logger = setup_logger(__name__)


class VoiceSpeaker:
    """
    Converts text to speech and plays it through the system speakers.

    Primary backend  : gTTS (Google TTS) + pygame  — natural, high-quality voice.
    Fallback backend : pyttsx3 (espeak-ng)          — offline, lower quality.
    """

    def __init__(self) -> None:
        self._gtts_ok = False
        self._pyttsx3_ok = False
        self._pygame = None
        self._gtts_cls = None
        self._engine = None

        self._init_gtts()
        if not self._gtts_ok:
            self._init_pyttsx3()

    # ------------------------------------------------------------------ #
    #  Initialisation                                                      #
    # ------------------------------------------------------------------ #

    def _init_gtts(self) -> None:
        try:
            import pygame
            from gtts import gTTS  # noqa: F401 — import to validate availability

            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=2048)
            pygame.mixer.init()

            self._pygame = pygame
            from gtts import gTTS
            self._gtts_cls = gTTS
            self._gtts_ok = True
            logger.info("✓ Speaker ready  [gTTS + pygame]")
        except Exception as exc:
            logger.warning(f"⚠️  gTTS/pygame unavailable: {exc} — trying pyttsx3…")

    def _init_pyttsx3(self) -> None:
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.setProperty("rate", settings.VOICE_RATE)
            engine.setProperty("volume", settings.VOICE_VOLUME)

            # Prefer a lower-pitched voice if available (more Jarvis-like)
            voices = engine.getProperty("voices")
            if voices:
                engine.setProperty("voice", voices[0].id)

            self._engine = engine
            self._pyttsx3_ok = True
            logger.info("✓ Speaker ready  [pyttsx3]")
        except Exception as exc:
            logger.error(f"❌ No TTS backend available: {exc}")

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def speak(self, text: str) -> None:
        """Convert *text* to speech and block until playback completes."""
        if not text or not text.strip():
            return

        # Always echo to console so the user can read the response
        print(f"\n{'─'*60}")
        print(f"🤖  JARVIS: {text}")
        print(f"{'─'*60}\n")
        logger.info(f"🔊 Speaking: {text[:80]}{'…' if len(text) > 80 else ''}")

        if self._gtts_ok:
            self._speak_gtts(text)
        elif self._pyttsx3_ok:
            self._speak_pyttsx3(text)
        else:
            logger.error("❌ No TTS backend — cannot speak")

    # ------------------------------------------------------------------ #
    #  Backends                                                            #
    # ------------------------------------------------------------------ #

    def _speak_gtts(self, text: str) -> None:
        tmp: Optional[str] = None
        try:
            tts = self._gtts_cls(text=text, lang="en", slow=False)

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as fh:
                tmp = fh.name
            tts.save(tmp)

            self._pygame.mixer.music.load(tmp)
            self._pygame.mixer.music.play()

            # Block until playback finishes
            clock = self._pygame.time.Clock()
            while self._pygame.mixer.music.get_busy():
                clock.tick(10)

        except Exception as exc:
            logger.error(f"❌ gTTS playback error: {exc}")
            # Attempt fallback
            if self._pyttsx3_ok:
                self._speak_pyttsx3(text)
        finally:
            if tmp:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass

    def _speak_pyttsx3(self, text: str) -> None:
        try:
            self._engine.say(text)
            self._engine.runAndWait()
        except Exception as exc:
            logger.error(f"❌ pyttsx3 error: {exc}")

