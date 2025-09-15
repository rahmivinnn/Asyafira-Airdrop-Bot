# utils/captcha.py
import os
import time
import logging
import requests
from typing import Optional, Dict, Any
from datetime import datetime

# Setup logger
logger = logging.getLogger(__name__)

def manual_captcha_input(response: requests.Response) -> Optional[str]:
    """
    Handle captcha through manual user input.
    
    Args:
        response: The response containing captcha challenge
    
    Returns:
        Captcha solution string or None if failed
    """
    try:
        print("\n" + "="*60)
        print("🤖 CAPTCHA DETECTED!")
        print("="*60)
        print(f"URL: {response.url}")
        print(f"Status Code: {response.status_code}")
        print("\nResponse preview:")
        print("-" * 40)
        print(response.text[:500] + "..." if len(response.text) > 500 else response.text)
        print("-" * 40)
        
        print("\n📋 Instructions:")
        print("1. Open the URL in your browser")
        print("2. Complete the captcha challenge")
        print("3. Check if the page loads successfully")
        print("4. Enter 'success' if completed, or 'skip' to skip this attempt")
        
        while True:
            user_input = input("\n🔐 Enter captcha result (success/skip): ").strip().lower()
            
            if user_input == "success":
                print("✅ Captcha marked as solved. Continuing...")
                return "solved"
            elif user_input == "skip":
                print("⏭️ Skipping captcha challenge.")
                return None
            else:
                print("❌ Invalid input. Please enter 'success' or 'skip'.")
    
    except KeyboardInterrupt:
        print("\n⏹️ Captcha handling interrupted by user.")
        return None
    except Exception as e:
        logger.error(f"Error in manual captcha input: {e}")
        return None

def solve_with_2captcha(site_key: str, page_url: str, api_key: Optional[str] = None) -> Optional[str]:
    """
    Solve captcha using 2captcha service.
    
    Args:
        site_key: The site key for the captcha
        page_url: The URL where captcha is located
        api_key: 2captcha API key (if None, gets from environment)
    
    Returns:
        Captcha solution token or None if failed
    """
    api_key = api_key or os.getenv("TWOCAPTCHA_API_KEY")
    
    if not api_key:
        logger.warning("2captcha API key not configured")
        return None
    
    try:
        logger.info("Attempting to solve captcha with 2captcha service")
        
        # Submit captcha to 2captcha
        submit_url = "http://2captcha.com/in.php"
        submit_data = {
            "key": api_key,
            "method": "userrecaptcha",
            "googlekey": site_key,
            "pageurl": page_url,
            "json": 1
        }
        
        logger.debug("Submitting captcha to 2captcha")
        submit_response = requests.post(submit_url, data=submit_data, timeout=30)
        submit_result = submit_response.json()
        
        if submit_result.get("status") != 1:
            logger.error(f"2captcha submit failed: {submit_result.get('error_text')}")
            return None
        
        captcha_id = submit_result.get("request")
        logger.info(f"Captcha submitted to 2captcha with ID: {captcha_id}")
        
        # Wait for solution
        result_url = "http://2captcha.com/res.php"
        max_wait_time = 300  # 5 minutes
        check_interval = 10  # 10 seconds
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            time.sleep(check_interval)
            elapsed_time += check_interval
            
            result_data = {
                "key": api_key,
                "action": "get",
                "id": captcha_id,
                "json": 1
            }
            
            result_response = requests.get(result_url, params=result_data, timeout=30)
            result = result_response.json()
            
            if result.get("status") == 1:
                solution = result.get("request")
                logger.info("Captcha solved successfully with 2captcha")
                return solution
            elif result.get("error_text") == "CAPCHA_NOT_READY":
                logger.debug(f"Captcha not ready, waiting... ({elapsed_time}s elapsed)")
                continue
            else:
                logger.error(f"2captcha error: {result.get('error_text')}")
                return None
        
        logger.error("2captcha timeout: captcha not solved within time limit")
        return None
        
    except requests.RequestException as e:
        logger.error(f"2captcha request error: {e}")
        return None
    except Exception as e:
        logger.error(f"2captcha unexpected error: {e}")
        return None

