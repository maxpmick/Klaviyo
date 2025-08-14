"""
Tooltip component for providing helpful information
"""

import tkinter as tk
from typing import Optional


class ToolTip:
    """
    Creates a tooltip for a given widget
    """
    
    def __init__(self, widget: tk.Widget, text: str, delay: int = 500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip_window = None
        self.id = None
        
        self.widget.bind('<Enter>', self.on_enter)
        self.widget.bind('<Leave>', self.on_leave)
        self.widget.bind('<ButtonPress>', self.on_leave)
    
    def on_enter(self, event=None):
        """Mouse entered widget"""
        self.schedule_tooltip()
    
    def on_leave(self, event=None):
        """Mouse left widget"""
        self.cancel_tooltip()
        self.hide_tooltip()
    
    def schedule_tooltip(self):
        """Schedule tooltip to appear after delay"""
        self.cancel_tooltip()
        self.id = self.widget.after(self.delay, self.show_tooltip)
    
    def cancel_tooltip(self):
        """Cancel scheduled tooltip"""
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
    
    def show_tooltip(self):
        """Show the tooltip"""
        if self.tooltip_window:
            return
        
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 25
        
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        
        # Create tooltip content
        label = tk.Label(
            self.tooltip_window,
            text=self.text,
            background="#2b2b2b",
            foreground="#ffffff",
            relief="solid",
            borderwidth=1,
            font=("Segoe UI", 9),
            wraplength=350,
            justify="left",
            padx=8,
            pady=5
        )
        label.pack()
    
    def hide_tooltip(self):
        """Hide the tooltip"""
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None


def add_tooltip(widget: tk.Widget, text: str, delay: int = 500) -> ToolTip:
    """
    Convenience function to add a tooltip to a widget
    
    Args:
        widget: The widget to add tooltip to
        text: Tooltip text
        delay: Delay in milliseconds before showing tooltip
    
    Returns:
        ToolTip instance
    """
    return ToolTip(widget, text, delay)