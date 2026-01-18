# Windows Deployment Guide

## Quick Start (5 phút)

### 1. Clone Repository
```powershell
git clone https://github.com/ltminh88/browser_automator.git
cd browser_automator
```

### 2. Cài đặt
Double-click `install.bat` hoặc chạy:
```powershell
.\install.bat
```

### 3. Đăng nhập tài khoản
Double-click `setup.bat` để mở browser và đăng nhập:
- Perplexity (tài khoản Pro để dùng Deep Research)
- Google/Gemini

### 4. Cấu hình API Key
Tạo file `.env` từ template:
```powershell
copy .env.example .env
notepad .env
```

Sửa file `.env`:
```
BROWSER_API_KEY=your-secret-api-key-here
API_HOST=0.0.0.0
API_PORT=8000
```

### 5. Khởi động Server
Double-click `start_server.bat` hoặc:
```powershell
.\start_server.bat
```

---

## Chạy như Windows Service (Auto-start)

### Yêu cầu
Download NSSM từ: https://nssm.cc/download
Copy `nssm.exe` vào `C:\Windows\System32`

### Cài đặt Service
Chạy **với quyền Administrator**:
```powershell
.\install_service.bat
```

### Quản lý Service
```powershell
# Xem trạng thái
nssm status BrowserAutomatorAPI

# Dừng service
nssm stop BrowserAutomatorAPI

# Khởi động lại
nssm restart BrowserAutomatorAPI

# Gỡ cài đặt
nssm remove BrowserAutomatorAPI confirm
```

---

## Mở Firewall (để truy cập từ xa)

```powershell
# Chạy PowerShell với quyền Admin
New-NetFirewallRule -DisplayName "Browser Automator API" -Direction Inbound -Port 8000 -Protocol TCP -Action Allow
```

---

## Test API

```powershell
# Health Check
Invoke-RestMethod -Uri "http://localhost:8000/health"

# Query với API Key
$headers = @{ "X-API-Key" = "your-secret-key"; "Content-Type" = "application/json" }
$body = '{"platform": "perplexity", "query": "Hello"}'
Invoke-RestMethod -Uri "http://localhost:8000/query" -Method POST -Headers $headers -Body $body
```

---

## Files

| File | Mô tả |
|------|-------|
| `install.bat` | Cài đặt dependencies |
| `setup.bat` | Đăng nhập Perplexity/Gemini |
| `start_server.bat` | Khởi động API server |
| `install_service.bat` | Cài đặt như Windows Service |
| `.env` | Cấu hình API Key và Port |
