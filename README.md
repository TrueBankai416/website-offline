# Website Offline Cloner

A Python GUI application that allows you to create offline clones of websites by downloading the HTML and static assets (CSS, JavaScript, images, etc.).

## Features

- Simple and intuitive GUI built with tkinter
- Downloads HTML, CSS, JavaScript, and image files
- Creates a local directory structure for the cloned website
- Real-time logging of the cloning process
- Progress indication during download
- Handles relative and absolute URLs
- User-friendly error handling

## Requirements

- Python 3.6 or higher
- Required packages (install with `pip install -r requirements.txt`):
  - requests
  - beautifulsoup4
  - lxml

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

1. Run the application:
   ```bash
   python website_cloner.py
   ```

2. Enter the URL of the website you want to clone

3. Choose an output directory (or use the default `./cloned_website`)

4. Click "Clone Website" to start the process

5. Wait for the cloning to complete. You can monitor progress in the log area.

6. Once completed, open the `index.html` file in the output directory with your web browser to view the offline clone.

## How It Works

The application:

1. Downloads the main HTML page from the specified URL
2. Parses the HTML to find linked resources (CSS, JS, images)
3. Downloads all static assets and saves them in an `assets` folder
4. Modifies the HTML to point to the local copies of assets
5. Saves the modified HTML as `index.html`

## Limitations

- Only downloads resources directly linked in the main HTML page
- Does not handle dynamic content loaded via JavaScript
- Does not clone entire website structure (only the specified page)
- Some websites may block automated downloads
- Does not handle complex authentication or session-based content

## License

This project is open source and available under the MIT License.
