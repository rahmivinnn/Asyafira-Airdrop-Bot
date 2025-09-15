#!/usr/bin/env python3
# main.py
import os
import sys
import json
import logging
import argparse
from datetime import datetime, time as dtime
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger

# Import our modules
from utils.claimer import claim_task, extract_url_from_cookie
from utils.telegram import (
    notify_claim_start, notify_claim_success, notify_claim_failure,
    notify_scheduler_start, send_telegram_message
)

# Load environment variables
load_dotenv()

def setup_logging():
    """
    Setup logging configuration with rotating file handler.
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    # Get log configuration from environment
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    max_log_size = int(os.getenv("MAX_LOG_SIZE", "5")) * 1024 * 1024  # Convert MB to bytes
    log_backup_count = int(os.getenv("LOG_BACKUP_COUNT", "10"))
    
    # Setup root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        'logs/claimer.log',
        maxBytes=max_log_size,
        backupCount=log_backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level, logging.INFO))
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # Reduce noise from external libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('apscheduler').setLevel(logging.WARNING)
    
    return logger

def job_claim(task_url: str, method: str = "POST", payload: dict = None):
    """
    Job wrapper function for claim execution.
    
    Args:
        task_url: URL to claim
        method: HTTP method to use
        payload: Optional JSON payload
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting claim job for: {task_url}")
        
        # Send start notification
        notify_claim_start(task_url, method)
        
        # Perform the claim
        success, message, response_file_path = claim_task(
            task_url=task_url,
            method=method,
            payload=payload
        )
        
        # Send result notification
        if success:
            logger.info("Claim completed successfully")
            notify_claim_success(task_url, message, response_file_path)
        else:
            logger.error(f"Claim failed: {message}")
            notify_claim_failure(task_url, message, response_file_path)
    
    except Exception as e:
        error_msg = f"Unexpected error in claim job: {e}"
        logger.error(error_msg)
        notify_claim_failure(task_url, error_msg, None)

