# Changelog

Tất cả các thay đổi đáng chú ý của dự án Browser Automator sẽ được ghi lại trong file này.

---

## [2026-02-16] - Fix API Response bị cắt ngắn

**Ngày giờ:** 2026-02-16 20:30 (GMT+7)

### 🐛 Bug Fix

#### `automators/perplexity.py` — Hàm `extract_response()`

**Vấn đề:** API trả về response bị cắt ngắn (truncated). Hàm `extract_response()` return quá sớm khi text > 50 ký tự mà không kiểm tra AI đã hoàn thành streaming hay chưa.

**Nguyên nhân gốc (dòng 486-491 cũ):**
- `max_wait = 60s` — quá ngắn cho response dài
- Return ngay khi `len(current_text) > 50` sau chỉ 2s chờ thêm
- `stable_count >= 2` (6s) — quá ít để xác nhận AI đã xong
- Không có cơ chế kiểm tra UI completion signals

**Thay đổi chi tiết:**

| Thuộc tính | Trước | Sau |
|------------|-------|-----|
| `max_wait` | 60s | 180s (3 phút) |
| Điều kiện return sớm | `text > 50 chars` → return ngay | Đã xoá hoàn toàn |
| `stable_count` required | 2 polls (6s) | 3 polls (9s) |
| UI signal detection | Không có | JavaScript kiểm tra Copy/Share/Stop buttons |

**Logic mới:**
1. **Copy/Share button xuất hiện** → AI đã xong → return response
2. **Stop button vẫn visible** → AI đang generate → reset stable_count, tiếp tục đợi
3. **Streaming animation detected** (`.animate-pulse`, `.animate-spin`) → tiếp tục đợi
4. **Không detect signal nào** → dùng text stability (3 polls liên tiếp = 9s text không đổi) → return
5. **Timeout 180s** → return text cuối cùng có được

**Số dòng thay đổi:** +181 / -35
