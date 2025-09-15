import json
import os
import time
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from cryptography.fernet import Fernet
import browser_cookie3
import logging
from config.database import get_database

class CookieManager:
    """Advanced cookie management system for Asyafira Airdrop Bot"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.db = get_database()
        
        # Encryption setup
        self.encryption_key = config.get('COOKIE_ENCRYPTION_KEY')
        self.cipher = None
        if self.encryption_key:
            try:
                self.cipher = Fernet(self.encryption_key.encode())
            except Exception as e:
                self.logger.error(f"Failed to initialize encryption: {e}")
        
        # Cookie storage
        self.cookies = {}
        self.session_cookies = {}
        self.cookie_file = "config/cookies.json"
        self.backup_file = "config/backups/cookies_backup.json"
        
        # Browser settings
        self.user_agent = config.get('USER_AGENT', 
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Auto-refresh settings
        self.auto_refresh = config.get('COOKIE_AUTO_REFRESH', True)
        self.refresh_interval = int(config.get('COOKIE_REFRESH_INTERVAL', 3600))  # 1 hour
        self.last_refresh = 0
        
        # Load existing cookies
        self.load_cookies()
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive cookie data"""
        if self.cipher and data:
            try:
                return self.cipher.encrypt(data.encode()).decode()
            except Exception as e:
                self.logger.error(f"Encryption failed: {e}")
                return data
        return data
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt cookie data"""
        if self.cipher and encrypted_data:
            try:
                return self.cipher.decrypt(encrypted_data.encode()).decode()
            except Exception as e:
                self.logger.error(f"Decryption failed: {e}")
                return encrypted_data
        return encrypted_data
    
    def extract_cookies_from_string(self, cookie_string: str, domain: str = None) -> Dict[str, str]:
        """Extract cookies from cookie string format"""
        cookies = {}
        
        if not cookie_string:
            return cookies
        
        try:
            # Handle different cookie string formats
            if cookie_string.startswith('Cookie: '):
                cookie_string = cookie_string[8:]
            
            # Split by semicolon and parse each cookie
            for cookie_pair in cookie_string.split(';'):
                cookie_pair = cookie_pair.strip()
                if '=' in cookie_pair:
                    name, value = cookie_pair.split('=', 1)
                    cookies[name.strip()] = value.strip()
        
        except Exception as e:
            self.logger.error(f"Failed to parse cookie string: {e}")
        
        return cookies
    
    def extract_cookies_from_browser(self, browser: str = 'chrome', domain: str = None) -> Dict[str, Any]:
        """Extract cookies from browser"""
        cookies = {}
        
        try:
            if browser.lower() == 'chrome':
                browser_cookies = browser_cookie3.chrome(domain_name=domain)
            elif browser.lower() == 'firefox':
                browser_cookies = browser_cookie3.firefox(domain_name=domain)
            elif browser.lower() == 'edge':
                browser_cookies = browser_cookie3.edge(domain_name=domain)
            else:
                browser_cookies = browser_cookie3.load(domain_name=domain)
            
            for cookie in browser_cookies:
                cookies[cookie.name] = {
                    'value': cookie.value,
                    'domain': cookie.domain,
                    'path': cookie.path,
                    'expires': cookie.expires,
                    'secure': cookie.secure,
                    'httpOnly': getattr(cookie, 'httpOnly', False)
                }
            
            self.logger.info(f"Extracted {len(cookies)} cookies from {browser}")
            
        except Exception as e:
            self.logger.error(f"Failed to extract cookies from {browser}: {e}")
        
        return cookies
    
    def setup_selenium_driver(self, headless: bool = True, profile_path: str = None) -> webdriver.Chrome:
        """Setup Selenium WebDriver with cookie support"""
        options = Options()
        
        if headless:
            options.add_argument('--headless')
        
        options.add_argument(f'--user-agent={self.user_agent}')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')
        options.add_argument('--disable-javascript')
        
        if profile_path:
            options.add_argument(f'--user-data-dir={profile_path}')
        
        # Disable logging
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            driver = webdriver.Chrome(
                service=webdriver.chrome.service.Service(ChromeDriverManager().install()),
                options=options
            )
            
            # Set timeouts
            driver.implicitly_wait(10)
            driver.set_page_load_timeout(30)
            
            return driver
            
        except Exception as e:
            self.logger.error(f"Failed to setup Selenium driver: {e}")
            raise
    
    def extract_cookies_with_selenium(self, url: str, wait_for_element: str = None, 
                                    login_required: bool = False) -> Dict[str, Any]:
        """Extract cookies using Selenium automation"""
        cookies = {}
        driver = None
        
        try:
            driver = self.setup_selenium_driver(
                headless=self.config.get('BROWSER_HEADLESS', True)
            )
            
            self.logger.info(f"Navigating to {url}")
            driver.get(url)
            
            # Wait for specific element if provided
            if wait_for_element:
                WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element))
                )
            
            # Handle login if required
            if login_required:
                self._handle_login(driver)
            
            # Extract cookies
            selenium_cookies = driver.get_cookies()
            
            for cookie in selenium_cookies:
                cookies[cookie['name']] = {
                    'value': cookie['value'],
                    'domain': cookie['domain'],
                    'path': cookie['path'],
                    'expires': cookie.get('expiry'),
                    'secure': cookie.get('secure', False),
                    'httpOnly': cookie.get('httpOnly', False),
                    'sameSite': cookie.get('sameSite', 'Lax')
                }
            
            self.logger.info(f"Extracted {len(cookies)} cookies with Selenium")
            
        except Exception as e:
            self.logger.error(f"Failed to extract cookies with Selenium: {e}")
        
        finally:
            if driver:
                driver.quit()
        
        return cookies
    
    def _handle_login(self, driver: webdriver.Chrome) -> bool:
        """Handle automatic login if credentials are provided"""
        try:
            # This is a placeholder for login automation
            # Implement specific login logic based on the target site
            
            # Example: Look for login form
            login_form = driver.find_elements(By.CSS_SELECTOR, 'form[action*="login"]')
            if login_form:
                self.logger.info("Login form detected, manual intervention may be required")
                # Add specific login automation here
            
            return True
            
        except Exception as e:
            self.logger.error(f"Login handling failed: {e}")
            return False
    
    def validate_cookies(self, cookies: Dict[str, Any], test_url: str = None) -> bool:
        """Validate cookies by making a test request"""
        if not cookies:
            return False
        
        try:
            session = requests.Session()
            
            # Set cookies
            for name, cookie_data in cookies.items():
                if isinstance(cookie_data, dict):
                    value = cookie_data.get('value', '')
                    domain = cookie_data.get('domain', '')
                else:
                    value = str(cookie_data)
                    domain = ''
                
                session.cookies.set(name, value, domain=domain)
            
            # Set headers
            session.headers.update({
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
            
            # Test request
            if test_url:
                response = session.get(test_url, timeout=10)
                
                # Check if we're still logged in (basic check)
                if response.status_code == 200:
                    # Look for signs of successful authentication
                    content = response.text.lower()
                    
                    # Common indicators of being logged out
                    logout_indicators = ['login', 'sign in', 'authenticate', 'unauthorized']
                    login_indicators = ['dashboard', 'profile', 'logout', 'account']
                    
                    logout_found = any(indicator in content for indicator in logout_indicators)
                    login_found = any(indicator in content for indicator in login_indicators)
                    
                    if login_found and not logout_found:
                        self.logger.info("Cookies validation successful")
                        return True
                    else:
                        self.logger.warning("Cookies may be invalid or expired")
                        return False
                else:
                    self.logger.warning(f"Test request failed with status {response.status_code}")
                    return False
            else:
                # Just check if cookies are set
                return len(session.cookies) > 0
        
        except Exception as e:
            self.logger.error(f"Cookie validation failed: {e}")
            return False
    
    def save_cookies(self, cookies: Dict[str, Any], domain: str = None, encrypt: bool = None) -> bool:
        """Save cookies to file and database"""
        if encrypt is None:
            encrypt = self.config.get('COOKIE_ENCRYPTION_ENABLED', True)
        
        try:
            # Prepare cookies for storage
            storage_cookies = {}
            db_cookies = []
            
            for name, cookie_data in cookies.items():
                if isinstance(cookie_data, dict):
                    value = cookie_data.get('value', '')
                    cookie_info = cookie_data
                else:
                    value = str(cookie_data)
                    cookie_info = {
                        'value': value,
                        'domain': domain or '',
                        'path': '/',
                        'expires': None,
                        'secure': False,
                        'httpOnly': False,
                        'sameSite': 'Lax'
                    }
                
                # Encrypt if enabled
                if encrypt:
                    value = self.encrypt_data(value)
                
                storage_cookies[name] = {
                    **cookie_info,
                    'value': value,
                    'encrypted': encrypt,
                    'saved_at': datetime.now().isoformat()
                }
                
                # Prepare for database
                db_cookies.append({
                    'domain': cookie_info.get('domain', domain or ''),
                    'name': name,
                    'value': value,
                    'expires': cookie_info.get('expires'),
                    'path': cookie_info.get('path', '/'),
                    'secure': cookie_info.get('secure', False),
                    'httpOnly': cookie_info.get('httpOnly', False),
                    'sameSite': cookie_info.get('sameSite', 'Lax')
                })
            
            # Save to file
            os.makedirs(os.path.dirname(self.cookie_file), exist_ok=True)
            
            with open(self.cookie_file, 'w') as f:
                json.dump(storage_cookies, f, indent=2)
            
            # Save to database
            self.db.save_cookies(db_cookies, encrypt=encrypt)
            
            # Create backup
            if self.config.get('COOKIE_BACKUP_ENABLED', True):
                os.makedirs(os.path.dirname(self.backup_file), exist_ok=True)
                with open(self.backup_file, 'w') as f:
                    json.dump(storage_cookies, f, indent=2)
            
            # Update internal storage
            self.cookies.update(cookies)
            
            self.logger.info(f"Saved {len(cookies)} cookies")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save cookies: {e}")
            return False
    
    def load_cookies(self, source: str = 'file') -> Dict[str, Any]:
        """Load cookies from file or database"""
        cookies = {}
        
        try:
            if source == 'file' and os.path.exists(self.cookie_file):
                with open(self.cookie_file, 'r') as f:
                    stored_cookies = json.load(f)
                
                for name, cookie_data in stored_cookies.items():
                    value = cookie_data.get('value', '')
                    
                    # Decrypt if encrypted
                    if cookie_data.get('encrypted', False):
                        value = self.decrypt_data(value)
                    
                    cookies[name] = {
                        **cookie_data,
                        'value': value
                    }
            
            elif source == 'database':
                db_cookies = self.db.get_cookies()
                
                for cookie in db_cookies:
                    cookies[cookie['name']] = cookie
            
            self.cookies.update(cookies)
            self.logger.info(f"Loaded {len(cookies)} cookies from {source}")
            
        except Exception as e:
            self.logger.error(f"Failed to load cookies from {source}: {e}")
        
        return cookies
    
    def get_cookies_for_domain(self, domain: str) -> Dict[str, str]:
        """Get cookies for specific domain"""
        domain_cookies = {}
        
        for name, cookie_data in self.cookies.items():
            if isinstance(cookie_data, dict):
                cookie_domain = cookie_data.get('domain', '')
                if domain in cookie_domain or cookie_domain in domain:
                    domain_cookies[name] = cookie_data.get('value', '')
            else:
                domain_cookies[name] = str(cookie_data)
        
        return domain_cookies
    
    def get_cookie_header(self, domain: str = None) -> str:
        """Get cookies formatted as HTTP Cookie header"""
        cookies = self.get_cookies_for_domain(domain) if domain else self.cookies
        
        cookie_pairs = []
        for name, cookie_data in cookies.items():
            if isinstance(cookie_data, dict):
                value = cookie_data.get('value', '')
            else:
                value = str(cookie_data)
            
            cookie_pairs.append(f"{name}={value}")
        
        return '; '.join(cookie_pairs)
    
    def refresh_cookies(self, url: str = None, force: bool = False) -> bool:
        """Refresh cookies if needed"""
        current_time = time.time()
        
        if not force and (current_time - self.last_refresh) < self.refresh_interval:
            return True
        
        if not self.auto_refresh and not force:
            return True
        
        try:
            self.logger.info("Refreshing cookies...")
            
            if url:
                # Extract fresh cookies from the URL
                fresh_cookies = self.extract_cookies_with_selenium(url)
                
                if fresh_cookies:
                    self.save_cookies(fresh_cookies)
                    self.last_refresh = current_time
                    self.logger.info("Cookies refreshed successfully")
                    return True
            else:
                # Try to refresh from browser
                fresh_cookies = self.extract_cookies_from_browser()
                
                if fresh_cookies:
                    self.save_cookies(fresh_cookies)
                    self.last_refresh = current_time
                    self.logger.info("Cookies refreshed from browser")
                    return True
            
            self.logger.warning("Failed to refresh cookies")
            return False
            
        except Exception as e:
            self.logger.error(f"Cookie refresh failed: {e}")
            return False
    
    def clear_cookies(self, domain: str = None) -> bool:
        """Clear cookies"""
        try:
            if domain:
                # Clear cookies for specific domain
                self.cookies = {
                    name: cookie_data for name, cookie_data in self.cookies.items()
                    if not (isinstance(cookie_data, dict) and 
                           domain in cookie_data.get('domain', ''))
                }
            else:
                # Clear all cookies
                self.cookies = {}
            
            # Update file
            with open(self.cookie_file, 'w') as f:
                json.dump(self.cookies, f, indent=2)
            
            self.logger.info(f"Cleared cookies{' for ' + domain if domain else ''}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear cookies: {e}")
            return False
    
    def export_cookies(self, format_type: str = 'json', file_path: str = None) -> str:
        """Export cookies in various formats"""
        if not file_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = f"config/exports/cookies_export_{timestamp}.{format_type}"
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        try:
            if format_type == 'json':
                with open(file_path, 'w') as f:
                    json.dump(self.cookies, f, indent=2)
            
            elif format_type == 'netscape':
                # Netscape cookie format
                with open(file_path, 'w') as f:
                    f.write("# Netscape HTTP Cookie File\n")
                    f.write("# This is a generated file! Do not edit.\n\n")
                    
                    for name, cookie_data in self.cookies.items():
                        if isinstance(cookie_data, dict):
                            domain = cookie_data.get('domain', '')
                            path = cookie_data.get('path', '/')
                            secure = 'TRUE' if cookie_data.get('secure', False) else 'FALSE'
                            expires = cookie_data.get('expires', 0)
                            value = cookie_data.get('value', '')
                            
                            f.write(f"{domain}\tTRUE\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")
            
            self.logger.info(f"Cookies exported to {file_path}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Failed to export cookies: {e}")
            return None
    
    def import_cookies(self, file_path: str, format_type: str = 'json') -> bool:
        """Import cookies from file"""
        try:
            if format_type == 'json':
                with open(file_path, 'r') as f:
                    imported_cookies = json.load(f)
                
                self.cookies.update(imported_cookies)
                self.save_cookies(imported_cookies)
            
            self.logger.info(f"Cookies imported from {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import cookies: {e}")
            return False
    
    def get_session_with_cookies(self, domain: str = None) -> requests.Session:
        """Get requests session with cookies applied"""
        session = requests.Session()
        
        # Apply cookies
        cookies = self.get_cookies_for_domain(domain) if domain else self.cookies
        
        for name, cookie_data in cookies.items():
            if isinstance(cookie_data, dict):
                value = cookie_data.get('value', '')
                cookie_domain = cookie_data.get('domain', domain or '')
            else:
                value = str(cookie_data)
                cookie_domain = domain or ''
            
            session.cookies.set(name, value, domain=cookie_domain)
        
        # Set headers
        session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        return session
    
    def monitor_cookie_health(self) -> Dict[str, Any]:
        """Monitor cookie health and validity"""
        health_report = {
            'total_cookies': len(self.cookies),
            'expired_cookies': 0,
            'valid_cookies': 0,
            'encrypted_cookies': 0,
            'last_refresh': self.last_refresh,
            'next_refresh': self.last_refresh + self.refresh_interval,
            'issues': []
        }
        
        current_time = time.time()
        
        for name, cookie_data in self.cookies.items():
            if isinstance(cookie_data, dict):
                # Check expiration
                expires = cookie_data.get('expires')
                if expires and expires < current_time:
                    health_report['expired_cookies'] += 1
                    health_report['issues'].append(f"Cookie '{name}' has expired")
                else:
                    health_report['valid_cookies'] += 1
                
                # Check encryption
                if cookie_data.get('encrypted', False):
                    health_report['encrypted_cookies'] += 1
        
        # Check if refresh is needed
        if (current_time - self.last_refresh) > self.refresh_interval:
            health_report['issues'].append("Cookies need refresh")
        
        return health_report