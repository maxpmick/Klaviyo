# Klaviyo Checkout Snapshot Sync Tool - GUI Application

A professional GUI application for syncing Klaviyo checkout snapshots, built with Python and CustomTkinter.

## Features

- **Modern GUI Interface**: Clean, professional interface using CustomTkinter
- **Secure API Key Storage**: API keys are stored securely using the system keyring
- **Real-time Progress Tracking**: Live progress bars and detailed logging
- **Dry Run Mode**: Preview changes before applying them
- **Background Processing**: Non-blocking operations with cancellation support
- **Comprehensive Tooltips**: Helpful explanations for all features
- **Persistent Configuration**: Settings are saved between sessions
- **Error Handling**: Robust error handling with user-friendly messages

## Installation

### Prerequisites
- **Python 3.7 or higher** (Python 3.8+ recommended)
- **Operating System**: Windows 10+, macOS 10.14+, or Linux with GUI support

### Quick Installation

1. **Clone or download** the application files to your local machine

2. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Installation**:
   ```bash
   python run_klaviyo_gui.py
   ```

### Alternative Installation (Virtual Environment - Recommended)

1. **Create a virtual environment**:
   ```bash
   python -m venv klaviyo_gui_env
   ```

2. **Activate the virtual environment**:
   - **Windows**: `klaviyo_gui_env\Scripts\activate`
   - **macOS/Linux**: `source klaviyo_gui_env/bin/activate`

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python run_klaviyo_gui.py
   ```

### Required Dependencies
- `customtkinter>=5.2.0` - Modern GUI framework
- `requests>=2.31.0` - HTTP client for API calls
- `keyring>=24.0.0` - Secure credential storage
- `python-dotenv>=1.0.0` - Environment variable support
- `urllib3>=1.26.0` - HTTP library
- `certifi>=2023.0.0` - SSL certificates

### Build Dependencies (Optional)
- `cx_Freeze>=6.15.0` - For creating standalone executables

## Usage

### Running the Application

**Recommended method:**
```bash
python run_klaviyo_gui.py
```

**Alternative method:**
```bash
python klaviyo_gui/main.py
```

### First-Time Setup

When you first launch the application, it will automatically open to the Configuration tab:

1. **Enter your Klaviyo API Key**:
   - Navigate to your Klaviyo account settings
   - Go to "Settings" → "API Keys"
   - Copy your Private API Key (starts with `pk_` or `sk_`)
   - Paste it into the API Key field

2. **Test the connection**:
   - Click "Test Connection" to verify your API key works
   - Wait for the green "✓ Connection successful!" message

3. **Configure default settings**:
   - Set a default Segment ID (optional)
   - Choose your preferred theme
   - Adjust advanced settings if needed

4. **Save the configuration**:
   - Click "Save Configuration"
   - Your settings will be preserved between sessions

5. **Switch to the Main tab** to start syncing

### Getting Your API Key

1. Log into your Klaviyo account
2. Navigate to **Settings** → **API Keys**
3. Create a new **Private API Key** or use an existing one
4. Ensure the key has the following permissions:
   - Read access to Lists and Segments
   - Read access to Profiles
   - Write access to Profiles (for updating checkout snapshots)
   - Read access to Events

### Main Operations

#### 1. Configure Sync Parameters

- **Segment ID**: Enter the ID of the Klaviyo segment containing profiles to sync
  - Find this in Klaviyo under "Lists & Segments"
  - Example: `UM5yp4`

- **Event Name**: Specify the event to search for in profile histories
  - Common examples: "Checkout Started", "Started Checkout"
  - Must match exactly as it appears in Klaviyo

- **Dry Run Mode**:
  - ✅ **Enabled (Recommended)**: Preview changes without making updates
  - ❌ **Disabled**: Make actual updates to Klaviyo profiles

#### 2. Start Sync Process

1. **Verify your settings** are correct
2. **Click "Start Sync"** to begin processing
3. **Monitor progress** in real-time:
   - Progress bar shows completion percentage
   - Activity log displays detailed information
   - Status updates show profiles processed, matched, and updated

#### 3. Review Results

**Dry Run Results:**
- Shows exactly what would be updated
- Displays preview of checkout snapshot data
- No actual changes are made to Klaviyo

**Live Run Results:**
- Shows actual update statistics
- Confirms successful profile updates
- Reports any errors encountered

#### 4. Managing the Process

- **Stop**: Click "Stop" to cancel the current sync
- **Clear Log**: Clear the activity log (doesn't affect results)
- **Monitor**: Watch the progress bar and status updates

## Configuration Options

### API Configuration
- **API Key**: Your Klaviyo API key (securely stored)
- **Default Segment ID**: Default segment to use in the main interface
- **Test Connection**: Verify API connectivity

### Application Settings
- **Theme**: Choose from blue, green, or dark-blue color schemes
- **Placeholder Image URL**: Default image for products without images

### Advanced Settings
- **API Revision**: Klaviyo API revision date (default: 2025-07-15)
- **Request Timeout**: HTTP request timeout in seconds
- **Max Retries**: Maximum retry attempts for failed requests

## File Structure

```
klaviyo_gui/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── gui/
│   ├── main_window.py     # Root window with tabs
│   ├── main_tab.py        # Primary operations interface
│   ├── config_tab.py      # Settings and API configuration
│   └── components/
│       └── tooltip.py     # Tooltip implementation
├── core/
│   ├── api_client.py      # Klaviyo API client
│   ├── data_processor.py  # Profile processing logic
│   └── models.py          # Data structures
├── config/
│   ├── settings.py        # Configuration management
│   └── defaults.py        # Default values
└── utils/
    ├── threading.py       # Background task management
    └── validation.py      # Input validation
