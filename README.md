# Browser Automator

A Python-based browser automation tool for querying AI platforms (Perplexity, Gemini) via Selenium, with a FastAPI server for remote access.

## Features

- 🤖 **Multi-Platform Support**: Query Perplexity and Gemini
- 🧠 **Model Selection**: Choose from 15+ AI models (GPT, Claude, Grok, etc.)
- 🔬 **Deep Research**: Enable Perplexity's Deep Research mode
- 🌐 **API Server**: Remote access via REST API
- 🔐 **API Key Auth**: Secure your endpoints
- 📦 **JSON Export**: All responses saved to JSON files

## Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/browser_automator.git
cd browser_automator

# Install dependencies
pip install -r requirements.txt
```

## Setup (First Time)

Run setup to login to your accounts:

```bash
python main.py --setup
```

This opens a browser where you can:
1. Login to Perplexity (Pro account for Deep Research)
2. Login to Google/Gemini
3. Close browser when done

Session is saved for future use.

## CLI Usage

```bash
# Query Perplexity
python main.py --query "Your question" --model "gpt-5.2"

# Query Gemini
python main.py --platform gemini --query "Your question"

# Deep Research Mode
python main.py --query "Complex topic" --deep-research
```

## API Server

### Start Server

```bash
export BROWSER_API_KEY="your-secret-key"  # Linux/Mac
# $env:BROWSER_API_KEY = "your-secret-key"  # Windows PowerShell

python -m uvicorn api_server:app --host 0.0.0.0 --port 8000
```

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/models` | List available models |
| POST | `/query` | Query AI platform |
| POST | `/deep-research` | Deep Research mode |

### Example Request

```bash
curl -X POST http://localhost:8000/query \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '{"platform": "perplexity", "query": "Hello", "model": "sonar"}'
```

## Available Models

**Standard**: Sonar, GPT-5.2, Claude Sonnet 4.5, Gemini 3 Flash, Grok 4.1

**Reasoning**: Gemini 3.0 Pro, GPT-5.2 Thinking, Claude Sonnet 4.5 Thinking, Grok 4.1 Thinking

## Project Structure

```
browser_automator/
├── main.py              # CLI entry point
├── api_server.py        # FastAPI server
├── api_config.py        # API configuration
├── config.py            # Platform config & selectors
├── requirements.txt     # Dependencies
├── Dockerfile           # Container deployment
├── automators/
│   ├── base.py          # Base automator class
│   ├── perplexity.py    # Perplexity implementation
│   └── gemini.py        # Gemini implementation
├── drivers/
│   └── factory.py       # Chrome driver factory
└── data/                # Response JSON files
```

## License

MIT
