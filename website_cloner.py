import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
import threading
import time
from pathlib import Path
import mimetypes
from collections import deque


class WebsiteCloner:
    def __init__(self, root):
        self.root = root
        self.root.title("Full Website Offline Cloner")
        self.root.geometry("900x700")
        
        # Variables
        self.url_var = tk.StringVar()
        self.output_dir_var = tk.StringVar(value="./cloned_website")
        self.progress_var = tk.StringVar(value="Ready to clone entire website")
        self.is_cloning = False
        
        # Crawling variables
        self.max_depth_var = tk.IntVar(value=3)
        self.max_pages_var = tk.IntVar(value=100)
        self.delay_var = tk.DoubleVar(value=1.0)
        
        # Internal crawling state
        self.downloaded_files = set()
        self.downloaded_pages = set()
        self.url_queue = deque()
        self.base_domain = None
        self.base_url = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # URL input
        ttk.Label(main_frame, text="Website URL:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        url_frame = ttk.Frame(main_frame)
        url_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Entry(url_frame, textvariable=self.url_var, width=60).grid(row=0, column=0, sticky=(tk.W, tk.E))
        url_frame.columnconfigure(0, weight=1)
        
        # Output directory
        ttk.Label(main_frame, text="Output Directory:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Entry(dir_frame, textvariable=self.output_dir_var, width=50).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(dir_frame, text="Browse", command=self.browse_directory).grid(row=0, column=1, padx=(5, 0))
        dir_frame.columnconfigure(0, weight=1)
        
        # Crawling options frame
        options_frame = ttk.LabelFrame(main_frame, text="Crawling Options", padding="10")
        options_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Max depth
        ttk.Label(options_frame, text="Max Depth:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        depth_spin = ttk.Spinbox(options_frame, from_=1, to=10, width=10, textvariable=self.max_depth_var)
        depth_spin.grid(row=0, column=1, padx=(0, 20))
        
        # Max pages
        ttk.Label(options_frame, text="Max Pages:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        pages_spin = ttk.Spinbox(options_frame, from_=1, to=1000, width=10, textvariable=self.max_pages_var)
        pages_spin.grid(row=0, column=3, padx=(0, 20))
        
        # Delay
        ttk.Label(options_frame, text="Delay (s):").grid(row=0, column=4, sticky=tk.W, padx=(0, 10))
        delay_spin = ttk.Spinbox(options_frame, from_=0.1, to=10.0, increment=0.1, width=10, textvariable=self.delay_var)
        delay_spin.grid(row=0, column=5)
        
        # Clone button
        self.clone_button = ttk.Button(main_frame, text="Clone Entire Website", command=self.start_cloning)
        self.clone_button.grid(row=5, column=0, pady=(0, 10))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Status label
        ttk.Label(main_frame, textvariable=self.progress_var).grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Log output
        ttk.Label(main_frame, text="Log:").grid(row=8, column=0, sticky=tk.W, pady=(0, 5))
        self.log_text = scrolledtext.ScrolledText(main_frame, height=12, width=90)
        self.log_text.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.rowconfigure(9, weight=1)
        
    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir_var.set(directory)
            
    def log_message(self, message):
        self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
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
        
    def start_cloning(self):
        if self.is_cloning:
            return
            
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
            
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            self.url_var.set(url)
            
        output_dir = self.output_dir_var.get().strip()
        if not output_dir:
            messagebox.showerror("Error", "Please specify an output directory")
            return
            
        # Reset crawling state
        self.downloaded_files.clear()
        self.downloaded_pages.clear()
        self.url_queue.clear()
            
        self.is_cloning = True
        self.clone_button.config(state='disabled')
        self.progress_bar.start()
        self.log_text.delete(1.0, tk.END)
        
        # Start cloning in a separate thread
        max_depth = self.max_depth_var.get()
        max_pages = self.max_pages_var.get()
        delay = self.delay_var.get()
        
        thread = threading.Thread(target=self.clone_website, args=(url, output_dir, max_depth, max_pages, delay))
        thread.daemon = True
        thread.start()
        
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

    def clone_website(self, url, output_dir, max_depth=3, max_pages=100, delay=1.0):
        try:
            self.progress_var.set("Starting full website clone...")
            self.log_message(f"Starting full website clone: {url}")
            self.log_message(f"Max depth: {max_depth}, Max pages: {max_pages}, Delay: {delay}s")
            
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
            
            self.log_message(f"Crawling up to {max_pages} pages with max depth {max_depth}")
            
            while self.url_queue and pages_downloaded < max_pages:
                current_url, depth = self.url_queue.popleft()
                
                # Skip if already downloaded
                if current_url in self.downloaded_pages:
                    continue
                    
                # Skip if depth exceeded
                if depth > max_depth:
                    continue
                    
                try:
                    self.progress_var.set(f"Downloading page {pages_downloaded + 1}/{max_pages} (depth: {depth})")
                    self.log_message(f"Downloading page {pages_downloaded + 1}/{max_pages}: {current_url} (depth: {depth})")
                    
                    # Download the page
                    response = self.session.get(current_url, timeout=30)
                    response.raise_for_status()
                    
                    # Parse HTML
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Download assets for this page
                    self.download_page_assets(soup, current_url, output_dir)
                    
                    # Extract internal links for further crawling
                    if depth < max_depth:
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
                    if delay > 0:
                        time.sleep(delay)
                        
                except Exception as e:
                    self.log_message(f"Failed to download page {current_url}: {str(e)}")
                    continue
            
            self.progress_var.set("Website crawling completed!")
            self.log_message(f"Website crawling completed!")
            self.log_message(f"Downloaded {pages_downloaded} pages and {len(self.downloaded_files)} assets")
            self.log_message(f"Files saved to: {output_dir}")
            self.log_message(f"Open {os.path.join(output_dir, 'index.html')} in your browser to view the offline site")
            
            messagebox.showinfo("Success", f"Website crawling completed!\nDownloaded {pages_downloaded} pages and {len(self.downloaded_files)} assets\nSaved to: {output_dir}")
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error: {str(e)}"
            self.progress_var.set("Error occurred during cloning")
            self.log_message(error_msg)
            messagebox.showerror("Error", error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.progress_var.set("Error occurred during cloning")
            self.log_message(error_msg)
            messagebox.showerror("Error", error_msg)
            
        finally:
            self.is_cloning = False
            self.clone_button.config(state='normal')
            self.progress_bar.stop()
            
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


def main():
    root = tk.Tk()
    app = WebsiteCloner(root)
    root.mainloop()


if __name__ == "__main__":
    main()
