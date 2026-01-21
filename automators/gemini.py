import os
import sys
import time

# Allow imports from parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from automators.base import BaseAutomator
from config import GEMINI_URL, GEMINI_SELECTORS
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

class GeminiAutomator(BaseAutomator):
    def navigate(self):
        print(f"Navigating to {GEMINI_URL}...")
        self.driver.get(GEMINI_URL)
        time.sleep(3)
        
        # Check if login is required
        current_url = self.driver.current_url
        if "accounts.google.com" in current_url:
            print("Login check: You are redirected to the login page.")
            print("Please MANUALY log in to the browser window opened.")
            print("Once logged in, the script will likely need to be restarted or we wait here.")
            # We can enter a loop waiting for the user to login and reach gemini
            max_wait = 120
            elapsed = 0
            while "gemini.google.com" not in self.driver.current_url and elapsed < max_wait:
                print(f"Waiting for manual login... ({elapsed}s/{max_wait}s)")
                time.sleep(5)
                elapsed += 5
            
            if "gemini.google.com" in self.driver.current_url:
                print("Login detected! Proceeding.")
            else:
                print("Timeout waiting for login.")

    def query(self, text: str):
        """
        Submit a query to Gemini.
        Uses clipboard paste to prevent prompt from being split into multiple messages.
        """
        # Sanitize the text - remove newlines and normalize whitespace
        clean_text = text.replace('\n', ' ').replace('\r', ' ')
        clean_text = ' '.join(clean_text.split())  # Normalize multiple spaces
        
        print(f"[Gemini] Prompt length: {len(clean_text)} chars")
        
        # Wait for input
        input_selector = GEMINI_SELECTORS["input_area"]
        print(f"Waiting for input area: {input_selector}")
        try:
            input_el = self.wait_for_element(input_selector)
        except:
            print("Could not find input area. Are you logged in?")
            return

        print("Typing query...")
        input_el.click()
        time.sleep(0.5)
        
        # Method 1: Use JavaScript to set the value directly (for contenteditable)
        # This prevents character-by-character issues
        try:
            # For contenteditable divs, we need to set innerHTML or textContent
            self.driver.execute_script("""
                var element = arguments[0];
                var text = arguments[1];
                
                // Clear existing content
                element.innerHTML = '';
                
                // Set the text content
                element.textContent = text;
                
                // Trigger input event so Gemini recognizes the change
                var event = new Event('input', { bubbles: true });
                element.dispatchEvent(event);
            """, input_el, clean_text)
            print("[Gemini] Text injected via JavaScript")
        except Exception as e:
            print(f"[Gemini] JavaScript injection failed: {e}, falling back to send_keys")
            # Fallback: send the entire text at once (not char by char)
            input_el.send_keys(clean_text)
            
        time.sleep(0.5)
        
        # Submit with Enter key
        input_el.send_keys(Keys.RETURN)
        print("Query submitted.")
        time.sleep(5)

    def extract_response(self) -> str:
        print("Waiting for response generation...")
        time.sleep(10) # Wait for Gemini to think
        
        soup = self.get_soup()
        # Find response containers
        # Gemini structure is complex. Look for specific model-response tags or similar.
        # Based on config, we look for 'model-response' tag or class.
        
        responses = soup.select(GEMINI_SELECTORS["response_container"])
        if not responses:
            # Fallback to class search
            responses = soup.select(".model-response-text") 
            
        if not responses:
             return "Could not extract response. Selectors might be outdated."

        latest = responses[-1].get_text(separator="\n", strip=True)
        return latest
