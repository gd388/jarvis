"""Voice speaker module for text-to-speech conversion"""

import logging
from config.settings import settings
from utils import setup_logger

logger = setup_logger(__name__)

# Lazy import of pyttsx3 to handle missing audio system
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except Exception as e:
    PYTTSX3_AVAILABLE = False
    logger.warning(f"⚠️ pyttsx3 not available: {e}")


class VoiceSpeaker:
    """
    Handles text-to-speech conversion and audio output.
    Uses pyttsx3 for offline text-to-speech.
    """
    
    def __init__(self, rate: int = None, volume: float = None, 
                 voice_id: int = 0):
        """
        Initialize the voice speaker.
        
        Args:
            rate: Speech rate (words per minute, default: settings.VOICE_RATE)
            volume: Volume level 0.0-1.0 (default: settings.VOICE_VOLUME)
            voice_id: Voice ID (0=default, 1=alternative if available)
        """
        if not PYTTSX3_AVAILABLE:
            raise Exception("pyttsx3 not available - audio system not configured")
        
        self.engine = pyttsx3.init()
        self.rate = rate or settings.VOICE_RATE
        self.volume = volume or settings.VOICE_VOLUME
        
        # Configure engine
        self.engine.setProperty('rate', self.rate)
        self.engine.setProperty('volume', self.volume)
        
        # Set voice if available
        voices = self.engine.getProperty('voices')
        if voice_id < len(voices):
            self.engine.setProperty('voice', voices[voice_id].id)
            logger.info(f"Voice set to: {voices[voice_id].name}")
        
        logger.info(f"Speaker initialized - Rate: {self.rate}, Volume: {self.volume}")
    
    def speak(self, text: str, is_response: bool = False) -> bool:
        """
        Convert text to speech and play it.
        
        Args:
            text: Text to speak
            is_response: If True, marks this as LLM response (for logging)
            
        Returns:
            True if successful, False otherwise
        """
        if not text or not text.strip():
            logger.warning("⚠️ Empty text provided to speaker")
            return False
        
        try:
            prefix = "🤖 Response:" if is_response else "🔊 Speaking:"
            logger.info(f"{prefix} {text[:100]}...")
            
            self.engine.say(text)
            self.engine.runAndWait()
            
            logger.info("✓ Speech completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error during speech output: {e}")
            return False
    
    def speak_notification(self, notification: str) -> bool:
        """
        Speak a system notification or message.
        
        Args:
            notification: Notification text
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"📢 Notification: {notification}")
            self.engine.say(notification)
            self.engine.runAndWait()
            return True
        except Exception as e:
            logger.error(f"❌ Error speaking notification: {e}")
            return False
    
    def adjust_rate(self, rate: int) -> None:
        """
        Adjust speech rate.
        
        Args:
            rate: New speech rate (words per minute)
        """
        self.rate = rate
        self.engine.setProperty('rate', rate)
        logger.info(f"Speech rate adjusted to: {rate}")
    
    def adjust_volume(self, volume: float) -> None:
        """
        Adjust speech volume.
        
        Args:
            volume: New volume level (0.0-1.0)
        """
        if 0.0 <= volume <= 1.0:
            self.volume = volume
            self.engine.setProperty('volume', volume)
            logger.info(f"Volume adjusted to: {volume}")
        else:
            logger.warning(f"⚠️ Invalid volume: {volume}. Must be 0.0-1.0")
