# Oddspark Performance Testing Report

**Date:** 05/03/2026 - 06/03/2026

**Environment:** AWS EC2 Staging (Bare-metal load testing)

**System:** Laravel Octane/Swoole behind Nginx

**Constraint:** Chỉ thay đổi config (nginx, octane, supervisor, sysctl) - KHÔNG sửa code

---

## 1. Infrastructure

| Component | Detail |
|-----------|--------|
| Bastion | 54.64.106.44 (ubuntu) - chạy JMeter |
| Instance 228 | 10.1.4.228 - 2 vCPU, 3.8GB RAM - Active in ALB |
| Instance 235 | 10.1.3.235 - 2 vCPU, 3.8GB RAM - Active in ALB |
| Load Tool | Apache JMeter 5.6.3 trên Bastion |
| Test Plan | `StrikerKeirin_performance-bk1215.jmx` |
| App Stack | PHP 8.2 + Swoole 5.1.1 + Nginx + Supervisor |
| EBS | gp3, 6000 IOPS (upgraded từ default 3000) |

---

## 2. Chiến thuật Test

### 2.1 Phương pháp

- **Monitoring**: Song song khi JMeter chạy, thu thập metrics trên từng instance mỗi 30 giây, tổng cộng **10 rounds** (tổng ~5 phút monitoring)
- **Progressive tuning**: Sau mỗi lần test → phân tích bottleneck → apply config fix → test lại → so sánh kết quả
- **Bare-metal testing**: Test trực tiếp trên EC2 instances để kiểm soát hoàn toàn config OS/nginx/octane

### 2.2 Kịch bản JMeter chi tiết

#### Test Plan: `StrikerKeirin_performance-bk1215.jmx`

File JMX mô phỏng traffic thực tế của hệ thống Oddspark, bao gồm **9 UltimateThreadGroup** (enabled) chạy song song, chia theo loại cược và hành vi người dùng:

| ThreadGroup | Threads | Start Delay | Ramp-up | Hold | Shutdown | Mô tả |
|-------------|---------|-------------|---------|------|----------|-------|
| 競馬＿投票 (Keiba Vote) | 20 | 0s | 180s | 600s | 180s | Đặt cược đua ngựa |
| 競馬＿情報 (Keiba Info) | 20 | 0s | 180s | 600s | 180s | Xem thông tin đua ngựa |
| 競輪＿投票 (Keirin Vote) | **1,500** | 0s | 180s | 600s | 180s | Đặt cược đua xe đạp |
| 競輪＿情報 (Keirin Info) | **2,500** | 0s | 180s | 600s | 180s | Xem thông tin đua xe đạp |
| オートレース＿投票 (Auto Vote) | 20 | 0s | 180s | 600s | 180s | Đặt cược đua ô tô |
| オートレース＿情報 (Auto Info) | 20 | 0s | 180s | 600s | 180s | Xem thông tin đua ô tô |
| LOTO＿投票 (Loto Vote) | 10 | 0s | 180s | 600s | 180s | Đặt cược Loto |
| LOTO＿情報 (Loto Info) | 10 | 0s | 180s | 600s | 180s | Xem thông tin Loto |
| 共通起動時 (Common Startup) | 10 | 0s | 180s | 600s | 180s | Common APIs (version check, etc.) |

**Tổng max concurrent threads: ~4,110 users**

#### Load Profile Timeline

```
Phase 1 - Ramp-up (0 → 180s = 3 phút):
  Tăng dần từ 0 → 4,110 concurrent threads trong 180 giây
  (~23 threads/giây được thêm vào)

Phase 2 - Steady State (180s → 780s = 10 phút):
  Giữ nguyên 4,110 concurrent threads trong 600 giây
  Mỗi thread lặp vô hạn (loops=-1), gửi requests liên tục

Phase 3 - Ramp-down (780s → 960s = 3 phút):
  Giảm dần từ 4,110 → 0 threads trong 180 giây

Tổng thời gian test: ~16 phút
```

