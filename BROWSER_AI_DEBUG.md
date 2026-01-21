# Browser AI Debug: Prompt Bị Tách Khi Gửi Lên Gemini

## Vấn Đề
Prompt từ VN Stock Signals được gửi đến Browser AI, nhưng khi Browser AI paste vào Gemini chat, prompt bị tách thành nhiều messages riêng biệt, khiến Gemini không hiểu đầy đủ context.

## Screenshot Minh Họa
Từ screenshots user gửi, prompt bị tách như sau:

```
Message 1: "Price>SMA200 + RSI<30 + MACD cắt lên = MUA. 2) Price<SMA200 thì CHỈ BÁN hoặc CHỜ..."
[Gemini dừng câu trả lời]

Message 2: "- Giá: 73.5- RSI: N/A, MACD: N/A"
[Gemini dừng câu trả lời]

Message 3: "- Tín hiệu: BUYĐưa ra khuyến nghị với vùng giá cụ thể."
```

## Full Prompt Được Gửi Từ VN Stock Signals

### 1. System Prompt (PRICING Agent Example)
```
Bạn là PRICING AGENT phân tích định giá và vùng vào lệnh cho cổ phiếu. Xem xét: 1) Entry có nằm trong Support/Fib61.8/POC zone không? 2) Stop loss đặt dưới support 2-3%? 3) TP1 tại kháng cự gần, TP2 tại Fib extension? Nếu không có vùng giá rõ ràng thì signal=CHỜ. CHỈ trả lời JSON: {"m_name":"PRICING", "signal":"MUA/BÁN/CHỜ", "score":0-100, "zones":{"entry":[min,max],"sl":X,"tp":[tp1,tp2]}, "rationale":"lý_do_ngắn_gọn"}
```

### 2. Response Format (appended with space)
```
DATA INPUT: {user_prompt}. OUTPUT JSON SCHEMA v2.0.1 (strict): {"m_name":"AGENT_NAME","signal":"BUY|SELL|WAIT","score":0-100,"veto":false,"zones":{"entry":[min,max],"sl":price,"tp":[tp1,tp2]},"metrics":{},"rationale":["max 2 bullets"]}. CRITICAL RULES: confidence<60=>signal=WAIT, No clear setup=>signal=WAIT, Capital preservation>Profit, JSON ONLY no explanation.
```

### 3. User Prompt (stock data)
```
Phân tích cổ phiếu DPM. Giá: 24.3, RSI: N/A, MACD: N/A, Tín hiệu: BUY. Đưa ra khuyến nghị với vùng giá cụ thể.
```

### 4. Full Combined Prompt (sent to Browser AI)
```python
full_prompt = f"{system_prompt} {user_prompt}"
```

**Kết quả full_prompt (EXPECTED - single line):**
```
Bạn là PRICING AGENT phân tích định giá và vùng vào lệnh cho cổ phiếu. Xem xét: 1) Entry có nằm trong Support/Fib61.8/POC zone không? 2) Stop loss đặt dưới support 2-3%? 3) TP1 tại kháng cự gần, TP2 tại Fib extension? Nếu không có vùng giá rõ ràng thì signal=CHỜ. CHỈ trả lời JSON: {"m_name":"PRICING", "signal":"MUA/BÁN/CHỜ", "score":0-100, "zones":{"entry":[min,max],"sl":X,"tp":[tp1,tp2]}, "rationale":"lý_do_ngắn_gọn"} DATA INPUT: {user_prompt}. OUTPUT JSON SCHEMA v2.0.1 (strict): {"m_name":"AGENT_NAME","signal":"BUY|SELL|WAIT","score":0-100,"veto":false,"zones":{"entry":[min,max],"sl":price,"tp":[tp1,tp2]},"metrics":{},"rationale":["max 2 bullets"]}. CRITICAL RULES: confidence<60=>signal=WAIT, No clear setup=>signal=WAIT, Capital preservation>Profit, JSON ONLY no explanation. Phân tích cổ phiếu DPM. Giá: 24.3, RSI: N/A, MACD: N/A, Tín hiệu: BUY. Đưa ra khuyến nghị với vùng giá cụ thể.
```

## Nguyên Nhân Có Thể

### 1. Ký Tự Gây Line Break
Các ký tự sau có thể gây line break khi paste vào Gemini:
- `:` (colon) - đặc biệt sau label như "Giá:", "RSI:"
- `-` (hyphen/dash) ở đầu dòng
- `{` và `}` (JSON braces)
- Unicode characters tiếng Việt

### 2. Browser Automator Có Thể Xử Lý Sai
- Tách text theo ký tự đặc biệt
- Gửi nhiều request thay vì 1
- Timeout giữa các chunk text

### 3. Gemini UI Có Thể Interpret Newlines
- Gemini có thể interpret một số characters là line break
- Khi paste dài, Gemini tự động split

## Troubleshooting Suggestions

### 1. Log Exact String Browser AI Receives
```python
# Trong Browser AI server, log FULL prompt trước khi paste
print(f"FULL_PROMPT_START>>>")
print(repr(full_prompt))  # repr() shows all escape characters
print(f"<<<FULL_PROMPT_END")
```

### 2. Check For Hidden Newlines
```python
# Check if prompt contains any newlines
if '\n' in full_prompt or '\r' in full_prompt:
    print("WARNING: Prompt contains newlines!")
    full_prompt = full_prompt.replace('\n', ' ').replace('\r', ' ')
```

### 3. Encode All Special Characters
```python
# Remove/replace characters that might cause issues
clean_prompt = full_prompt.replace(':', ': ').replace('-', '- ')
```

### 4. Test With Minimal Prompt
```
Test với prompt đơn giản không có JSON, dấu đặc biệt:
"Phân tích cổ phiếu VCB giá 73 ngàn đồng RSI 75 MACD dương ADX 49. Đưa ra khuyến nghị."
```

### 5. Monitor Browser Console
Kiểm tra browser console logs khi paste để xem có errors hay warnings không.

## Test Commands

### Curl test thành công (single-line, không bị tách):
```bash
curl -X POST http://localhost:1905/query \
  -H "Content-Type: application/json" \
  -d '{"platform": "gemini", "query": "Bạn là PRICING AGENT phân tích định giá. DATA INPUT: Phân tích cổ phiếu DPM Giá 24.3 RSI N/A MACD N/A Tín hiệu BUY. Đưa ra khuyến nghị với vùng giá cụ thể. CHỈ trả lời JSON: {m_name:PRICING, signal:MUA/BÁN/CHỜ, score:0-100, rationale:lý_do}"}'
```

### API Endpoint gọi từ VN Stock Signals:
```
POST http://localhost:1905/query
Headers: X-API-Key: [key]
Body: {
  "platform": "gemini",
  "query": "[full_prompt]"
}
```

## Contact
Khi debug, cần kiểm tra:
1. Exact string được nhận bởi Browser AI `/query` endpoint
2. Exact string được paste vào Gemini input
3. Có sự khác biệt gì giữa 2 cái này không
