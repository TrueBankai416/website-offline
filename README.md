# Website Offline Cloner

A comprehensive Python application that creates complete offline clones of websites by recursively crawling and downloading all pages and assets. Available in multiple interface formats.

## Features

### 🔄 **Full Website Crawling**
- **Recursive crawling** of entire websites, not just single pages
- **Intelligent link following** within the same domain
- **Configurable crawling depth** and page limits
- **Maintains original site structure** with proper directory hierarchy
- **Smart link rewriting** to work offline

### 🎯 **Multiple Interface Options**
- **GUI Version**: Full tkinter-based graphical interface
- **CLI Version**: Command-line interface perfect for automation
- **Web Interface**: Browser-based Flask application

### 💾 **Comprehensive Asset Download**
- Downloads HTML, CSS, JavaScript, images, fonts, and icons
- Handles relative and absolute URLs automatically
- Creates proper local directory structure
- Updates all file references to point to local copies
- Real-time progress tracking and detailed logging

## Requirements

- Python 3.6 or higher
- Required packages (install with `pip install -r requirements.txt`):
  - requests
  - beautifulsoup4
  - lxml
  - flask (for web interface)

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd website-offline
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 🖥️ GUI Version (Primary Interface)
```bash
python3 website_cloner.py
```
- Full graphical interface with progress tracking
- URL input field and directory selection
- Real-time logging and progress bar
- One-click website cloning

### 💻 CLI Version (For Automation & Advanced Users)
```bash
# Basic usage
python3 cli_cloner.py example.com

# Advanced usage with custom settings
python3 cli_cloner.py https://example.com \
  --output my_website \
  --depth 5 \
  --pages 200 \
  --delay 1.0
```

**CLI Options:**
- `-o, --output`: Output directory (default: `./cloned_website`)
- `-d, --depth`: Maximum crawling depth (default: `3`)
- `-p, --pages`: Maximum number of pages to download (default: `100`)
- `--delay`: Delay between requests in seconds (default: `1.0`)

### 🌐 Web Interface (Browser-Based)
```bash
python3 web_cloner.py
# Then visit http://localhost:5000
```
- Browser-based interface using Flask
- Perfect for remote usage or when GUI isn't available
- Real-time progress updates via web interface

## How It Works

The enhanced cloner:

1. **Starts** with the specified URL as the entry point
2. **Downloads** the HTML page and parses it for internal links
3. **Crawls** through all discovered internal links up to the specified depth
4. **Downloads** all static assets (CSS, JS, images, fonts) for each page
5. **Rewrites** all internal links to work with the offline structure
6. **Maintains** the original directory structure of the website
7. **Saves** everything in a complete, browseable offline copy

## Advanced Features

### Crawling Controls
- **Depth Limiting**: Prevents infinite crawling loops
- **Page Limits**: Controls total download size
- **Domain Filtering**: Only crawls within the target domain
- **Rate Limiting**: Respects server resources with configurable delays

### Smart Link Handling
- **Relative Path Conversion**: All links work offline
- **Directory Structure**: Maintains original site hierarchy
- **Asset Organization**: Centralizes assets while preserving references

### Error Handling
- **Network Resilience**: Continues crawling despite individual page failures
- **Timeout Management**: Handles slow or unresponsive pages
- **Progress Reporting**: Detailed logging of successes and failures

## Examples

### Clone a small blog
```bash
python3 cli_cloner.py myblog.com --depth 3 --pages 50
```

### Clone a documentation site with high fidelity
```bash
python3 cli_cloner.py docs.example.com --depth 5 --pages 500 --delay 0.5
```

### Quick single-page clone
```bash
python3 cli_cloner.py landing-page.com --depth 1 --pages 1
```

## Limitations

- **Dynamic Content**: Does not execute JavaScript or handle content loaded dynamically
- **Authentication**: Cannot handle login-protected content
- **Forms**: Form submissions will not work offline
- **External Resources**: Only downloads resources from the same domain
- **Server Restrictions**: Some websites may block automated crawling

## Respectful Crawling

This tool includes built-in rate limiting and respects server resources:
- Default 1-second delay between requests
- Configurable delay settings
- Reasonable default limits on pages and depth
- Proper User-Agent headers

Always ensure you have permission to crawl the target website and respect robots.txt files.

## License

This project is open source and available under the MIT License.
