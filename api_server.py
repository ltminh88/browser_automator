"""
Browser Automation API Server
FastAPI-based server for remote browser automation.
"""

import asyncio
import threading
import time
import os
import sys
import json
from typing import Optional

# Allow running this script directly
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api_config import API_KEY, AVAILABLE_MODELS
from drivers.factory import get_driver
from automators.perplexity import PerplexityAutomator
from automators.gemini import GeminiAutomator
from config import DATA_DIR

# --- FastAPI App ---
app = FastAPI(
    title="Browser Automation API",
    description="API for querying Perplexity and Gemini via browser automation",
    version="1.0.0"
)

# --- Thread-safe Lock for Sequential Processing ---
# threading.Lock() ensures only ONE browser session runs at a time
browser_lock = threading.Lock()
queue_count = 0  # Track pending requests

# --- Pydantic Models ---
class QueryRequest(BaseModel):
    platform: str = "perplexity"  # "perplexity" or "gemini"
    query: str
    model: Optional[str] = None

class DeepResearchRequest(BaseModel):
    query: str
    model: Optional[str] = None

class QueryResponse(BaseModel):
    success: bool
    platform: str
    query: str
    model: Optional[str] = None
    response: str
    timestamp: int
    file_path: Optional[str] = None
    error: Optional[str] = None

# --- Authentication ---
async def verify_api_key(x_api_key: str = Header(None)):
    if not API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Server API key not configured. Set BROWSER_API_KEY environment variable."
        )
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )
    return x_api_key

# --- Helper Functions ---
def save_response(platform: str, query: str, response: str) -> str:
    """Save response to JSON file and return file path."""
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
    
    return filepath

# --- Global Persistent Browser Session ---
_persistent_driver = None
_request_count = 0
_max_requests_before_refresh = 10  # Refresh browser every N requests

def is_driver_alive():
    """Check if the driver is still functional."""
    global _persistent_driver
    if _persistent_driver is None:
        return False
    try:
        # Try to get current URL - will fail if browser is closed
        _ = _persistent_driver.current_url
        return True
    except Exception:
        return False

def get_persistent_driver():
    """Get or create a persistent browser driver that stays open."""
    global _persistent_driver, _request_count
    
    # Check if we need to refresh driver
    if _request_count >= _max_requests_before_refresh:
        print(f"[Browser] Refreshing browser after {_request_count} requests...")
        close_persistent_driver()
        _request_count = 0
    
    # Check if existing driver is still alive
    if _persistent_driver is not None and not is_driver_alive():
        print("[Browser] Driver is dead, recreating...")
        close_persistent_driver()
    
    if _persistent_driver is None:
        print("[Browser] Creating new persistent browser session...")
        try:
            _persistent_driver = get_driver(headless=False)
        except Exception as e:
            print(f"[Browser] Failed to initialize driver: {e}")
            raise e
    
    return _persistent_driver

def reset_browser():
    """Reset browser to home page for next query."""
    global _persistent_driver
    try:
        if _persistent_driver and is_driver_alive():
            _persistent_driver.get("https://www.perplexity.ai/")
            time.sleep(2)
    except Exception as e:
        print(f"[Browser] Reset failed, recreating driver: {e}")
        close_persistent_driver()
        _persistent_driver = get_driver(headless=False)

def close_persistent_driver():
    """Close the persistent driver (for cleanup)."""
    global _persistent_driver
    if _persistent_driver:
        try:
            _persistent_driver.quit()
        except:
            pass
        _persistent_driver = None

def run_query(platform: str, query: str, model: Optional[str] = None, deep_research: bool = False) -> dict:
    """Execute browser automation query using persistent browser session."""
    global _persistent_driver, _request_count
    
    _request_count += 1
    print(f"[Browser] Request #{_request_count} starting...")
    
    try:
        driver = get_persistent_driver()
        
        if platform == "perplexity":
            # Navigate to fresh page
            driver.get("https://www.perplexity.ai/")
            time.sleep(3)
            
            automator = PerplexityAutomator(driver)
            
            if deep_research:
                automator.enable_deep_research()
                
            if model:
                automator.select_model(model)
                
        elif platform == "gemini":
            driver.get("https://gemini.google.com/")
            time.sleep(3)
            automator = GeminiAutomator(driver)
        else:
            raise ValueError(f"Unknown platform: {platform}")
        
        automator.query(query)
        response = automator.extract_response()
        
        # Save to file
        file_path = save_response(platform, query, response)
        
        return {
            "success": True,
            "platform": platform,
            "query": query,
            "model": model,
            "response": response,
            "timestamp": int(time.time()),
            "file_path": file_path
        }
        
    except Exception as e:
        print(f"[Browser] Query failed: {e}")
        # Try to recover by resetting browser
        try:
            close_persistent_driver()
        except:
            pass
        
        return {
            "success": False,
            "platform": platform,
            "query": query,
            "model": model,
            "response": "",
            "timestamp": int(time.time()),
            "error": str(e)
        }
    # NOTE: We do NOT close the driver here - it stays open for next request

# --- Endpoints ---

@app.get("/health")
async def health_check():
    """Health check endpoint for K8s probes."""
    return {"status": "healthy", "timestamp": int(time.time())}

@app.get("/models")
async def get_models(api_key: str = Depends(verify_api_key)):
    """Get available models for Perplexity."""
    return AVAILABLE_MODELS

@app.post("/query", response_model=QueryResponse)
async def query_ai(request: QueryRequest, api_key: str = Depends(verify_api_key)):
    """
    Send a query to Perplexity or Gemini.
    Requests are processed sequentially using threading.Lock to avoid browser conflicts.
    """
    global queue_count
    queue_count += 1
    position = queue_count
    print(f"[Queue] Request #{position} received: {request.query[:50]}...")
    
    def process_with_lock():
        global queue_count
        with browser_lock:
            print(f"[Queue] Request #{position} - Acquired lock, processing...")
            result = run_query(
                request.platform,
                request.query,
                request.model,
                False  # deep_research
            )
            print(f"[Queue] Request #{position} - Completed, releasing lock")
            queue_count -= 1
            return result
    
    # Run in executor with lock
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, process_with_lock)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
    
    return QueryResponse(**result)

@app.post("/deep-research", response_model=QueryResponse)
async def deep_research(request: DeepResearchRequest, api_key: str = Depends(verify_api_key)):
    """
    Run Deep Research query on Perplexity.
    Automatically enables Deep Research mode.
    Uses threading.Lock to ensure sequential processing.
    """
    global queue_count
    queue_count += 1
    position = queue_count
    print(f"[Queue] Deep Research #{position} received: {request.query[:50]}...")
    
    def process_with_lock():
        global queue_count
        with browser_lock:
            print(f"[Queue] Deep Research #{position} - Acquired lock, processing...")
            result = run_query(
                "perplexity",
                request.query,
                request.model,
                True  # deep_research
            )
            print(f"[Queue] Deep Research #{position} - Completed, releasing lock")
            queue_count -= 1
            return result
    
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, process_with_lock)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
    
    return QueryResponse(**result)

# --- Main Entry Point ---
if __name__ == "__main__":
    import uvicorn
    from api_config import HOST, PORT
    
    if not API_KEY:
        print("ERROR: BROWSER_API_KEY must be set before starting the server.")
        print("Usage: export BROWSER_API_KEY=your-secret-key")
        exit(1)
    
    print(f"Starting Browser Automation API on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
