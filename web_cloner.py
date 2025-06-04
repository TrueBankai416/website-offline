#!/usr/bin/env python3
"""
Web-based interface for the website cloner using Flask.
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
import threading
import time
import json
from pathlib import Path
import uuid
from collections import deque


app = Flask(__name__)

# Store cloning jobs
cloning_jobs = {}


class WebsiteCloner:
    def __init__(self, job_id, max_depth=3, max_pages=100, delay=1.0):
        self.job_id = job_id
        self.downloaded_files = set()
        self.downloaded_pages = set()
        self.url_queue = deque()
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.delay = delay
        self.base_domain = None
        self.base_url = None
        self.status = "initializing"
        self.progress = 0
        self.logs = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def log_message(self, message):
        timestamp = time.strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        print(log_entry)
        
    def update_status(self, status, progress=None):
        self.status = status
        if progress is not None:
            self.progress = progress
            
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
            
    def clone_website(self, url, output_dir):
        try:
            self.update_status("starting", 5)
            self.log_message(f"Starting full website clone: {url}")
            self.log_message(f"Max depth: {self.max_depth}, Max pages: {self.max_pages}, Delay: {self.delay}s")
            
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
                    progress = min(95, int((pages_downloaded / self.max_pages) * 95))
                    self.update_status(f"downloading_page_{pages_downloaded + 1}", progress)
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
            
            self.update_status("completed", 100)
            self.log_message(f"Website crawling completed!")
            self.log_message(f"Downloaded {pages_downloaded} pages and {len(self.downloaded_files)} assets")
            self.log_message(f"Files saved to: {output_dir}")
            self.log_message(f"Open {os.path.join(output_dir, 'index.html')} in your browser to view the offline site")
            
        except Exception as e:
            self.update_status("error", 0)
            self.log_message(f"Error: {str(e)}")


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/clone', methods=['POST'])
def clone_website():
    data = request.get_json()
    url = data.get('url', '').strip()
    output_dir = data.get('output_dir', './cloned_website').strip()
    max_depth = data.get('max_depth', 3)
    max_pages = data.get('max_pages', 100)
    delay = data.get('delay', 1.0)
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
        
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Create cloner instance with crawling parameters
    cloner = WebsiteCloner(job_id, max_depth=max_depth, max_pages=max_pages, delay=delay)
    cloning_jobs[job_id] = cloner
    
    # Start cloning in background thread
    thread = threading.Thread(target=cloner.clone_website, args=(url, output_dir))
    thread.daemon = True
    thread.start()
    
    return jsonify({'job_id': job_id})


@app.route('/status/<job_id>')
def get_status(job_id):
    if job_id not in cloning_jobs:
        return jsonify({'error': 'Job not found'}), 404
        
    cloner = cloning_jobs[job_id]
    return jsonify({
        'status': cloner.status,
        'progress': cloner.progress,
        'logs': cloner.logs[-10:]  # Return last 10 log entries
    })


@app.route('/logs/<job_id>')
def get_logs(job_id):
    if job_id not in cloning_jobs:
        return jsonify({'error': 'Job not found'}), 404
        
    cloner = cloning_jobs[job_id]
    return jsonify({'logs': cloner.logs})


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create the HTML template
    html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Full Website Offline Cloner</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .container { background: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        input[type="text"] { width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 4px; }
        button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #005a87; }
        button:disabled { background: #ccc; cursor: not-allowed; }
        .progress-bar { width: 100%; background: #ddd; border-radius: 4px; overflow: hidden; margin: 10px 0; }
        .progress-fill { height: 20px; background: #007cba; transition: width 0.3s; }
        .logs { background: #000; color: #0f0; padding: 10px; border-radius: 4px; height: 300px; overflow-y: auto; font-family: monospace; }
        .status { margin: 10px 0; font-weight: bold; }
    </style>
</head>
<body>
    <h1>Full Website Offline Cloner</h1>
    
    <div class="container">
        <h3>Clone Entire Website</h3>
        <input type="text" id="url" placeholder="Enter website URL (e.g., example.com)" />
        <input type="text" id="outputDir" value="./cloned_website" placeholder="Output directory" />
        <div style="margin: 15px 0; padding: 10px; background: #e8f4f8; border-radius: 4px;">
            <strong>Crawling Options:</strong><br>
            Max Depth: <input type="number" id="maxDepth" value="3" min="1" max="10" style="width: 60px;"> 
            Max Pages: <input type="number" id="maxPages" value="100" min="1" max="1000" style="width: 80px;">
            Delay (s): <input type="number" id="delay" value="1.0" min="0.1" max="10" step="0.1" style="width: 60px;">
        </div>
        <button onclick="startCloning()" id="cloneBtn">Clone Entire Website</button>
    </div>
    
    <div class="container" id="progressContainer" style="display: none;">
        <h3>Progress</h3>
        <div class="status" id="status">Ready</div>
        <div class="progress-bar">
            <div class="progress-fill" id="progressFill" style="width: 0%;"></div>
        </div>
        <div id="progressText">0%</div>
    </div>
    
    <div class="container" id="logsContainer" style="display: none;">
        <h3>Logs</h3>
        <div class="logs" id="logs"></div>
    </div>

    <script>
        let currentJobId = null;
        let statusInterval = null;
        
        function startCloning() {
            const url = document.getElementById('url').value.trim();
            const outputDir = document.getElementById('outputDir').value.trim();
            const maxDepth = parseInt(document.getElementById('maxDepth').value) || 3;
            const maxPages = parseInt(document.getElementById('maxPages').value) || 100;
            const delay = parseFloat(document.getElementById('delay').value) || 1.0;
            
            if (!url) {
                alert('Please enter a URL');
                return;
            }
            
            document.getElementById('cloneBtn').disabled = true;
            document.getElementById('progressContainer').style.display = 'block';
            document.getElementById('logsContainer').style.display = 'block';
            
            fetch('/clone', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    url: url, 
                    output_dir: outputDir,
                    max_depth: maxDepth,
                    max_pages: maxPages,
                    delay: delay
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Error: ' + data.error);
                    document.getElementById('cloneBtn').disabled = false;
                    return;
                }
                
                currentJobId = data.job_id;
                startStatusChecking();
            })
            .catch(error => {
                alert('Error: ' + error);
                document.getElementById('cloneBtn').disabled = false;
            });
        }
        
        function startStatusChecking() {
            statusInterval = setInterval(checkStatus, 1000);
        }
        
        function checkStatus() {
            if (!currentJobId) return;
            
            fetch(`/status/${currentJobId}`)
            .then(response => response.json())
            .then(data => {
                document.getElementById('status').textContent = data.status;
                document.getElementById('progressFill').style.width = data.progress + '%';
                document.getElementById('progressText').textContent = data.progress + '%';
                
                // Update logs
                const logsDiv = document.getElementById('logs');
                logsDiv.innerHTML = data.logs.join('\\n');
                logsDiv.scrollTop = logsDiv.scrollHeight;
                
                if (data.status === 'completed' || data.status === 'error') {
                    clearInterval(statusInterval);
                    document.getElementById('cloneBtn').disabled = false;
                    
                    if (data.status === 'completed') {
                        alert('Website cloned successfully!');
                    } else {
                        alert('Cloning failed. Check logs for details.');
                    }
                }
            });
        }
    </script>
</body>
</html>
    '''
    
    with open('templates/index.html', 'w') as f:
        f.write(html_template)
    
    print("Starting web server at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
