import os
import logging
from datetime import datetime
import glob

LOG_DIR = None
CURRENT_LOG_FILE = None
MAX_LOG_FILES = 3

def create_log_path():
    global LOG_DIR
    app_data_path = os.path.join(os.getenv('APPDATA'), 'AlternativeDesktop')

    # Create AppData/AlternativeDesktop/logs directory if it doesn't exist
    logs_dir = os.path.join(app_data_path, 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    LOG_DIR = logs_dir
    return logs_dir

def setup_logging():
    global CURRENT_LOG_FILE
    # Ensure the log directory is set up
    create_log_path()
    
    # Generate a new log file name with a timestamp
    log_file_path = os.path.join(LOG_DIR, f"alternative_desktop_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    CURRENT_LOG_FILE = log_file_path
    # Set up logging with a file handler for the new log file
    handler = logging.FileHandler(log_file_path)

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[handler, logging.StreamHandler()]
    )
    
    # Rotate the logs, keeping only the latest 3 files
    rotate_logs()

# Dev logging calls with nothing, to use global LOG_DIR. Installed version calls with logs_dir.
def rotate_logs(logs_dir = None):
    if LOG_DIR is None and logs_dir is None:
        raise ValueError("LOG_DIR is not set. Call create_log_path() first.")
    elif logs_dir is None:
        # Get a list of log files sorted by creation time
        print("Using global log dir")
        log_files = sorted(glob.glob(os.path.join(LOG_DIR, "alternative_desktop_*.log")), key=os.path.getctime)
    else:
        print("using called logs dir")
        log_files = sorted(glob.glob(os.path.join(logs_dir, "alternative_desktop_*.log")), key=os.path.getctime)

    # If there are more than MAX_LOG_FILES, remove the oldest ones
    while len(log_files) > MAX_LOG_FILES:
        oldest_log = log_files.pop(0)
        os.remove(oldest_log)


def get_current_log_file():
    return CURRENT_LOG_FILE