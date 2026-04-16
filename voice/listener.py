"""Voice listener module for speech-to-text conversion"""

import logging
from typing import Optional
from config.settings import settings
from utils import setup_logger

logger = setup_logger(__name__)

# Lazy import of speech_recognition to handle missing PyAudio
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except Exception as e:
    SPEECH_RECOGNITION_AVAILABLE = False
    logger.warning(f"⚠️ speech_recognition not available: {e}")


class VoiceListener:
    """
    Handles speech recognition from microphone.
    Converts speech to text with error handling.
    """
    
    def __init__(self, timeout: int = None, retry_attempts: int = None):
        """
        Initialize the voice listener.
        
        Args:
            timeout: Seconds to wait for speech (default: settings.TIMEOUT)
            retry_attempts: Number of retry attempts (default: settings.RETRY_ATTEMPTS)
        """
        if not SPEECH_RECOGNITION_AVAILABLE:
            raise Exception("speech_recognition not available - PyAudio or audio system not configured")
        
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.timeout = timeout or settings.TIMEOUT
        self.retry_attempts = retry_attempts or settings.RETRY_ATTEMPTS
        
        # Adjust for ambient noise once during initialization
        logger.info("Initializing listener... calibrating microphone noise levels")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        logger.info("Microphone calibration complete")
    
    def listen(self, phrase_time_limit: int = 10) -> Optional[str]:
        """
        Listen to microphone and convert speech to text.
        
        Args:
            phrase_time_limit: Maximum seconds to listen for speech
            
        Returns:
            Recognized text or None if failed
        """
        try:
            logger.info("🎤 Listening...")
            with self.microphone as source:
                audio_data = self.recognizer.listen(
                    source,
                    timeout=self.timeout,
                    phrase_time_limit=phrase_time_limit
                )
            
            logger.info("Processing audio...")
            text = self.recognizer.recognize_google(audio_data)
            logger.info(f"✓ Recognized: '{text}'")
            return text
            
        except sr.UnknownValueError:
            logger.warning("⚠️ Could not understand audio. Please speak clearly.")
            return None
        except sr.RequestError as e:
            logger.error(f"❌ API request failed: {e}")
            return None
        except sr.WaitTimeoutError:
            logger.warning("⚠️ No speech detected. Please try again.")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error during listening: {e}")
            return None
    
    def listen_for_wake_word(self, wake_word: str = None) -> bool:
        """
        Continuously listen for wake word.
        
        Args:
            wake_word: Wake word to listen for (default: settings.WAKE_WORD)
            
        Returns:
            True if wake word detected, False otherwise
        """
        wake_word = (wake_word or settings.WAKE_WORD).lower()
        max_attempts = self.retry_attempts
        
        for attempt in range(1, max_attempts + 1):
            recognized_text = self.listen(phrase_time_limit=3)
            
            if recognized_text:
                if wake_word in recognized_text.lower():
                    logger.info(f"✓ Wake word '{wake_word}' detected!")
                    return True
                else:
                    logger.debug(f"Detected text: '{recognized_text}' - not wake word")
            
            if attempt < max_attempts:
                logger.info(f"Retry {attempt}/{max_attempts - 1}...")
        
        return False
    
    def listen_command(self) -> Optional[str]:
        """
        Listen for user command after wake word activation.
        
        Args:
            Returns:
            Command text or None if failed
        """
        logger.info("🎤 Listening for command...")
        return self.listen(phrase_time_limit=15)
