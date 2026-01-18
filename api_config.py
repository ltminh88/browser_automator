import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_KEY = os.getenv("BROWSER_API_KEY")
HOST = os.getenv("API_HOST", "0.0.0.0")
PORT = int(os.getenv("API_PORT", "8000"))

# Available Models (Perplexity)
AVAILABLE_MODELS = {
    "standard": [
        "Sonar",
        "GPT-5.2",
        "Claude Sonnet 4.5",
        "Gemini 3 Flash",
        "Grok 4.1",
        "Claude Opus 4.5"
    ],
    "reasoning": [
        "Gemini 3.0 Pro",
        "Kimi K2 Thinking",
        "Gemini 3 Flash Thinking",
        "GPT-5.2 Thinking",
        "Claude Sonnet 4.5 Thinking",
        "Claude Opus 4.5 Thinking",
        "Grok 4.1 Thinking"
    ]
}

# Validate API Key on import
if not API_KEY:
    print("WARNING: BROWSER_API_KEY environment variable is not set!")
    print("Set it before starting the server: export BROWSER_API_KEY=your-secret-key")
