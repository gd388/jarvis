"""Main assistant logic — state machine orchestrating voice I/O and the LLM."""

import logging
import time

from voice.listener import VoiceListener
from voice.speaker import VoiceSpeaker
from llm.groq_client import GroqClient
from config.settings import settings
from utils import setup_logger

logger = setup_logger(__name__)

# Commands that end the active session (return to standby)
_SESSION_END = {"stop", "exit", "quit", "goodbye", "bye", "sleep", "standby"}

# Commands that fully shut down the program
_SHUTDOWN = {"shutdown", "power off", "terminate"}


class JarvisAssistant:
    """
    Jarvis voice assistant.

    State machine
    ─────────────
    STANDBY  ──(wake word)──►  ACTIVE  ──(stop/exit)──►  STANDBY
                                  │
                              (shutdown)
                                  ▼
                               EXIT
    """

    def __init__(self) -> None:
        logger.info("=" * 60)
        logger.info("🚀  Initialising Jarvis AI Assistant")
        logger.info("=" * 60)

        self.listener = VoiceListener()
        self.speaker = VoiceSpeaker()
        self.llm = GroqClient()

        logger.info("✓  All systems online — Jarvis ready")

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _is_session_end(self, text: str) -> bool:
        lower = text.lower()
        return any(cmd in lower for cmd in _SESSION_END)

    def _is_shutdown(self, text: str) -> bool:
        lower = text.lower()
        return any(cmd in lower for cmd in _SHUTDOWN)

    def _safe_respond(self, query: str) -> str:
        """Call the LLM and return a response string; never raises."""
        try:
            return self.llm.get_response(query)
        except Exception as exc:
            logger.error(f"❌ LLM error: {exc}")
            return (
                "I'm sorry, I ran into a problem reaching my language model. "
                "Please try again in a moment."
            )

    # ------------------------------------------------------------------ #
    #  State: STANDBY                                                      #
    # ------------------------------------------------------------------ #

    def _standby(self) -> bool:
        """
        Block until the wake word is detected.

        Returns True  → transition to ACTIVE.
        Returns False → should shut down (KeyboardInterrupt caught here).
        """
        logger.info(f"💤  Standby — listening for wake word '{settings.WAKE_WORD}' …")
        try:
            self.listener.listen_for_wake_word()
            return True
        except KeyboardInterrupt:
            return False

    # ------------------------------------------------------------------ #
    #  State: ACTIVE                                                       #
    # ------------------------------------------------------------------ #

    def _active_session(self) -> bool:
        """
        Run one full conversation session (wake → commands → stop/exit).

        Returns True  → reenter standby.
        Returns False → shut down entirely.
        """
        self.speaker.speak("Yes, sir. How can I help you?")
        consecutive_failures = 0

        while True:
            command = self.listener.listen_command()

            # ── No speech received ──────────────────────────────────── #
            if not command:
                consecutive_failures += 1
                if consecutive_failures >= 2:
                    self.speaker.speak(
                        "I haven't heard anything for a while. "
                        "Returning to standby. Say 'Rise' when you need me."
                    )
                    return True  # back to standby
                self.speaker.speak(
                    "I didn't catch that. Could you please repeat?"
                )
                continue

            consecutive_failures = 0   # reset on successful recognition
            logger.info(f"💬  Command: '{command}'")

            # ── Shutdown ─────────────────────────────────────────────── #
            if self._is_shutdown(command):
                self.speaker.speak(
                    "Understood. Shutting down all systems. Goodbye, sir."
                )
                return False  # full exit

            # ── End session ──────────────────────────────────────────── #
            if self._is_session_end(command):
                self.speaker.speak(
                    "Of course. Going to standby. Say 'Rise' whenever you need me."
                )
                return True  # back to standby

            # ── Process with LLM ─────────────────────────────────────── #
            response = self._safe_respond(command)
            self.speaker.speak(response)

            # Small gap so the mic isn't triggered by the tail of playback
            time.sleep(0.3)

    # ------------------------------------------------------------------ #
    #  Main loop                                                           #
    # ------------------------------------------------------------------ #

    def run(self) -> None:
        """Entry point — runs forever until shutdown command or Ctrl-C."""
        self.speaker.speak(
            "Jarvis online. All systems operational. "
            f"Say '{settings.WAKE_WORD}' to activate me."
        )

        try:
            while True:
                # ── STANDBY ── #
                if not self._standby():
                    break   # KeyboardInterrupt

                # ── ACTIVE ── #
                keep_running = self._active_session()
                if not keep_running:
                    break   # shutdown command

        except KeyboardInterrupt:
            pass
        finally:
            logger.info("=" * 60)
            logger.info("🔌  Jarvis offline")
            logger.info("=" * 60)

