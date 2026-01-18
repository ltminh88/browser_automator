import os

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# Chrome User Data Directory (Profile)
# This allows the user to log in once manually, and we reuse the session.
# We will create a fresh profile directory for this tool to avoid conflicts with the main browser.
USER_DATA_DIR = os.path.join(BASE_DIR, "chrome_profile")

# Platform URLs
PERPLEXITY_URL = "https://www.perplexity.ai/"
GEMINI_URL = "https://gemini.google.com/"

# Selectors (Subject to change as sites update)
# Using generic selectors where possible or specific classes if stable.

PERPLEXITY_SELECTORS = {
    "input_area": "#ask-input", 
    "submit_button": "button[aria-label='Submit']",
    "response_container": ".prose", 
    "model_menu_button": "button[aria-label='Choose a model']",
    "model_items_all": "//*[@role='menuitem']", # Select all items to filter in Python
    "mode_search_button": "//button[.//div[contains(text(), 'Search')]]",
    "mode_deep_research_item": "//div[@role='menuitem'][.//div[contains(text(), 'Deep research')]]",
    # Direct button selector targeting the Telescope icon
    "mode_deep_research_direct_btn": "//button[descendant::*[name()='use' and contains(@href, 'telescope')]]"
}

GEMINI_SELECTORS = {
    "login_check": "a[href*='accounts.google.com']", 
    "input_area": "div[role='textbox']", 
    "submit_button": "button[aria-label='Send message']", 
    "response_container": "div.markdown", 
    "latest_response": ".message-content", 
}
