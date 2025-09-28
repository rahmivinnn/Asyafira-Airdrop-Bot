# utils/simple_claimer.py
import os
import json
import time
import logging
import requests
import re
from typing import Tuple, Optional, Dict, Any
from urllib.parse import urlparse

# Setup logger
logger = logging.getLogger(__name__)

def build_headers(cookie: Optional[str] = None) -> Dict[str, str]:
    """
    Build HTTP headers with cookie for Zealy.io requests.
    
    Args:
        cookie: Cookie string, if None will get from environment
    
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
        "Referer": "https://zealy.io/",
    }
    
    if cookie:
        headers["Cookie"] = cookie.strip().strip('"')
    
    return headers

def extract_zealy_url_from_cookie(cookie: Optional[str] = None) -> Optional[str]:
    """
    Extract Zealy.io task URL from cookie data.
    
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
        # Common patterns for Zealy.io URLs in cookies
        url_patterns = [
            r'zealy\.io[^;\s]*',
            r'https?://[^;\s]*zealy\.io[^;\s]*',
            r'url=([^;\s]*zealy\.io[^;\s]*)',
            r'task_url=([^;\s]*zealy\.io[^;\s]*)',
            r'claim_url=([^;\s]*zealy\.io[^;\s]*)',
        ]
        
        for pattern in url_patterns:
            matches = re.findall(pattern, cookie, re.IGNORECASE)
            for match in matches:
                # Clean up the URL
                url = match.strip().strip('"').strip("'")
                
                # Ensure it's a complete URL
                if not url.startswith(('http://', 'https://')):
                    url = f"https://{url}"
                
                # Validate URL format
                parsed = urlparse(url)
                if parsed.netloc and 'zealy.io' in parsed.netloc:
                    logger.info(f"Extracted Zealy URL from cookie: {url}")
                    return url
        
        # Try to construct common Zealy.io claim endpoints
        domain_patterns = [
            r'domain=([^;\s]*zealy\.io[^;\s]*)',
            r'host=([^;\s]*zealy\.io[^;\s]*)',
        ]
        
        for pattern in domain_patterns:
            matches = re.findall(pattern, cookie, re.IGNORECASE)
            for match in matches:
                domain = match.strip().strip('"').strip("'")
                if domain and 'zealy.io' in domain:
                    # Common Zealy.io claim endpoints
                    common_endpoints = [
                        '/api/claim',
                        '/api/tasks/claim',
                        '/api/quests/claim',
                        '/claim',
                        '/tasks/claim'
                    ]
                    for endpoint in common_endpoints:
                        url = f"https://{domain}{endpoint}"
                        logger.info(f"Constructed Zealy URL: {url}")
                        return url
        
        logger.warning("Could not extract Zealy.io URL from cookie")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting URL from cookie: {e}")
        return None

def claim_zealy_task(task_url: str,
                    method: str = "POST",
                    payload: Optional[Dict[str, Any]] = None,
                    max_retries: int = 3,
                    timeout: int = 30) -> Tuple[bool, str]:
    """
    Perform the claim request to Zealy.io task URL.
    
    Args:
        task_url: Zealy.io URL to send the claim request
        method: HTTP method (GET or POST)
        payload: Optional JSON payload for POST requests
        max_retries: Maximum number of retries
        timeout: Request timeout in seconds
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    headers = build_headers()
    attempt = 0
    
    logger.info(f"Starting claim attempt for Zealy URL: {task_url}")
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
                return True, msg
            
            elif 400 <= response.status_code < 500:
                # Client error - usually no point in retrying
                logger.error(f"Client error ({response.status_code}): {msg}")
                return False, f"Client error ({response.status_code}): {msg}"
            
            else:
                # Server error or other - retry
                logger.warning(f"Server error ({response.status_code}), attempt {attempt}/{max_retries}")
                if attempt < max_retries:
                    logger.info(f"Waiting 5s before retry...")
                    time.sleep(5)
                    continue
                else:
                    return False, f"Server error ({response.status_code}): {msg}"
        
        except requests.exceptions.Timeout:
            logger.warning(f"Request timeout on attempt {attempt}/{max_retries}")
            if attempt < max_retries:
                logger.info(f"Waiting 5s before retry...")
                time.sleep(5)
                continue
            return False, f"Request timeout after {attempt} attempts"
        
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Connection error on attempt {attempt}/{max_retries}: {e}")
            if attempt < max_retries:
                logger.info(f"Waiting 5s before retry...")
                time.sleep(5)
                continue
            return False, f"Connection error after {attempt} attempts: {e}"
        
        except requests.RequestException as e:
            logger.error(f"Request exception on attempt {attempt}/{max_retries}: {e}")
            if attempt < max_retries:
                logger.info(f"Waiting 5s before retry...")
                time.sleep(5)
                continue
            return False, f"Request error after {attempt} attempts: {e}"
        
        except Exception as e:
            logger.error(f"Unexpected error on attempt {attempt}/{max_retries}: {e}")
            if attempt < max_retries:
                logger.info(f"Waiting 5s before retry...")
                time.sleep(5)
                continue
            return False, f"Unexpected error after {attempt} attempts: {e}"
    
    return False, f"Exceeded maximum retries ({max_retries}) without success"