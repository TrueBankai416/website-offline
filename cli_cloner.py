#!/usr/bin/env python3
"""
Command-line version of the website cloner with full site crawling.
"""

import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
import argparse
import sys
from pathlib import Path
from collections import deque
import re
import time


class WebsiteCloner:
    def __init__(self, max_depth=3, max_pages=100, delay=1.0):
        self.downloaded_files = set()
        self.downloaded_pages = set()
        self.url_queue = deque()
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.delay = delay
        self.base_domain = None
        self.base_url = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def log_message(self, message):
        print(f"[INFO] {message}")
        
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
        
    def download_asset(self, url, assets_dir, filename):
        """Download and save an asset file."""
        try:
            # Skip if already downloaded
            if url in self.downloaded_files:
                return True
                
            self.downloaded_files.add(url)
            
            self.log_message(f"Downloading asset: {url}")
            
            response = self.session.get(url, timeout=10)
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
    
    def clone_website(self, url, output_dir):
        try:
            self.log_message(f"Starting full website clone: {url}")
            
            # Set up base URLs
            self.base_url = url
            parsed_url = urllib.parse.urlparse(url)
            self.base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
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
                    
                    # Download the page
                    response = self.session.get(current_url, timeout=30)
                    response.raise_for_status()
                    
                    # Parse HTML
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
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
            
            self.log_message(f"Website crawling completed!")
            self.log_message(f"Downloaded {pages_downloaded} pages and {len(self.downloaded_files)} assets")
            self.log_message(f"Files saved to: {output_dir}")
            self.log_message(f"Open {os.path.join(output_dir, 'index.html')} in your browser to view the offline site")
            
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Network error: {str(e)}")
            return False
            
        except Exception as e:
            print(f"[ERROR] Unexpected error: {str(e)}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Clone an entire website for offline viewing')
    parser.add_argument('url', help='URL of the website to clone')
    parser.add_argument('-o', '--output', default='./cloned_website', 
                       help='Output directory (default: ./cloned_website)')
    parser.add_argument('-d', '--depth', type=int, default=3,
                       help='Maximum crawling depth (default: 3)')
    parser.add_argument('-p', '--pages', type=int, default=100,
                       help='Maximum number of pages to download (default: 100)')
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay between requests in seconds (default: 1.0)')
    
    args = parser.parse_args()
    
    url = args.url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    output_dir = args.output.strip()
    
    print(f"Full Website Cloner")
    print(f"URL: {url}")
    print(f"Output: {output_dir}")
    print(f"Max Depth: {args.depth}")
    print(f"Max Pages: {args.pages}")
    print(f"Request Delay: {args.delay}s")
    print("-" * 50)
    
    cloner = WebsiteCloner(max_depth=args.depth, max_pages=args.pages, delay=args.delay)
    success = cloner.clone_website(url, output_dir)
    
    if success:
        print("\n✅ Website cloning completed successfully!")
        print(f"Open {os.path.join(output_dir, 'index.html')} in your browser")
        sys.exit(0)
    else:
        print("\n❌ Website cloning failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
