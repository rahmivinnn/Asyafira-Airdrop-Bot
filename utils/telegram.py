# utils/telegram.py
import os
import logging
import requests
from typing import Optional, Dict, Any
from datetime import datetime

# Setup logger
logger = logging.getLogger(__name__)

def format_message(text: str, parse_mode: str = "HTML") -> str:
    """
    Format message text based on parse mode.
    
    Args:
        text: Message text
        parse_mode: Telegram parse mode (HTML or Markdown)
    
    Returns:
        Formatted message text
    """
    if parse_mode == "HTML":
        # Escape HTML special characters
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
    
    return text

def send_telegram_message(text: str, 
                         token: Optional[str] = None, 
                         chat_id: Optional[str] = None,
                         parse_mode: str = "HTML",
                         disable_notification: bool = False,
                         timeout: int = 30) -> bool:
    """
    Send a message to Telegram chat using bot token.
    
    Args:
        text: Message text to send
        token: Telegram bot token (if None, gets from environment)
        chat_id: Telegram chat ID (if None, gets from environment)
        parse_mode: Message parse mode (HTML or Markdown)
        disable_notification: Send message silently
        timeout: Request timeout in seconds
    
    Returns:
        True if message sent successfully, False otherwise
    """
    try:
        token = token or os.getenv("TELEGRAM_TOKEN")
        chat_id = chat_id or os.getenv("CHAT_ID")
        
        if not token or not chat_id:
            logger.error("Telegram token or chat_id not configured")
            return False
        
        # Telegram API endpoint
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        
        # Prepare payload
        payload = {
            "chat_id": chat_id,
            "text": text[:4096],  # Telegram message limit
            "parse_mode": parse_mode,
            "disable_notification": disable_notification
        }
        
        logger.debug(f"Sending Telegram message to chat {chat_id}")
        
        # Send request
        response = requests.post(url, json=payload, timeout=timeout)
        response.raise_for_status()
        
        logger.info("Telegram message sent successfully")
        return True
        
    except requests.exceptions.Timeout:
        logger.error("Telegram request timeout")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Telegram message: {e}")
        return False

def send_document(file_path: str,
                 caption: Optional[str] = None,
                 token: Optional[str] = None,
                 chat_id: Optional[str] = None,
                 timeout: int = 60) -> bool:
    """
    Send a document file to Telegram chat.
    
    Args:
        file_path: Path to the file to send
        caption: Optional caption for the document
        token: Telegram bot token (if None, gets from environment)
        chat_id: Telegram chat ID (if None, gets from environment)
        timeout: Request timeout in seconds
    
    Returns:
        True if document sent successfully, False otherwise
    """
    try:
        token = token or os.getenv("TELEGRAM_TOKEN")
        chat_id = chat_id or os.getenv("CHAT_ID")
        
        if not token or not chat_id:
            logger.error("Telegram token or chat_id not configured")
            return False
        
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
        
        # Check file size (Telegram limit is 50MB)
        file_size = os.path.getsize(file_path)
        if file_size > 50 * 1024 * 1024:  # 50MB
            logger.error(f"File too large: {file_size} bytes (max 50MB)")
            return False
        
        # Telegram API endpoint
        url = f"https://api.telegram.org/bot{token}/sendDocument"
        
        # Prepare files and data
        with open(file_path, 'rb') as file:
            files = {'document': file}
            data = {
                'chat_id': chat_id,
                'caption': caption[:1024] if caption else None  # Telegram caption limit
            }
            
            logger.debug(f"Sending document {file_path} to chat {chat_id}")
            
            # Send request
            response = requests.post(url, files=files, data=data, timeout=timeout)
            response.raise_for_status()
        
        logger.info(f"Document sent successfully: {file_path}")
        return True
        
    except requests.exceptions.Timeout:
        logger.error("Telegram document upload timeout")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Telegram document: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Telegram document: {e}")
        return False

