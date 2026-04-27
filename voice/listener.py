"""Voice listener — speech-to-text via microphone using SpeechRecognition."""

import time
from typing import Optional, TYPE_CHECKING

import speech_recognition as sr

from config.settings import settings
from utils import setup_logger

if TYPE_CHECKING:
    from voice.speaker import VoiceSpeaker

logger = setup_logger(__name__)


class VoiceListener:
    """Captures microphone audio and converts it to text."""

    def __init__(self, speaker: Optional["VoiceSpeaker"] = None) -> None:
        self._speaker = speaker
        self.recognizer = sr.Recognizer()

        # Fixed low threshold — ambient RMS ≈ 14, speech RMS ≈ 3000-6000.
        # Dynamic mode raises threshold after TTS playback → Jarvis goes deaf.
        self.recognizer.dynamic_energy_threshold = False
        self.recognizer.energy_threshold = 15
        self.recognizer.pause_threshold = 0.7
        self.recognizer.non_speaking_duration = 0.4
        self.recognizer.phrase_threshold = 0.1
        self.recognizer.operation_timeout = None

        self._mic_device = self._find_mic_index()
        logger.info(
            f"✓ Microphone ready  "
            f"(device={self._mic_device}, energy_threshold={self.recognizer.energy_threshold})"
        )

    # ------------------------------------------------------------------ #
    #  Mic discovery                                                       #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _find_mic_index() -> Optional[int]:
        """Return device index by NAME only — no test-open.

        Test-opening flushes the PipeWire device list so the returned index
        is out-of-range by the time the caller actually opens it.
        """
        names = sr.Microphone.list_microphone_names()
        for priority in ("pipewire", "sysdefault"):
            for idx, name in enumerate(names):
                if priority in name.lower():
                    logger.info(f"🎙️  Selected mic [{idx}] '{name}'")
                    return idx
        if names:
            logger.info(f"🎙️  Fallback mic [0] '{names[0]}'")
            return 0
        return None

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def listen_for_wake_word(self) -> bool:
        """Block until the wake word is spoken. Uses listen() for phrase-aware capture."""
        wake_word = settings.WAKE_WORD.lower()
        wake_word_norm = wake_word.replace(" ", "")
        # Re-discover mic index fresh — device list can shift between runs
        mic_idx = self._find_mic_index()
        logger.info(f"👂 Waiting for wake word: '{wake_word}' …  (mic device={mic_idx})")

        try:
            with sr.Microphone(device_index=mic_idx, sample_rate=16000) as source:
                while True:
                    if self._speaker and self._speaker.is_speaking:
                        time.sleep(0.1)
                        continue

                    try:
                        # timeout=20: wait up to 20s for speech to START, then record the phrase
                        audio = self.recognizer.listen(
                            source, timeout=20, phrase_time_limit=5
                        )
                        text = self.recognizer.recognize_google(audio).strip().lower()
                        text_norm = text.replace(" ", "")
                        logger.info(f"🗣️  Heard: '{text}'")
                        if wake_word_norm in text_norm:
                            logger.info("🔔 Wake word detected!")
                            return True
                    except sr.WaitTimeoutError:
                        logger.debug("⏱️  No speech — still listening for wake word")
                    except sr.UnknownValueError:
                        logger.debug("🔇 Could not understand audio")
                    except sr.RequestError as exc:
                        logger.error(f"❌ Speech API error: {exc}")
                        time.sleep(1)
                    except Exception as exc:
                        logger.warning(f"⚠️  Mic error: {exc} — reopening")
                        break   # exit inner loop, reopen mic

        except Exception as exc:
            logger.warning(f"⚠️  Could not open mic device={mic_idx} ({exc}) — trying other devices")
            # Try every other valid index rather than blindly falling back to None
            candidates = list(range(len(sr.Microphone.list_microphone_names())))
            for fallback_idx in candidates:
                if fallback_idx == mic_idx:
                    continue
                try:
                    with sr.Microphone(device_index=fallback_idx, sample_rate=16000) as source:
                        logger.info(f"🎙️  Wake-word fallback mic [{fallback_idx}]")
                        while True:
                            if self._speaker and self._speaker.is_speaking:
                                time.sleep(0.1)
                                continue
                            try:
                                audio = self.recognizer.listen(source, timeout=20, phrase_time_limit=5)
                                text = self.recognizer.recognize_google(audio).strip().lower()
                                text_norm = text.replace(" ", "")
                                logger.info(f"🗣️  Heard: '{text}'")
                                if wake_word_norm in text_norm:
                                    logger.info("🔔 Wake word detected!")
                                    return True
                            except sr.WaitTimeoutError:
                                logger.debug("⏱️  No speech — still listening")
                            except sr.UnknownValueError:
                                logger.debug("🔇 Could not understand audio")
                            except sr.RequestError as exc2:
                                logger.error(f"❌ Speech API error: {exc2}")
                                time.sleep(1)
                            except Exception as exc2:
                                logger.warning(f"⚠️  Mic error: {exc2} — next device")
                                break   # try next candidate
                        break  # exited inner while — reopen same device (recurse)
                except Exception:
                    continue
            else:
                logger.error("❌ No usable microphone found")
                time.sleep(2)

        return self.listen_for_wake_word()   # reopen mic and retry

    def listen_command(self) -> Optional[str]:
        """Listen for one command phrase. Returns recognised text or None."""
        # Wait for Jarvis to finish speaking
        if self._speaker:
            while self._speaker.is_speaking:
                time.sleep(0.05)
            time.sleep(0.35)   # brief echo cooldown

        # Re-discover mic index fresh each time
        mic_idx = self._find_mic_index()
        logger.info("🎤 Listening for your command…")

        try:
            with sr.Microphone(device_index=mic_idx, sample_rate=16000) as source:
                for attempt in range(1, settings.COMMAND_RETRIES + 1):
                    try:
                        audio = self.recognizer.listen(
                            source,
                            timeout=settings.COMMAND_TIMEOUT,
                            phrase_time_limit=settings.PHRASE_LIMIT,
                        )
                        text = self.recognizer.recognize_google(audio).strip()
                        logger.info(f"🗣️  Command: '{text}'")
                        return text
                    except sr.WaitTimeoutError:
                        logger.warning(
                            f"⚠️  Attempt {attempt}/{settings.COMMAND_RETRIES} — no speech detected"
                        )
                    except sr.UnknownValueError:
                        logger.warning(
                            f"⚠️  Attempt {attempt}/{settings.COMMAND_RETRIES} — could not understand"
                        )
                    except sr.RequestError as exc:
                        logger.error(f"❌ Speech API error: {exc}")
                        return None
                    except (OSError, AttributeError, Exception) as exc:
                        logger.warning(f"⚠️  Mic stream error: {exc}")
                        return None
        except Exception as exc:
            logger.warning(f"⚠️  Could not open mic device={mic_idx} ({exc}) — trying other devices")
            candidates = list(range(len(sr.Microphone.list_microphone_names())))
            for fallback_idx in candidates:
                if fallback_idx == mic_idx:
                    continue
                try:
                    with sr.Microphone(device_index=fallback_idx, sample_rate=16000) as source:
                        logger.info(f"🎙️  Command fallback mic [{fallback_idx}]")
                        try:
                            audio = self.recognizer.listen(
                                source,
                                timeout=settings.COMMAND_TIMEOUT,
                                phrase_time_limit=settings.PHRASE_LIMIT,
                            )
                            text = self.recognizer.recognize_google(audio).strip()
                            logger.info(f"🗣️  Command: '{text}'")
                            return text
                        except sr.WaitTimeoutError:
                            logger.warning("⚠️  No speech on fallback mic")
                        except sr.UnknownValueError:
                            logger.warning("⚠️  Could not understand on fallback mic")
                        except Exception:
                            pass
                        return None  # got a working mic, but no valid speech
                except Exception:
                    continue
            logger.error("❌ No usable microphone found")
            return None

        logger.warning("⚠️  No command received after all attempts")
        return None
