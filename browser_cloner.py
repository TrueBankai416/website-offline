#!/usr/bin/env python3
"""
Enhanced website cloner with headless browser support for JavaScript-heavy sites and authentication.
"""

import os
import time
import json
import urllib.parse
from pathlib import Path
from collections import deque
import argparse
import sys

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.safari.service import Service as SafariService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from bs4 import BeautifulSoup
import requests
import shutil
import platform


class BrowserWebsiteCloner:
    def __init__(self, max_depth=3, max_pages=100, delay=1.0, headless=True, wait_time=5.0, browser="auto"):
        self.downloaded_files = set()
        self.downloaded_pages = set()
        self.url_queue = deque()
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.delay = delay
        self.headless = headless
        self.wait_time = wait_time
        self.browser = browser
        self.detected_browser = None
        self.base_domain = None
        self.base_url = None
        self.driver = None
        
        # Authentication settings
        self.auth_username = None
        self.auth_password = None
        self.auth_login_url = None
        self.auth_username_field = "username"
        self.auth_password_field = "password"
        self.auth_submit_selector = "input[type='submit'], button[type='submit'], button"
        self.auth_cookies = {}
        self.auth_headers = {}
        
    def log_message(self, message):
        print(f"[INFO] {message}")
        
    def detect_available_browsers(self):
        """Detect which browsers are available on the system."""
        available_browsers = []
        
        # Check for Chrome
        chrome_paths = [
            "google-chrome",
            "google-chrome-stable", 
            "chrome",
            "chromium",
            "chromium-browser",
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
        ]
        
        for path in chrome_paths:
            if shutil.which(path) or os.path.exists(path):
                available_browsers.append("chrome")
                break
                
        # Check for Firefox
        firefox_paths = [
            "firefox",
            "firefox-esr",
            "/usr/bin/firefox",
            "/usr/bin/firefox-esr", 
            "/Applications/Firefox.app/Contents/MacOS/firefox",
            "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
            "C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe"
        ]
        
        for path in firefox_paths:
            if shutil.which(path) or os.path.exists(path):
                available_browsers.append("firefox")
                break
                
        # Check for Edge (Windows/macOS)
        edge_paths = [
            "msedge",
            "microsoft-edge",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
            "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe"
        ]
        
        for path in edge_paths:
            if shutil.which(path) or os.path.exists(path):
                available_browsers.append("edge")
                break
                
        # Check for Safari (macOS only)
        if platform.system() == "Darwin":
            safari_path = "/Applications/Safari.app/Contents/MacOS/Safari"
            if os.path.exists(safari_path):
                available_browsers.append("safari")
        
        return available_browsers
        
    def select_best_browser(self):
        """Select the best available browser."""
        if self.browser != "auto":
            return self.browser
            
        available = self.detect_available_browsers()
        
        if not available:
            raise Exception("No supported browsers found. Please install Chrome, Firefox, Edge, or Safari.")
            
        # Priority order: Chrome > Firefox > Edge > Safari
        priority = ["chrome", "firefox", "edge", "safari"]
        
        for browser in priority:
            if browser in available:
                return browser
                
        return available[0]  # Fallback to first available
        
    def setup_browser(self):
        """Initialize the headless browser."""
        try:
            # Select the best available browser
            selected_browser = self.select_best_browser()
            self.detected_browser = selected_browser
            
            self.log_message(f"Using browser: {selected_browser}")
            
            if selected_browser == "chrome":
                return self._setup_chrome()
            elif selected_browser == "firefox":
                return self._setup_firefox()
            elif selected_browser == "edge":
                return self._setup_edge()
            elif selected_browser == "safari":
                return self._setup_safari()
            else:
                raise Exception(f"Unsupported browser: {selected_browser}")
                
        except Exception as e:
            self.log_message(f"Failed to initialize browser: {str(e)}")
            return False
            
    def _setup_chrome(self):
        """Setup Chrome browser."""
        try:
            chrome_options = ChromeOptions()
            if self.headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
            
            service = ChromeService(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            
            self.log_message("Chrome browser initialized successfully")
            return True
            
        except Exception as e:
            self.log_message(f"Failed to initialize Chrome: {str(e)}")
            return False
            
    def _setup_firefox(self):
        """Setup Firefox browser."""
        try:
            firefox_options = FirefoxOptions()
            if self.headless:
                firefox_options.add_argument("--headless")
            firefox_options.add_argument("--width=1920")
            firefox_options.add_argument("--height=1080")
            firefox_options.set_preference("general.useragent.override", 
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0")
            
            service = FirefoxService(GeckoDriverManager().install())
            self.driver = webdriver.Firefox(service=service, options=firefox_options)
            self.driver.set_page_load_timeout(30)
            
            self.log_message("Firefox browser initialized successfully")
            return True
            
        except Exception as e:
            self.log_message(f"Failed to initialize Firefox: {str(e)}")
            return False
            
    def _setup_edge(self):
        """Setup Edge browser."""
        try:
            edge_options = EdgeOptions()
            if self.headless:
                edge_options.add_argument("--headless")
            edge_options.add_argument("--no-sandbox")
            edge_options.add_argument("--disable-dev-shm-usage")
            edge_options.add_argument("--disable-gpu")
            edge_options.add_argument("--window-size=1920,1080")
            edge_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59")
            
            service = EdgeService(EdgeChromiumDriverManager().install())
            self.driver = webdriver.Edge(service=service, options=edge_options)
            self.driver.set_page_load_timeout(30)
            
            self.log_message("Edge browser initialized successfully")
            return True
            
        except Exception as e:
            self.log_message(f"Failed to initialize Edge: {str(e)}")
            return False
            
    def _setup_safari(self):
        """Setup Safari browser (macOS only)."""
        try:
            if platform.system() != "Darwin":
                raise Exception("Safari is only available on macOS")
                
            # Safari doesn't support headless mode through Selenium
            if self.headless:
                self.log_message("Safari doesn't support headless mode, running in visible mode")
                
            service = SafariService()
            self.driver = webdriver.Safari(service=service)
            self.driver.set_page_load_timeout(30)
            
            # Set window size for Safari
            self.driver.set_window_size(1920, 1080)
            
            self.log_message("Safari browser initialized successfully")
            return True
            
        except Exception as e:
            self.log_message(f"Failed to initialize Safari: {str(e)}")
            return False
            
    def cleanup_browser(self):
        """Clean up browser resources."""
        if self.driver:
            try:
                self.driver.quit()
                self.log_message("Browser cleaned up")
            except Exception as e:
                self.log_message(f"Error cleaning up browser: {str(e)}")
                
    def set_authentication(self, username=None, password=None, login_url=None, 
                          username_field="username", password_field="password",
                          submit_selector="input[type='submit'], button[type='submit'], button"):
        """Set authentication credentials and login parameters."""
        self.auth_username = username
        self.auth_password = password
        self.auth_login_url = login_url
        self.auth_username_field = username_field
        self.auth_password_field = password_field
        self.auth_submit_selector = submit_selector
        
    def set_cookies(self, cookies_dict):
        """Set custom cookies for authentication."""
        self.auth_cookies = cookies_dict
        
    def set_headers(self, headers_dict):
        """Set custom headers for authentication."""
        self.auth_headers = headers_dict
        
    def perform_login(self):
        """Perform login if authentication is configured."""
        if not self.auth_username or not self.auth_password:
            return True
            
        try:
            login_url = self.auth_login_url or self.base_url
            self.log_message(f"Performing login at: {login_url}")
            
            self.driver.get(login_url)
            time.sleep(2)
            
            # Find and fill username field
            username_field = self.driver.find_element(By.NAME, self.auth_username_field)
            username_field.clear()
            username_field.send_keys(self.auth_username)
            
            # Find and fill password field
            password_field = self.driver.find_element(By.NAME, self.auth_password_field)
            password_field.clear()
            password_field.send_keys(self.auth_password)
            
            # Submit form
            submit_button = self.driver.find_element(By.CSS_SELECTOR, self.auth_submit_selector)
            submit_button.click()
            
            # Wait for page to load after login
            time.sleep(3)
            
            self.log_message("Login completed")
            return True
            
        except Exception as e:
            self.log_message(f"Login failed: {str(e)}")
            return False
            
    def add_custom_cookies(self):
        """Add custom cookies to the browser session."""
        if not self.auth_cookies:
            return
            
        try:
            for name, value in self.auth_cookies.items():
                self.driver.add_cookie({"name": name, "value": value})
            self.log_message(f"Added {len(self.auth_cookies)} custom cookies")
        except Exception as e:
            self.log_message(f"Failed to add cookies: {str(e)}")
            
    def wait_for_page_load(self, additional_wait=None):
        """Wait for page to fully load including JavaScript."""
        try:
            # Wait for document ready state
            WebDriverWait(self.driver, 10).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Additional wait for dynamic content
            wait_time = additional_wait or self.wait_time
            if wait_time > 0:
                time.sleep(wait_time)
                
            return True
        except TimeoutException:
            self.log_message("Page load timeout, continuing anyway")
            return False
            
    def get_page_with_js(self, url):
        """Load a page and execute JavaScript, returning the rendered HTML."""
        try:
            self.log_message(f"Loading page with JavaScript: {url}")
            
            self.driver.get(url)
            self.wait_for_page_load()
            
            # Get the rendered HTML after JavaScript execution
            html = self.driver.page_source
            return html
            
        except Exception as e:
            self.log_message(f"Failed to load page {url}: {str(e)}")
            return None
            
    def normalize_url(self, url):
        """Normalize URL by removing fragments and query parameters for crawling purposes."""
        parsed = urllib.parse.urlparse(url)
        return urllib.parse.urlunparse((
            parsed.scheme, parsed.netloc, parsed.path, '', '', ''
        ))
        
    def is_same_domain(self, url):
        """Check if URL belongs to the same domain as the base URL."""
        parsed = urllib.parse.urlparse(url)
        base_parsed = urllib.parse.urlparse(self.base_url)
        return parsed.netloc == base_parsed.netloc
        
    def url_to_local_path(self, url):
        """Convert URL to local file path."""
        parsed = urllib.parse.urlparse(url)
        path = parsed.path.strip('/')
        
        # Handle root path
        if not path:
            return 'index.html'
            
        # Handle directory paths (add index.html)
        if path.endswith('/') or '.' not in os.path.basename(path):
            if path.endswith('/'):
                path = path[:-1]
            return f"{path}/index.html" if path else "index.html"
            
        return path
        
    def create_local_directories(self, output_dir, local_path):
        """Create necessary directories for the local path."""
        full_path = os.path.join(output_dir, local_path)
        directory = os.path.dirname(full_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        return full_path
        
    def extract_internal_links(self, soup, current_url):
        """Extract all internal links from the page for crawling."""
        links = set()
        
        # Extract from <a> tags
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Skip non-HTTP links
            if href.startswith(('mailto:', 'tel:', 'javascript:', '#')):
                continue
                
            absolute_url = urllib.parse.urljoin(current_url, href)
            normalized_url = self.normalize_url(absolute_url)
            
            if self.is_same_domain(normalized_url):
                # Only crawl HTML pages (avoid PDFs, images, etc.)
                parsed = urllib.parse.urlparse(normalized_url)
                path = parsed.path.lower()
                if (not path or path.endswith('/') or path.endswith('.html') or 
                    path.endswith('.htm') or '.' not in os.path.basename(path)):
                    links.add(normalized_url)
                    
        return links
        
    def download_asset(self, url, assets_dir, filename):
        """Download and save an asset file."""
        try:
            # Skip if already downloaded
            if url in self.downloaded_files:
                return True
                
            self.downloaded_files.add(url)
            
            self.log_message(f"Downloading asset: {url}")
            
            # Use requests for asset downloads (faster than browser)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            headers.update(self.auth_headers)
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Save the file
            file_path = os.path.join(assets_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(response.content)
                
            self.log_message(f"Saved asset: {filename}")
            return True
            
        except Exception as e:
            self.log_message(f"Failed to download asset {url}: {str(e)}")
            return False
            
    def download_page_assets(self, soup, current_url, output_dir):
        """Download all assets (CSS, JS, images, etc.) for a page."""
        assets_dir = os.path.join(output_dir, 'assets')
        os.makedirs(assets_dir, exist_ok=True)
        
        asset_counter = len(self.downloaded_files)
        
        # Download CSS files
        css_links = soup.find_all('link', rel='stylesheet')
        for i, link in enumerate(css_links):
            href = link.get('href')
            if href:
                absolute_url = urllib.parse.urljoin(current_url, href)
                filename = f'style_{asset_counter}_{i}.css'
                if self.download_asset(absolute_url, assets_dir, filename):
                    # Update the link to point to local file
                    current_local_path = self.url_to_local_path(current_url)
                    current_dir = os.path.dirname(current_local_path)
                    if current_dir:
                        rel_path = os.path.relpath(f'assets/{filename}', current_dir)
                        link['href'] = rel_path.replace('\\', '/')
                    else:
                        link['href'] = f'assets/{filename}'
        
        # Download JavaScript files
        script_tags = soup.find_all('script', src=True)
        for i, script in enumerate(script_tags):
            src = script.get('src')
            if src:
                absolute_url = urllib.parse.urljoin(current_url, src)
                filename = f'script_{asset_counter}_{i}.js'
                if self.download_asset(absolute_url, assets_dir, filename):
                    # Update the src to point to local file
                    current_local_path = self.url_to_local_path(current_url)
                    current_dir = os.path.dirname(current_local_path)
                    if current_dir:
                        rel_path = os.path.relpath(f'assets/{filename}', current_dir)
                        script['src'] = rel_path.replace('\\', '/')
                    else:
                        script['src'] = f'assets/{filename}'
        
        # Download images
        img_tags = soup.find_all('img', src=True)
        for i, img in enumerate(img_tags):
            src = img.get('src')
            if src:
                absolute_url = urllib.parse.urljoin(current_url, src)
                # Get file extension from URL
                parsed_src = urllib.parse.urlparse(absolute_url)
                path = parsed_src.path
                ext = os.path.splitext(path)[1] or '.jpg'
                filename = f'image_{asset_counter}_{i}{ext}'
                
                if self.download_asset(absolute_url, assets_dir, filename):
                    # Update the src to point to local file
                    current_local_path = self.url_to_local_path(current_url)
                    current_dir = os.path.dirname(current_local_path)
                    if current_dir:
                        rel_path = os.path.relpath(f'assets/{filename}', current_dir)
                        img['src'] = rel_path.replace('\\', '/')
                    else:
                        img['src'] = f'assets/{filename}'
        
        # Download other assets (fonts, icons, etc.)
        for tag in soup.find_all(['link', 'source']):
            href = tag.get('href')
            if href and tag.get('rel') not in ['stylesheet']:
                absolute_url = urllib.parse.urljoin(current_url, href)
                parsed_href = urllib.parse.urlparse(absolute_url)
                if parsed_href.path:
                    ext = os.path.splitext(parsed_href.path)[1]
                    if ext in ['.woff', '.woff2', '.ttf', '.eot', '.ico', '.svg']:
                        filename = f'asset_{asset_counter}_{len(self.downloaded_files)}{ext}'
                        if self.download_asset(absolute_url, assets_dir, filename):
                            current_local_path = self.url_to_local_path(current_url)
                            current_dir = os.path.dirname(current_local_path)
                            if current_dir:
                                rel_path = os.path.relpath(f'assets/{filename}', current_dir)
                                tag['href'] = rel_path.replace('\\', '/')
                            else:
                                tag['href'] = f'assets/{filename}'
                                
    def rewrite_links(self, soup, current_url, output_dir):
        """Rewrite all links in the HTML to point to local files."""
        # Handle regular links (a href)
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urllib.parse.urljoin(current_url, href)
            
            if self.is_same_domain(absolute_url):
                # Convert to local path
                local_path = self.url_to_local_path(absolute_url)
                # Calculate relative path from current page
                current_local_path = self.url_to_local_path(current_url)
                current_dir = os.path.dirname(current_local_path)
                
                if current_dir:
                    # Calculate relative path
                    rel_path = os.path.relpath(local_path, current_dir)
                    link['href'] = rel_path.replace('\\', '/')  # Ensure forward slashes
                else:
                    link['href'] = local_path
                    
        # Handle form actions
        for form in soup.find_all('form', action=True):
            action = form['action']
            if action and not action.startswith(('http://', 'https://', 'mailto:', 'tel:')):
                absolute_url = urllib.parse.urljoin(current_url, action)
                if self.is_same_domain(absolute_url):
                    local_path = self.url_to_local_path(absolute_url)
                    current_local_path = self.url_to_local_path(current_url)
                    current_dir = os.path.dirname(current_local_path)
                    
                    if current_dir:
                        rel_path = os.path.relpath(local_path, current_dir)
                        form['action'] = rel_path.replace('\\', '/')
                    else:
                        form['action'] = local_path
                        
    def clone_website(self, url, output_dir):
        """Clone entire website with JavaScript execution and authentication support."""
        try:
            self.log_message(f"Starting enhanced website clone with browser: {url}")
            self.log_message(f"Max depth: {self.max_depth}, Max pages: {self.max_pages}, Delay: {self.delay}s")
            
            # Set up base URLs
            self.base_url = url
            parsed_url = urllib.parse.urlparse(url)
            self.base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Initialize browser
            if not self.setup_browser():
                return False
                
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            try:
                # Add custom cookies if provided
                self.driver.get(self.base_url)
                self.add_custom_cookies()
                
                # Perform login if credentials provided
                if self.auth_username and self.auth_password:
                    if not self.perform_login():
                        self.log_message("Login failed, continuing without authentication")
                
                # Initialize crawling queue
                normalized_start_url = self.normalize_url(url)
                self.url_queue.append((normalized_start_url, 0))  # (url, depth)
                
                pages_downloaded = 0
                
                self.log_message(f"Crawling up to {self.max_pages} pages with max depth {self.max_depth}")
                
                while self.url_queue and pages_downloaded < self.max_pages:
                    current_url, depth = self.url_queue.popleft()
                    
                    # Skip if already downloaded
                    if current_url in self.downloaded_pages:
                        continue
                        
                    # Skip if depth exceeded
                    if depth > self.max_depth:
                        continue
                        
                    try:
                        self.log_message(f"Downloading page {pages_downloaded + 1}/{self.max_pages}: {current_url} (depth: {depth})")
                        
                        # Get the page with JavaScript execution
                        html = self.get_page_with_js(current_url)
                        if not html:
                            continue
                            
                        # Parse HTML
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Download assets for this page
                        self.download_page_assets(soup, current_url, output_dir)
                        
                        # Extract internal links for further crawling
                        if depth < self.max_depth:
                            internal_links = self.extract_internal_links(soup, current_url)
                            for link in internal_links:
                                if link not in self.downloaded_pages:
                                    self.url_queue.append((link, depth + 1))
                        
                        # Rewrite links to work offline
                        self.rewrite_links(soup, current_url, output_dir)
                        
                        # Save the modified HTML
                        local_path = self.url_to_local_path(current_url)
                        full_path = self.create_local_directories(output_dir, local_path)
                        
                        with open(full_path, 'w', encoding='utf-8') as f:
                            f.write(str(soup))
                        
                        self.downloaded_pages.add(current_url)
                        pages_downloaded += 1
                        
                        self.log_message(f"Saved: {local_path}")
                        
                        # Be respectful - add delay between requests
                        if self.delay > 0:
                            time.sleep(self.delay)
                            
                    except Exception as e:
                        self.log_message(f"Failed to download page {current_url}: {str(e)}")
                        continue
                
                self.log_message(f"Enhanced website crawling completed!")
                self.log_message(f"Downloaded {pages_downloaded} pages and {len(self.downloaded_files)} assets")
                self.log_message(f"Files saved to: {output_dir}")
                self.log_message(f"Open {os.path.join(output_dir, 'index.html')} in your browser to view the offline site")
                
                return True
                
            finally:
                self.cleanup_browser()
                
        except Exception as e:
            self.log_message(f"Unexpected error: {str(e)}")
            self.cleanup_browser()
            return False


def main():
    parser = argparse.ArgumentParser(description='Enhanced website cloner with JavaScript execution and authentication')
    parser.add_argument('url', help='URL of the website to clone')
    parser.add_argument('-o', '--output', default='./cloned_website', 
                       help='Output directory (default: ./cloned_website)')
    parser.add_argument('-d', '--depth', type=int, default=3,
                       help='Maximum crawling depth (default: 3)')
    parser.add_argument('-p', '--pages', type=int, default=100,
                       help='Maximum number of pages to download (default: 100)')
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay between requests in seconds (default: 1.0)')
    parser.add_argument('--wait-time', type=float, default=5.0,
                       help='Wait time for JavaScript execution (default: 5.0)')
    parser.add_argument('--no-headless', action='store_true',
                       help='Run browser in non-headless mode (visible)')
    parser.add_argument('--browser', choices=['auto', 'chrome', 'firefox', 'edge', 'safari'], 
                       default='auto', help='Browser to use (default: auto-detect)')
    
    # Authentication options
    auth_group = parser.add_argument_group('authentication')
    auth_group.add_argument('--username', help='Username for login authentication')
    auth_group.add_argument('--password', help='Password for login authentication')
    auth_group.add_argument('--login-url', help='URL of login page (if different from main URL)')
    auth_group.add_argument('--username-field', default='username', help='Name of username form field')
    auth_group.add_argument('--password-field', default='password', help='Name of password form field')
    auth_group.add_argument('--cookies', help='JSON string of cookies for authentication')
    auth_group.add_argument('--headers', help='JSON string of custom headers')
    
    args = parser.parse_args()
    
    url = args.url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    output_dir = args.output.strip()
    
    print(f"Enhanced Website Cloner with Browser Support")
    print(f"URL: {url}")
    print(f"Output: {output_dir}")
    print(f"Max Depth: {args.depth}")
    print(f"Max Pages: {args.pages}")
    print(f"Request Delay: {args.delay}s")
    print(f"JS Wait Time: {args.wait_time}s")
    print(f"Headless: {not args.no_headless}")
    if args.username:
        print(f"Authentication: Enabled (Username: {args.username})")
    print("-" * 60)
    
    cloner = BrowserWebsiteCloner(
        max_depth=args.depth, 
        max_pages=args.pages, 
        delay=args.delay,
        headless=not args.no_headless,
        wait_time=args.wait_time,
        browser=args.browser
    )
    
    # Set up authentication if provided
    if args.username and args.password:
        cloner.set_authentication(
            username=args.username,
            password=args.password,
            login_url=args.login_url,
            username_field=args.username_field,
            password_field=args.password_field
        )
    
    # Set custom cookies if provided
    if args.cookies:
        try:
            cookies = json.loads(args.cookies)
            cloner.set_cookies(cookies)
            print(f"Loaded {len(cookies)} custom cookies")
        except Exception as e:
            print(f"Failed to parse cookies: {e}")
    
    # Set custom headers if provided
    if args.headers:
        try:
            headers = json.loads(args.headers)
            cloner.set_headers(headers)
            print(f"Loaded {len(headers)} custom headers")
        except Exception as e:
            print(f"Failed to parse headers: {e}")
    
    success = cloner.clone_website(url, output_dir)
    
    if success:
        print("\n✅ Enhanced website cloning completed successfully!")
        print(f"Open {os.path.join(output_dir, 'index.html')} in your browser")
        sys.exit(0)
    else:
        print("\n❌ Enhanced website cloning failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
