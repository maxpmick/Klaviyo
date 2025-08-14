"""
Configuration management with secure API key storage
"""

import os
import json
import logging
import keyring
from typing import Optional, Dict, Any
from pathlib import Path
from .defaults import *


class ConfigManager:
    """
    Manages application configuration with secure API key storage
    """
    
    SERVICE_NAME = "KlaviyoSyncTool"
    API_KEY_USERNAME = "api_key"
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_dir = Path.home() / ".klaviyo_sync"
        self.config_file = self.config_dir / CONFIG_FILENAME
        self._config = {}
        self._ensure_config_dir()
        self.load_config()
    
    def _ensure_config_dir(self):
        """Ensure configuration directory exists"""
        self.config_dir.mkdir(exist_ok=True)
    
    def load_config(self):
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self._config = json.load(f)
                self.logger.info("Configuration loaded successfully")
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
                self._config = {}
        else:
            self._config = {}
            self.logger.info("No existing configuration found, using defaults")
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
            self.logger.info("Configuration saved successfully")
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
            raise
    
    def get_api_key(self) -> Optional[str]:
        """Get API key from secure storage"""
        try:
            api_key = keyring.get_password(self.SERVICE_NAME, self.API_KEY_USERNAME)
            return api_key
        except Exception as e:
            self.logger.error(f"Error retrieving API key: {e}")
            return None
    
    def set_api_key(self, api_key: str):
        """Store API key securely"""
        try:
            keyring.set_password(self.SERVICE_NAME, self.API_KEY_USERNAME, api_key)
            self.logger.info("API key stored securely")
        except Exception as e:
            self.logger.error(f"Error storing API key: {e}")
            raise
    
    def delete_api_key(self):
        """Delete stored API key"""
        try:
            keyring.delete_password(self.SERVICE_NAME, self.API_KEY_USERNAME)
            self.logger.info("API key deleted")
        except Exception as e:
            self.logger.error(f"Error deleting API key: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self._config[key] = value
    
    def get_segment_id(self) -> str:
        """Get segment ID with fallback to default"""
        return self.get("segment_id", DEFAULT_SEGMENT_ID)
    
    def set_segment_id(self, segment_id: str):
        """Set segment ID"""
        self.set("segment_id", segment_id)
    
    def get_metric_names(self) -> list:
        """Get metric names with fallback to default"""
        return self.get("metric_names", DEFAULT_METRIC_NAMES)
    
    def set_metric_names(self, metric_names: list):
        """Set metric names"""
        self.set("metric_names", metric_names)
    
    def get_revision(self) -> str:
        """Get API revision with fallback to default"""
        return self.get("revision", DEFAULT_REVISION)
    
    def set_revision(self, revision: str):
        """Set API revision"""
        self.set("revision", revision)
    
    
    def get_window_geometry(self) -> Dict[str, int]:
        """Get window geometry"""
        return self.get("window_geometry", {
            "width": DEFAULT_WINDOW_WIDTH,
            "height": DEFAULT_WINDOW_HEIGHT,
            "x": None,
            "y": None
        })
    
    def set_window_geometry(self, width: int, height: int, x: int = None, y: int = None):
        """Set window geometry"""
        self.set("window_geometry", {
            "width": width,
            "height": height,
            "x": x,
            "y": y
        })
    
    def get_theme(self) -> str:
        """Get UI theme"""
        return self.get("theme", DEFAULT_THEME)
    
    def set_theme(self, theme: str):
        """Set UI theme"""
        self.set("theme", theme)
    
    def get_log_level(self) -> str:
        """Get logging level"""
        return self.get("log_level", DEFAULT_LOG_LEVEL)
    
    def set_log_level(self, level: str):
        """Set logging level"""
        self.set("log_level", level)
    
    def get_max_retries(self) -> int:
        """Get max API retries"""
        return self.get("max_retries", DEFAULT_MAX_RETRIES)
    
    def set_max_retries(self, retries: int):
        """Set max API retries"""
        self.set("max_retries", retries)
    
    def get_timeout(self) -> int:
        """Get API timeout"""
        return self.get("timeout", DEFAULT_TIMEOUT)
    
    def set_timeout(self, timeout: int):
        """Set API timeout"""
        self.set("timeout", timeout)
    
    def is_first_run(self) -> bool:
        """Check if this is the first run"""
        return not self.config_file.exists() or not self.get_api_key()
    
    def export_config(self) -> Dict[str, Any]:
        """Export configuration (excluding sensitive data)"""
        config = self._config.copy()
        # Add non-sensitive defaults
        config.update({
            "has_api_key": bool(self.get_api_key()),
            "config_file": str(self.config_file),
            "version": "1.0.0"
        })
        return config
    
    def import_config(self, config_data: Dict[str, Any], include_api_key: bool = False):
        """Import configuration"""
        # Filter out sensitive or system-specific data
        excluded_keys = {"has_api_key", "config_file", "version"}
        
        for key, value in config_data.items():
            if key not in excluded_keys:
                self.set(key, value)
        
        self.save_config()
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self._config = {}
        if self.config_file.exists():
            self.config_file.unlink()
        self.logger.info("Configuration reset to defaults")


# Global configuration instance
config = ConfigManager()