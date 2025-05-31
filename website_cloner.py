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


class WebsiteCloner:
    def __init__(self, root):
        self.root = root
        self.root.title("Website Offline Cloner")
        self.root.geometry("800x600")
        
        # Variables
        self.url_var = tk.StringVar()
        self.output_dir_var = tk.StringVar(value="./cloned_website")
        self.progress_var = tk.StringVar(value="Ready to clone website")
        self.is_cloning = False
        
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
        
        # Clone button
        self.clone_button = ttk.Button(main_frame, text="Clone Website", command=self.start_cloning)
        self.clone_button.grid(row=4, column=0, pady=(0, 10))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Status label
        ttk.Label(main_frame, textvariable=self.progress_var).grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Log output
        ttk.Label(main_frame, text="Log:").grid(row=7, column=0, sticky=tk.W, pady=(0, 5))
        self.log_text = scrolledtext.ScrolledText(main_frame, height=15, width=80)
        self.log_text.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.rowconfigure(8, weight=1)
        
    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir_var.set(directory)
            
    def log_message(self, message):
        self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
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
            
        self.is_cloning = True
        self.clone_button.config(state='disabled')
        self.progress_bar.start()
        self.log_text.delete(1.0, tk.END)
        
        # Start cloning in a separate thread
        thread = threading.Thread(target=self.clone_website, args=(url, output_dir))
        thread.daemon = True
        thread.start()
        
    def clone_website(self, url, output_dir):
        try:
            self.progress_var.set("Starting website clone...")
            self.log_message(f"Starting to clone: {url}")
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Parse the base URL
            parsed_url = urllib.parse.urlparse(url)
            base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Download the main page
            self.progress_var.set("Downloading main page...")
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
            
            # Track downloaded files to avoid duplicates
            downloaded_files = set()
            
            # Download CSS files
            self.progress_var.set("Downloading CSS files...")
            self.log_message("Downloading CSS files...")
            css_links = soup.find_all('link', rel='stylesheet')
            for i, link in enumerate(css_links):
                href = link.get('href')
                if href:
                    self.download_asset(href, base_domain, assets_dir, downloaded_files, f'style_{i}.css')
                    # Update the link to point to local file
                    link['href'] = f'assets/style_{i}.css'
            
            # Download JavaScript files
            self.progress_var.set("Downloading JavaScript files...")
            self.log_message("Downloading JavaScript files...")
            script_tags = soup.find_all('script', src=True)
            for i, script in enumerate(script_tags):
                src = script.get('src')
                if src:
                    self.download_asset(src, base_domain, assets_dir, downloaded_files, f'script_{i}.js')
                    # Update the src to point to local file
                    script['src'] = f'assets/script_{i}.js'
            
            # Download images
            self.progress_var.set("Downloading images...")
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
                    
                    self.download_asset(src, base_domain, assets_dir, downloaded_files, filename)
                    # Update the src to point to local file
                    img['src'] = f'assets/{filename}'
            
            # Download other assets (fonts, etc.)
            self.progress_var.set("Downloading other assets...")
            self.log_message("Downloading other assets...")
            
            # Handle @import in CSS and other linked resources
            for tag in soup.find_all(['link', 'source']):
                href = tag.get('href')
                if href and tag.get('rel') not in ['stylesheet']:
                    parsed_href = urllib.parse.urlparse(href)
                    if parsed_href.path:
                        ext = os.path.splitext(parsed_href.path)[1]
                        if ext in ['.woff', '.woff2', '.ttf', '.eot', '.ico']:
                            filename = f'asset_{len(downloaded_files)}{ext}'
                            self.download_asset(href, base_domain, assets_dir, downloaded_files, filename)
                            tag['href'] = f'assets/{filename}'
            
            # Save the modified HTML
            self.progress_var.set("Saving HTML file...")
            self.log_message("Saving modified HTML file...")
            
            html_file = os.path.join(output_dir, 'index.html')
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            
            self.progress_var.set("Clone completed successfully!")
            self.log_message(f"Website cloned successfully to: {output_dir}")
            self.log_message(f"Open {html_file} in your browser to view the offline site")
            
            messagebox.showinfo("Success", f"Website cloned successfully!\nSaved to: {output_dir}")
            
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
            
    def download_asset(self, url, base_domain, assets_dir, downloaded_files, filename):
        try:
            # Make URL absolute
            if url.startswith('//'):
                url = 'https:' + url
            elif url.startswith('/'):
                url = base_domain + url
            elif not url.startswith(('http://', 'https://')):
                url = base_domain + '/' + url
                
            # Skip if already downloaded
            if url in downloaded_files:
                return
                
            downloaded_files.add(url)
            
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
            
        except Exception as e:
            self.log_message(f"Failed to download {url}: {str(e)}")


def main():
    root = tk.Tk()
    app = WebsiteCloner(root)
    root.mainloop()


if __name__ == "__main__":
    main()
