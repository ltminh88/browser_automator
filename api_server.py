"""
Browser Automation API Server
FastAPI-based server for remote browser automation.
"""

import asyncio
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

# --- Request Queue for Sequential Processing ---
request_lock = asyncio.Lock()

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

def run_query(platform: str, query: str, model: Optional[str] = None, deep_research: bool = False) -> dict:
    """Execute browser automation query synchronously."""
    driver = None
    try:
        driver = get_driver(headless=False)  # Use visible browser for Mac compatibility
        
        if platform == "perplexity":
            automator = PerplexityAutomator(driver)
            automator.navigate()
            
            if deep_research:
                automator.enable_deep_research()
                
            if model:
                automator.select_model(model)
                
        elif platform == "gemini":
            automator = GeminiAutomator(driver)
            automator.navigate()
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
        return {
            "success": False,
            "platform": platform,
            "query": query,
            "model": model,
            "response": "",
            "timestamp": int(time.time()),
            "error": str(e)
        }
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

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
    Requests are processed sequentially to avoid browser conflicts.
    """
    async with request_lock:
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            run_query,
            request.platform,
            request.query,
            request.model,
            False  # deep_research
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        return QueryResponse(**result)

@app.post("/deep-research", response_model=QueryResponse)
async def deep_research(request: DeepResearchRequest, api_key: str = Depends(verify_api_key)):
    """
    Run Deep Research query on Perplexity.
    Automatically enables Deep Research mode.
    """
    async with request_lock:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            run_query,
            "perplexity",
            request.query,
            request.model,
            True  # deep_research
        )
        
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
