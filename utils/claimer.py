# utils/claimer.py
import os
import json
import time
import logging
import requests
import re
from datetime import datetime
from typing import Tuple, Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
from .captcha import handle_captcha

# Setup logger
logger = logging.getLogger(__name__)

def build_headers(cookie: Optional[str] = None, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Build HTTP headers with cookie and additional headers.
    
    Args:
        cookie: Cookie string, if None will get from environment
        additional_headers: Additional headers to include
    
    Returns:
        Dictionary of headers
    """
    cookie = cookie if cookie is not None else os.getenv("COOKIE")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }
    
    if cookie:
        headers["Cookie"] = cookie.strip().strip('"')
    
    if additional_headers:
        headers.update(additional_headers)
    
    return headers

def extract_url_from_cookie(cookie: Optional[str] = None) -> Optional[str]:
    """
    Extract task URL from cookie data.
    
    Args:
        cookie: Cookie string, if None will get from environment
    
    Returns:
        Extracted URL or None if not found
    """
    cookie = cookie if cookie is not None else os.getenv("COOKIE")
    
    if not cookie:
        logger.warning("No cookie found to extract URL from")
        return None
    
    try:
        # Common patterns for URLs in cookies
        url_patterns = [
            r'url=([^;\s]+)',
            r'task_url=([^;\s]+)',
            r'claim_url=([^;\s]+)',
            r'endpoint=([^;\s]+)',
            r'api_url=([^;\s]+)',
            r'target=([^;\s]+)',
            r'https?://[^;\s]+'
        ]
        
        for pattern in url_patterns:
            matches = re.findall(pattern, cookie, re.IGNORECASE)
            for match in matches:
                # Clean up the URL
                url = match.strip().strip('"').strip("'")
                
                # Validate URL format
                if url.startswith(('http://', 'https://')):
                    parsed = urlparse(url)
                    if parsed.netloc:  # Valid domain
                        logger.info(f"Extracted URL from cookie: {url}")
                        return url
        
        # Try to find domain and construct URL
        domain_patterns = [
            r'domain=([^;\s]+)',
            r'host=([^;\s]+)',
            r'site=([^;\s]+)'
        ]
        
        for pattern in domain_patterns:
            matches = re.findall(pattern, cookie, re.IGNORECASE)
            for match in matches:
                domain = match.strip().strip('"').strip("'")
                if domain and '.' in domain:
                    # Common airdrop endpoints
                    common_endpoints = ['/claim', '/api/claim', '/task/claim', '/airdrop/claim']
                    for endpoint in common_endpoints:
                        url = f"https://{domain}{endpoint}"
                        logger.info(f"Constructed URL from domain: {url}")
                        return url
        
        logger.warning("Could not extract URL from cookie")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting URL from cookie: {e}")
        return None

def save_raw_response(response: requests.Response, success: bool) -> Optional[str]:
    """
    Save raw response to file with timestamp.
    
    Args:
        response: requests.Response object
        success: Whether the request was successful
    
    Returns:
        Path to saved file or None if saving disabled
    """
    if not os.getenv("SAVE_RAW_RESPONSES", "true").lower() == "true":
        return None
    
    try:
        # Create responses directory if it doesn't exist
        responses_dir = "responses"
        if not os.path.exists(responses_dir):
            os.makedirs(responses_dir)
        
        # Generate timestamp
        timestamp = datetime.now().isoformat().replace(":", "-").replace(".", "-")
        status = "success" if success else "failed"
        
        # Try to parse as JSON first
        try:
            response_data = {
                "timestamp": datetime.now().isoformat(),
                "url": response.url,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.json()
            }
            filename = f"{timestamp}_{status}_response.json"
            filepath = os.path.join(responses_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
                
        except (json.JSONDecodeError, ValueError):
            # Save as text if not JSON
            response_data = {
                "timestamp": datetime.now().isoformat(),
                "url": response.url,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content": response.text
            }
            filename = f"{timestamp}_{status}_response.txt"
            filepath = os.path.join(responses_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Timestamp: {response_data['timestamp']}\n")
                f.write(f"URL: {response_data['url']}\n")
                f.write(f"Status Code: {response_data['status_code']}\n")
                f.write(f"Headers: {json.dumps(response_data['headers'], indent=2)}\n")
                f.write(f"\nContent:\n{response_data['content']}")
        
        logger.info(f"Raw response saved to: {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Failed to save raw response: {e}")
        return None

def detect_captcha(response: requests.Response) -> bool:
    """
    Detect if response contains captcha challenge.
    
    Args:
        response: requests.Response object
    
    Returns:
        True if captcha detected, False otherwise
    """
    # Common captcha indicators
    captcha_indicators = [
        "captcha",
        "recaptcha",
        "hcaptcha",
        "cloudflare",
        "challenge",
        "verification",
        "robot",
        "human"
    ]
    
    response_text = response.text.lower()
    
    for indicator in captcha_indicators:
        if indicator in response_text:
            return True
    
    # Check for common captcha status codes
    if response.status_code in [403, 429]:
        return True
    
    return False

def claim_task(task_url: str,
               method: str = "POST",
               payload: Optional[Dict[str, Any]] = None,
               max_retries: Optional[int] = None,
               timeout: Optional[int] = None,
               retry_delay: Optional[int] = None) -> Tuple[bool, str, Optional[str]]:
    """
    Perform the claim request to task_url using the Cookie header.
    
    Args:
        task_url: URL to send the claim request
        method: HTTP method (GET or POST)
        payload: Optional JSON payload for POST requests
        max_retries: Maximum number of retries
        timeout: Request timeout in seconds
        retry_delay: Delay between retries in seconds
    
    Returns:
        Tuple of (success: bool, message: str, response_file_path: Optional[str])
    """
    # Get configuration from environment with defaults
    max_retries = max_retries or int(os.getenv("MAX_RETRIES", "3"))
    timeout = timeout or int(os.getenv("REQUEST_TIMEOUT", "30"))
    retry_delay = retry_delay or int(os.getenv("RETRY_DELAY", "5"))
    
    headers = build_headers()
    attempt = 0
    response_file_path = None
    
    logger.info(f"Starting claim attempt for URL: {task_url}")
    logger.info(f"Method: {method}, Max retries: {max_retries}, Timeout: {timeout}s")
    
    while attempt < max_retries:
        try:
            attempt += 1
            logger.info(f"Attempt {attempt}/{max_retries}")
            
            # Make the request
            if method.upper() == "GET":
                response = requests.get(task_url, headers=headers, timeout=timeout)
            else:
                # Default to POST
                if payload is not None:
                    headers["Content-Type"] = "application/json"
                    response = requests.post(task_url, json=payload, headers=headers, timeout=timeout)
                else:
                    response = requests.post(task_url, headers=headers, timeout=timeout)
            
            logger.info(f"Response status: {response.status_code}")
            
            # Check for captcha
            if detect_captcha(response):
                logger.warning("Captcha detected in response")
                captcha_result = handle_captcha(response)
                if not captcha_result:
                    logger.error("Captcha handling failed")
                    response_file_path = save_raw_response(response, False)
                    return False, "Captcha challenge failed", response_file_path
                else:
                    logger.info("Captcha handled successfully, retrying request")
                    continue
            
            # Parse response
            try:
                json_resp = response.json()
                content_preview = json.dumps(json_resp, indent=2)[:500]
                msg = f"Status: {response.status_code}\nContent: {content_preview}"
            except (json.JSONDecodeError, ValueError):
                content_preview = response.text[:500]
                msg = f"Status: {response.status_code}\nContent: {content_preview}"
            
            # Determine success based on status code
            if 200 <= response.status_code < 300:
                logger.info(f"Claim successful on attempt {attempt}")
                response_file_path = save_raw_response(response, True)
                return True, msg, response_file_path
            
            elif 400 <= response.status_code < 500:
                # Client error - usually no point in retrying
                logger.error(f"Client error ({response.status_code}): {msg}")
                response_file_path = save_raw_response(response, False)
                return False, f"Client error ({response.status_code}): {msg}", response_file_path
            
            else:
                # Server error or other - retry
                logger.warning(f"Server error ({response.status_code}), attempt {attempt}/{max_retries}")
                if attempt < max_retries:
                    logger.info(f"Waiting {retry_delay}s before retry...")
                    time.sleep(retry_delay)
                    continue
                else:
                    response_file_path = save_raw_response(response, False)
                    return False, f"Server error ({response.status_code}): {msg}", response_file_path
        
        except requests.exceptions.Timeout:
            logger.warning(f"Request timeout on attempt {attempt}/{max_retries}")
            if attempt < max_retries:
                logger.info(f"Waiting {retry_delay}s before retry...")
                time.sleep(retry_delay)
                continue
            return False, f"Request timeout after {attempt} attempts", None
        
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error on attempt {attempt}/{max_retries}: {e}")
            if attempt < max_retries:
                logger.info(f"Waiting {retry_delay}s before retry...")
                time.sleep(retry_delay)
                continue
            return False, f"Connection error after {attempt} attempts: {e}", None
        
        except requests.RequestException as e:
            logger.error(f"Request exception on attempt {attempt}/{max_retries}: {e}")
            if attempt < max_retries:
                logger.info(f"Waiting {retry_delay}s before retry...")
                time.sleep(retry_delay)
                continue
            return False, f"Request error after {attempt} attempts: {e}", None
        
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt}/{max_retries}: {e}")
            if attempt < max_retries:
                logger.info(f"Waiting {retry_delay}s before retry...")
                time.sleep(retry_delay)
                continue
            return False, f"Unexpected error after {attempt} attempts: {e}", None
    
    return False, f"Exceeded maximum retries ({max_retries}) without success", None