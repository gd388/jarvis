"""Voice listener — speech-to-text via microphone using SpeechRecognition."""

import logging
import os
import sys
import time
from typing import Optional, TYPE_CHECKING

import speech_recognition as sr

from config.settings import settings
from utils import setup_logger

if TYPE_CHECKING:
    from voice.speaker import VoiceSpeaker

logger = setup_logger(__name__)


def _quiet_mic():
    """Open sr.Microphone() with Jack/PortAudio noise silenced.

    Redirects both fd 1 (stdout) and fd 2 (stderr) to /dev/null during the
    PortAudio device probe, then restores them.  Jack's libjack writes noise
    from background threads, so we hold the redirect for 0.5 s after open.
    """
    mic = sr.Microphone()
    sys.stdout.flush()
    sys.stderr.flush()
    saved_1 = os.dup(1)
    saved_2 = os.dup(2)
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, 1)
    os.dup2(devnull, 2)
    os.close(devnull)
    try:
        mic.__enter__()
        time.sleep(0.5)          # let Jack background threads finish
    except Exception:
        os.dup2(saved_1, 1)
        os.dup2(saved_2, 2)
        os.close(saved_1)
        os.close(saved_2)
        raise
    os.dup2(saved_1, 1)
    os.dup2(saved_2, 2)
    os.close(saved_1)
    os.close(saved_2)
    return mic


class VoiceListener:
    """
    Captures microphone audio and converts it to text.

    Pass *speaker* so the listener can suppress mic captures that happen
    while Jarvis is speaking (avoids self-pickup echo).
    """

    def __init__(self, speaker: Optional["VoiceSpeaker"] = None) -> None:
        self._speaker = speaker
        self.recognizer = sr.Recognizer()

        # Tune recognizer — favour capturing full sentences
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15
        self.recognizer.dynamic_energy_ratio = 1.5
        self.recognizer.pause_threshold = 1.5       # wait longer for pauses between words
        self.recognizer.non_speaking_duration = 0.6
        self.recognizer.phrase_threshold = 0.3       # min length to count as speech
        self.recognizer.operation_timeout = None      # no socket timeout

        logger.info("🎙️  Calibrating microphone for ambient noise…")
        for attempt in range(3):
            try:
                mic = _quiet_mic()
                try:
                    self.recognizer.adjust_for_ambient_noise(mic, duration=2.0)
                finally:
                    mic.__exit__(None, None, None)
                break
            except Exception as exc:
                logger.warning(f"⚠️  Mic open attempt {attempt+1}/3 failed: {exc}")
                time.sleep(1.0)
        else:
            raise RuntimeError("Could not open microphone after 3 attempts")

        # Lower the threshold so soft speech isn't rejected
        self.recognizer.energy_threshold = max(
            50, self.recognizer.energy_threshold * 0.65
        )
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

        Returns None on silence, noise, self-speech, or API errors — never raises.
        """
        # Don't listen while Jarvis is speaking — we'd just pick up its own voice
        if self._speaker and self._speaker.is_speaking:
            return None
        # Extra guard: wait a moment after speaking stops so echoes die out
        if self._speaker:
            time.sleep(0.3)

        try:
            mic = _quiet_mic()
            try:
                logger.debug("🎤 Listening…")
                audio = self.recognizer.listen(
                    mic,
                    timeout=listen_timeout,
                    phrase_time_limit=phrase_time_limit,
                )
            finally:
                mic.__exit__(None, None, None)

            text = self.recognizer.recognize_google(
                audio, language="en-IN"
            ).strip().lower()
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

