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


app = Flask(__name__)

# Store cloning jobs
cloning_jobs = {}


class WebsiteCloner:
    def __init__(self, job_id):
        self.job_id = job_id
        self.downloaded_files = set()
        self.status = "initializing"
        self.progress = 0
        self.logs = []
        
    def log_message(self, message):
        timestamp = time.strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        print(log_entry)
        
    def update_status(self, status, progress=None):
        self.status = status
        if progress is not None:
            self.progress = progress
            
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
            self.update_status("starting", 5)
            self.log_message(f"Starting to clone: {url}")
            
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)
            
            # Parse the base URL
            parsed_url = urllib.parse.urlparse(url)
            base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Download the main page
            self.update_status("downloading_main", 10)
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
            self.update_status("downloading_css", 25)
            self.log_message("Downloading CSS files...")
            css_links = soup.find_all('link', rel='stylesheet')
            for i, link in enumerate(css_links):
                href = link.get('href')
                if href:
                    if self.download_asset(href, base_domain, assets_dir, f'style_{i}.css'):
                        link['href'] = f'assets/style_{i}.css'
            
            # Download JavaScript files
            self.update_status("downloading_js", 50)
            self.log_message("Downloading JavaScript files...")
            script_tags = soup.find_all('script', src=True)
            for i, script in enumerate(script_tags):
                src = script.get('src')
                if src:
                    if self.download_asset(src, base_domain, assets_dir, f'script_{i}.js'):
                        script['src'] = f'assets/script_{i}.js'
            
            # Download images
            self.update_status("downloading_images", 75)
            self.log_message("Downloading images...")
            img_tags = soup.find_all('img', src=True)
            for i, img in enumerate(img_tags):
                src = img.get('src')
                if src:
                    parsed_src = urllib.parse.urlparse(src)
                    path = parsed_src.path
                    ext = os.path.splitext(path)[1] or '.jpg'
                    filename = f'image_{i}{ext}'
                    
                    if self.download_asset(src, base_domain, assets_dir, filename):
                        img['src'] = f'assets/{filename}'
            
            # Download other assets
            self.update_status("downloading_assets", 90)
            self.log_message("Downloading other assets...")
            
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
            self.update_status("saving", 95)
            self.log_message("Saving HTML file...")
            
            html_file = os.path.join(output_dir, 'index.html')
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(str(soup))
            
            self.update_status("completed", 100)
            self.log_message(f"Website cloned successfully to: {output_dir}")
            self.log_message(f"Open {html_file} in your browser to view the offline site")
            
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
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
        
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Create cloner instance
    cloner = WebsiteCloner(job_id)
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
    <title>Website Offline Cloner</title>
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
    <h1>Website Offline Cloner</h1>
    
    <div class="container">
        <h3>Clone Website</h3>
        <input type="text" id="url" placeholder="Enter website URL (e.g., example.com)" />
        <input type="text" id="outputDir" value="./cloned_website" placeholder="Output directory" />
        <button onclick="startCloning()" id="cloneBtn">Clone Website</button>
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
                body: JSON.stringify({ url: url, output_dir: outputDir })
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
