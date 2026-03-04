# CLAUDE.md - Browser Automator

> 📌 **Context file for AI assistants** - Đọc file này trước khi làm việc với project.
>
> ⚠️ **BẮT BUỘC**: Trước khi thực hiện bất kỳ thay đổi code nào, hãy đọc [`STATE_MACHINES.md`](STATE_MACHINES.md) để hiểu flow và trạng thái của từng component. Mọi thay đổi phải tuân theo state machine tương ứng.

## State Machines (Tham chiếu bắt buộc)

File [`STATE_MACHINES.md`](STATE_MACHINES.md) mô tả 7 state machines cho toàn bộ hệ thống:

| # | State Machine | File liên quan | Khi nào cần đọc |
|---|---------------|----------------|-----------------|
| 1 | Browser Driver Lifecycle | `api_server.py`, `drivers/factory.py` | Sửa driver init, health check, retry logic |
| 2 | Request Pipeline | `api_server.py` | Sửa API endpoints, auth, lock, error handling |
| 3 | Perplexity Query Flow | `automators/perplexity.py` | Sửa navigate, query, submit |
| 4 | Gemini Query Flow | `automators/gemini.py` | Sửa Gemini login, query, text injection |
| 5 | Response Extraction | `automators/perplexity.py` | Sửa polling logic, completion detection |
| 6 | Model Selection | `automators/perplexity.py` | Sửa model menu, thinking toggle |
| 7 | Deep Research | `automators/perplexity.py` | Sửa deep research activation |

**Quy tắc**: Khi thay đổi code trong bất kỳ file nào ở cột "File liên quan", phải kiểm tra state machine tương ứng để đảm bảo transition logic vẫn đúng. Nếu thay đổi làm thay đổi state/transition, phải cập nhật `STATE_MACHINES.md` cùng lúc.

## Project Status
- **Current state**: Production (v1.1.0 - Container)
- **Last updated**: 2026-03-04
- **Primary use**: Backend AI query engine cho VN Stock Signals
- **Deployment**: Docker container trên server 172.104.44.51:8000
- **Branch**: `container` (production), `main` (local dev)

---

## Current Work (Đang làm dở)

### 🔴 HIGH PRIORITY - Prompt Splitting Bug
- [ ] **Prompt bị tách khi paste vào Gemini** - 80% done
  - **Vấn đề**: Khi VN Stock Signals gửi prompt dài, Browser AI paste vào Gemini bị tách thành nhiều messages
  - **Đã làm**: 
    - ✅ Sanitize newlines trong `gemini.py` và `perplexity.py` (lines 46-48)
    - ✅ Document troubleshooting trong `BROWSER_AI_DEBUG.md`
    - ✅ JavaScript injection method để bypass character-by-character issues
  - **Còn thiếu**:
    - [ ] Test với prompt cực dài (>2000 chars)
    - [ ] Handle các ký tự Unicode đặc biệt (tiếng Việt có dấu)
    - [ ] Escape JSON braces `{`, `}` có thể gây issues

### 🟡 MEDIUM PRIORITY
- [ ] Model selection không ổn định - selectors có thể break khi Perplexity update UI
- [ ] Deep Research timeout khi query phức tạp

---

## Known Issues & Bugs

### 1. **Prompt Splitting** (Critical)
   - **Mô tả**: Prompt dài bị tách thành nhiều messages khi paste vào Gemini
   - **Root cause**: Ký tự đặc biệt (`:`, `-`, `{`, `}`) hoặc newlines trong prompt
   - **Workaround**: Đã thêm sanitization trong `query()` method
   - **File**: `automators/gemini.py:46-48`, `automators/perplexity.py:30-32`

### 2. **Model Menu Selector Fragile**
   - **Mô tả**: Perplexity thay đổi UI, selector cho model menu có thể outdated
   - **Root cause**: CSS selectors cứng, không dynamic
   - **Workaround**: Đã thêm multiple fallback selectors trong `select_model()`
   - **File**: `automators/perplexity.py:113-129`

### 3. **Chrome Profile Lock**
   - **Mô tả**: Chrome báo lỗi "Address already in use" nếu có session cũ
   - **Root cause**: Lock files không được cleanup
   - **Workaround**: Gọi `cleanup_profile_locks()` khi startup
   - **File**: `api_server.py:173-192`

### 4. **Syntax Error in perplexity.py**
   - **Mô tả**: Duplicate `except` block trong `toggle_reasoning()` method
   - **File**: `automators/perplexity.py:305-306` - duplicate of line 302
   - **Fix cần làm**: Xóa lines 305-306

---

## Technical Decisions

| Quyết định | Lý do |
|------------|-------|
| `undetected-chromedriver` | Bypass Cloudflare và các detection mechanisms |
| `FastAPI` | Async support, auto-generated docs, dễ integrate với VN Stock Signals |
| `BeautifulSoup` | Parse HTML response từ AI platforms |
| `threading.Lock()` | Serialize browser requests, tránh race conditions |
| Persistent browser session | Giữ login state, giảm thời gian khởi động mỗi request |
| JavaScript injection cho text input | Bypass character-by-character typing issues |
| Chrome Profile directory | Lưu login cookies, không cần login lại |

---

## Development Commands

