"""
Main entry point for the Klaviyo Checkout Snapshot Sync Tool GUI
"""

import sys
import logging
import tkinter as tk
import os
from pathlib import Path
try:
    from dotenv import load_dotenv as _load_dotenv
except Exception:
    _load_dotenv = None

# Determine if running as a frozen executable (compiled binary)
if getattr(sys, 'frozen', False):
    # Running as compiled binary
    application_path = Path(sys.executable).parent
    # Add the application directory to Python path
    sys.path.insert(0, str(application_path))
else:
    # Running as script
    application_path = Path(__file__).parent
    # Add the parent directory to the path so we can import our modules
    sys.path.insert(0, str(application_path.parent))

# Load environment variables from a .env file if present (useful on Windows/macOS)
try:
    if _load_dotenv:
        _load_dotenv()
except Exception:
    pass

# Ensure Requests/SSL can find a CA bundle when frozen on Windows
try:
    import certifi
    ca_path = certifi.where()
    # Set both env vars commonly respected by Requests/OpenSSL
    os.environ.setdefault("SSL_CERT_FILE", ca_path)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", ca_path)
    # If available, extend certifi with Windows' certificate store (enterprise CAs, etc.)
    try:
        import certifi_win32  # type: ignore  # noqa: F401
    except Exception:
        pass
except Exception:
    pass

# Set environment variable for customtkinter to find assets when frozen
# Prefer actual packaged assets if present; otherwise do not override defaults
if getattr(sys, 'frozen', False):
    # 1) Check alongside the executable (useful for onedir/cx_Freeze)
    ctk_assets_path = application_path / "customtkinter" / "assets"
    if ctk_assets_path.exists():
        os.environ['CTK_THEME_PATH'] = str(ctk_assets_path)
    else:
        # 2) Check PyInstaller onefile extraction dir (_MEIPASS)
        meipass = getattr(sys, '_MEIPASS', None)
        if meipass:
            meipass_assets = Path(meipass) / "customtkinter" / "assets"
            if meipass_assets.exists():
                os.environ['CTK_THEME_PATH'] = str(meipass_assets)
else:
    # Running as script - use default CustomTkinter behavior (no override)
    os.environ['CTK_THEME_PATH'] = str(application_path)

from klaviyo_gui.config.settings import config
from klaviyo_gui.gui.main_window import MainWindow


def setup_logging():
    """Setup logging configuration"""
    try:
        log_level = getattr(logging, config.get_log_level().upper(), logging.INFO)
        
        # Create logs directory
        log_dir = config.config_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s %(levelname)s [%(name)s] | %(message)s",
            handlers=[
                logging.FileHandler(log_dir / "klaviyo_sync.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Reduce noise from some libraries
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        
    except Exception as e:
        # Fallback logging setup if config fails
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s %(levelname)s | %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        logging.error(f"Failed to setup full logging: {e}")


def check_dependencies():
    """Check if required dependencies are available"""
    missing_deps = []
    
    try:
        import customtkinter
    except ImportError:
        missing_deps.append("customtkinter")
    
    try:
        import requests
    except ImportError:
        missing_deps.append("requests")
    
    try:
        import keyring  # noqa: F401
    except Exception:
        # Optional; we'll fall back to env/config file if missing
        pass
    
    if missing_deps:
        print("Missing required dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("\nPlease install them using:")
        print(f"  pip install {' '.join(missing_deps)}")
        return False
    
    return True


def main():
    """Main application entry point"""
    # Only print to console if not running as frozen binary
    if not getattr(sys, 'frozen', False):
        print("Klaviyo Checkout Snapshot Sync Tool")
        print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting Klaviyo Checkout Snapshot Sync Tool")
        
        # Create and run the main window
        app = MainWindow()
        app.run()
        
        logger.info("Application closed normally")
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        
        # Show error dialog if tkinter is available
        try:
            root = tk.Tk()
            root.withdraw()  # Hide the root window
            import tkinter.messagebox
            tkinter.messagebox.showerror(
                "Application Error",
                f"An unexpected error occurred:\n\n{str(e)}\n\nCheck the log file for more details."
            )
            root.destroy()
        except Exception:
            pass  # If we can't show the dialog, just continue
        
        sys.exit(1)


if __name__ == "__main__":
    main()