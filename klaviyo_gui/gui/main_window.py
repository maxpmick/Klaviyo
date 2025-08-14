"""
Main application window with tabbed interface
"""

import tkinter as tk
import customtkinter as ctk
import logging
from typing import Optional
from ..config.settings import config
from .main_tab import MainTab
from .config_tab import ConfigTab
from .logs_tab import LogsTab


class MainWindow:
    """
    Main application window with tabbed interface
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.root = None
        self.tabview = None
        self.main_tab = None
        self.config_tab = None
        self.logs_tab = None
        
        # Set customtkinter theme
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme(config.get_theme())
    
    def create_window(self):
        """Create and configure the main window"""
        self.root = ctk.CTk()
        self.root.title("Klaviyo Checkout Snapshot Sync Tool")
        
        # Set window geometry from config
        geometry = config.get_window_geometry()
        width = geometry["width"]
        height = geometry["height"]
        
        if geometry["x"] is not None and geometry["y"] is not None:
            self.root.geometry(f"{width}x{height}+{geometry['x']}+{geometry['y']}")
        else:
            self.root.geometry(f"{width}x{height}")
        
        # Set minimum size
        self.root.minsize(600, 400)
        
        # Configure window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Create main layout
        self.create_layout()
        
        self.logger.info("Main window created")
    
    def create_layout(self):
        """Create the main layout with tabs"""
        # Create tabview
        self.tabview = ctk.CTkTabview(self.root)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs
        main_tab_frame = self.tabview.add("Main")
        config_tab_frame = self.tabview.add("Configuration")
        logs_tab_frame = self.tabview.add("Logs")
        
        # Initialize tab content
        self.main_tab = MainTab(main_tab_frame)
        self.config_tab = ConfigTab(config_tab_frame)
        self.logs_tab = LogsTab(logs_tab_frame)
        
        # Connect logging from main tab to logs tab
        self.main_tab.logs_tab = self.logs_tab
        
        # Add tooltips to tabs (note: CustomTkinter tabs don't support direct tooltips)
        # The tab functionality is explained through the content within each tab
        
        # Set default tab
        self.tabview.set("Main")
        
        self.logger.info("Main layout created with tabs")
    
    def on_closing(self):
        """Handle window closing"""
        try:
            # Save window geometry
            geometry = self.root.geometry()
            # Parse geometry string (e.g., "800x600+100+50")
            size_pos = geometry.split('+')
            size = size_pos[0].split('x')
            width = int(size[0])
            height = int(size[1])
            
            x = None
            y = None
            if len(size_pos) >= 3:
                x = int(size_pos[1])
                y = int(size_pos[2])
            
            config.set_window_geometry(width, height, x, y)
            config.save_config()
            
            # Cancel any running tasks
            if self.main_tab:
                self.main_tab.cleanup()
            
            self.logger.info("Application closing")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
        
        finally:
            self.root.destroy()
    
    def run(self):
        """Start the application"""
        if not self.root:
            self.create_window()
        
        # Check if this is first run
        if config.is_first_run():
            self.tabview.set("Configuration")
            self.config_tab.show_first_run_message()
        
        self.logger.info("Starting application main loop")
        self.root.mainloop()
    
    def get_root(self) -> Optional[ctk.CTk]:
        """Get the root window"""
        return self.root
    
    def switch_to_main_tab(self):
        """Switch to the main tab"""
        if self.tabview:
            self.tabview.set("Main")
    
    def switch_to_config_tab(self):
        """Switch to the configuration tab"""
        if self.tabview:
            self.tabview.set("Configuration")
    
    def refresh_main_tab(self):
        """Refresh the main tab (e.g., after config changes)"""
        if self.main_tab:
            self.main_tab.refresh()