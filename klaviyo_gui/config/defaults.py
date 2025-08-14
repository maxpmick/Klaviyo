"""
Default configuration values for the Klaviyo Checkout Snapshot Sync Tool
"""

# API Configuration
DEFAULT_REVISION = "2025-07-15"
DEFAULT_BASE_URL = "https://a.klaviyo.com/api"
DEFAULT_TIMEOUT = 60
DEFAULT_MAX_RETRIES = 5

# Application Defaults
DEFAULT_SEGMENT_ID = "UM5yp4"
DEFAULT_METRIC_NAMES = ["Checkout Started", "Started Checkout"]
DEFAULT_CURRENCY = "USD"

# UI Configuration
DEFAULT_WINDOW_WIDTH = 800
DEFAULT_WINDOW_HEIGHT = 600
DEFAULT_THEME = "blue"

# Processing Defaults
DEFAULT_BATCH_SIZE = 25
DEFAULT_COURTESY_DELAY = 0.2  # seconds between batches
DEFAULT_PAGE_DELAY = 0.1      # seconds between API pages

# Logging
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s %(levelname)s | %(message)s"

# File paths
CONFIG_FILENAME = "klaviyo_sync_config.json"
LOG_FILENAME = "klaviyo_sync.log"