def parse_datetime(datetime_str: str) -> datetime:
    """
    Parse datetime string in various formats.
    
    Args:
        datetime_str: Datetime string to parse
    
    Returns:
        Parsed datetime object
    
    Raises:
        ValueError: If datetime string is invalid
    """
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(datetime_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Invalid datetime format: {datetime_str}. Expected formats like 'YYYY-MM-DD HH:MM:SS'")

def parse_time_str(time_str: str) -> dtime:
    """
    Parse time string in HH:MM format.
    
    Args:
        time_str: Time string to parse
    
    Returns:
        Parsed time object
    
    Raises:
        ValueError: If time string is invalid
    """
    try:
        hour, minute = map(int, time_str.split(":"))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Invalid time values")
        return dtime(hour, minute)
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid time format: {time_str}. Expected HH:MM format")

def validate_config() -> bool:
    """
    Validate required configuration.
    
    Returns:
        True if configuration is valid
    """
    logger = logging.getLogger(__name__)
    
    # Check required environment variables
    required_vars = ["COOKIE"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    # Check Telegram configuration (optional but warn if missing)
    if not os.getenv("TELEGRAM_TOKEN") or not os.getenv("CHAT_ID"):
        logger.warning("Telegram notifications not configured (TELEGRAM_TOKEN or CHAT_ID missing)")
    
    return True

def main():
    """
    Main entry point.
    """
    # Setup logging first
    logger = setup_logging()
    logger.info("Asyafira Airdrop Bot starting...")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Asyafira Airdrop Bot - Advanced auto-claim with scheduling",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run once immediately (URL auto-extracted from cookie)
  python main.py --run-once
  
  # Schedule daily at specific time (URL auto-extracted from cookie)
  python main.py --daily-time "09:00"
  
  # Run with manual URL override
  python main.py --task-url "https://example.com/claim" --run-once
  
  # Schedule for specific datetime
  python main.py --run-datetime "2025-09-14 13:30:00"
  
  # With custom payload
  python main.py --run-once --payload '{"action":"claim"}'
  
  # Using environment variables (set COOKIE in .env for auto URL extraction)
  python main.py --daily-time "07:00"
"""
    )
    
    parser.add_argument(
        "--task-url", 
        type=str, 
        help="Task URL to claim (optional - will auto-extract from cookie if not provided)"
    )
    
    parser.add_argument(
        "--run-datetime", 
        type=str, 
        help="Run once at specific datetime (YYYY-MM-DD HH:MM:SS format)"
    )
    
    parser.add_argument(
        "--daily-time", 
        type=str, 
        help="Run daily at specific time (HH:MM format)"
    )
    
    parser.add_argument(
        "--run-once", 
        action="store_true", 
        help="Run claim once immediately"
    )
    
    parser.add_argument(
        "--method", 
        type=str, 
        default="POST", 
        choices=["GET", "POST"], 
        help="HTTP method (default: POST)"
    )
    
    parser.add_argument(
        "--payload", 
        type=str, 
        help="JSON payload for POST requests"
    )
    
    parser.add_argument(
        "--test-telegram", 
        action="store_true", 
        help="Test Telegram notifications and exit"
    )
    
    parser.add_argument(
        "--validate-config", 
        action="store_true", 
        help="Validate configuration and exit"
    )
    
    args = parser.parse_args()
    
    # Validate configuration
    if not validate_config():
        logger.error("Configuration validation failed")
        sys.exit(1)
    
    if args.validate_config:
        logger.info("Configuration validation passed")
        sys.exit(0)
    
    # Test Telegram if requested
    if args.test_telegram:
        logger.info("Testing Telegram notifications...")
        success = send_telegram_message("🧪 Test message from Asyafira Airdrop Bot")
        if success:
            logger.info("Telegram test successful")
            sys.exit(0)
        else:
            logger.error("Telegram test failed")
            sys.exit(1)
    
    # Get configuration from args or environment
    task_url = args.task_url or os.getenv("TASK_URL")
    run_datetime_str = args.run_datetime or os.getenv("RUN_DATETIME")
    daily_time_str = args.daily_time or os.getenv("DAILY_CLAIM_TIME")
    method = args.method or os.getenv("HTTP_METHOD", "POST")
    
    # Parse payload
    payload = None
    payload_str = args.payload or os.getenv("JSON_PAYLOAD")
    if payload_str:
        try:
            payload = json.loads(payload_str)
            logger.info("JSON payload loaded successfully")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {e}")
            sys.exit(1)
    
    # Validate task URL - try to extract from cookie if not provided
    if not task_url:
        logger.info("No task URL provided, attempting to extract from cookie...")
        task_url = extract_url_from_cookie()
        
        if not task_url:
            logger.error("Task URL is required. Provide via --task-url, TASK_URL in .env, or ensure URL is available in cookie")
            sys.exit(1)
        else:
            logger.info("Successfully extracted task URL from cookie")
    
    logger.info(f"Target URL: {task_url}")
    logger.info(f"HTTP Method: {method}")
    if payload:
        logger.info(f"Payload: {json.dumps(payload, indent=2)}")
    
    # Handle immediate run
    if args.run_once:
        logger.info("Running claim immediately...")
        job_claim(task_url, method, payload)
        return
    
    # Setup scheduler
    scheduler = BackgroundScheduler(timezone='UTC')
    job_added = False
    
    # Handle datetime scheduling
    if run_datetime_str:
        try:
            run_datetime = parse_datetime(run_datetime_str)
            
            # Check if datetime is in the future
            if run_datetime <= datetime.now():
                logger.error(f"Scheduled datetime {run_datetime} is in the past")
                sys.exit(1)
            
            scheduler.add_job(
                func=job_claim,
                trigger=DateTrigger(run_date=run_datetime),
                args=[task_url, method, payload],
                id="datetime_claim",
                name=f"Claim at {run_datetime}"
            )
            
            schedule_info = f"One-time run at {run_datetime}"
            logger.info(f"Scheduled: {schedule_info}")
            job_added = True
            
        except ValueError as e:
            logger.error(f"Invalid datetime: {e}")
            sys.exit(1)
    
    # Handle daily scheduling
    if daily_time_str:
        try:
            daily_time = parse_time_str(daily_time_str)
            
            scheduler.add_job(
                func=job_claim,
                trigger=CronTrigger(
                    hour=daily_time.hour,
                    minute=daily_time.minute,
                    timezone='UTC'
                ),
                args=[task_url, method, payload],
                id="daily_claim",
                name=f"Daily claim at {daily_time_str}"
            )
            
            schedule_info = f"Daily at {daily_time_str} UTC"
            logger.info(f"Scheduled: {schedule_info}")
            job_added = True
            
        except ValueError as e:
            logger.error(f"Invalid time: {e}")
            sys.exit(1)
    
    # Check if any job was added
    if not job_added:
        logger.error("No scheduling option provided. Use --run-once, --run-datetime, or --daily-time")
        sys.exit(1)
    
    # Start scheduler
    try:
        scheduler.start()
        
        # Send scheduler start notification
        if run_datetime_str:
            schedule_info = f"One-time run at {run_datetime_str}"
        else:
            schedule_info = f"Daily at {daily_time_str} UTC"
        
        notify_scheduler_start(task_url, schedule_info)
        
        logger.info("Scheduler started successfully")
        logger.info("Press Ctrl+C to stop the bot...")
        
        # Keep the script running
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutdown signal received")
        
    except Exception as e:
        logger.error(f"Scheduler error: {e}")
        sys.exit(1)
    
    finally:
        # Shutdown scheduler
        try:
            scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped gracefully")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
        
        logger.info("Asyafira Airdrop Bot stopped")

if __name__ == "__main__":
    main()