```
Threads
4110 |          ┌──────────────────────┐
     |         /                        \
     |        /                          \
     |       /     Steady State           \
     |      /      (600s = 10 min)         \
     |     /                                \
   0 |____/                                  \____
     0   180s                          780s    960s
         Ramp-up                       Ramp-down
         (3 min)                       (3 min)
```

#### Phân bố traffic theo module (tính theo threads)

```
競輪 (Keirin/Đua xe đạp):  4,000 threads (97.3%) ← chiếm đa số
  - Info: 2,500 threads (60.8%)
  - Vote: 1,500 threads (36.5%)

競馬 (Keiba/Đua ngựa):       40 threads (1.0%)
オートレース (Auto Racing):    40 threads (1.0%)
LOTO:                         20 threads (0.5%)
共通 (Common):                10 threads (0.2%)
```

#### User Agent & Data-driven

- Mỗi ThreadGroup sử dụng CSV data files (`data/ua_vote_15.csv`, `data/ua_info_15.csv`) chứa User-Agent strings cho APP/SP/PC
- Traffic được phân bổ theo weight: `weight_APP`, `weight_SP`, `weight_PC` → mô phỏng tỷ lệ mobile app / smartphone web / desktop
- ThroughputController điều khiển % request theo từng platform

#### AutoStop (DISABLED)

```
AutoStop config: Error rate > 50% kéo dài 60 giây → dừng test
Status: DISABLED (enabled="false")
```
→ Test chạy hết 16 phút bất kể error rate bao nhiêu.

#### JMeter Launch Command

```bash
/opt/apache-jmeter-5.6.3/bin/jmeter -n \
  -t StrikerKeirin_performance-bk1215.jmx \
  -JHOST=api.sp.st.oddspark.com \
  -JPORT=8000 \
  -Jprefix=/app/api \
  -Jtimeband=15 \
  -l result/jmeter_results.jtl \
  -j jmeter.log
```

| Param | Value | Mô tả |
|-------|-------|-------|
| HOST | api.sp.st.oddspark.com | Target host |
| PORT | 8000 | Octane port đặt trong cùng ALB của stg listen port 8000 |
| prefix | /app/api | URL prefix cho tất cả API calls |
| timeband | 15 | Chọn CSV data file theo timeband |


### 2.3 Monitoring Metrics (10 rounds × 30 giây = 5 phút)

Trong khi JMeter chạy, thu thập đồng thời trên mỗi instance:

| Metric | Command | Mô tả |
|--------|---------|-------|
| CPU | `top -bn1` | user%, sys%, iowait%, idle% |
| RAM | `free -m` | total, used, free, available |
| Connections | `ss -s` | ESTABLISHED, CLOSE_WAIT, TIME_WAIT |
| File Descriptors | `ls /proc/<pid>/fd \| wc -l` | FD count cho nginx & octane processes |
| Nginx status | `curl localhost/nginx_status` | Active connections, requests/sec |
| Octane logs | `tail /var/log/octane-error.log` | Error messages |

Monitoring chạy **10 rounds**, mỗi round cách nhau **30 giây**, bắt đầu cùng lúc với JMeter. Tổng thời gian monitoring ~5 phút, rơi vào **giai đoạn ramp-up + đầu steady state** của JMeter (khi load tăng dần tới peak).

---

## 3. Những vấn đề phát hiện

### 3.1 Kiến trúc Request Flow

```
JMeter (Bastion) → EC2 Nginx(:80) → Octane/Swoole(:8000) → OPCrawler → NAT Gateway → Akamai → On-Premise DC
                                                                  ↑
                                                         Blocking I/O scraping
                                                         (crawl HTML từ sp.st.oddspark.com)
```

- Request từ user đi qua Nginx reverse proxy → Octane xử lý PHP logic
- Một số API endpoints trigger **OPCrawler** — module crawl HTML từ `sp.st.oddspark.com`
- OPCrawler gửi HTTP request qua **NAT Gateway → Internet → Akamai CDN → On-Premise datacenter**
- Đây là operation **blocking I/O** — worker bị block cho tới khi nhận response (~200-500ms)

