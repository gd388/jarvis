"""Mock voice components for demo/testing without audio hardware"""

import logging
from typing import Optional
from config.settings import settings
from utils import setup_logger

logger = setup_logger(__name__)


class MockVoiceListener:
    """Mock listener that simulates voice input for demo purposes"""
    
    def __init__(self, timeout: int = None, retry_attempts: int = None):
        self.timeout = timeout or settings.TIMEOUT
        self.retry_attempts = retry_attempts or settings.RETRY_ATTEMPTS
        logger.info("🎤 MockVoiceListener initialized (demo mode - no microphone needed)")
    
    def listen(self, phrase_time_limit: int = 10) -> Optional[str]:
        """Simulate listening to microphone - prompts user for text input"""
        try:
            logger.info("🎤 (Demo) Listening for speech...")
            text = input("🎙️ [DEMO MODE] Speak (or type): ").strip()
            if text:
                logger.info(f"✓ Recognized: '{text}'")
                return text
            return None
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            return None
    
    def listen_for_wake_word(self, wake_word: str = None) -> bool:
        """Listen for wake word"""
        wake_word = (wake_word or settings.WAKE_WORD).lower()
        logger.info(f"🎤 (Demo) Waiting for wake word: '{wake_word}'")
        
        for attempt in range(1, self.retry_attempts + 1):
            recognized_text = self.listen(phrase_time_limit=3)
            if recognized_text:
                if wake_word in recognized_text.lower():
                    logger.info(f"✓ Wake word '{wake_word}' detected!")
                    return True
                else:
                    logger.debug(f"Detected: '{recognized_text}' - not wake word")
            
            if attempt < self.retry_attempts:
                logger.info(f"Retry {attempt}/{self.retry_attempts - 1}...")
        
        return False
    
    def listen_command(self) -> Optional[str]:
        """Listen for user command"""
        logger.info("🎤 (Demo) Listening for command...")
        return self.listen(phrase_time_limit=15)


class MockVoiceSpeaker:
    """Mock speaker that simulates voice output for demo purposes"""
    
    def __init__(self, rate: int = None, volume: float = None, voice_id: int = 0):
        self.rate = rate or settings.VOICE_RATE
        self.volume = volume or settings.VOICE_VOLUME
        logger.info(f"🔊 MockVoiceSpeaker initialized (demo mode - no audio output)")
    
    def speak(self, text: str, is_response: bool = False) -> bool:
        """Simulate speaking - prints text to console"""
        if not text or not text.strip():
            logger.warning("⚠️ Empty text provided to speaker")
            return False
        
        try:
            prefix = "🤖 Response:" if is_response else "🔊 Speaking:"
            logger.info(f"{prefix} {text[:100]}...")
            print(f"\n{'='*60}")
            print(f"🤖 JARVIS: {text}")
            print(f"{'='*60}\n")
            return True
        except Exception as e:
            logger.error(f"❌ Error during speech output: {e}")
            return False
    
    def speak_notification(self, notification: str) -> bool:
        """Speak a system notification"""
        try:
            logger.info(f"📢 Notification: {notification}")
            print(f"\n📢 {notification}\n")
            return True
        except Exception as e:
            logger.error(f"❌ Error speaking notification: {e}")
            return False
    
    def adjust_rate(self, rate: int) -> None:
        """Adjust speech rate (no-op in demo)"""
        self.rate = rate
        logger.info(f"Speech rate adjusted to: {rate} (demo mode)")
    
    def adjust_volume(self, volume: float) -> None:
        """Adjust volume (no-op in demo)"""
        if 0.0 <= volume <= 1.0:
            self.volume = volume
            logger.info(f"Volume adjusted to: {volume} (demo mode)")
        else:
            logger.warning(f"⚠️ Invalid volume: {volume}. Must be 0.0-1.0")
