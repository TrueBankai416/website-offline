#!/usr/bin/env python3
"""
GUI version of the Enhanced Browser Website Cloner with JavaScript execution and authentication.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import time
import json
from browser_cloner import BrowserWebsiteCloner
from selenium.webdriver.common.by import By


class BrowserClonerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Enhanced Browser Website Cloner")
        self.root.geometry("1000x800")
        
        # Variables
        self.url_var = tk.StringVar()
        self.output_dir_var = tk.StringVar(value="./cloned_website")
        self.progress_var = tk.StringVar(value="Ready to clone JavaScript-heavy websites")
        self.is_cloning = False
        
        # Crawling variables
        self.max_depth_var = tk.IntVar(value=3)
        self.max_pages_var = tk.IntVar(value=100)
        self.delay_var = tk.DoubleVar(value=1.0)
        self.wait_time_var = tk.DoubleVar(value=5.0)
        self.headless_var = tk.BooleanVar(value=True)
        self.browser_var = tk.StringVar(value="auto")
        
        # Authentication variables
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.login_url_var = tk.StringVar()
        self.username_field_var = tk.StringVar(value="username")
        self.password_field_var = tk.StringVar(value="password")
        self.cookies_var = tk.StringVar()
        self.headers_var = tk.StringVar()
        
        # Browser cloner instance
        self.cloner = None
        self.should_stop = False
        self.cloning_thread = None
        
        self.setup_ui()
        self.detect_browsers()
        
    def setup_ui(self):
        # Main frame with scrollbar
        main_canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )
        
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_frame = ttk.Frame(scrollable_frame, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Enhanced Browser Website Cloner", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        subtitle_label = ttk.Label(main_frame, text="JavaScript Execution • Authentication • Multi-Browser Support", 
                                  font=("Arial", 10, "italic"))
        subtitle_label.grid(row=1, column=0, columnspan=2, pady=(0, 20))
        
        current_row = 2
        
        # URL input
        url_frame = ttk.LabelFrame(main_frame, text="Website URL", padding="10")
        url_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        current_row += 1
        
        ttk.Entry(url_frame, textvariable=self.url_var, width=80).grid(row=0, column=0, sticky=(tk.W, tk.E))
        url_frame.columnconfigure(0, weight=1)
        
        # Output directory
        output_frame = ttk.LabelFrame(main_frame, text="Output Directory", padding="10")
        output_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        current_row += 1
        
        ttk.Entry(output_frame, textvariable=self.output_dir_var, width=70).grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(output_frame, text="Browse", command=self.browse_directory).grid(row=0, column=1, padx=(5, 0))
        output_frame.columnconfigure(0, weight=1)
        
        # Browser selection and options
        browser_frame = ttk.LabelFrame(main_frame, text="Browser & Crawling Options", padding="10")
        browser_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        current_row += 1
        
        # Browser selection row
        ttk.Label(browser_frame, text="Browser:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.browser_combo = ttk.Combobox(browser_frame, textvariable=self.browser_var, width=15, state="readonly")
        self.browser_combo.grid(row=0, column=1, padx=(0, 20))
        
        # Headless checkbox
        ttk.Checkbutton(browser_frame, text="Headless Mode", variable=self.headless_var).grid(row=0, column=2, padx=(0, 20))
        
        # Crawling options row 1
        ttk.Label(browser_frame, text="Max Depth:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        ttk.Spinbox(browser_frame, from_=1, to=10, width=10, textvariable=self.max_depth_var).grid(row=1, column=1, padx=(0, 20), pady=(10, 0))
        
        ttk.Label(browser_frame, text="Max Pages:").grid(row=1, column=2, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        ttk.Spinbox(browser_frame, from_=1, to=1000, width=10, textvariable=self.max_pages_var).grid(row=1, column=3, padx=(0, 20), pady=(10, 0))
        
        # Crawling options row 2
        ttk.Label(browser_frame, text="Delay (s):").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        ttk.Spinbox(browser_frame, from_=0.1, to=10.0, increment=0.1, width=10, textvariable=self.delay_var).grid(row=2, column=1, padx=(0, 20), pady=(5, 0))
        
        ttk.Label(browser_frame, text="JS Wait (s):").grid(row=2, column=2, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        ttk.Spinbox(browser_frame, from_=0.1, to=30.0, increment=0.5, width=10, textvariable=self.wait_time_var).grid(row=2, column=3, padx=(0, 20), pady=(5, 0))
        
        # Authentication frame
        auth_frame = ttk.LabelFrame(main_frame, text="Authentication (Optional)", padding="10")
        auth_frame.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        current_row += 1
        
        # Username/Password authentication
        creds_frame = ttk.LabelFrame(auth_frame, text="Login Credentials", padding="5")
        creds_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(creds_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Entry(creds_frame, textvariable=self.username_var, width=25).grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(creds_frame, text="Password:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        ttk.Entry(creds_frame, textvariable=self.password_var, width=25, show="*").grid(row=0, column=3)
        
        ttk.Label(creds_frame, text="Login URL:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        ttk.Entry(creds_frame, textvariable=self.login_url_var, width=60).grid(row=1, column=1, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Form field names
        fields_frame = ttk.LabelFrame(auth_frame, text="Form Field Names", padding="5")
        fields_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(fields_frame, text="Username Field:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        ttk.Entry(fields_frame, textvariable=self.username_field_var, width=20).grid(row=0, column=1, padx=(0, 20))
        
        ttk.Label(fields_frame, text="Password Field:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        ttk.Entry(fields_frame, textvariable=self.password_field_var, width=20).grid(row=0, column=3)
        
        # Advanced authentication
        advanced_frame = ttk.LabelFrame(auth_frame, text="Advanced Authentication", padding="5")
        advanced_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(advanced_frame, text="Cookies (JSON):").grid(row=0, column=0, sticky=(tk.W, tk.N), padx=(0, 10))
        cookies_text = tk.Text(advanced_frame, height=3, width=70)
        cookies_text.grid(row=0, column=1, sticky=(tk.W, tk.E))
        cookies_text.bind('<KeyRelease>', lambda e: self.cookies_var.set(cookies_text.get(1.0, tk.END).strip()))
        
        ttk.Label(advanced_frame, text="Headers (JSON):").grid(row=1, column=0, sticky=(tk.W, tk.N), padx=(0, 10), pady=(5, 0))
        headers_text = tk.Text(advanced_frame, height=3, width=70)
        headers_text.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(5, 0))
        headers_text.bind('<KeyRelease>', lambda e: self.headers_var.set(headers_text.get(1.0, tk.END).strip()))
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=current_row, column=0, columnspan=2, pady=(0, 10))
        current_row += 1
        
        self.clone_button = ttk.Button(control_frame, text="Clone Website with Browser", command=self.start_cloning)
        self.clone_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="Stop Cloning", command=self.stop_cloning, state='disabled')
        self.stop_button.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Button(control_frame, text="Detect Browsers", command=self.detect_browsers).grid(row=0, column=2, padx=(0, 10))
        
        ttk.Button(control_frame, text="Debug Login Fields", command=self.debug_login_fields).grid(row=0, column=3)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress_bar.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
        current_row += 1
        
        # Status label
        ttk.Label(main_frame, textvariable=self.progress_var).grid(row=current_row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        current_row += 1
        
        # Log output
        ttk.Label(main_frame, text="Log:").grid(row=current_row, column=0, sticky=tk.W, pady=(0, 5))
        current_row += 1
        self.log_text = scrolledtext.ScrolledText(main_frame, height=12, width=100)
        self.log_text.grid(row=current_row, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        scrollable_frame.columnconfigure(0, weight=1)
        
        # Pack canvas and scrollbar
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def detect_browsers(self):
        """Detect available browsers and populate the combo box."""
        try:
            cloner = BrowserWebsiteCloner()
            available_browsers = cloner.detect_available_browsers()
            
            browser_options = ["auto"] + available_browsers
            self.browser_combo['values'] = browser_options
            
            if available_browsers:
                self.log_message(f"Detected browsers: {', '.join(available_browsers)}")
            else:
                self.log_message("No browsers detected. Please install Chrome, Firefox, Edge, or Safari.")
                
        except Exception as e:
            self.log_message(f"Error detecting browsers: {str(e)}")
            
    def debug_login_fields(self):
        """Debug login fields on a website to help find correct field names."""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a URL first")
            return
            
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        login_url = self.login_url_var.get().strip() or url
        
        def debug_fields():
            try:
                self.log_message(f"Inspecting login fields at: {login_url}")
                
                # Create a temporary cloner for debugging
                debug_cloner = BrowserWebsiteCloner(browser=self.browser_var.get(), headless=False)
                
                if not debug_cloner.setup_browser():
                    self.log_message("Failed to initialize browser for debugging")
                    return
                    
                debug_cloner.driver.get(login_url)
                time.sleep(3)
                
                # Find all input fields
                input_fields = debug_cloner.driver.find_elements(By.TAG_NAME, "input")
                
                self.log_message(f"Found {len(input_fields)} input fields:")
                
                for i, field in enumerate(input_fields):
                    try:
                        field_type = field.get_attribute("type") or "text"
                        field_name = field.get_attribute("name") or ""
                        field_id = field.get_attribute("id") or ""
                        field_class = field.get_attribute("class") or ""
                        field_placeholder = field.get_attribute("placeholder") or ""
                        
                        self.log_message(f"  Field {i+1}: type='{field_type}', name='{field_name}', id='{field_id}', class='{field_class}', placeholder='{field_placeholder}'")
                        
                    except Exception as e:
                        self.log_message(f"  Field {i+1}: Error reading attributes - {str(e)}")
                
                self.log_message("Login field inspection completed. Look for username/email and password fields above.")
                self.log_message("Use the 'name' or 'id' values in the Username Field and Password Field settings.")
                
                # Keep browser open for 10 seconds for manual inspection
                self.log_message("Browser will stay open for 10 seconds for manual inspection...")
                time.sleep(10)
                
                debug_cloner.cleanup_browser()
                
            except Exception as e:
                self.log_message(f"Debug failed: {str(e)}")
                
        # Run in separate thread
        thread = threading.Thread(target=debug_fields)
        thread.daemon = True
        thread.start()
            
    def log_message(self, message):
        self.log_text.insert(tk.END, f"{time.strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def browse_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir_var.set(directory)
            
    def stop_cloning(self):
        """Stop the cloning process."""
        if self.is_cloning:
            self.should_stop = True
            self.log_message("Stop requested by user...")
            
            # Clean up browser if active
            if self.cloner and self.cloner.driver:
                try:
                    self.cloner.cleanup_browser()
                    self.log_message("Browser cleaned up")
                except Exception as e:
                    self.log_message(f"Error cleaning up browser: {str(e)}")
                    
            self.progress_var.set("Cloning stopped by user")
            self.is_cloning = False
            self.clone_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.progress_bar.stop()
            
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
        self.should_stop = False
        self.clone_button.config(state='disabled')
        self.stop_button.config(state='normal')
        self.progress_bar.start()
        self.log_text.delete(1.0, tk.END)
        
        # Start cloning in a separate thread
        self.cloning_thread = threading.Thread(target=self.clone_website, args=(url, output_dir))
        self.cloning_thread.daemon = True
        self.cloning_thread.start()
        
    def clone_website(self, url, output_dir):
        try:
            self.progress_var.set("Initializing enhanced browser cloner...")
            self.log_message(f"Starting enhanced browser clone: {url}")
            
            # Create cloner instance with settings
            self.cloner = BrowserWebsiteCloner(
                max_depth=self.max_depth_var.get(),
                max_pages=self.max_pages_var.get(),
                delay=self.delay_var.get(),
                headless=self.headless_var.get(),
                wait_time=self.wait_time_var.get(),
                browser=self.browser_var.get()
            )
            
            # Override log_message method to show in GUI
            original_log = self.cloner.log_message
            self.cloner.log_message = self.log_message
            
            # Set up authentication if provided
            username = self.username_var.get().strip()
            password = self.password_var.get().strip()
            
            if username and password:
                login_url = self.login_url_var.get().strip() or None
                self.cloner.set_authentication(
                    username=username,
                    password=password,
                    login_url=login_url,
                    username_field=self.username_field_var.get().strip(),
                    password_field=self.password_field_var.get().strip()
                )
                self.log_message(f"Authentication configured for user: {username}")
                
                # Store original perform_login method before overriding
                self.cloner.perform_login_original = self.cloner.perform_login
                self.cloner.perform_login = self.enhanced_perform_login
                
            # Set custom cookies if provided
            cookies_text = self.cookies_var.get().strip()
            if cookies_text:
                try:
                    cookies = json.loads(cookies_text)
                    self.cloner.set_cookies(cookies)
                    self.log_message(f"Loaded {len(cookies)} custom cookies")
                except Exception as e:
                    self.log_message(f"Failed to parse cookies: {e}")
                    
            # Set custom headers if provided
            headers_text = self.headers_var.get().strip()
            if headers_text:
                try:
                    headers = json.loads(headers_text)
                    self.cloner.set_headers(headers)
                    self.log_message(f"Loaded {len(headers)} custom headers")
                except Exception as e:
                    self.log_message(f"Failed to parse headers: {e}")
                    
            # Start cloning with stop checks
            success = self.clone_website_with_stop_check(url, output_dir)
            
            if success:
                self.progress_var.set("Enhanced cloning completed successfully!")
                self.log_message("✅ Enhanced website cloning completed successfully!")
                messagebox.showinfo("Success", f"Enhanced website cloning completed!\nSaved to: {output_dir}")
            else:
                self.progress_var.set("Enhanced cloning failed")
                self.log_message("❌ Enhanced website cloning failed!")
                messagebox.showerror("Error", "Enhanced website cloning failed. Check the log for details.")
                
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.progress_var.set("Error occurred during enhanced cloning")
            self.log_message(error_msg)
            messagebox.showerror("Error", error_msg)
            
        finally:
            self.is_cloning = False
            self.clone_button.config(state='normal')
            self.stop_button.config(state='disabled')
            self.progress_bar.stop()
            
    def find_login_field(self, field_type, field_name):
        """Try to find login field using multiple strategies."""
        strategies = []
        
        # Strategy 1: Use provided field name
        if field_name:
            strategies.extend([
                (By.NAME, field_name),
                (By.ID, field_name),
                (By.CSS_SELECTOR, f'[name="{field_name}"]'),
                (By.CSS_SELECTOR, f'[id="{field_name}"]')
            ])
        
        # Strategy 2: Common field names based on type
        if field_type == "username":
            common_names = ["username", "user", "email", "login", "userid", "user_name", "loginname", "valUserName"]
        else:  # password
            common_names = ["password", "pass", "passwd", "pwd", "user_password", "valPassword"]
            
        for name in common_names:
            strategies.extend([
                (By.NAME, name),
                (By.ID, name),
                (By.CSS_SELECTOR, f'[name="{name}"]'),
                (By.CSS_SELECTOR, f'[id="{name}"]')
            ])
            
        # Strategy 3: Input type selectors
        if field_type == "username":
            strategies.extend([
                (By.CSS_SELECTOR, 'input[type="text"]'),
                (By.CSS_SELECTOR, 'input[type="email"]'),
                (By.CSS_SELECTOR, 'input:not([type="password"]):not([type="hidden"]):not([type="submit"])'),
            ])
        else:  # password
            strategies.append((By.CSS_SELECTOR, 'input[type="password"]'))
            
        # Try each strategy
        for by, value in strategies:
            try:
                elements = self.cloner.driver.find_elements(by, value)
                if elements:
                    # For multiple elements, try to pick the most likely one
                    element = elements[0]
                    self.log_message(f"Found {field_type} field using {by}='{value}'")
                    return element
            except Exception:
                continue
                
        return None

    def enhanced_perform_login(self):
        """Enhanced login method with user dialog on failure."""
        try:
            # Call the original perform_login method directly
            if not self.cloner.auth_username or not self.cloner.auth_password:
                return True
                
            login_url = self.cloner.auth_login_url or self.cloner.base_url
            self.log_message(f"Performing login at: {login_url}")
            
            self.cloner.driver.get(login_url)
            time.sleep(2)
            
            # Find username field using enhanced detection
            username_field = self.find_login_field("username", self.cloner.auth_username_field)
            if not username_field:
                raise Exception(f"Could not find username field. Tried field name: '{self.cloner.auth_username_field}' and common alternatives.")
                
            username_field.clear()
            username_field.send_keys(self.cloner.auth_username)
            self.log_message(f"Filled username field")
            
            # Find password field using enhanced detection
            password_field = self.find_login_field("password", self.cloner.auth_password_field)
            if not password_field:
                raise Exception(f"Could not find password field. Tried field name: '{self.cloner.auth_password_field}' and common alternatives.")
                
            password_field.clear()
            password_field.send_keys(self.cloner.auth_password)
            self.log_message(f"Filled password field")
            
            # Submit form
            submit_button = self.cloner.driver.find_element(By.CSS_SELECTOR, self.cloner.auth_submit_selector)
            submit_button.click()
            self.log_message(f"Clicked submit button")
            
            # Wait for page to load after login
            time.sleep(3)
            
            self.log_message("Login completed")
            return True
            
        except Exception as e:
            self.log_message(f"Login failed: {str(e)}")
            
            # Ask user whether to continue or abort
            response = messagebox.askyesno(
                "Login Failed", 
                f"Login failed: {str(e)}\n\nWould you like to continue without authentication?",
                icon='warning'
            )
            
            if not response:
                self.log_message("User chose to abort after login failure")
                self.should_stop = True
                return False
            else:
                self.log_message("User chose to continue without authentication")
                return True
                
    def clone_website_with_stop_check(self, url, output_dir):
        """Clone website with periodic stop checks."""
        if self.should_stop:
            return False
            
        # Call original clone_website method
        return self.cloner.clone_website(url, output_dir)


def main():
    root = tk.Tk()
    app = BrowserClonerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
