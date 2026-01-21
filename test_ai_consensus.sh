#!/bin/bash
# ====================================================
# AI CONSENSUS - 6 AGENT PROMPTS FOR BROWSER AI TEST
# Platform: gemini (or change to perplexity)
# ====================================================

API_KEY="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"
API_URL="http://localhost:1905/query"
PLATFORM="gemini"  # Change to "perplexity" if needed

# Sample stock data for testing
STOCK="VCB"
PRICE="100000"
RSI="65"
MACD="0.5"

echo "======================================================"
echo "Testing AI Consensus 6 Agents with Browser AI ($PLATFORM)"
echo "Stock: $STOCK | Price: $PRICE | RSI: $RSI | MACD: $MACD"
echo "======================================================"

# ====== AGENT 1: PRICING ======
echo ""
echo "=== AGENT 1: PRICING ==="
curl -s -X POST $API_URL \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"platform\": \"$PLATFORM\",
    \"query\": \"PRICING AGENT | Định giá & Vùng vào lệnh. Stock: $STOCK, Price: $PRICE VND, RSI: $RSI, MACD: $MACD. RULES: Entry PHẢI nằm trong Support/Fib61.8/POC zone. Stop loss = dưới support 2-3%. TP1 = kháng cự gần nhất. Không có vùng giá rõ => signal=CHỜ. TRẢ LỜI BẰNG TIẾNG VIỆT. OUTPUT JSON: {m_name:PRICING, signal:MUA|BÁN|CHỜ, score:0-100, rationale:[lý do]}\"
  }"

# ====== AGENT 2: TRADING ======
echo ""
echo ""
echo "=== AGENT 2: TRADING ==="
curl -s -X POST $API_URL \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"platform\": \"$PLATFORM\",
    \"query\": \"TRADING/RISK AGENT | Quản lý rủi ro. Stock: $STOCK, Price: $PRICE VND, RSI: $RSI, MACD: $MACD. RULES: R:R PHẢI > 1:2, nếu không => signal=CHỜ. Position size tối đa 5% portfolio. Bảo toàn vốn > Lợi nhuận. TRẢ LỜI BẰNG TIẾNG VIỆT. OUTPUT JSON: {m_name:TRADING, signal:MUA|BÁN|CHỜ, score:0-100, rationale:[lý do]}\"
  }"

# ====== AGENT 3: TECHNICAL ======
echo ""
echo ""
echo "=== AGENT 3: TECHNICAL ==="
curl -s -X POST $API_URL \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"platform\": \"$PLATFORM\",
    \"query\": \"TECHNICAL AGENT | Phân tích kỹ thuật. Stock: $STOCK, Price: $PRICE VND, RSI: $RSI, MACD: $MACD. RULES: Price>SMA200 + RSI<30 + MACD cắt lên = MUA. Price<SMA200 = CHỈ BÁN/CHỜ. RSI>70 = cảnh báo BÁN. Sideway => signal=CHỜ. TRẢ LỜI BẰNG TIẾNG VIỆT. OUTPUT JSON: {m_name:TECHNICAL, signal:MUA|BÁN|CHỜ, score:0-100, rationale:[lý do]}\"
  }"

# ====== AGENT 4: MACRO ======
echo ""
echo ""
echo "=== AGENT 4: MACRO ==="
curl -s -X POST $API_URL \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"platform\": \"$PLATFORM\",
    \"query\": \"MACRO AGENT | Kinh tế vĩ mô + Quyền VETO. Stock: $STOCK (VN bank). RULES: DXY tăng + Fed hawkish + FII bán ròng => veto=true. VIX>25 => RỦI RO CAO. FII mua ròng + DXY giảm => tích cực. Trung lập => signal=CHỜ. TRẢ LỜI BẰNG TIẾNG VIỆT. OUTPUT JSON: {m_name:MACRO, signal:MUA|BÁN|CHỜ, score:0-100, veto:true|false, rationale:[lý do]}\"
  }"

# ====== AGENT 5: PATTERNS ======
echo ""
echo ""
echo "=== AGENT 5: PATTERNS ==="
curl -s -X POST $API_URL \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"platform\": \"$PLATFORM\",
    \"query\": \"PATTERNS AGENT | Nhận diện mẫu hình. Stock: $STOCK, RSI: $RSI, MACD: $MACD. PATTERNS: Vai đầu vai, Double Top/Bottom, Tam giác, Wedge. RULES: Breakout + Vol xác nhận = Xác nhận. Không có mẫu rõ => signal=CHỜ. TRẢ LỜI BẰNG TIẾNG VIỆT. OUTPUT JSON: {m_name:PATTERNS, signal:MUA|BÁN|CHỜ, score:0-100, pattern:tên_mẫu, rationale:[lý do]}\"
  }"

# ====== AGENT 6: SENTIMENT ======
echo ""
echo ""
echo "=== AGENT 6: SENTIMENT ==="
curl -s -X POST $API_URL \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"platform\": \"$PLATFORM\",
    \"query\": \"SENTIMENT AGENT | Tâm lý thị trường. Stock: $STOCK (VN bank). RULES: Cực kỳ sợ hãi (<25) = cơ hội MUA. Cực kỳ tham lam (>75) = cảnh báo BÁN. Trung lập (40-60) => signal=CHỜ. TRẢ LỜI BẰNG TIẾNG VIỆT. OUTPUT JSON: {m_name:SENTIMENT, signal:MUA|BÁN|CHỜ, score:0-100, fear_greed:cực_sợ|sợ|trung_lập|tham|cực_tham, rationale:[lý do]}\"
  }"

echo ""
echo ""
echo "======================================================"
echo "Test completed!"
echo "======================================================"
