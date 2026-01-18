import undetected_chromedriver as uc
# from selenium.webdriver.common.options import Options
from browser_automator.config import USER_DATA_DIR

def get_driver(headless=False, use_profile=True):
    """
    Returns a configured Chrome driver instance.
    
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
    
    # undetected-chromedriver handles headless mode internally if we pass headless=True to the Chrome() constructor,
    # but sometimes explicit flags helper.
    # However, uc.Chrome(headless=True) is the recommended way.
    
    print(f"Initializing Chrome Driver (Headless: {headless})...")
    try:
        driver = uc.Chrome(options=options, headless=headless, use_subprocess=True)
        return driver
    except Exception as e:
        print(f"Failed to initialize driver: {e}")
        raise e
