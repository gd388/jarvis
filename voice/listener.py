"""Voice listener — speech-to-text via microphone using SpeechRecognition."""

import logging
from typing import Optional

import speech_recognition as sr

from config.settings import settings
from utils import setup_logger

logger = setup_logger(__name__)


class VoiceListener:
    """
    Captures microphone audio and converts it to text.

    - listen_for_wake_word(): blocks until the wake word is detected.
    - listen_command(): listens once for a user command (with retries).
    """

    def __init__(self) -> None:
        self.recognizer = sr.Recognizer()

        # Tune recognizer
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8       # secs of silence = end of phrase
        self.recognizer.non_speaking_duration = 0.5

        logger.info("🎙️  Calibrating microphone for ambient noise…")
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1.5)
        logger.info(
            f"✓ Microphone ready  (energy threshold: {self.recognizer.energy_threshold:.0f})"
        )

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _listen_once(
        self,
        listen_timeout: int = 5,
        phrase_time_limit: int = 8,
    ) -> Optional[str]:
        """
        Record one phrase from the microphone and return its text.

        Returns None on silence, noise, or API errors — never raises.
        """
        try:
            with sr.Microphone() as source:
                logger.debug("🎤 Listening…")
                audio = self.recognizer.listen(
                    source,
                    timeout=listen_timeout,
                    phrase_time_limit=phrase_time_limit,
                )

            text = self.recognizer.recognize_google(audio).strip().lower()
            logger.info(f"🗣️  Heard: '{text}'")
            return text

        except sr.WaitTimeoutError:
            logger.debug("⏱️  Timeout — no speech detected")
            return None
        except sr.UnknownValueError:
            logger.debug("🔇 Could not understand audio")
            return None
        except sr.RequestError as exc:
            logger.error(f"❌ Google Speech API error: {exc}")
            return None
        except Exception as exc:
            logger.error(f"❌ Unexpected listener error: {exc}")
            return None

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def listen_for_wake_word(self) -> bool:
        """
        Loop indefinitely, sampling short audio chunks, until the wake word
        (settings.WAKE_WORD) is heard.  Returns True when detected.
        """
        wake_word = settings.WAKE_WORD.lower()
        logger.info(f"👂 Waiting for wake word: '{wake_word}' …")

        while True:
            text = self._listen_once(listen_timeout=5, phrase_time_limit=3)
            if text and wake_word in text:
                logger.info(f"🔔 Wake word detected in: '{text}'")
                return True

    def listen_command(self) -> Optional[str]:
        """
        Listen for a command after activation.

        Retries up to settings.COMMAND_RETRIES times. Returns the recognised
        text or None if all attempts fail.
        """
        logger.info("🎤 Listening for your command…")

        for attempt in range(1, settings.COMMAND_RETRIES + 1):
            text = self._listen_once(
                listen_timeout=settings.COMMAND_TIMEOUT,
                phrase_time_limit=settings.PHRASE_LIMIT,
            )
            if text:
                return text

            if attempt < settings.COMMAND_RETRIES:
                logger.warning(
                    f"⚠️  Attempt {attempt}/{settings.COMMAND_RETRIES} — "
                    "no speech detected. Please speak clearly."
                )

        logger.warning("⚠️  No command received after all attempts")
        return None

