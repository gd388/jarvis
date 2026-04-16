"""LLM module for Groq API integration"""

from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
import logging
from config.settings import settings
from utils import setup_logger

logger = setup_logger(__name__)


class GroqClient:
    """
    Handles communication with Groq LLM API.
    Uses langchain-groq for integration.
    """
    
    SYSTEM_PROMPT = """You are Jarvis, a helpful and intelligent AI assistant inspired by the Iron Man AI.
You are friendly, efficient, and always ready to help. Keep responses concise but informative.
You respond naturally to user queries with useful and accurate information.
Always aim to be helpful, harmless, and honest."""
    
    def __init__(self, model: str = None, api_key: str = None, 
                 temperature: float = 0.7, max_tokens: int = 1024):
        """
        Initialize Groq LLM client.
        
        Args:
            model: Model name (default: settings.MODEL_NAME)
            api_key: Groq API key (default: settings.GROQ_API_KEY)
            temperature: Response creativity (0.0-2.0, default: 0.7)
            max_tokens: Maximum response tokens (default: 1024)
        """
        self.model = model or settings.MODEL_NAME
        self.api_key = api_key or settings.GROQ_API_KEY
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not configured")
        
        try:
            self.llm = ChatGroq(
                model=self.model,
                api_key=self.api_key,
                temperature=temperature,
                max_tokens=max_tokens
            )
            logger.info(f"✓ Groq LLM initialized - Model: {self.model}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Groq LLM: {e}")
            raise
    
    def get_response(self, user_query: str) -> str:
        """
        Get response from Groq LLM for user query.
        
        Args:
            user_query: User's text input
            
        Returns:
            LLM response text
            
        Raises:
            Exception: If API call fails
        """
        if not user_query or not user_query.strip():
            logger.warning("⚠️ Empty query provided to LLM")
            return "I didn't receive a valid query. Please try again."
        
        try:
            logger.info(f"📤 Sending to Groq: '{user_query[:100]}...'")
            
            messages = [
                SystemMessage(content=self.SYSTEM_PROMPT),
                HumanMessage(content=user_query)
            ]
            
            response = self.llm.invoke(messages)
            result = response.content
            
            logger.info(f"📥 Groq response: '{result[:100]}...'")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error calling Groq API: {e}")
            raise
    
    def validate_connection(self) -> bool:
        """
        Validate connection to Groq API with a simple test.
        
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            logger.info("🔍 Validating Groq connection...")
            test_response = self.get_response("Say 'Connection successful' in one sentence.")
            logger.info("✓ Groq connection validated")
            return True
        except Exception as e:
            logger.error(f"❌ Groq connection validation failed: {e}")
            return False
