import os
import re
import subprocess
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


def get_chrome_major_version():
    """Auto-detect the installed Chrome major version.

    Returns:
        int or None: The major version number (e.g. 145), or None if detection fails.
    """
    candidates = [
        "/usr/bin/google-chrome-stable",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "google-chrome-stable",
        "google-chrome",
    ]

    for binary in candidates:
        try:
            output = subprocess.check_output(
                [binary, "--version"], stderr=subprocess.DEVNULL, timeout=5
            ).decode().strip()
            # Output format: "Google Chrome 145.0.7632.75" or "Chromium 145.0.7632.75"
            match = re.search(r"(\d+)\.", output)
            if match:
                version = int(match.group(1))
                print(f"[Driver] Detected Chrome version: {output} (major: {version})")
                return version
        except (FileNotFoundError, subprocess.SubprocessError):
            continue

    print("[Driver] WARNING: Could not detect Chrome version, letting undetected-chromedriver decide")
    return None


def get_driver(headless=False, use_profile=True):
    """
    Returns a configured Chrome driver instance.
    Automatically detects container environment and adds necessary flags.
    Pins ChromeDriver version to match the installed Chrome to prevent mismatch.

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

    # Auto-detect and pin ChromeDriver version to match installed Chrome
    chrome_major = get_chrome_major_version()

    print(f"Initializing Chrome Driver (Headless: {headless}, Container: {is_container()}, Chrome Major: {chrome_major})...")
    try:
        driver = uc.Chrome(
            options=options,
            headless=headless,
            use_subprocess=True,
            version_main=chrome_major,
        )
        return driver
    except Exception as e:
        print(f"Failed to initialize driver: {e}")
        raise e
