#!/usr/bin/env python3
"""
Command-line version of the website cloner.
"""

import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
import argparse
import sys
from pathlib import Path


class WebsiteCloner:
    def __init__(self):
        self.downloaded_files = set()
        
    def log_message(self, message):
        print(f"[INFO] {message}")
        
    def download_asset(self, url, base_domain, assets_dir, filename):
        try:
            # Make URL absolute
            if url.startswith('//'):
                url = 'https:' + url
            elif url.startswith('/'):
                url = base_domain + url
            elif not url.startswith(('http://', 'https://')):
                url = base_domain + '/' + url
                
            # Skip if already downloaded
            if url in self.downloaded_files:
                return True
                
            self.downloaded_files.add(url)
            
            self.log_message(f"Downloading: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Save the file
            file_path = os.path.join(assets_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(response.content)
                
            self.log_message(f"Saved: {filename}")
            return True
            
        except Exception as e:
            self.log_message(f"Failed to download {url}: {str(e)}")
            return False
            
    def clone_website(self, url, output_dir):
        try:
            self.log_message(f"Starting to clone: {url}")
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Parse the base URL
            parsed_url = urllib.parse.urlparse(url)
            base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Download the main page
            self.log_message("Downloading main page...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Create assets directory
            assets_dir = os.path.join(output_dir, 'assets')
            os.makedirs(assets_dir, exist_ok=True)
            
            # Download CSS files
            self.log_message("Downloading CSS files...")
            css_links = soup.find_all('link', rel='stylesheet')
            for i, link in enumerate(css_links):
                href = link.get('href')
                if href:
                    if self.download_asset(href, base_domain, assets_dir, f'style_{i}.css'):
                        # Update the link to point to local file
                        link['href'] = f'assets/style_{i}.css'
            
            # Download JavaScript files
            self.log_message("Downloading JavaScript files...")
            script_tags = soup.find_all('script', src=True)
            for i, script in enumerate(script_tags):
                src = script.get('src')
                if src:
                    if self.download_asset(src, base_domain, assets_dir, f'script_{i}.js'):
                        # Update the src to point to local file
                        script['src'] = f'assets/script_{i}.js'
            
            # Download images
            self.log_message("Downloading images...")
            img_tags = soup.find_all('img', src=True)
            for i, img in enumerate(img_tags):
                src = img.get('src')
                if src:
                    # Get file extension from URL
                    parsed_src = urllib.parse.urlparse(src)
                    path = parsed_src.path
                    ext = os.path.splitext(path)[1] or '.jpg'
                    filename = f'image_{i}{ext}'
                    
                    if self.download_asset(src, base_domain, assets_dir, filename):
                        # Update the src to point to local file
                        img['src'] = f'assets/{filename}'
            
            # Download other assets (fonts, etc.)
            self.log_message("Downloading other assets...")
            
            # Handle other linked resources
            for tag in soup.find_all(['link', 'source']):
                href = tag.get('href')
                if href and tag.get('rel') not in ['stylesheet']:
                    parsed_href = urllib.parse.urlparse(href)
                    if parsed_href.path:
                        ext = os.path.splitext(parsed_href.path)[1]
                        if ext in ['.woff', '.woff2', '.ttf', '.eot', '.ico']:
                            filename = f'asset_{len(self.downloaded_files)}{ext}'
                            if self.download_asset(href, base_domain, assets_dir, filename):
                                tag['href'] = f'assets/{filename}'
            
            # Save the modified HTML
            self.log_message("Saving HTML file...")
            
            html_file = os.path.join(output_dir, 'index.html')
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            
            self.log_message(f"Website cloned successfully to: {output_dir}")
            self.log_message(f"Open {html_file} in your browser to view the offline site")
            
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Network error: {str(e)}")
            return False
            
        except Exception as e:
            print(f"[ERROR] Unexpected error: {str(e)}")
            return False


def main():
    parser = argparse.ArgumentParser(description='Clone a website for offline viewing')
    parser.add_argument('url', help='URL of the website to clone')
    parser.add_argument('-o', '--output', default='./cloned_website', 
                       help='Output directory (default: ./cloned_website)')
    
    args = parser.parse_args()
    
    url = args.url.strip()
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    output_dir = args.output.strip()
    
    print(f"Website Cloner")
    print(f"URL: {url}")
    print(f"Output: {output_dir}")
    print("-" * 50)
    
    cloner = WebsiteCloner()
    success = cloner.clone_website(url, output_dir)
    
    if success:
        print("\n✅ Cloning completed successfully!")
        print(f"Open {os.path.join(output_dir, 'index.html')} in your browser")
        sys.exit(0)
    else:
        print("\n❌ Cloning failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