def extract_captcha_info(response: requests.Response) -> Dict[str, Any]:
    """
    Extract captcha information from response.
    
    Args:
        response: The response containing captcha
    
    Returns:
        Dictionary with captcha information
    """
    captcha_info = {
        "type": "unknown",
        "site_key": None,
        "page_url": response.url,
        "detected": True
    }
    
    response_text = response.text.lower()
    
    # Detect reCAPTCHA
    if "recaptcha" in response_text or "g-recaptcha" in response_text:
        captcha_info["type"] = "recaptcha"
        # Try to extract site key (simplified)
        import re
        site_key_match = re.search(r'data-sitekey=["\']([^"\'\']+)["\']', response.text, re.IGNORECASE)
        if site_key_match:
            captcha_info["site_key"] = site_key_match.group(1)
    
    # Detect hCaptcha
    elif "hcaptcha" in response_text or "h-captcha" in response_text:
        captcha_info["type"] = "hcaptcha"
        import re
        site_key_match = re.search(r'data-sitekey=["\']([^"\'\']+)["\']', response.text, re.IGNORECASE)
        if site_key_match:
            captcha_info["site_key"] = site_key_match.group(1)
    
    # Detect Cloudflare challenge
    elif "cloudflare" in response_text or "cf-challenge" in response_text:
        captcha_info["type"] = "cloudflare"
    
    # Detect other challenges
    elif any(keyword in response_text for keyword in ["challenge", "verification", "robot"]):
        captcha_info["type"] = "generic"
    
    return captcha_info

def handle_captcha(response: requests.Response) -> bool:
    """
    Main captcha handling function.
    
    Args:
        response: The response containing captcha challenge
    
    Returns:
        True if captcha was handled successfully, False otherwise
    """
    try:
        logger.warning("Captcha detected, attempting to handle...")
        
        # Extract captcha information
        captcha_info = extract_captcha_info(response)
        logger.info(f"Captcha type detected: {captcha_info['type']}")
        
        # Send Telegram notification
        try:
            from .telegram import notify_captcha_detected
            notify_captcha_detected(response.url)
        except Exception as e:
            logger.debug(f"Failed to send captcha notification: {e}")
        
        # Check if manual captcha handling is enabled
        manual_captcha_enabled = os.getenv("MANUAL_CAPTCHA", "true").lower() == "true"
        
        if manual_captcha_enabled:
            logger.info("Attempting manual captcha handling")
            result = manual_captcha_input(response)
            if result:
                return True
        
        # Try automatic solving if API key is available
        if captcha_info["site_key"] and captcha_info["type"] in ["recaptcha", "hcaptcha"]:
            logger.info("Attempting automatic captcha solving")
            solution = solve_with_2captcha(
                captcha_info["site_key"], 
                captcha_info["page_url"]
            )
            if solution:
                logger.info("Captcha solved automatically")
                # Note: In a real implementation, you would need to submit
                # the solution back to the original form/endpoint
                return True
        
        logger.warning("All captcha handling methods failed")
        return False
        
    except Exception as e:
        logger.error(f"Error in captcha handling: {e}")
        return False

def wait_for_cloudflare(response: requests.Response, max_wait: int = 30) -> bool:
    """
    Wait for Cloudflare challenge to complete.
    
    Args:
        response: The response with Cloudflare challenge
        max_wait: Maximum time to wait in seconds
    
    Returns:
        True if challenge appears to be completed
    """
    try:
        logger.info(f"Waiting for Cloudflare challenge to complete (max {max_wait}s)")
        
        print("\n" + "="*60)
        print("☁️ CLOUDFLARE CHALLENGE DETECTED")
        print("="*60)
        print(f"URL: {response.url}")
        print("\n📋 Instructions:")
        print("1. Open the URL in your browser")
        print("2. Wait for Cloudflare challenge to complete")
        print("3. The page should load automatically")
        print(f"4. Waiting up to {max_wait} seconds...")
        
        # Simple wait - in a real implementation, you might want to
        # periodically check if the challenge is completed
        for i in range(max_wait):
            print(f"\r⏳ Waiting... {max_wait - i}s remaining", end="", flush=True)
            time.sleep(1)
        
        print("\n✅ Wait completed. Continuing with request...")
        return True
        
    except KeyboardInterrupt:
        print("\n⏹️ Cloudflare wait interrupted by user.")
        return False
    except Exception as e:
        logger.error(f"Error waiting for Cloudflare: {e}")
        return False