### 3.2 Root Cause Chain (theo thứ tự phát hiện)

| # | Bottleneck | Triệu chứng | Severity |
|---|-----------|-------------|----------|
| 1 | **EBS IOPS thiếu** | 85% CPU iowait, server gần như đứng | Critical - FIXED |
| 2 | **Quá nhiều workers (32)** | RAM 97% (3.7/3.8GB), OOM risk | Critical - FIXED |
| 3 | **Nginx worker_connections thấp** | Từ chối connection khi >20K concurrent | High - FIXED |
| 4 | **File descriptor exhaustion** | "Too many open files" (Error 23), server crash | Critical - FIXED |
| 5 | **CLOSE_WAIT connection leak** | 37,485 leaked sockets, FD 99.6% | Critical - CẦN FIX CODE |
| 6 | **OPCrawler blocking I/O** | CPU idle giữa các I/O wait, chỉ spike không đều | Medium - CẦN FIX CODE |

### 3.3 CLOSE_WAIT Connection Leak - Root Cause Analysis

**CLOSE_WAIT** là trạng thái TCP socket khi remote server đã đóng connection (gửi FIN), nhưng local application **chưa gọi close()** để giải phóng socket.

```
Normal flow:
  App → send request → receive response → close() → socket released → FD freed

OPCrawler bug:
  App → send request → receive response → [KHÔNG close()] → socket stuck CLOSE_WAIT → FD leaked forever
```

**Chi tiết:**
- OPCrawler nhận response từ sp.st.oddspark.com nhưng KHÔNG gọi `close()` trên socket
- Remote server (sp.st.oddspark.com) timeout và đóng connection → gửi FIN → local socket chuyển sang CLOSE_WAIT
- Local app không bao giờ close → socket bị giữ vĩnh viễn cho tới khi process restart
- Mỗi leaked connection = 1 file descriptor + ~20KB kernel memory
- Tích lũy theo thời gian: Peak **37,485 CLOSE_WAIT connections** = ~750MB memory bị hold

**Quan trọng:** Việc close connection **KHÔNG mất dữ liệu**. Data đã nằm hoàn chỉnh trong application buffer khi response được nhận. `close()` chỉ giải phóng TCP socket — không ảnh hưởng gì tới data đã nhận.

**Suggest (code change):** Team dev cần thêm `curl_close()` hoặc `$response->getBody()->close()` trong OPCrawler sau khi xử lý response.

**Xử lý tạm thời:** Thay đổi file descriptors trên OS.

---

## 4. Các thay đổi đã áp dụng

### 4.1 EBS IOPS

```
BEFORE: gp3 default (3000 IOPS)
AFTER:  gp3 6000 IOPS
```

### 4.2 Sysctl TCP/Network Tuning

File: `/etc/sysctl.d/99-performance.conf`

```ini
net.ipv4.tcp_tw_reuse = 1          # Reuse TIME_WAIT sockets
net.ipv4.tcp_fin_timeout = 15      # Giảm từ 60s → giải phóng closed connections nhanh hơn
net.core.somaxconn = 4096          # Tăng listen backlog từ 128
net.ipv4.tcp_max_syn_backlog = 4096
net.core.netdev_max_backlog = 4096
net.ipv4.ip_local_port_range = 1024 65535  # Mở rộng ephemeral port range
net.ipv4.tcp_keepalive_time = 60   # Phát hiện dead connections nhanh hơn
net.ipv4.tcp_keepalive_intvl = 10
net.ipv4.tcp_keepalive_probes = 6
fs.file-max = 131072               # Tăng từ 65535
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
```

### 4.3 Nginx Config

File: `/etc/nginx/nginx.conf`

| Setting | Before | After |
|---------|--------|-------|
| worker_connections | 1024 | 65535 |
| multi_accept | off (default) | on |
| use | (default) | epoll |
| tcp_nopush | off | on |
| tcp_nodelay | off | on |
| worker_rlimit_nofile | (default) | 65535 |

File: `/etc/nginx/conf.d/sop-api.conf`

