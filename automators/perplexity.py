from browser_automator.automators.base import BaseAutomator
from browser_automator.config import PERPLEXITY_URL, PERPLEXITY_SELECTORS
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

class PerplexityAutomator(BaseAutomator):
    def navigate(self):
        print(f"Navigating to {PERPLEXITY_URL}...")
        self.driver.get(PERPLEXITY_URL)
        time.sleep(3) # Initial load wait

    def query(self, text: str):
        # Wait for input area
        input_selector = PERPLEXITY_SELECTORS["input_area"]
        print(f"Waiting for input area: {input_selector}")
        input_el = self.wait_for_element(input_selector)
        
        print("Typing query...")
        input_el.click()
        input_el.clear()
        
        # Type slowly to simulate human behavior
        for char in text:
            input_el.send_keys(char)
            time.sleep(0.05)
        
        time.sleep(0.5)
        input_el.send_keys(Keys.RETURN)
        print("Query submitted.")
        time.sleep(5) # Wait for generation to start

    def select_model(self, model_name: str):
        """
        Selects an AI model from the dropdown (Case-Insensitive).
        Args:
            model_name (str): Partial name of the model (e.g., "gpt", "claude", "sonar").
        """
        print(f"Attempting to select model: {model_name} (Case-Insensitive)")
        try:
            # Click the model menu button
            menu_btn_selector = PERPLEXITY_SELECTORS["model_menu_button"]
            menu_btn = self.wait_for_element(menu_btn_selector)
            menu_btn.click()
            time.sleep(3) # Wait for animation
            
            # Find all menu items
            item_selector = PERPLEXITY_SELECTORS["model_items_all"]
            items = self.driver.find_elements(By.XPATH, item_selector)
            
            target_model = model_name.lower()
            found = False
            
            for item in items:
                # Get text of the item (handling potential nested structure)
                item_text = item.text.lower()
                # Check for match
                if target_model in item_text:
                    print(f"Found matching model: '{item.text}' -> Click")
                    item.click()
                    found = True
                    break
            
            if not found:
                print(f"Model '{model_name}' not found in available options.")
                # Optional: Close menu by clicking background or just ignore
            else:
                time.sleep(1) # Wait for selection to apply
                
        except Exception as e:
            print(f"Failed to select model '{model_name}': {e}")
            print("Creating screenshots for debugging if needed...")

    def enable_deep_research(self):
        """
        Enables Deep Research mode.
        """
        print("Attempting to enable Deep Research...")
        try:
            # OPTION 1: Dynamic Discovery (Best for Pro UI)
            # Find the input container first to narrow down scope
            input_area = self.wait_for_element(PERPLEXITY_SELECTORS["input_area"])
            # Usually the buttons are siblings or parents/cousins. 
            # Let's search document-wide for buttons with "Deep" in aria-label or title
            
            potential_btns = self.driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Deep') or contains(@title, 'Deep')]")
            if potential_btns:
                for btn in potential_btns:
                    if btn.is_displayed():
                        print(f"Found button with 'Deep' label: {btn.get_attribute('aria-label')}")
                        btn.click()
                        print("Deep Research mode ENABLED (via Dynamic Label Search).")
                        time.sleep(1)
                        return

            # OPTION 2: Icon Pattern Matching (Telescope)
            # Look for button containing specific SVG path data or class if we knew it.
            # Since we don't, we'll try the config selector again as a fallback.
            try:
                direct_btn_selector = PERPLEXITY_SELECTORS["mode_deep_research_direct_btn"]
                direct_btn = self.driver.find_element(By.XPATH, direct_btn_selector)
                if direct_btn.is_displayed():
                    direct_btn.click()
                    print("Deep Research mode ENABLED (via Config Selector).")
                    time.sleep(1)
                    return
            except:
                pass

            # OPTION 3: Menu Selection (Standard Interface Fallback)
            print("Direct button not found. Trying Menu...")
            
            # 1. Click the "Search" mode button (usually 'Search' or 'Sonar')
            # We need to find the button that opens the mode menu.
            # It usually has the text of the *current* mode.
            mode_btn_selector = PERPLEXITY_SELECTORS["mode_search_button"]
            try:
                mode_btn = self.driver.find_element(By.XPATH, mode_btn_selector)
                mode_btn.click()
                time.sleep(1)
            except:
                # Try finding any button with a dropdown indicator near input
                print("Could not find standard Search mode button.")
                raise Exception("Search mode button missing")

            # 2. Click "Deep Research" item
            dr_item_selector = PERPLEXITY_SELECTORS["mode_deep_research_item"]
            dr_item = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, dr_item_selector))
            )
            dr_item.click()
            print("Deep Research mode ENABLED (via Menu).")
            time.sleep(1) 

        except Exception as e:
            print(f"Failed to enable Deep Research. Debug Info:")
            print(f"Error: {e}")
            # print_page_source_snippet() # Optional logic to print HTML for debugging

    def extract_response(self) -> str:
        # Wait for generation to likely finish or check for a "searching" indicator
        # For V1, we use a simple sleep and then extract. Refinement: check for specific "stopped" state.
        print("Waiting for response generation...")
        time.sleep(10) # Adjust based on query complexity
        
        soup = self.get_soup()
        # Perplexity responses are usually in a prose container.
        # We need to find the LAST one since conversation history might be present.
        containers = soup.select(PERPLEXITY_SELECTORS["response_container"])
        
        if not containers:
            return ""
        
        # Get the last container which supposedly holds the answer to the latest query
        latest_answer = containers[-1].get_text(separator="\n", strip=True)
        return latest_answer
