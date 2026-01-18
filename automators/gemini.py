from browser_automator.automators.base import BaseAutomator
from browser_automator.config import GEMINI_URL, GEMINI_SELECTORS
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time

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
        # ContentEditable divs can't always be cleared with clear(). 
        # But usually start empty for new chat.
        
        for char in text:
            input_el.send_keys(char)
            time.sleep(0.02)
            
        time.sleep(0.5)
        # Often Gemini needs the send button clicked or Enter.
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