```

## Data Storage

- **Configuration**: Stored in `~/.klaviyo_sync/klaviyo_sync_config.json`
- **API Keys**: Stored securely in system keyring
- **Logs**: Stored in `~/.klaviyo_sync/logs/klaviyo_sync.log`

## Security

- API keys are stored using the system's secure keyring service
- API keys are masked in the UI by default
- No sensitive data is stored in plain text configuration files
- All API communications use HTTPS

## Troubleshooting

### Common Issues

#### Installation Problems

**"Missing required dependencies" error:**
```bash
# Solution: Install all dependencies
pip install -r requirements.txt

# If using virtual environment:
source klaviyo_gui_env/bin/activate  # macOS/Linux
# or
klaviyo_gui_env\Scripts\activate     # Windows
pip install -r requirements.txt
```

**"Python not found" error:**
- Ensure Python 3.7+ is installed
- Try `python3` instead of `python`
- Verify Python is in your system PATH

#### Connection Issues

**"Connection failed" error:**
1. **Verify API Key**: Ensure it starts with `pk_` or `sk_`
2. **Check Permissions**: API key needs profile read/write access
3. **Test Internet**: Verify you can access `https://a.klaviyo.com`
4. **Firewall**: Ensure your firewall allows HTTPS connections

**"Invalid API key format" error:**
- API key should be 32+ characters
- Should start with `pk_` (public) or `sk_` (private)
- No spaces or extra characters

#### Data Issues

**"No profiles found" error:**
1. **Verify Segment ID**: Check it exists in your Klaviyo account
2. **Check Segment Size**: Ensure the segment contains profiles
3. **API Permissions**: Verify read access to segments and profiles

**"No events found" error:**
1. **Event Name**: Must match exactly (case-sensitive)
2. **Profile History**: Profiles must have the specified event
3. **Date Range**: Events might be outside the search timeframe

#### Application Issues

**Application won't start:**
1. **Python Version**: Requires Python 3.7+
   ```bash
   python --version
   ```
2. **Dependencies**: Reinstall requirements
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```
3. **Log Files**: Check `~/.klaviyo_sync/logs/klaviyo_sync.log`

**GUI doesn't appear:**
- **Linux**: Install tkinter: `sudo apt-get install python3-tk`
- **macOS**: Ensure you're using system Python or Python from python.org
- **Windows**: Reinstall Python with "tcl/tk and IDLE" option

**Performance Issues:**
- **Large Segments**: Use smaller batch sizes in advanced settings
- **Timeout Errors**: Increase timeout value in Configuration
- **Memory Usage**: Process segments in smaller chunks

### Getting Help

1. **Activity Log**: Check the real-time log in the application
2. **Log Files**: Review detailed logs at `~/.klaviyo_sync/logs/klaviyo_sync.log`
3. **API Permissions**: Verify your Klaviyo API key has:
   - Lists and Segments: Read access
   - Profiles: Read and Write access
   - Events: Read access

### Debug Mode

For detailed debugging, you can run the application with verbose logging:

```bash
# Set environment variable for debug mode
export KLAVIYO_DEBUG=1  # macOS/Linux
# or
set KLAVIYO_DEBUG=1     # Windows

python run_klaviyo_gui.py
```

## Building Executables

To create a standalone executable that doesn't require Python installation:

### Windows Executable

```bash
python klaviyo_gui/build.py
```

This creates a `dist/` folder with the executable and all dependencies.

### macOS Application Bundle

```bash
python klaviyo_gui/build.py --platform macos
```

### Linux AppImage

```bash
python klaviyo_gui/build.py --platform linux
```

## Migration from Command Line

This GUI application provides the same functionality as the original `fetch_metrics.py` script with these advantages:

- **User-friendly interface** instead of command-line arguments
- **Real-time progress tracking** instead of terminal output
- **Secure credential storage** instead of environment variables
- **Persistent configuration** instead of repeated parameter entry
- **Background processing** with cancellation support
- **Comprehensive tooltips** explaining each feature
- **Professional visual design** with consistent styling

All the core business logic and API interactions remain the same, ensuring consistent results.

## Advanced Features

### Tooltips and Help
- **Hover over any element** to see helpful tooltips
- **Detailed explanations** for all configuration options
- **Context-sensitive help** throughout the interface

### Configuration Management
- **Automatic saving** of window size and position
- **Secure API key storage** using system keyring
- **Theme customization** with multiple color schemes
- **Advanced settings** for timeout and retry behavior

### Error Handling
- **Graceful error recovery** with detailed error messages
- **Automatic retry logic** for transient network issues
- **Comprehensive logging** for troubleshooting
- **User-friendly error dialogs** with suggested solutions

## Support

For technical support or feature requests, please refer to the activity log and log files for detailed error information. The application includes comprehensive error handling and logging to help diagnose any issues.