```nginx
# Thêm upstream keepalive (giảm TCP handshake overhead Nginx→Octane)
upstream octane_backend {
    server 127.0.0.1:8000;
    keepalive 16;
}

# Thêm proxy cache cho sp.st.oddspark.com (30s TTL)
location / {
    proxy_cache sp_cache;
    proxy_cache_valid 200 30s;
    proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
    proxy_cache_lock on;              # Ngăn thundering herd
    proxy_cache_lock_timeout 5s;
}

# Giảm timeout
proxy_connect_timeout 30;         # Từ 60
proxy_send_timeout 30;            # Từ 60

# Thêm nginx_status endpoint (cho monitoring)
location = /nginx_status {
    stub_status on;
    allow 127.0.0.1;
    deny all;
    access_log off;
}
```

### 4.4 Octane Workers

```ini
--workers=8 --max-requests=2000
```
- 8 workers × ~100MB = 0.8GB → RAM ~48% → an toàn

### 4.5 File Descriptor Limits (ulimit)

```bash
# /etc/security/limits.d/99-nofile.conf
* soft nofile 131072
* hard nofile 131072
root soft nofile 131072
root hard nofile 131072

# /etc/systemd/system/nginx.service.d/nofile.conf (systemd override)
[Service]
LimitNOFILE=131072

# /etc/supervisor/conf.d/limits.conf
[supervisord]
minfds=131072
```

**Cách tính ulimit hợp lý cho server hiện tại:**
- Peak FD cần: ~85,000 (40K ESTABLISHED + 24K CLOSE_WAIT + overhead)
- Mỗi socket ~3-10KB kernel memory → 85K sockets × 10KB = ~850MB (trong tầm 3.8GB)
- Chọn 131,072 (128K) = ~1.5× peak với buffer an toàn

---

## 5. Kết quả sau mỗi lần Test

### Test 1 - Baseline (config gốc, trước mọi thay đổi)

| Metric | Value |
|--------|-------|
| Avg Response Time | 2,542ms |
| Error Rate | 90.80% |
| CPU | 100% (**85% iowait**, 15% user) |
| RAM | 3.7/3.8GB (97%) |
| Workers | 32 |
| Trạng thái | Server gần crash, disk I/O bottleneck |

**Phân tích:** 85% CPU thực chất là **iowait** (chờ disk I/O), không phải xử lý thực. EBS gp3 default chỉ có 3000 IOPS, không đủ cho 32 workers ghi log + swap memory. 32 workers chiếm gần hết 3.8GB RAM → OS bắt đầu swap → disk I/O bão hòa → iowait 85%.

**Thay đổi sau Test 1:**
- Tăng EBS IOPS 3000 → 6000
- Apply sysctl tuning (14 params)
- Nginx: worker_connections 1024→20480, multi_accept, epoll, proxy_cache, upstream keepalive
- Octane: workers 32→8, max-requests 500→2000


### Test 2 - Worker connections 65535

| Metric | Value |
|--------|-------|
| Avg Response Time | 2,707ms |
| Error Rate | 90.51% |
| CPU | 100% |
| RAM | Gần cạn |
| FD Usage | 64,800/65,535 (99%) |
| Trạng thái | **CRASH** - "Too many open files" (Error 23) |

**Phân tích:** Tăng worker_connections cho phép Nginx accept nhiều connection hơn → OPCrawler tạo nhiều outgoing connections hơn → CLOSE_WAIT tích lũy nhanh hơn → FD usage đạt 99% ulimit (65,535) → kernel từ chối mở file/socket mới → Octane crash với lỗi `liblzma.so.5: cannot open shared object file: Error 23`. Instance 235 Octane rơi vào trạng thái FATAL trong supervisor.

**Thay đổi sau Test 3:**
- ulimit: 65535 → 131072 (tất cả layers: limits.conf, systemd, supervisor)
- fs.file-max: 65535 → 131072

---

### Test 3 - ulimit 131072 (lần test cuối cùng)

