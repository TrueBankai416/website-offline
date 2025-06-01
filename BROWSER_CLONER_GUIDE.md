# Browser-Enhanced Website Cloner

## Overview

The **Browser-Enhanced Website Cloner** (`browser_cloner.py`) uses a headless Chrome browser to clone JavaScript-heavy websites and sites requiring authentication. This solves the limitations of static cloning for modern web applications.

## 🚀 **Key Features**

### **Multi-Browser Support**
- ✅ **Auto-detection** of available browsers
- ✅ **Chrome, Firefox, Edge, Safari** support
- ✅ **Smart fallback** system - uses best available browser
- ✅ **Manual browser selection** or automatic detection

### **JavaScript Execution**
- ✅ **Full JavaScript execution** using headless browsers
- ✅ **Dynamic content capture** (AJAX, XHR, SPAs)
- ✅ **Rendered DOM extraction** after all scripts run
- ✅ **Configurable wait times** for content loading

### **Authentication Support**
- ✅ **Username/Password login forms**
- ✅ **Custom cookies** for session authentication
- ✅ **Custom headers** (API keys, tokens)
- ✅ **Flexible login URL configuration**

### **Enhanced Crawling**
- ✅ **Complete website crawling** with JavaScript sites
- ✅ **Session persistence** across pages
- ✅ **Asset downloading** with authentication headers
- ✅ **Smart error handling** and retries

## 📋 **Installation**

### **Dependencies**
```bash
pip install -r requirements.txt
```

### **Chrome Browser**
The cloner requires Chrome browser:

**Ubuntu/Debian:**
```bash
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' | tee /etc/apt/sources.list.d/google-chrome.list
apt-get update
apt-get install -y google-chrome-stable
```

**MacOS:**
```bash
brew install --cask google-chrome
```

