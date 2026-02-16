import os
import sys
import time
import json

# Allow imports from parent directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from automators.base import BaseAutomator
from config import PERPLEXITY_URL, PERPLEXITY_SELECTORS
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class PerplexityAutomator(BaseAutomator):
    def navigate(self):
        print(f"Navigating to {PERPLEXITY_URL}...")
        self.driver.get(PERPLEXITY_URL)
        time.sleep(3) # Initial load wait

    def query(self, text: str):
        """
        Query with retry logic and improved text input.
        Sanitizes text and sends entire string at once to prevent splitting.
        """
        # Sanitize the text - remove newlines and normalize whitespace
        clean_text = text.replace('\n', ' ').replace('\r', ' ')
        clean_text = ' '.join(clean_text.split())  # Normalize multiple spaces
        
        print(f"[Perplexity] Prompt length: {len(clean_text)} chars")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Wait for input area - refind each time to avoid stale reference
                input_selector = PERPLEXITY_SELECTORS["input_area"]
                print(f"Waiting for input area: {input_selector} (attempt {attempt + 1})")
                
                # Wait a bit for page to stabilize after model selection
                time.sleep(2)
                
                # Dismiss any overlays first by pressing Escape
                try:
                    body = self.driver.find_element(By.TAG_NAME, 'body')
                    body.send_keys(Keys.ESCAPE)
                    time.sleep(0.5)
                except:
                    pass
                
                input_el = self.wait_for_element(input_selector)
                
                # Scroll element into view and use JavaScript click to bypass overlays
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", input_el)
                time.sleep(0.5)
                
                print("Inputting query...")
                # Use JavaScript click instead of Selenium click to bypass overlays
                try:
                    self.driver.execute_script("arguments[0].focus();", input_el)
                    self.driver.execute_script("arguments[0].click();", input_el)
                except:
                    input_el.click()
                time.sleep(0.5)
                
                # Clear any existing text
                try:
                    input_el.clear()
                except:
                    pass
                
                # Send entire text at once (NOT char by char) to prevent splitting
                input_el.send_keys(clean_text)
                
                time.sleep(0.5)
                input_el.send_keys(Keys.RETURN)
                print("Query submitted.")
                time.sleep(5)  # Wait for generation to start
                return  # Success - exit the retry loop
                
            except Exception as e:
                print(f"Query attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    print("Retrying...")
                    time.sleep(2)
                else:
                    raise e

    def select_model(self, model_name: str, enable_reasoning: bool = False):
        """
        Selects an AI model from the dropdown (Case-Insensitive).
        Improved with multiple selectors and overlay handling.
        
        Args:
            model_name: Partial name of the model (e.g., "gpt", "claude", "sonar")
            enable_reasoning: Whether to enable "With reasoning" toggle
        """
        print(f"Attempting to select model: {model_name} (Case-Insensitive), reasoning={enable_reasoning}")
        try:
            # First, dismiss any overlays by clicking the body and pressing Escape
            try:
                body = self.driver.find_element(By.TAG_NAME, 'body')
                body.send_keys(Keys.ESCAPE)
                time.sleep(0.5)
            except:
                pass
            
            # Try multiple selectors for the model menu button
            # Based on user's HTML: aria-label shows current model name, icon uses #pplx-icon-cpu
            menu_selectors = [
                # Look for button containing the CPU/chip icon (most specific)
                "button:has(svg use[*|href='#pplx-icon-cpu'])",
                "button:has(use[href='#pplx-icon-cpu'])",
                # Look for button with aria-label containing known model names
                "button[aria-label*='Sonar']",
                "button[aria-label*='Gemini']",
                "button[aria-label*='GPT']",
                "button[aria-label*='Claude']",
                "button[aria-label*='Grok']",
                "button[aria-label*='Kimi']",
                # XPATH for SVG with cpu icon
                "//button[.//use[contains(@href, 'pplx-icon-cpu')]]",
                "//button[.//use[contains(@*[local-name()='href'], 'pplx-icon-cpu')]]",
                # Fallback: original selectors
                "button[aria-label='Choose a model']",
                "button[aria-label='Select model']"
            ]
            
            menu_btn = None
            for selector in menu_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    # Take the first visible element
                    for elem in elements:
                        if elem.is_displayed():
                            menu_btn = elem
                            print(f"Found menu button with selector: {selector}, aria-label: {elem.get_attribute('aria-label')}")
                            break
                    if menu_btn:
                        break
                except Exception as e:
                    continue
            
            if not menu_btn:
                print(f"Could not find model menu button with any selector")
                return
            
            # Scroll to element and click
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", menu_btn)
            time.sleep(0.5)
            menu_btn.click()
            time.sleep(2)  # Wait for menu animation
            
            # Find all menu items - try multiple selectors
            item_selectors = [
                "div[role='menuitem']",
                "[role='menuitem']",
                "//*[@role='menuitem']"
            ]
            
            items = []
            for selector in item_selectors:
                try:
                    if selector.startswith("//"):
                        items = self.driver.find_elements(By.XPATH, selector)
                    else:
                        items = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if items:
                        print(f"Found {len(items)} menu items with selector: {selector}")
                        break
                except:
                    continue
            
            if not items:
                print("No menu items found, closing menu")
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                return
            
            target_model = model_name.lower()
            found = False
            need_thinking = False
            
            # Check if model name contains "Thinking" — Perplexity shows "Thinking" 
            # as a separate menu item, not combined with model names
            if 'thinking' in target_model:
                base_model = target_model.replace('thinking', '').strip()
                need_thinking = True
                print(f"Model '{model_name}' contains 'Thinking' -> will select base model '{base_model}' + click 'Thinking' item")
            else:
                base_model = target_model
            
            # Log all available models for debugging
            print(f"Available models: {[item.text for item in items if item.text.strip()]}")
            
            for item in items:
                item_text = item.text.lower().strip()
                if base_model in item_text or item_text in base_model:
                    # Skip the "Thinking" item itself when looking for base model
                    if item_text == 'thinking':
                        continue
                    print(f"Found matching model: '{item.text}' -> Click")
                    # Scroll to item and click
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
                    time.sleep(0.3)
                    item.click()
                    found = True
                    break
            
            if not found:
                print(f"Model '{model_name}' (base: '{base_model}') not found in available options.")
                self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            else:
                print("Model selected, waiting for page to stabilize...")
                time.sleep(2)
                
                # If model name had "Thinking", click the separate Thinking menu item
                if need_thinking:
                    print("Now selecting 'Thinking' mode from menu...")
                    # Re-find the menu button (old reference may be stale after model selection)
                    reopen_btn = None
                    for selector in menu_selectors:
                        try:
                            if selector.startswith("//"):
                                elements = self.driver.find_elements(By.XPATH, selector)
                            else:
                                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for elem in elements:
                                if elem.is_displayed():
                                    reopen_btn = elem
                                    break
                            if reopen_btn:
                                break
                        except:
                            continue
                    
                    if not reopen_btn:
                        print("Warning: Could not re-find model menu button for Thinking selection")
                        self.toggle_reasoning(enable=True)
                    else:
                        reopen_btn.click()
                        time.sleep(2)
                    
                    # Re-fetch menu items and find "Thinking"
                    thinking_found = False
                    for selector in item_selectors:
                        try:
                            if selector.startswith("//"):
                                items = self.driver.find_elements(By.XPATH, selector)
                            else:
                                items = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            if items:
                                break
                        except:
                            continue
                    
                    re_items = [item.text for item in items if item.text.strip()] if items else []
                    print(f"Re-opened menu items: {re_items}")
                    
                    for item in items:
                        if item.text.lower().strip() == 'thinking':
                            print(f"Found 'Thinking' item -> Click")
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", item)
                            time.sleep(0.3)
                            item.click()
                            thinking_found = True
                            break
                    
                    if not thinking_found:
                        print("Warning: 'Thinking' item not found in menu, trying toggle_reasoning fallback")
                        self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                        time.sleep(0.5)
                        self.toggle_reasoning(enable=True)
                    else:
                        print("Thinking mode selected, waiting for page to stabilize...")
                        time.sleep(2)
                
                # Toggle reasoning if requested (and not already handled by Thinking)
                elif enable_reasoning:
                    self.toggle_reasoning(enable=True)
                
        except Exception as e:
            print(f"Failed to select model '{model_name}': {e}")

    def toggle_reasoning(self, enable: bool = True):
        """
        Toggles the 'With reasoning' option.
        The reasoning toggle appears as a menu item that can be clicked.
        """
        print(f"Toggling reasoning mode: {'ON' if enable else 'OFF'}")
        try:
            # The "With reasoning" option appears as a menu item or a toggle switch
            # First, try to find it as a menu item with text "reasoning"
            toggle_selectors = [
                # Menu item with "reasoning" text
                "//div[@role='menuitem'][contains(., 'reasoning')]",
                "//*[contains(@class, 'menuitem')][contains(., 'reasoning')]",
                "//div[contains(text(), 'reasoning')]",
                "//span[contains(text(), 'reasoning')]",
                # Switch role elements
                "[role='switch']",
                "button[role='switch']",
                # Input checkbox
                "input[type='checkbox']"
            ]
            
            toggle = None
            for selector in toggle_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for elem in elements:
                        if elem.is_displayed():
                            elem_text = elem.text.lower() if elem.text else ""
                            # Check if element or its text contains "reasoning"
                            if 'reasoning' in elem_text:
                                toggle = elem
                                print(f"Found reasoning toggle: '{elem.text}' with selector: {selector}")
                                break
                            # For switch elements, check parent text
                            if selector in ["[role='switch']", "button[role='switch']", "input[type='checkbox']"]:
                                parent_text = self.driver.execute_script(
                                    "return arguments[0].closest('div')?.textContent || '';", 
                                    elem
                                )
                                if 'reasoning' in parent_text.lower():
                                    toggle = elem
                                    print(f"Found reasoning switch in parent with selector: {selector}")
                                    break
                    if toggle:
                        break
                except Exception as e:
                    continue
            
            if not toggle:
                print("Could not find reasoning toggle")
                return
            
            # For menu items, just click to toggle
            # For switches, check state first
            is_switch = toggle.get_attribute("role") == "switch" or toggle.tag_name == "input"
            
            if is_switch:
                current_state = toggle.get_attribute("aria-checked") == "true" or \
                               toggle.get_attribute("data-state") == "checked" or \
                               toggle.get_attribute("checked") is not None
                
                if enable and not current_state:
                    print("Enabling reasoning...")
                    toggle.click()
                    time.sleep(1)
                elif not enable and current_state:
                    print("Disabling reasoning...")
                    toggle.click()
                    time.sleep(1)
                else:
                    print(f"Reasoning already {'enabled' if enable else 'disabled'}")
            else:
                # It's a menu item - click to toggle
                if enable:
                    print("Clicking reasoning menu item...")
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", toggle)
                    time.sleep(0.3)
                    toggle.click()
                    time.sleep(1)
                
        except Exception as e:
            print(f"Failed to toggle reasoning: {e}")

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
        """
        Extract the response from Perplexity.
        Waits for generation to complete using multiple signals:
        1. UI completion indicators (Copy/Share buttons, Stop button gone)
        2. Text content stability over multiple consecutive polls
        3. Follow-up input area appearing
        """
        print("Waiting for response generation...")
        
        max_wait = 180  # 3 minutes max for long responses
        poll_interval = 3
        waited = 0
        last_text = ""
        stable_count = 0
        required_stable = 3  # Need 3 consecutive stable polls (9s of no change)
        
        while waited < max_wait:
            time.sleep(poll_interval)
            waited += poll_interval
            
            # Check for UI completion signals via JavaScript
            try:
                completion_signals = self.driver.execute_script("""
                    var result = {isGenerating: false, hasCopyBtn: false, hasShareBtn: false};
                    
                    // Stop button visible = still generating
                    var stopBtns = document.querySelectorAll('button[aria-label="Stop"], button[aria-label="Cancel"]');
                    for (var i = 0; i < stopBtns.length; i++) {
                        if (stopBtns[i].offsetParent !== null) {
                            result.isGenerating = true;
                            break;
                        }
                    }
                    
                    // Streaming animation/cursor = still generating
                    var cursors = document.querySelectorAll('.animate-pulse, .streaming-cursor, [class*="cursor"][class*="blink"], .animate-spin');
                    for (var i = 0; i < cursors.length; i++) {
                        if (cursors[i].offsetParent !== null) {
                            result.isGenerating = true;
                            break;
                        }
                    }
                    
                    // Copy button visible = generation complete
                    var copyBtns = document.querySelectorAll('button[aria-label="Copy"], button[aria-label="Copy Answer"], button[aria-label="Copy to clipboard"]');
                    for (var i = 0; i < copyBtns.length; i++) {
                        if (copyBtns[i].offsetParent !== null) {
                            result.hasCopyBtn = true;
                            break;
                        }
                    }
                    
                    // Share button visible = generation complete
                    var shareBtns = document.querySelectorAll('button[aria-label="Share"], button[aria-label="Share Answer"]');
                    for (var i = 0; i < shareBtns.length; i++) {
                        if (shareBtns[i].offsetParent !== null) {
                            result.hasShareBtn = true;
                            break;
                        }
                    }
                    
                    return result;
                """)
            except Exception as e:
                print(f"JS completion check failed: {e}")
                completion_signals = {"isGenerating": True, "hasCopyBtn": False, "hasShareBtn": False}
            
            # Extract current text
            soup = self.get_soup()
            containers = soup.select(PERPLEXITY_SELECTORS["response_container"])
            
            if not containers:
                print(f"Waiting for response containers... ({waited}s/{max_wait}s)")
                continue
            
            current_text = containers[-1].get_text(separator="\n", strip=True)
            
            if not current_text:
                print(f"Empty response, waiting... ({waited}s/{max_wait}s)")
                continue
            
            text_len = len(current_text)
            is_generating = completion_signals.get("isGenerating", False)
            has_copy = completion_signals.get("hasCopyBtn", False)
            has_share = completion_signals.get("hasShareBtn", False)
            
            # Strong completion signal: Copy or Share button appeared
            if (has_copy or has_share) and text_len > 50:
                print(f"UI completion signal detected (copy={has_copy}, share={has_share}) at {waited}s, {text_len} chars")
                # Final re-fetch for most up-to-date content
                time.sleep(1)
                soup = self.get_soup()
                containers = soup.select(PERPLEXITY_SELECTORS["response_container"])
                if containers:
                    final_text = containers[-1].get_text(separator="\n", strip=True)
                    print(f"Returning response: {len(final_text)} chars")
                    return final_text
                return current_text
            
            # Stop button present = definitely still generating, reset stability
            if is_generating:
                print(f"Still generating... ({waited}s, {text_len} chars)")
                last_text = current_text
                stable_count = 0
                continue
            
            # Text stability check (fallback when UI signals aren't detected)
            if current_text == last_text:
                stable_count += 1
                if stable_count >= required_stable and text_len > 50:
                    print(f"Response stabilized after {waited}s ({text_len} chars, {stable_count} stable polls)")
                    return current_text
                else:
                    print(f"Text stable ({stable_count}/{required_stable})... ({waited}s, {text_len} chars)")
            else:
                stable_count = 0
                last_text = current_text
                print(f"Text still changing... ({waited}s, {text_len} chars)")
        
        # Final attempt after max wait
        print(f"Max wait reached ({max_wait}s), extracting final response...")
        soup = self.get_soup()
        containers = soup.select(PERPLEXITY_SELECTORS["response_container"])
        
        if not containers:
            print("No response containers found")
            return ""
        
        latest_answer = containers[-1].get_text(separator="\n", strip=True)
        print(f"Final response: {len(latest_answer)} chars")
        return latest_answer
