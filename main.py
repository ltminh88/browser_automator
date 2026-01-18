import argparse
import json
import os
import sys
import time

# Allow running this script directly from anywhere
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from browser_automator.drivers.factory import get_driver
from browser_automator.automators.perplexity import PerplexityAutomator
from browser_automator.automators.gemini import GeminiAutomator
from browser_automator.config import DATA_DIR, PERPLEXITY_URL, GEMINI_URL

def save_response(platform, query, response):
    timestamp = int(time.time())
    filename = f"{platform}_response_{timestamp}.json"
    filepath = os.path.join(DATA_DIR, filename)
    
    data = {
        "platform": platform,
        "query": query,
        "response": response,
        "timestamp": timestamp
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Response saved to {filepath}")

def main():
    parser = argparse.ArgumentParser(description="Browser Automation for Perplexity and Gemini")
    parser.add_argument("--platform", choices=["perplexity", "gemini"], help="Target platform (required unless --setup is used)")
    parser.add_argument("--query", help="Query text (required unless --setup is used)")
    parser.add_argument("--model", help="Specific model to use (Perplexity only, e.g. 'GPT', 'Grok')")
    parser.add_argument("--deep-research", action="store_true", help="Enable Deep Research mode (Perplexity only)")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode (default: False for stability)")
    parser.add_argument("--setup", action="store_true", help="Launch browser for manual login and Cloudflare resolution")
    
    args = parser.parse_args()
    
    if args.setup:
        # ... (setup logic remains same) ...
        print("Starting SETUP mode...")
        print("Opening browser. Please manually:")
        print("1. Log in to Google/Gemini.")
        print("2. Solve any Cloudflare CAPTCHAs on Perplexity.")
        print("3. Close the browser window when done.")
        
        driver = get_driver(headless=False)
        try:
            driver.get(PERPLEXITY_URL)
            driver.execute_script(f"window.open('{GEMINI_URL}', '_blank');")
            print("Browser is open. Waiting for you to close it manually (or Ctrl+C)...")
            while True:
                time.sleep(1)
                try:
                    _ = driver.window_handles
                except:
                    print("Browser closed.")
                    break
        except KeyboardInterrupt:
            print("Setup interrupted.")
        finally:
            try:
                driver.quit()
            except:
                pass
        return

    # Auto-infer platform if model or deep-research is specified
    if (args.model or args.deep_research) and not args.platform:
        args.platform = "perplexity"

    if not args.platform or not args.query:
        parser.error("--platform and --query are required unless --setup is used.")
    
    print(f"Starting automation for {args.platform}...")
    
    # Initialize driver
    driver = get_driver(headless=args.headless)
    
    try:
        automator = None
        if args.platform == "perplexity":
            automator = PerplexityAutomator(driver)
            automator.navigate()
            
            if args.deep_research:
                automator.enable_deep_research()
                
            if args.model:
                automator.select_model(args.model)
                
        elif args.platform == "gemini":
            automator = GeminiAutomator(driver)
            automator.navigate()
            
        automator.query(args.query)
        response = automator.extract_response()
        
        print("\n--- RESPONSE ---")
        print(response)
        print("----------------")
        
        if response:
            save_response(args.platform, args.query, response)
        else:
            print("No response extracted.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Closing browser...")
        driver.quit()

if __name__ == "__main__":
    main()