| Metric | Value | So với Test 1 (Baseline) |
|--------|-------|--------------------------|
| Avg Response Time | 2,102ms | -17% |
| Error Rate | 86.37% | -4.4% (tốt hơn) |
| CPU (OS peak) | 100% | Tương đương nhưng 0% iowait |
| CPU (CloudWatch Avg 1min) | ~70% | Xem phần 6 |
| CPU (CloudWatch Max 10s) | ~80% | Xem phần 6 |
| RAM Free (min) | 241MB | Tốt hơn (không swap) |
| FD Usage (peak) | 130,560/131,072 (99.6%) | Cao nhưng KHÔNG crash |
| CLOSE_WAIT (peak) | 37,485 | Vẫn leak nhưng server survive |
| Trạng thái | **Ổn định - KHÔNG CRASH** | Cải thiện đáng kể |

**Monitoring chi tiết Instance 235 — 10 rounds × 30 giây:**

| Round | Time | FD Used | CLOSE_WAIT | ESTABLISHED | RAM Free | RAM Available | CPU |
|-------|------|---------|------------|-------------|----------|---------------|-----|
| 1 | 0:00 | 35,000 | 11,600 | ~18,000 | 1,813MB | ~2,800MB | idle |
| 2 | 0:30 | 65,000 | 20,300 | ~30,000 | 1,462MB | ~2,400MB | 50% |
| 3 | 1:00 | 95,000 | 28,300 | ~45,000 | 1,113MB | ~1,900MB | idle |
| 4 | 1:30 | 117,000 | 33,700 | ~55,000 | 829MB | ~1,400MB | 100% |
| 5 | 2:00 | 122,000 | 30,700 | ~60,000 | 653MB | ~1,100MB | 100% |
| 6 | 2:30 | 121,000 | 32,800 | ~58,000 | 576MB | ~900MB | 100% |
| 7 | 3:00 | 122,000 | 36,700 | ~55,000 | 490MB | ~750MB | 50% |
| 8 | 3:30 | **130,560** | **37,485** | ~58,000 | 332MB | ~550MB | 100% |
| 9 | 4:00 | 123,000 | 35,500 | ~56,000 | 278MB | ~450MB | idle |
| 10 | 4:30 | 114,000 | 34,400 | ~50,000 | **241MB** | ~400MB | idle |

**Observations:**
- FD tăng gần tuyến tính từ 35K → 130K trong 3.5 phút → ~27K FD/phút bị consume
- CLOSE_WAIT chiếm ~30% tổng FD (37K/130K) — đây là FD bị "leak" vĩnh viễn
- RAM free giảm liên tục từ 1,813MB → 241MB — mỗi CLOSE_WAIT socket chiếm ~20KB kernel memory
- CPU pattern: spike 100% khi workers đang xử lý, drop về idle khi tất cả workers đang chờ I/O
- Server survive toàn bộ test mặc dù FD đạt 99.6% capacity

---

## 6. Tổng hợp so sánh 

```
                    Test 1          Test 2          Test 3
                  (Baseline)     (wc=65535)     (ulimit 131K)
                  ─────────────  ─────────────  ─────────────
Response Time      2,542ms        2,707ms        2,102ms (-17%)
Error Rate         90.80%         90.51%         86.37% (-4.4%)
CPU iowait         85%            0%             0%  ← FIXED
RAM Usage          97%            ~90%           ~94% (do CLOSE_WAIT)
FD Peak            N/A            64.8K (CRASH)  130.5K (survive)
CLOSE_WAIT         (chưa đo)      ~30K           37.5K (leak)
Server Status      Near crash     CRASH          STABLE ✓
```

**Cải thiện từ Baseline → Test 3:**
- Response time: -17% (2,542ms → 2,102ms)
- Error rate: -4.4% tuyệt đối (90.80% → 86.37%)
- CPU iowait: 85% → 0% (FIXED hoàn toàn)
- Server stability: Gần crash → Ổn định dưới load 4,110 concurrent users

---

## 7. CloudWatch vs OS - CPU Discrepancy

