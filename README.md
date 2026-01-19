# Browser Automator API

🤖 **API Server tự động hóa trình duyệt để query các AI platform** (Perplexity, Gemini) với đầy đủ tính năng chọn model và Deep Research.

## 📋 Mục lục

- [Tính năng](#-tính-năng)
- [Cài đặt](#-cài-đặt)
- [Thiết lập ban đầu](#-thiết-lập-ban-đầu)
- [Sử dụng CLI](#-sử-dụng-cli)
- [Sử dụng API Server](#-sử-dụng-api-server)
- [API Endpoints](#-api-endpoints)
- [Models hỗ trợ](#-models-hỗ-trợ)
- [Ví dụ thực tế](#-ví-dụ-thực-tế)
- [Cấu trúc dự án](#-cấu-trúc-dự-án)

---

## ✨ Tính năng

| Tính năng | Mô tả |
|-----------|-------|
| 🌐 **Multi-Platform** | Hỗ trợ Perplexity và Google Gemini |
| 🧠 **Model Selection** | Chọn từ 15+ AI models (GPT, Claude, Grok, Gemini...) |
| 🔬 **Deep Research** | Kích hoạt chế độ nghiên cứu sâu của Perplexity |
| 🌍 **REST API** | Gọi từ xa qua HTTP endpoints |
| 🔐 **API Key Auth** | Bảo mật endpoints với API key |
| 📦 **JSON Export** | Lưu tất cả responses thành file JSON |
| 🛡️ **Anti-Detection** | Sử dụng undetected-chromedriver |

---

## 📦 Cài đặt

### Yêu cầu hệ thống
- Python 3.9+
- Google Chrome browser
- Git (optional)

### Bước 1: Clone repository
```bash
git clone https://github.com/ltminh88/browser_automator.git
cd browser_automator
```

### Bước 2: Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### Trên Windows
Double-click `install.bat` để tự động cài đặt.

---

## 🔧 Thiết lập ban đầu

### Đăng nhập tài khoản (Bắt buộc lần đầu)

Chạy lệnh setup để mở browser và đăng nhập:

```bash
python main.py --setup
```

**Trong browser mở ra, hãy:**
1. Đăng nhập vào **Perplexity** (tài khoản Pro để dùng Deep Research)
2. Đăng nhập vào **Google/Gemini**
3. Đóng browser khi hoàn tất

> ⚠️ Session đăng nhập sẽ được lưu lại, không cần đăng nhập lại cho các lần sau.

---

## 💻 Sử dụng CLI

### Cú pháp cơ bản
```bash
python main.py --query "Câu hỏi của bạn" [OPTIONS]
```

### Các tham số

| Tham số | Mô tả | Mặc định |
|---------|-------|----------|
| `--query` | Câu hỏi cần gửi | (bắt buộc) |
| `--platform` | Platform: `perplexity` hoặc `gemini` | `perplexity` |
| `--model` | Chọn AI model cụ thể | Mặc định của platform |
| `--deep-research` | Bật chế độ Deep Research | Tắt |
| `--headless` | Chạy ẩn browser | Tắt |
| `--setup` | Mở browser để đăng nhập | - |

### Ví dụ CLI

```bash
# Query Perplexity với model mặc định
python main.py --query "Thủ đô Việt Nam là gì?"

# Chọn model cụ thể
python main.py --query "Giải thích quantum computing" --model "gpt-5.2"

# Sử dụng model Reasoning
python main.py --query "Giải bài toán khó" --model "gpt-5.2 thinking"

# Deep Research mode
python main.py --query "Phân tích thị trường AI 2025" --deep-research

# Kết hợp Deep Research + Model
python main.py --query "Nghiên cứu về ung thư" --model "claude sonnet" --deep-research

# Query Gemini
python main.py --query "Viết code Python" --platform gemini
```

---

## 🌐 Sử dụng API Server

### Khởi động server

**Trên Mac/Linux:**
```bash
export BROWSER_API_KEY="your-secret-api-key"
python -m uvicorn api_server:app --host 0.0.0.0 --port 8000
```

**Trên Windows (PowerShell):**
```powershell
$env:BROWSER_API_KEY = "your-secret-api-key"
python -m uvicorn api_server:app --host 0.0.0.0 --port 8000
```

**Hoặc dùng file .env:**
```bash
# Tạo file .env
echo 'BROWSER_API_KEY=your-secret-api-key' > .env

# Chạy server
python -m uvicorn api_server:app --host 0.0.0.0 --port 8000
```

### Kiểm tra server đang chạy
```bash
curl http://localhost:8000/health
# {"status": "healthy", "timestamp": 1768751822}
```

---

## 📡 API Endpoints

### `GET /health`
Health check endpoint.

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{"status": "healthy", "timestamp": 1768751822}
```

---

### `GET /models`
Lấy danh sách models có sẵn.

```bash
curl http://localhost:8000/models \
  -H "X-API-Key: your-api-key"
```

**Response:**
```json
{
  "standard": ["Sonar", "GPT-5.2", "Claude Sonnet 4.5", ...],
  "reasoning": ["Gemini 3.0 Pro", "GPT-5.2 Thinking", ...]
}
```

---

### `POST /query`
Gửi query tới Perplexity hoặc Gemini.

**Request:**
```bash
curl -X POST http://localhost:8000/query \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "perplexity",
    "query": "What is AI?",
    "model": "gpt-5.2"
  }'
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `platform` | string | No | `perplexity` (default) hoặc `gemini` |
| `query` | string | Yes | Câu hỏi cần gửi |
| `model` | string | No | Model AI cụ thể |

**Response:**
```json
{
  "success": true,
  "platform": "perplexity",
  "query": "What is AI?",
  "model": "gpt-5.2",
  "response": "AI (Artificial Intelligence) là...",
  "timestamp": 1768748780,
  "file_path": "/path/to/perplexity_response_1768748780.json"
}
```

---

### `POST /deep-research`
Chạy Deep Research trên Perplexity.

**Request:**
```bash
curl -X POST http://localhost:8000/deep-research \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Phân tích chi tiết về thị trường AI 2025",
    "model": "gpt-5.2"
  }'
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | Yes | Chủ đề cần nghiên cứu |
| `model` | string | No | Model AI cụ thể |

> ⚠️ Deep Research yêu cầu tài khoản Perplexity Pro

---

## 🤖 Models hỗ trợ

### Standard Models
| Model | Tên sử dụng | Mô tả |
|-------|-------------|-------|
| Sonar | `sonar` | Default Perplexity model |
| GPT-5.2 | `gpt-5.2` | OpenAI's latest |
| Claude Sonnet 4.5 | `claude sonnet` | Anthropic |
| Claude Opus 4.5 | `claude opus` | Anthropic Pro |
| Gemini 3 Flash | `gemini flash` | Google |
| Grok 4.1 | `grok` | xAI |

### Reasoning Models (Thinking)
| Model | Tên sử dụng | Mô tả |
|-------|-------------|-------|
| Gemini 3.0 Pro | `gemini pro` | Google Reasoning |
| GPT-5.2 Thinking | `gpt-5.2 thinking` | OpenAI Reasoning |
| Claude Sonnet Thinking | `claude sonnet thinking` | Anthropic Reasoning |
| Grok 4.1 Thinking | `grok thinking` | xAI Reasoning |
| Kimi K2 Thinking | `kimi thinking` | Moonshot AI |

> 💡 Model matching là **case-insensitive** và **partial match**. Ví dụ: `gpt` sẽ match với `GPT-5.2`.

---

## 📝 Ví dụ thực tế

### Python Script
```python
import requests

API_URL = "http://localhost:8000"
API_KEY = "your-api-key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Query Perplexity
response = requests.post(
    f"{API_URL}/query",
    headers=headers,
    json={
        "platform": "perplexity",
        "query": "Explain quantum computing",
        "model": "gpt-5.2"
    }
)

result = response.json()
print(result["response"])
```

### JavaScript/Node.js
```javascript
const response = await fetch('http://localhost:8000/query', {
  method: 'POST',
  headers: {
    'X-API-Key': 'your-api-key',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    platform: 'perplexity',
    query: 'What is machine learning?'
  })
});

const data = await response.json();
console.log(data.response);
```

### PowerShell
```powershell
$headers = @{
    "X-API-Key" = "your-api-key"
    "Content-Type" = "application/json"
}
$body = '{"platform":"perplexity","query":"Hello AI"}'

$response = Invoke-RestMethod -Uri "http://localhost:8000/query" `
    -Method POST -Headers $headers -Body $body

Write-Host $response.response
```

---

## 📁 Cấu trúc dự án

```
browser_automator/
├── main.py              # CLI entry point
├── api_server.py        # FastAPI server
├── api_config.py        # API configuration
├── config.py            # Platform selectors
├── requirements.txt     # Dependencies
├── .env.example         # Environment template
├── README.md            # Documentation
│
├── automators/
│   ├── base.py          # Base automator class
│   ├── perplexity.py    # Perplexity implementation
│   └── gemini.py        # Gemini implementation
│
├── drivers/
│   └── factory.py       # Chrome driver factory
│
├── data/                # Response JSON files
│
└── Windows Scripts/
    ├── install.bat
    ├── setup.bat
    ├── start_server.bat
    └── install_service.bat
```

---

## 🔒 Bảo mật

- **API Key**: Đặt qua environment variable `BROWSER_API_KEY`
- **Không commit .env**: File `.env` đã được thêm vào `.gitignore`
- **Chrome Profile**: Session đăng nhập được lưu local, không commit

---

## 🛠️ Troubleshooting

### Lỗi "No module named 'distutils'"
```bash
pip install setuptools
```

### Lỗi Chrome driver
```bash
# Kill tất cả Chrome processes
pkill -9 -f "Google Chrome"
pkill -9 -f "chromedriver"
```

### API trả về 401 Unauthorized
Kiểm tra header `X-API-Key` có đúng không.

### Deep Research không hoạt động
Đảm bảo đã đăng nhập tài khoản Perplexity Pro.

---

## 📄 License

MIT License

---

## 👨‍💻 Author

**ltminh88**

GitHub: [https://github.com/ltminh88/browser_automator](https://github.com/ltminh88/browser_automator)