**Windows:**
Download and install from [chrome.google.com](https://chrome.google.com)

## 🎯 **Usage Examples**

### **GUI Version (Recommended)**
```bash
python3 browser_cloner_gui.py
```
- **Complete graphical interface** with all options
- **Browser auto-detection** dropdown
- **Authentication forms** for username/password, cookies, headers
- **Real-time progress** and logging
- **All crawling options** in easy-to-use interface

### **Basic JavaScript-Heavy Site**
```bash
python3 browser_cloner.py https://spa-example.com \
  --output ./cloned_spa \
  --depth 3 \
  --pages 50 \
  --wait-time 5.0
```

### **Auto-Detect Browser**
```bash
python3 browser_cloner.py https://site.com \
  --browser auto \
  --depth 3 \
  --pages 100
```

### **Force Specific Browser**
```bash
python3 browser_cloner.py https://site.com \
  --browser firefox \
  --depth 3 \
  --pages 100
```

### **Login-Protected Site**
```bash
python3 browser_cloner.py https://protected-site.com \
  --username "your_username" \
  --password "your_password" \
  --login-url "https://protected-site.com/login" \
  --output ./protected_clone
```

### **API Key Authentication**
```bash
python3 browser_cloner.py https://api-site.com \
  --headers '{"Authorization": "Bearer your_api_key"}' \
  --output ./api_clone
```

### **Cookie-Based Authentication**
```bash
python3 browser_cloner.py https://cookie-site.com \
  --cookies '{"session_id": "abc123", "auth_token": "xyz789"}' \
  --output ./cookie_clone
```

### **Complex Authentication Example**
```bash
python3 browser_cloner.py https://complex-site.com \
  --username "user@example.com" \
  --password "secret123" \
  --username-field "email" \
  --password-field "passwd" \
  --login-url "https://complex-site.com/auth/login" \
  --wait-time 3.0 \
  --depth 5 \
  --pages 200
```

## ⚙️ **Command Line Options**

### **Basic Options**
- `url` - Website URL to clone
- `-o, --output` - Output directory (default: `./cloned_website`)
- `-d, --depth` - Maximum crawling depth (default: `3`)
- `-p, --pages` - Maximum pages to download (default: `100`)
- `--delay` - Delay between requests in seconds (default: `1.0`)

### **Browser Options**
- `--wait-time` - Wait time for JavaScript execution (default: `5.0`)
- `--no-headless` - Run browser in visible mode (for debugging)

### **Authentication Options**
- `--username` - Username for login forms
- `--password` - Password for login forms
- `--login-url` - URL of login page (if different from main URL)
- `--username-field` - Name of username form field (default: `username`)
- `--password-field` - Name of password form field (default: `password`)
- `--cookies` - JSON string of cookies `'{"name": "value"}'`
- `--headers` - JSON string of headers `'{"Authorization": "Bearer token"}'`

## 🎯 **Target Use Cases**

### **Perfect For:**
- ✅ **Single Page Applications (SPAs)**
- ✅ **React/Vue/Angular applications**
- ✅ **Sites with login requirements**
- ✅ **AJAX-heavy content**
- ✅ **Dynamic data loading**
- ✅ **API-driven applications**
- ✅ **Sites like alldata.com with heavy JavaScript**

### **Examples of Supported Sites:**
- Modern dashboards and admin panels
- Social media platforms (public sections)
- E-commerce sites with dynamic content
- Documentation sites with live examples
- Educational platforms with interactive content

## ⚠️ **Limitations**

### **What Works:**
- ✅ JavaScript execution and DOM capture
- ✅ Form-based authentication
- ✅ Cookie and header authentication
- ✅ Dynamic content loading
- ✅ AJAX and XHR requests

### **What Doesn't Work:**
- ❌ **Real-time features** (WebSockets, live chat)
- ❌ **Complex multi-step authentication** (2FA, CAPTCHA)
- ❌ **Video/audio streaming** content
- ❌ **Server-side form processing**
- ❌ **Dynamic API endpoints** that require active sessions

## 🛠️ **Technical Details**

### **Browser Configuration**
- **Headless Chrome** with full JavaScript support
- **1920x1080 viewport** for consistent rendering
- **Standard User-Agent** for compatibility
- **Automatic driver management** via webdriver-manager

### **Authentication Flow**
1. **Initialize browser** and navigate to site
2. **Add custom cookies** if provided
3. **Navigate to login URL** if different from main URL
4. **Fill and submit login form** automatically
5. **Wait for login completion** and session establishment
6. **Begin crawling** with authenticated session

### **Asset Handling**
- **JavaScript files** downloaded and locally referenced
- **CSS stylesheets** downloaded with authentication headers
- **Images and fonts** downloaded with session cookies
- **Relative paths** properly maintained for offline viewing

## 🚨 **Important Considerations**

### **Rate Limiting**
- Always use appropriate delays (`--delay`)
- Respect robots.txt files
- Monitor server response times
- Be considerate of target server resources

### **Authentication Security**
- **Never commit passwords** to version control
- Use environment variables for sensitive data
- Consider using cookie/token auth over passwords
- Test authentication flow before large crawls

### **Legal Compliance**
- Ensure you have permission to clone the target site
- Respect terms of service and copyright
- Only clone content you have rights to access
- Consider data privacy implications

## 📊 **Performance Comparison**

| Feature | Static Cloner | Browser Cloner |
|---------|---------------|----------------|
| **Speed** | ⚡ Very Fast | 🐌 Slower |
| **JavaScript** | ❌ No | ✅ Full Support |
| **Authentication** | ❌ Limited | ✅ Complete |
| **SPAs** | ❌ Shell Only | ✅ Full Content |
| **Resource Usage** | 💚 Low | 🔴 High |
| **Setup** | 💚 Simple | 🔴 Complex |

## 🎯 **When to Use Each**

### **Use Static Cloner When:**
- Site is mostly static HTML/CSS
- No authentication required
- Speed is priority
- Simple setup needed

### **Use Browser Cloner When:**
- Site heavily uses JavaScript
- Authentication is required
- Dynamic content is important
- Modern web app architecture

## 🔧 **Troubleshooting**

### **Common Issues:**

**"Cannot find Chrome binary"**
```bash
# Install Chrome browser first
apt-get install google-chrome-stable
```

**"Login failed"**
```bash
# Check form field names
python3 browser_cloner.py site.com --no-headless  # Debug visually
```

**"Page not loading"**
```bash
# Increase wait time
python3 browser_cloner.py site.com --wait-time 10.0
```

**"Memory issues"**
```bash
# Reduce pages and add delays
python3 browser_cloner.py site.com --pages 10 --delay 2.0
```

This enhanced cloner bridges the gap between static website cloning and full web application replication, making it possible to create offline copies of modern, dynamic websites that were previously impossible to clone effectively.