```bash
# === SETUP (First time) ===
# Mở browser để login manual vào Perplexity/Gemini
python main.py --setup

# === CLI MODE ===
# Query Perplexity
python main.py --query "Thủ đô Việt Nam là gì?"

# Query với model cụ thể
python main.py --query "Giải thích AI" --model "gpt-5.2"

# Query với Deep Research
python main.py --query "Phân tích thị trường" --deep-research

# Query Gemini
python main.py --query "Viết code Python" --platform gemini

# === API SERVER ===
# Start server (Mac/Linux)
export BROWSER_API_KEY="your-secret-key"
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload

# Start server (Windows)
set BROWSER_API_KEY=your-secret-key
python -m uvicorn api_server:app --host 0.0.0.0 --port 1905

# === TESTING ===
# Health check
curl http://localhost:8000/health

# Test query
curl -X POST http://localhost:8000/query \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"platform": "gemini", "query": "Hello"}'

# === CLEANUP ===
# Kill zombie Chrome processes (Mac)
pkill -9 -f "Google Chrome"
pkill -9 -f "chromedriver"

# Kill zombie Chrome processes (Windows)
taskkill /F /IM chrome.exe
taskkill /F /IM chromedriver.exe
```

---

## Code Conventions

### Logging Format
```python
print(f"[Platform] Action: {details}")  # e.g., [Gemini] Prompt length: 500 chars
print(f"Waiting for {element}...")
print(f"Error: {exception_message}")
```

### Error Handling Pattern
```python
try:
    # Primary method
    do_action()
except Exception as e:
    print(f"Action failed: {e}")
    # Fallback method
    do_fallback_action()
```

### Selector Pattern (Multi-fallback)
```python
selectors = [
    "primary_selector",
    "fallback_selector_1",
    "//xpath/fallback"
]

for selector in selectors:
    try:
        element = find_element(selector)
        if element.is_displayed():
            break
    except:
        continue
```

### Text Sanitization (Required for all user input)
```python
clean_text = text.replace('\n', ' ').replace('\r', ' ')
clean_text = ' '.join(clean_text.split())  # Normalize whitespace
```

### Naming Conventions
- Files: `snake_case.py`
- Classes: `PascalCase` (e.g., `PerplexityAutomator`)
- Functions: `snake_case` (e.g., `extract_response`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `PERPLEXITY_SELECTORS`)

---

## Project Structure

```
browser_automator/
├── main.py              # CLI entry point
├── api_server.py        # FastAPI server (main integration point)
├── api_config.py        # HOST, PORT, API_KEY config
├── config.py            # Platform URLs and CSS selectors
│
├── automators/
│   ├── base.py          # BaseAutomator class với shared methods
│   ├── perplexity.py    # Perplexity implementation (model selection, deep research)
│   └── gemini.py        # Gemini implementation
│
├── drivers/
│   └── factory.py       # undetected-chromedriver factory
│
├── chrome_profile/      # Saved login sessions (gitignored)
├── data/                # Response JSON files
│
├── CLAUDE.md            # This file - AI context
├── BROWSER_AI_DEBUG.md  # Debug guide for prompt splitting
├── README.md            # User documentation
└── WINDOWS_DEPLOY.md    # Windows deployment guide
```

---

## Roadmap / Next Features

### High Priority
1. **Fix prompt splitting completely** 
   - Add character escaping for JSON braces
   - Test với VN Stock Signals AI Consensus
   
2. **Better error recovery**
   - Auto-retry khi browser crash
   - Graceful handling khi session hết hạn

### Medium Priority
3. **Add Grok support**
   - x.com/grok integration
   
4. **Response streaming**
   - Return partial responses thay vì đợi complete

5. **Queue system**
   - Replace simple Lock với proper queue
   - Priority levels cho requests

### Nice to Have
6. **Docker deployment** ✅ DONE
   - Containerize với headless Chrome + Xvfb + tini + noVNC
   - Deploy trên server 172.104.44.51

7. **Multiple browser instances**
   - Pool of browsers cho parallel queries

---

## Important Notes

### ⚠️ CRITICAL
1. **Cần login manual lần đầu** - Chạy `python main.py --setup` và login vào Perplexity + Gemini
2. **Selectors có thể break** - Khi Perplexity/Gemini update UI, cần update `config.py`
3. **Chỉ 1 request tại 1 thời điểm** - `threading.Lock()` đảm bảo sequential processing
4. **Chrome profile quan trọng** - Không xóa `chrome_profile/` nếu không muốn login lại

### 📝 DEBUG TIPS
1. Xem `BROWSER_AI_DEBUG.md` cho prompt splitting issues
2. Chạy với `--headless=False` (default) để xem browser hoạt động
3. Log file: `browser_ai.log` (auto-created)
4. Response saved: `data/perplexity_response_*.json` hoặc `data/gemini_response_*.json`

### 🔗 INTEGRATION với VN Stock Signals
- VN Stock Signals gọi endpoint: `POST http://localhost:1905/query`
- Header: `X-API-Key: {BROWSER_API_KEY}`
- Body: `{"platform": "gemini", "query": "full_prompt_here"}`
- Used by: `openrouter_client.py` khi AI fallback sang Browser AI

---

## Environment Variables

```bash
# Required
BROWSER_API_KEY=your-secret-api-key  # Authentication cho API

# Optional  
CHROME_PATH=/path/to/chrome          # Custom Chrome binary
HEADLESS=false                       # Run headless (not recommended)
```

---

## API Endpoints Summary

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/health` | GET | No | Health check |
| `/models` | GET | Yes | List available models |
| `/query` | POST | Yes | Send query to Perplexity/Gemini |
| `/deep-research` | POST | Yes | Perplexity Deep Research mode |

---

## Changelog

### v1.0.0 (2026-01-27)
- Initial production release
- Multi-platform support (Perplexity + Gemini)
- Model selection với 15+ AI models
- Deep Research mode
- API server với authentication
- Persistent browser session

---

*Last updated: 2026-01-27 by AI Assistant*
