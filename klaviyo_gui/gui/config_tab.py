"""
Configuration tab for settings and API configuration
"""

import tkinter as tk
import customtkinter as ctk
import logging
from typing import Optional
from ..config.settings import config
from ..core.api_client import KlaviyoApiClient, ApiConfig
from ..utils.validation import validate_api_key
from .components.tooltip import add_tooltip


class ConfigTab:
    """
    Configuration and settings tab
    """
    
    def __init__(self, parent):
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        
        # UI elements
        self.api_key_entry = None
        self.api_key_var = None
        self.show_api_key_var = None
        self.segment_id_entry = None
        self.revision_entry = None
        self.timeout_entry = None
        self.retries_entry = None
        self.theme_combo = None
        self.test_button = None
        self.save_button = None
        self.status_label = None
        
        self.create_widgets()
        self.load_current_config()
    
    def create_widgets(self):
        """Create all widgets for the config tab"""
        # Main scrollable frame with consistent styling
        main_frame = ctk.CTkScrollableFrame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # API Configuration section
        self.create_api_section(main_frame)
        
        # Application Settings section
        self.create_app_settings_section(main_frame)
        
        # Advanced Settings section
        self.create_advanced_section(main_frame)
        
        # Control buttons
        self.create_control_section(main_frame)
        
        # Status section
        self.create_status_section(main_frame)
    
    def create_api_section(self, parent):
        """Create API configuration section"""
        api_frame = ctk.CTkFrame(parent)
        api_frame.pack(fill="x", padx=0, pady=(0, 15))
        
        # Title
        title_label = ctk.CTkLabel(api_frame, text="API Configuration", font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(pady=(20, 15))
        add_tooltip(title_label, "Configure your Klaviyo API credentials and connection settings")
        
        # API Key
        key_frame = ctk.CTkFrame(api_frame)
        key_frame.pack(fill="x", padx=20, pady=8)
        
        key_label = ctk.CTkLabel(key_frame, text="API Key:", font=ctk.CTkFont(size=14, weight="bold"))
        key_label.pack(anchor="w", padx=15, pady=(12, 8))
        add_tooltip(key_label, "Your Klaviyo API key - required for all operations")
        
        # API key entry with show/hide
        key_input_frame = ctk.CTkFrame(key_frame)
        key_input_frame.pack(fill="x", padx=15, pady=(0, 8))
        
        self.api_key_var = tk.StringVar()
        self.api_key_entry = ctk.CTkEntry(
            key_input_frame,
            textvariable=self.api_key_var,
            placeholder_text="pk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            show="*",
            height=32
        )
        self.api_key_entry.pack(side="left", fill="x", expand=True, padx=(8, 12), pady=8)
        
        self.show_api_key_var = ctk.BooleanVar()
        show_key_checkbox = ctk.CTkCheckBox(
            key_input_frame,
            text="Show",
            variable=self.show_api_key_var,
            command=self.toggle_api_key_visibility,
            font=ctk.CTkFont(size=12)
        )
        show_key_checkbox.pack(side="right", padx=8, pady=8)
        
        add_tooltip(self.api_key_entry, "Your Klaviyo API key (starts with pk_ for public or sk_ for private). Get this from your Klaviyo account settings under API Keys.")
        add_tooltip(show_key_checkbox, "Toggle API key visibility to show or hide the key characters for security")
        
        # Test connection button
        self.test_button = ctk.CTkButton(
            key_frame,
            text="Test Connection",
            command=self.test_connection,
            height=36,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.test_button.pack(pady=(8, 20))
        add_tooltip(self.test_button, "Test the API connection with the current key to verify it's valid and has proper permissions")
        
        # Default Segment ID
        segment_frame = ctk.CTkFrame(api_frame)
        segment_frame.pack(fill="x", padx=20, pady=(8, 20))
        
        segment_label = ctk.CTkLabel(segment_frame, text="Default Segment ID:", font=ctk.CTkFont(size=14, weight="bold"))
        segment_label.pack(anchor="w", padx=15, pady=(12, 8))
        add_tooltip(segment_label, "Default segment to pre-populate in the main interface")
        
        self.segment_id_entry = ctk.CTkEntry(segment_frame, placeholder_text="UM5yp4", height=32)
        self.segment_id_entry.pack(fill="x", padx=15, pady=(0, 12))
        add_tooltip(self.segment_id_entry, "Default segment ID to pre-populate in the main tab. You can always change this when running a sync.")
    
    def create_app_settings_section(self, parent):
        """Create application settings section"""
        app_frame = ctk.CTkFrame(parent)
        app_frame.pack(fill="x", padx=0, pady=(0, 15))
        
        # Title
        title_label = ctk.CTkLabel(app_frame, text="Application Settings", font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(pady=(20, 15))
        add_tooltip(title_label, "Customize the application appearance and behavior")
        
        # Theme selection
        theme_frame = ctk.CTkFrame(app_frame)
        theme_frame.pack(fill="x", padx=20, pady=(8, 20))
        
        theme_label = ctk.CTkLabel(theme_frame, text="Theme:", font=ctk.CTkFont(size=14, weight="bold"))
        theme_label.pack(anchor="w", padx=15, pady=(12, 8))
        add_tooltip(theme_label, "Choose the color scheme for the application interface")
        
        self.theme_combo = ctk.CTkComboBox(
            theme_frame,
            values=["blue", "green", "dark-blue"],
            state="readonly",
            height=32
        )
        self.theme_combo.pack(fill="x", padx=15, pady=(0, 12))
        add_tooltip(self.theme_combo, "Choose the application color theme. Changes take effect after restarting the application.")
        
    
    def create_advanced_section(self, parent):
        """Create advanced settings section"""
        advanced_frame = ctk.CTkFrame(parent)
        advanced_frame.pack(fill="x", padx=0, pady=(0, 15))
        
        # Title
        title_label = ctk.CTkLabel(advanced_frame, text="Advanced Settings", font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(pady=(20, 15))
        add_tooltip(title_label, "Advanced configuration options for API behavior and performance")
        
        # API Revision
        revision_frame = ctk.CTkFrame(advanced_frame)
        revision_frame.pack(fill="x", padx=15, pady=5)
        
        revision_label = ctk.CTkLabel(revision_frame, text="API Revision:")
        revision_label.pack(anchor="w", padx=10, pady=(10, 5))
        add_tooltip(revision_label, "Klaviyo API revision date - controls which API version to use")
        
        self.revision_entry = ctk.CTkEntry(revision_frame, placeholder_text="2025-07-15")
        self.revision_entry.pack(fill="x", padx=10, pady=(0, 10))
        add_tooltip(self.revision_entry, "Klaviyo API revision date (format: YYYY-MM-DD). Use the latest stable revision unless you need specific API features.")
        
        # Timeout and Retries
        network_frame = ctk.CTkFrame(advanced_frame)
        network_frame.pack(fill="x", padx=15, pady=5)
        
        # Timeout
        timeout_subframe = ctk.CTkFrame(network_frame)
        timeout_subframe.pack(fill="x", padx=10, pady=(10, 5))
        
        timeout_label = ctk.CTkLabel(timeout_subframe, text="Request Timeout (seconds):")
        timeout_label.pack(side="left", padx=(5, 10))
        add_tooltip(timeout_label, "How long to wait for API responses before timing out")
        
        self.timeout_entry = ctk.CTkEntry(timeout_subframe, placeholder_text="60", width=100)
        self.timeout_entry.pack(side="right", padx=5)
        add_tooltip(self.timeout_entry, "HTTP request timeout in seconds. Increase if you experience timeout errors with large segments.")
        
        # Max Retries
        retries_subframe = ctk.CTkFrame(network_frame)
        retries_subframe.pack(fill="x", padx=10, pady=(5, 15))
        
        retries_label = ctk.CTkLabel(retries_subframe, text="Max Retries:")
        retries_label.pack(side="left", padx=(5, 10))
        add_tooltip(retries_label, "Maximum number of retry attempts for failed API requests")
        
        self.retries_entry = ctk.CTkEntry(retries_subframe, placeholder_text="5", width=100)
        self.retries_entry.pack(side="right", padx=5)
        add_tooltip(self.retries_entry, "Maximum number of retry attempts for failed requests. Higher values provide better reliability but slower failure detection.")
    
    def create_control_section(self, parent):
        """Create control buttons section"""
        control_frame = ctk.CTkFrame(parent)
        control_frame.pack(fill="x", padx=10, pady=5)
        
        # Save button
        self.save_button = ctk.CTkButton(
            control_frame,
            text="Save Configuration",
            command=self.save_config,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=45,
            width=180
        )
        self.save_button.pack(side="left", padx=20, pady=20)
        add_tooltip(self.save_button, "Save all configuration changes to disk. Settings will be preserved between application sessions.")
        
        # Reset button
        reset_button = ctk.CTkButton(
            control_frame,
            text="Reset to Defaults",
            command=self.reset_config,
            height=45,
            width=160,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#fd7e14",
            hover_color="#e8690b"
        )
        reset_button.pack(side="right", padx=20, pady=20)
        add_tooltip(reset_button, "Reset all settings to default values. This will clear your API key and all custom settings - use with caution!")
    
    def create_status_section(self, parent):
        """Create status display section"""
        status_frame = ctk.CTkFrame(parent)
        status_frame.pack(fill="x", padx=10, pady=(5, 15))
        
        self.status_label = ctk.CTkLabel(
            status_frame, 
            text="Ready to configure",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(pady=10)
    
    def toggle_api_key_visibility(self):
        """Toggle API key visibility"""
        if self.show_api_key_var.get():
            self.api_key_entry.configure(show="")
        else:
            self.api_key_entry.configure(show="*")
    
    def load_current_config(self):
        """Load current configuration into UI"""
        # API Key
        api_key = config.get_api_key()
        if api_key:
            self.api_key_var.set(api_key)
        
        # Segment ID
        self.segment_id_entry.insert(0, config.get_segment_id())
        
        # Theme
        self.theme_combo.set(config.get_theme())
        
        # Note: Placeholder URL functionality removed as it's not in current UI
        
        # Revision
        self.revision_entry.insert(0, config.get_revision())
        
        # Timeout
        self.timeout_entry.insert(0, str(config.get_timeout()))
        
        # Retries
        self.retries_entry.insert(0, str(config.get_max_retries()))
    
    def test_connection(self):
        """Test API connection"""
        api_key = self.api_key_var.get().strip()
        
        if not validate_api_key(api_key):
            self.status_label.configure(text="Please enter a valid API key", text_color="red")
            return
        
        self.status_label.configure(text="Testing connection...", text_color="blue")
        self.test_button.configure(state="disabled")
        
        # Test in background
        def test_api():
            try:
                api_config = ApiConfig(api_key=api_key)
                client = KlaviyoApiClient(api_config)
                success = client.test_connection()
                
                if success:
                    self.status_label.configure(text="✓ Connection successful!", text_color="green")
                else:
                    self.status_label.configure(text="✗ Connection failed", text_color="red")
            except Exception as e:
                self.status_label.configure(text=f"✗ Connection error: {str(e)}", text_color="red")
            finally:
                self.test_button.configure(state="normal")
        
        # Run test in background
        import threading
        threading.Thread(target=test_api, daemon=True).start()
    
    def save_config(self):
        """Save configuration"""
        try:
            # API Key
            api_key = self.api_key_var.get().strip()
            if api_key:
                if not validate_api_key(api_key):
                    self.status_label.configure(text="Invalid API key format", text_color="red")
                    return
                config.set_api_key(api_key)
            
            # Segment ID
            segment_id = self.segment_id_entry.get().strip()
            if segment_id:
                config.set_segment_id(segment_id)
            
            # Theme
            theme = self.theme_combo.get()
            config.set_theme(theme)
            
            # Note: Placeholder URL functionality removed as it's not in current UI
            
            # Revision
            revision = self.revision_entry.get().strip()
            if revision:
                config.set_revision(revision)
            
            # Timeout
            try:
                timeout = int(self.timeout_entry.get().strip())
                config.set_timeout(timeout)
            except ValueError:
                self.status_label.configure(text="Invalid timeout value", text_color="red")
                return
            
            # Retries
            try:
                retries = int(self.retries_entry.get().strip())
                config.set_max_retries(retries)
            except ValueError:
                self.status_label.configure(text="Invalid retries value", text_color="red")
                return
            
            # Save to file
            config.save_config()
            
            self.status_label.configure(text="✓ Configuration saved successfully!", text_color="green")
            self.logger.info("Configuration saved")
            
        except Exception as e:
            self.status_label.configure(text=f"Error saving config: {str(e)}", text_color="red")
            self.logger.error(f"Error saving config: {e}")
    
    def reset_config(self):
        """Reset configuration to defaults"""
        # Show confirmation dialog
        result = tk.messagebox.askyesno(
            "Reset Configuration",
            "Are you sure you want to reset all settings to defaults?\nThis will clear your API key and all custom settings."
        )
        
        if result:
            try:
                config.reset_to_defaults()
                
                # Clear UI
                self.api_key_var.set("")
                self.segment_id_entry.delete(0, "end")
                self.segment_id_entry.insert(0, config.get_segment_id())
                self.theme_combo.set(config.get_theme())
                # Note: Placeholder URL functionality removed as it's not in current UI
                self.revision_entry.delete(0, "end")
                self.revision_entry.insert(0, config.get_revision())
                self.timeout_entry.delete(0, "end")
                self.timeout_entry.insert(0, str(config.get_timeout()))
                self.retries_entry.delete(0, "end")
                self.retries_entry.insert(0, str(config.get_max_retries()))
                
                self.status_label.configure(text="✓ Configuration reset to defaults", text_color="green")
                
            except Exception as e:
                self.status_label.configure(text=f"Error resetting config: {str(e)}", text_color="red")
    
    def show_first_run_message(self):
        """Show first run message"""
        self.status_label.configure(
            text="Welcome! Please configure your API key to get started.",
            text_color="blue"
        )