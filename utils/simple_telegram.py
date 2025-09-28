# utils/simple_telegram.py
import os
import logging
import requests
from typing import Optional

# Setup logger
logger = logging.getLogger(__name__)

def send_notification(text: str, 
                     token: Optional[str] = None, 
                     chat_id: Optional[str] = None,
                     timeout: int = 30) -> bool:
    """
    Send a simple notification to Telegram chat.
    
    Args:
        text: Message text to send
        token: Telegram bot token (if None, gets from environment)
        chat_id: Telegram chat ID (if None, gets from environment)
        timeout: Request timeout in seconds
    
    Returns:
        True if message sent successfully, False otherwise
    """
    try:
        token = token or os.getenv("TELEGRAM_TOKEN")
        chat_id = chat_id or os.getenv("CHAT_ID")
        
        if not token or not chat_id:
            logger.warning("Telegram token or chat_id not configured - skipping notification")
            return False
        
        # Telegram API endpoint
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        
        # Prepare payload
        payload = {
            "chat_id": chat_id,
            "text": text[:4096],  # Telegram message limit
            "parse_mode": "HTML"
        }
        
        logger.debug(f"Sending Telegram message to chat {chat_id}")
        
        # Send request
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        
        logger.info("Telegram notification sent successfully")
        return True
        
    except requests.exceptions.Timeout:
        logger.error("Telegram request timeout")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Telegram notification: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Telegram notification: {e}")
        return False