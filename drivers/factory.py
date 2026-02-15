import os
import sys

# Allow imports from parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import undetected_chromedriver as uc
from config import USER_DATA_DIR


def is_container():
    """Detect if running inside a container (Docker/Podman)."""
    return (
        os.path.exists('/.dockerenv') or
        os.environ.get('container') == 'podman' or
        os.environ.get('RUN_MODE') is not None
    )


def get_driver(headless=False, use_profile=True):
    """
    Returns a configured Chrome driver instance.
    Automatically detects container environment and adds necessary flags.
    
    Args:
        headless (bool): Whether to run in headless mode. 
                         Note: undetected-chromedriver handles headless differently to avoid detection.
        use_profile (bool): Whether to load the persistent user profile.
    """
    options = uc.ChromeOptions()
    
    if use_profile:
        # Point to a specific profile directory so we can persist login sessions
        options.add_argument(f"--user-data-dir={USER_DATA_DIR}")
    
    # Common anti-detection/stability args
    options.add_argument("--no-first-run")
    options.add_argument("--no-service-autorun")
    options.add_argument("--password-store=basic")
    
    # Container-specific flags
    if is_container() or os.environ.get('CHROME_NO_SANDBOX'):
        print("[Driver] Container environment detected, adding sandbox flags...")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-extensions")
        # Use the system Chrome in container instead of downloading
        options.binary_location = "/usr/bin/google-chrome-stable"
    
    print(f"Initializing Chrome Driver (Headless: {headless}, Container: {is_container()})...")
    try:
        driver = uc.Chrome(options=options, headless=headless, use_subprocess=True)
        return driver
    except Exception as e:
        print(f"Failed to initialize driver: {e}")
        raise e