Khi check CPU utilization trên CloudWatch Enhanced Monitoring:

| Phương pháp đo | Giá trị quan sát | Tại sao |
|----------------|-------------------|---------|
| `top -bn1` bên trong OS | 100% (peak) | Snapshot 1 giây duy nhất, bắt đúng lúc CPU peak |
| CloudWatch **Average**, Period=1min | ~70% | Trung bình 60 giây, bao gồm các idle phases |
| CloudWatch **Maximum**, Period=10s | ~80% | Gần sát hơn, nhưng vẫn bao gồm idle trong 10s window |

### Giải thích

CPU trên instance **KHÔNG duy trì 100% liên tục**. Do OPCrawler sử dụng blocking I/O, mỗi worker có pattern:

```
Worker lifecycle:
  [Gửi request tới sp.st.oddspark.com]  → CPU idle  (chờ network ~200-500ms)
  [Nhận response]                        → CPU 100%  (parse HTML ~50ms)
  [Gửi request tiếp]                    → CPU idle  (chờ network ~200-500ms)
  ...
```

Với 8 workers, khi tất cả workers đồng thời chờ network → CPU idle. Khi vài workers đồng thời xử lý response → CPU spike 100%. Pattern này lặp lại không đều.

**Dữ liệu monitoring chứng minh:**
```
Timeline Instance 235 (mỗi ô = 30s, đo bằng top):
| idle | 50% | idle | 100% | 100% | 100% | 50% | 100% | idle | idle |

Trung bình thực tế ≈ (0+50+0+100+100+100+50+100+0+0) / 10 = 50%
CloudWatch Average 1min = ~70% (cao hơn vì sample rate dày hơn, bắt thêm micro-spikes)
CloudWatch Maximum 10s  = ~80% (gần peak nhưng vẫn có idle trong window)
```

### Kết luận về CloudWatch

- Con số CloudWatch **Maximum 10s = 80%** hiện tại đã gần sát nhất có thể
- Để đạt CPU **ổn định 90%+** trên CloudWatch, cần tăng số workers (nhiều workers hơn = luôn có worker đang xử lý khi worker khác đang chờ I/O → CPU ít idle hơn)
- Chênh lệch 80% (CloudWatch) vs 100% (top) là bình thường cho workload blocking I/O, **không phải lỗi monitoring**

---

## 8. Khuyến nghị tiếp theo

### 8.1 Cần Team Dev fix (Code change required)

| Priority | Action | Impact |
|----------|--------|--------|
| **P0** | Fix CLOSE_WAIT leak trong OPCrawler | Giải phóng ~37K FD + ~750MB RAM. Response time sẽ ổn định thay vì degrade theo thời gian |
| | Thêm `curl_close()` hoặc `$response->getBody()->close()` sau khi xử lý response | |
| **P1** | Connection pooling cho OPCrawler | Reuse TCP connections tới sp.st.oddspark.com → giảm ~100-200ms/request |
| **P2** | Async/non-blocking crawling (Swoole coroutine) | Crawl nhiều trang song song → throughput tăng |

### 8.2 Config changes tiếp theo (tiếp tục test sau khi gửi report)

| Priority | Action | Expected Impact |
|----------|--------|----------------|
| **P1** | Tăng Octane workers 8 → 16 | CPU utilization đều hơn (~90%), giảm idle time, giảm queuing |
| **P2** | Tăng upstream keepalive 16 → 32 | Giảm TCP handshake overhead Nginx→Octane |
| **P3** | Tăng Nginx proxy_cache TTL 30s → 60-120s | Nhiều cache hit hơn → giảm load tới Octane |
| **P4** | Sau khi fix CLOSE_WAIT: giảm ulimit về 65535 | Giảm memory overhead |

### 8.3 Monitoring recommendations

- CloudWatch: Dùng **Maximum** statistic + **10s period** để thấy CPU sát thực tế
- Cài đặt CloudWatch Agent custom metric cho CLOSE_WAIT count → alert khi > 10,000
- Alert khi FD usage > 80% capacity (>104,000)

---
