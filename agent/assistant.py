"""Main assistant logic orchestrating voice, LLM, and conversation flow"""

import logging
import time
from typing import Optional
from config.settings import settings
from utils import setup_logger

# Try to import real audio components, fall back to mock if audio not available
try:
    from voice.listener import VoiceListener
    from voice.speaker import VoiceSpeaker
    AUDIO_AVAILABLE = True
except Exception as e:
    logger_init = setup_logger(__name__)
    logger_init.warning(f"⚠️ Audio components not available, using demo mode: {e}")
    from voice.mock_components import MockVoiceListener as VoiceListener
    from voice.mock_components import MockVoiceSpeaker as VoiceSpeaker
    AUDIO_AVAILABLE = False

from llm.groq_client import GroqClient

logger = setup_logger(__name__)


class JarvisAssistant:
    """
    Main Jarvis AI Assistant class.
    Orchestrates voice input/output, wake word detection, and LLM communication.
    """
    
    EXIT_COMMANDS = {"stop", "exit", "quit", "goodbye", "bye"}
    
    def __init__(self):
        """Initialize Jarvis assistant with all components"""
        logger.info("=" * 60)
        logger.info("🚀 Initializing Jarvis AI Assistant")
        if not AUDIO_AVAILABLE:
            logger.info("📢 DEMO MODE - Using text input/output (audio not available)")
        logger.info("=" * 60)
        
        try:
            # If audio was marked unavailable at import, use mocks directly
            if not AUDIO_AVAILABLE:
                logger.info("💡 Using mock audio components for demo mode")
                self.listener = VoiceListener()
                self.speaker = VoiceSpeaker()
            else:
                # Try to initialize real audio components
                self.listener = VoiceListener()
                self.speaker = VoiceSpeaker()
            
            self.llm = GroqClient()
            self.is_active = False
            self.wake_word = settings.WAKE_WORD.lower()
            self.last_wake_time = 0
            self.audio_available = AUDIO_AVAILABLE
            
            logger.info("✓ All components initialized successfully")
            if not AUDIO_AVAILABLE:
                logger.info("💡 Demo Mode: Type commands instead of speaking")
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            # If we got here with AUDIO_AVAILABLE=True, switch to mock mode
            if AUDIO_AVAILABLE:
                logger.info("⚠️ Falling back to mock components due to initialization error")
                try:
                    from voice.mock_components import MockVoiceListener, MockVoiceSpeaker
                    self.listener = MockVoiceListener()
                    self.speaker = MockVoiceSpeaker()
                    self.llm = GroqClient()
                    self.is_active = False
                    self.wake_word = settings.WAKE_WORD.lower()
                    self.last_wake_time = 0
                    self.audio_available = False
                    logger.info("✓ Switched to mock components successfully")
                except Exception as e2:
                    logger.error(f"❌ Failed to switch to mock components: {e2}")
                    raise
            else:
                raise
    
    def should_skip_wake_word(self) -> bool:
        """
        Check if we should skip wake word detection due to cooldown.
        Prevents re-triggering on assistant's own speech.
        
        Returns:
            True if should skip, False if should process
        """
        current_time = time.time()
        cooldown_active = (current_time - self.last_wake_time) < settings.WAKE_WORD_COOLDOWN
        return cooldown_active
    
    def wait_for_wake_word(self) -> bool:
        """
        Continuously wait for wake word detection.
        
        Returns:
            True if wake word detected, False if interrupted
        """
        logger.info(f"👁️ Jarvis standby mode... Waiting for '{self.wake_word}'")
        
        try:
            if self.listener.listen_for_wake_word(self.wake_word):
                self.last_wake_time = time.time()
                self.is_active = True
                self.speaker.speak_notification(f"Activated. Ready for your command.")
                return True
            return False
        except KeyboardInterrupt:
            logger.info("⏹️ Wake word monitoring interrupted")
            return False
        except Exception as e:
            logger.error(f"❌ Error in wake word detection: {e}")
            return False
    
    def process_command(self, command: str) -> Optional[str]:
        """
        Process user command through LLM.
        
        Args:
            command: User's spoken command
            
        Returns:
            LLM response or None if failed
        """
        if not command:
            return None
        
        # Check for exit commands
        if any(exit_cmd in command.lower() for exit_cmd in self.EXIT_COMMANDS):
            logger.info(f"📍 Exit command detected: '{command}'")
            return None  # Signal to exit
        
        try:
            logger.info(f"💬 Processing command: '{command}'")
            response = self.llm.get_response(command)
            return response
        except Exception as e:
            logger.error(f"❌ Failed to process command: {e}")
            return "Sorry, I encountered an error. Please try again."
    
    def handle_active_session(self) -> bool:
        """
        Handle an active conversation session after wake word.
        
        Returns:
            True to continue listening, False to return to standby
        """
        logger.info("🎯 Active session started")
        
        # Listen for command
        command = self.listener.listen_command()
        
        if not command:
            logger.info("⚠️ No command detected")
            return True  # Continue active session
        
        # Process command (check for exit)
        response = self.process_command(command)
        
        if response is None:  # Exit command detected
            self.speaker.speak_notification("Goodbye! Returning to standby.")
            self.is_active = False
            return False
        
        # Speak response
        self.speaker.speak(response, is_response=True)
        
        # Ask if user has more commands
        logger.info("✓ Response delivered. Waiting for next command...")
        return True  # Continue active session
    
    def run(self):
        """
        Main event loop for Jarvis assistant.
        Continuously listens for wake word, processes commands, and provides responses.
        """
        try:
            # Validate API connection (skip in demo mode)
            if self.audio_available:
                logger.info("🔗 Validating API connection...")
                if not self.llm.validate_connection():
                    logger.error("❌ Cannot connect to Groq API. Please check API key and network.")
                    return
            else:
                logger.info("💡 Skipping API validation in demo mode")
                self.speaker.speak_notification("Jarvis demo mode activated. Ready for your command.")
            
            # Main loop
            while True:
                try:
                    # Wait for wake word
                    if not self.wait_for_wake_word():
                        continue
                    
                    # Handle active session
                    while self.is_active:
                        if not self.handle_active_session():
                            break
                    
                except KeyboardInterrupt:
                    logger.info("\n⏹️ Received interrupt signal")
                    break
                except Exception as e:
                    logger.error(f"❌ Error in main loop: {e}")
                    self.speaker.speak_notification("An error occurred. Returning to standby.")
                    self.is_active = False
                    
        except KeyboardInterrupt:
            logger.info("\n⏹️ Shutting down Jarvis")
        except Exception as e:
            logger.error(f"❌ Fatal error: {e}")
        finally:
            self._cleanup()
    
    def _cleanup(self):
        """Cleanup resources before shutdown"""
        logger.info("🛑 Cleaning up resources...")
        try:
            self.speaker.speak_notification("Jarvis going offline. Goodbye.")
        except Exception:
            pass
        logger.info("=" * 60)
        logger.info("🔌 Jarvis offline")
        logger.info("=" * 60)
