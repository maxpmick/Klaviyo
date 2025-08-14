"""
Logs tab for activity monitoring
"""

import tkinter as tk
import customtkinter as ctk
import logging
from .components.tooltip import add_tooltip


class LogsTab:
    """
    Activity logs tab
    """
    
    def __init__(self, parent):
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        
        # UI elements
        self.log_text = None
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create all widgets for the logs tab"""
        # Main frame with consistent styling
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Title
        title_label = ctk.CTkLabel(main_frame, text="Activity Log", font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(pady=(15, 20))
        add_tooltip(title_label, "Real-time activity log showing detailed sync progress, results, and any errors")
        
        # Log section
        log_frame = ctk.CTkFrame(main_frame)
        log_frame.pack(fill="both", expand=True, padx=0, pady=(0, 15))
        
        # Text widget with scrollbar
        text_frame = ctk.CTkFrame(log_frame)
        text_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        self.log_text = ctk.CTkTextbox(text_frame, font=ctk.CTkFont(family="Consolas", size=11))
        self.log_text.pack(fill="both", expand=True, padx=8, pady=8)
        
        add_tooltip(self.log_text, "Real-time activity log showing detailed sync progress, API responses, error messages, and final results. Scroll to see full history.")
        
        # Control buttons
        control_frame = ctk.CTkFrame(main_frame)
        control_frame.pack(fill="x", padx=0, pady=0)
        
        # Clear log button
        clear_button = ctk.CTkButton(
            control_frame,
            text="Clear Log",
            command=self.clear_log,
            font=ctk.CTkFont(size=14),
            height=45,
            width=120,
            fg_color="#6c757d",
            hover_color="#5a6268"
        )
        clear_button.pack(side="right", padx=15, pady=15)
        add_tooltip(clear_button, "Clear all messages from the activity log. This does not affect the actual sync results.")
    
    def log_message(self, message: str):
        """Add message to log"""
        if self.log_text:
            self.log_text.insert("end", f"{message}\n")
            self.log_text.see("end")
    
    def clear_log(self):
        """Clear the log"""
        if self.log_text:
            self.log_text.delete("1.0", "end")