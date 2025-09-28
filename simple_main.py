#!/usr/bin/env python3
"""
Simple Zealy.io Task Claimer Bot
Focused on essential functionality for claiming tasks on zealy.io
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Import our modules
from utils.simple_claimer import claim_zealy_task
from utils.simple_telegram import send_notification

# Load environment variables
load_dotenv()

def setup_logging():
    """Setup basic logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('zealy_claimer.log')
        ]
    )
    return logging.getLogger(__name__)

def validate_config():
    """Validate required configuration."""
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
    
    return True

def main():
    """Main entry point."""
    logger = setup_logging()
    logger.info("Simple Zealy.io Task Claimer starting...")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Simple Zealy.io Task Claimer - Essential auto-claim functionality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run once immediately
  python simple_main.py --run-once
  
  # Run with specific URL
  python simple_main.py --task-url "https://zealy.io/api/claim" --run-once
  
  # Run with custom payload
  python simple_main.py --payload '{"action":"claim"}' --run-once
"""
    )
    
    parser.add_argument(
        "--task-url", 
        type=str, 
        help="Zealy.io task URL to claim (optional - will auto-extract from cookie if not provided)"
    )
    
    parser.add_argument(
        "--run-once", 
        action="store_true", 
        help="Run claim once immediately"
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
    
    args = parser.parse_args()
    
    # Validate configuration
    if not validate_config():
        logger.error("Configuration validation failed")
        sys.exit(1)
    
    # Test Telegram if requested
    if args.test_telegram:
        logger.info("Testing Telegram notifications...")
        success = send_notification("🧪 Test message from Simple Zealy Claimer")
        if success:
            logger.info("Telegram test successful")
            sys.exit(0)
        else:
            logger.error("Telegram test failed")
            sys.exit(1)
    
    # Get configuration from args or environment
    task_url = args.task_url or os.getenv("TASK_URL")
    method = os.getenv("HTTP_METHOD", "POST")
    
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
    
    # If no task URL provided, try to extract from cookie
    if not task_url:
        logger.info("No task URL provided, attempting to extract from cookie...")
        from utils.simple_claimer import extract_zealy_url_from_cookie
        task_url = extract_zealy_url_from_cookie()
        
        if not task_url:
            logger.error("Task URL is required. Provide via --task-url or TASK_URL in .env")
            sys.exit(1)
        else:
            logger.info("Successfully extracted task URL from cookie")
    
    logger.info(f"Target URL: {task_url}")
    logger.info(f"HTTP Method: {method}")
    if payload:
        logger.info(f"Payload: {json.dumps(payload, indent=2)}")
    
    # Run the claim
    if args.run_once:
        logger.info("Running claim immediately...")
        
        # Send start notification
        send_notification(f"🚀 Starting claim for: {task_url}")
        
        # Perform the claim
        success, message = claim_zealy_task(
            task_url=task_url,
            method=method,
            payload=payload
        )
        
        # Send result notification
        if success:
            logger.info("Claim completed successfully")
            send_notification(f"✅ Claim SUCCESS!\n\n{message}")
        else:
            logger.error(f"Claim failed: {message}")
            send_notification(f"❌ Claim FAILED!\n\n{message}")
    else:
        logger.info("No action specified. Use --run-once to claim immediately.")
        logger.info("Use --help for more options.")

if __name__ == "__main__":
    main()