def notify_claim_start(task_url: str, method: str = "POST") -> bool:
    """
    Send notification when claim process starts.
    
    Args:
        task_url: The task URL being claimed
        method: HTTP method being used
    
    Returns:
        True if notification sent successfully
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    message = f"🚀 <b>Claim Started</b>\n\n"
    message += f"⏰ <b>Time:</b> {timestamp}\n"
    message += f"🔗 <b>URL:</b> <code>{task_url}</code>\n"
    message += f"📡 <b>Method:</b> {method}\n\n"
    message += f"⏳ Processing claim request..."
    
    return send_telegram_message(message)

def notify_claim_success(task_url: str, 
                        response_message: str, 
                        response_file_path: Optional[str] = None) -> bool:
    """
    Send notification when claim succeeds.
    
    Args:
        task_url: The task URL that was claimed
        response_message: Response message from the claim
        response_file_path: Path to saved response file
    
    Returns:
        True if notification sent successfully
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    message = f"✅ <b>Claim SUCCESS</b>\n\n"
    message += f"⏰ <b>Time:</b> {timestamp}\n"
    message += f"🔗 <b>URL:</b> <code>{task_url}</code>\n\n"
    message += f"📋 <b>Response:</b>\n<pre>{response_message[:1000]}</pre>\n\n"
    
    if response_file_path:
        message += f"📁 <b>Response saved to:</b> <code>{response_file_path}</code>\n\n"
    
    message += f"🎉 Claim completed successfully!"
    
    # Send main message
    success = send_telegram_message(message)
    
    # Send response file if available and not too large
    if response_file_path and os.path.exists(response_file_path):
        file_size = os.path.getsize(response_file_path)
        if file_size < 10 * 1024 * 1024:  # 10MB limit for auto-send
            send_document(response_file_path, "Raw response data")
    
    return success

def notify_claim_failure(task_url: str, 
                        error_message: str, 
                        response_file_path: Optional[str] = None) -> bool:
    """
    Send notification when claim fails.
    
    Args:
        task_url: The task URL that failed
        error_message: Error message from the claim attempt
        response_file_path: Path to saved response file
    
    Returns:
        True if notification sent successfully
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    message = f"❌ <b>Claim FAILED</b>\n\n"
    message += f"⏰ <b>Time:</b> {timestamp}\n"
    message += f"🔗 <b>URL:</b> <code>{task_url}</code>\n\n"
    message += f"💥 <b>Error:</b>\n<pre>{error_message[:1000]}</pre>\n\n"
    
    if response_file_path:
        message += f"📁 <b>Response saved to:</b> <code>{response_file_path}</code>\n\n"
    
    message += f"🔄 Check logs for more details."
    
    # Send main message
    success = send_telegram_message(message)
    
    # Send response file if available and not too large
    if response_file_path and os.path.exists(response_file_path):
        file_size = os.path.getsize(response_file_path)
        if file_size < 10 * 1024 * 1024:  # 10MB limit for auto-send
            send_document(response_file_path, "Error response data")
    
    return success

def notify_scheduler_start(task_url: str, schedule_info: str) -> bool:
    """
    Send notification when scheduler starts.
    
    Args:
        task_url: The task URL to be claimed
        schedule_info: Information about the schedule
    
    Returns:
        True if notification sent successfully
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    message = f"⏰ <b>Scheduler Started</b>\n\n"
    message += f"🚀 <b>Started at:</b> {timestamp}\n"
    message += f"🔗 <b>Target URL:</b> <code>{task_url}</code>\n"
    message += f"📅 <b>Schedule:</b> {schedule_info}\n\n"
    message += f"🤖 Bot is now running and waiting for scheduled time..."
    
    return send_telegram_message(message)

def notify_captcha_detected(task_url: str) -> bool:
    """
    Send notification when captcha is detected.
    
    Args:
        task_url: The task URL where captcha was detected
    
    Returns:
        True if notification sent successfully
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    message = f"🤖 <b>Captcha Detected</b>\n\n"
    message += f"⏰ <b>Time:</b> {timestamp}\n"
    message += f"🔗 <b>URL:</b> <code>{task_url}</code>\n\n"
    message += f"🔐 Manual intervention may be required.\n"
    message += f"Check the console for captcha input prompt."
    
    return send_telegram_message(message)