"""
Main tab for primary operations interface
"""

import tkinter as tk
import customtkinter as ctk
import logging
from typing import Optional
from ..config.settings import config
from ..core.api_client import KlaviyoApiClient, ApiConfig
from ..core.data_processor import DataProcessor
from ..core.models import ProcessingStats
from ..utils.threading import task_manager
from ..utils.validation import validate_segment_id, validate_event_name
from .components.tooltip import add_tooltip


class MainTab:
    """
    Main operations interface tab
    """
    
    def __init__(self, parent):
        self.parent = parent
        self.logger = logging.getLogger(__name__)
        
        # UI elements
        self.segment_id_entry = None
        self.event_name_entry = None
        self.dry_run_var = None
        self.progress_bar = None
        self.progress_label = None
        self.start_button = None
        self.stop_button = None
        
        # State
        self.is_running = False
        self.current_task_id = "sync_task"
        self.logs_tab = None  # Will be set by main window
        
        self.create_widgets()
        self.refresh()
    
    def create_widgets(self):
        """Create all widgets for the main tab"""
        # Main frame with consistent styling
        main_frame = ctk.CTkFrame(self.parent)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Input section
        self.create_input_section(main_frame)
        
        # Progress section
        self.create_progress_section(main_frame)
        
        # Control buttons
        self.create_control_section(main_frame)
    
    def create_input_section(self, parent):
        """Create input fields section"""
        input_frame = ctk.CTkFrame(parent)
        input_frame.pack(fill="x", padx=0, pady=(0, 10))
        
        # Title
        title_label = ctk.CTkLabel(input_frame, text="Sync Configuration", font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(pady=(15, 20))
        add_tooltip(title_label, "Configure the parameters for syncing checkout snapshots from Klaviyo profiles")
        
        # Segment ID
        segment_frame = ctk.CTkFrame(input_frame)
        segment_frame.pack(fill="x", padx=15, pady=8)
        
        segment_label = ctk.CTkLabel(segment_frame, text="Segment ID:", font=ctk.CTkFont(size=14, weight="bold"))
        segment_label.pack(side="left", padx=(15, 10), pady=12)
        add_tooltip(segment_label, "The unique identifier for the Klaviyo segment containing profiles to process")
        
        self.segment_id_entry = ctk.CTkEntry(segment_frame, placeholder_text="e.g., UM5yp4", height=32)
        self.segment_id_entry.pack(side="left", fill="x", expand=True, padx=(0, 15), pady=12)
        self.segment_id_entry.insert(0, config.get_segment_id())
        
        add_tooltip(self.segment_id_entry, "Enter the Klaviyo segment ID containing profiles to sync")
        
        # Event Name
        event_frame = ctk.CTkFrame(input_frame)
        event_frame.pack(fill="x", padx=15, pady=8)
        
        event_label = ctk.CTkLabel(event_frame, text="Event Name:", font=ctk.CTkFont(size=14, weight="bold"))
        event_label.pack(side="left", padx=(15, 10), pady=12)
        add_tooltip(event_label, "The name of the event to search for in profile histories")
        
        self.event_name_entry = ctk.CTkEntry(event_frame, placeholder_text="e.g., Checkout Started", height=32)
        self.event_name_entry.pack(side="left", fill="x", expand=True, padx=(0, 15), pady=12)
        self.event_name_entry.insert(0, "Checkout Started")
        
        add_tooltip(self.event_name_entry, "Event name to search for in profile histories (e.g., 'Checkout Started', 'Started Checkout'). This should match exactly how the event appears in Klaviyo.")
        
        # Options
        options_frame = ctk.CTkFrame(input_frame)
        options_frame.pack(fill="x", padx=15, pady=(8, 15))
        
        # Dry run checkbox
        self.dry_run_var = ctk.BooleanVar(value=True)
        dry_run_checkbox = ctk.CTkCheckBox(options_frame, text="Dry Run (Preview Only)",
                                         variable=self.dry_run_var, font=ctk.CTkFont(size=14))
        dry_run_checkbox.pack(side="left", padx=15, pady=12)
        add_tooltip(dry_run_checkbox, "When enabled, shows a preview of what would be updated without making any actual changes to your Klaviyo data. Recommended for first-time use.")
    
    def create_progress_section(self, parent):
        """Create progress indicators section"""
        progress_frame = ctk.CTkFrame(parent)
        progress_frame.pack(fill="x", padx=0, pady=(0, 10))
        
        # Progress label
        self.progress_label = ctk.CTkLabel(progress_frame, text="Ready to start", font=ctk.CTkFont(size=14))
        self.progress_label.pack(pady=(15, 8))
        add_tooltip(self.progress_label, "Shows current sync status and processing statistics")
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=20)
        self.progress_bar.pack(fill="x", padx=15, pady=(0, 15))
        self.progress_bar.set(0)
        add_tooltip(self.progress_bar, "Visual indicator of sync progress showing percentage of profiles processed")
    
    
    def create_control_section(self, parent):
        """Create control buttons section"""
        control_frame = ctk.CTkFrame(parent)
        control_frame.pack(fill="x", padx=0, pady=(20, 0))
        
        # Start button
        self.start_button = ctk.CTkButton(
            control_frame,
            text="Start Sync",
            command=self.start_sync,
            font=ctk.CTkFont(size=16, weight="bold"),
            height=45,
            width=120
        )
        self.start_button.pack(side="left", padx=15, pady=15)
        add_tooltip(self.start_button, "Start the checkout snapshot sync process. Ensure your API key is configured and segment ID is valid before starting.")
        
        # Stop button
        self.stop_button = ctk.CTkButton(
            control_frame,
            text="Stop",
            command=self.stop_sync,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            width=100,
            fg_color="#dc3545",
            hover_color="#c82333"
        )
        self.stop_button.pack(side="left", padx=10, pady=15)
        self.stop_button.configure(state="disabled")
        add_tooltip(self.stop_button, "Immediately stop the current sync process. Any profiles already processed will remain updated.")
        
    
    def log_message(self, message: str):
        """Add message to log"""
        print(f"[LOG] {message}")  # Console backup
        if self.logs_tab:
            self.logs_tab.log_message(message)
    
    def clear_log(self):
        """Clear the log"""
        if self.logs_tab:
            self.logs_tab.clear_log()
    
    def update_progress(self, stats: ProcessingStats):
        """Update progress indicators"""
        if stats.total_profiles > 0:
            progress = stats.processed / stats.total_profiles
            self.progress_bar.set(progress)
            
            status = f"Processed {stats.processed}/{stats.total_profiles} profiles"
            if stats.matched > 0:
                status += f" | Matched: {stats.matched}"
            if stats.updated > 0:
                status += f" | Updated: {stats.updated}"
            if stats.errors > 0:
                status += f" | Errors: {stats.errors}"
            
            self.progress_label.configure(text=status)
    
    def start_sync(self):
        """Start the sync process"""
        # Validate inputs
        segment_id = self.segment_id_entry.get().strip()
        event_name = self.event_name_entry.get().strip()
        
        if not validate_segment_id(segment_id):
            self.log_message("Error: Please enter a valid segment ID")
            return
        
        if not validate_event_name(event_name):
            self.log_message("Error: Please enter a valid event name")
            return
        
        # Check API key
        api_key = config.get_api_key()
        if not api_key:
            self.log_message("Error: Please configure your API key in the Configuration tab")
            return
        
        # Get options
        dry_run = self.dry_run_var.get()
        
        # Update UI state
        self.is_running = True
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Starting sync...")
        
        # Save current segment ID
        config.set_segment_id(segment_id)
        config.save_config()
        
        # Log start
        mode = "DRY RUN" if dry_run else "LIVE"
        self.log_message(f"Starting {mode} sync for segment {segment_id}")
        self.log_message(f"Event name: {event_name}")
        
        # Start background task
        try:
            task_manager.start_task(
                self.current_task_id,
                self.run_sync,
                args=(api_key, segment_id, event_name, dry_run)
            )
            
            # Start monitoring
            self.monitor_task()
            
        except Exception as e:
            self.log_message(f"Error starting sync: {e}")
            self.sync_finished()
    
    def run_sync(self, api_key: str, segment_id: str, event_name: str, dry_run: bool):
        """Run sync in background thread"""
        try:
            # Create API client
            api_config = ApiConfig(
                api_key=api_key,
                revision=config.get_revision(),
                timeout=config.get_timeout(),
                max_retries=config.get_max_retries()
            )
            
            api_client = KlaviyoApiClient(api_config)
            
            # Create processor
            processor = DataProcessor(api_client=api_client)
            
            # Run processing
            result = processor.process_profiles(
                segment_id=segment_id,
                limit=None,
                dry_run=dry_run,
                progress_callback=self.update_progress,
                should_stop=lambda: task_manager.get_task(self.current_task_id).is_cancelled
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Sync error: {e}")
            raise
    
    def monitor_task(self):
        """Monitor background task progress"""
        task = task_manager.get_task(self.current_task_id)
        if not task:
            self.sync_finished()
            return
        
        # Get progress updates
        updates = task.get_progress_updates()
        for update in updates:
            if isinstance(update, ProcessingStats):
                self.update_progress(update)
            elif isinstance(update, str):
                self.log_message(update)
        
        # Check if task is finished
        if not task.is_alive():
            self.handle_task_completion(task)
            return
        
        # Schedule next check
        self.parent.after(100, self.monitor_task)
    
    def handle_task_completion(self, task):
        """Handle task completion"""
        if task.error:
            self.log_message(f"Sync failed: {task.error}")
        elif task.result:
            result = task.result
            if result.success:
                stats = result.stats
                if result.dry_run_results:
                    self.log_message(f"DRY RUN COMPLETE - {stats.matched} profiles would be updated")
                    self.log_message("Preview results:")
                    for preview in result.dry_run_results[:5]:  # Show first 5
                        self.log_message("---")
                        self.log_message(preview)
                    if len(result.dry_run_results) > 5:
                        self.log_message(f"... and {len(result.dry_run_results) - 5} more")
                else:
                    self.log_message(f"SYNC COMPLETE - Updated {stats.updated} profiles")
                
                self.log_message(f"Final stats: matched={stats.matched}, updated={stats.updated}, "
                               f"no_event={stats.no_event}, no_snapshot={stats.no_snapshot}, errors={stats.errors}")
            else:
                self.log_message(f"Sync failed: {result.error_message}")
        
        self.sync_finished()
    
    def stop_sync(self):
        """Stop the sync process"""
        task_manager.cancel_task(self.current_task_id)
        self.log_message("Stopping sync...")
    
    def sync_finished(self):
        """Reset UI after sync completion"""
        self.is_running = False
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.progress_label.configure(text="Sync completed")
    
    def refresh(self):
        """Refresh the tab (e.g., after config changes)"""
        # Update segment ID from config
        current_segment = self.segment_id_entry.get()
        config_segment = config.get_segment_id()
        if current_segment != config_segment:
            self.segment_id_entry.delete(0, "end")
            self.segment_id_entry.insert(0, config_segment)
    
    def cleanup(self):
        """Cleanup when closing"""
        if self.is_running:
            task_manager.cancel_task(self.current_task_id)