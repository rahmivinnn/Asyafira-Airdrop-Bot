# 🚀 Fitur Auto-Extract URL dari Cookie

## ✨ **Fitur Baru: URL Otomatis dari Cookie**

Bot sekarang dapat **otomatis mengekstrak URL task dari cookie** tanpa perlu memasukkan URL manual!

## 🔧 **Cara Kerja**

### 1. **Pattern Detection**
Bot akan mencari pattern URL dalam cookie:
- `task_url=https://example.com/claim`
- `claim_url=https://example.com/api/claim`
- `api_url=https://example.com/endpoint`
- `url=https://example.com/task`
- `endpoint=https://example.com/claim`
- `target=https://example.com/api`
- URL langsung: `https://example.com/claim`

### 2. **Domain Construction**
Jika tidak ada URL langsung, bot akan mencari domain dan membuat URL:
- `domain=example.com` → `https://example.com/claim`
- `host=api.example.com` → `https://api.example.com/claim`
- `site=airdrop.com` → `https://airdrop.com/api/claim`

## 📝 **Contoh Penggunaan**

### **Setup Cookie di .env**
```bash
# Contoh 1: Cookie dengan URL langsung
COOKIE="session_id=abc123; task_url=https://api.example.com/claim; user_token=xyz789"

# Contoh 2: Cookie dengan domain (bot akan construct URL)
COOKIE="session_id=abc123; domain=example.com; auth_token=xyz789"

# Contoh 3: Cookie dengan multiple patterns
COOKIE="user_id=123; claim_url=https://airdrop.example.com/api/claim; session=active"
```

### **Menjalankan Bot (Tanpa URL Manual)**
```bash
# Run sekali (URL auto-extract dari cookie)
./dist/AsyafiraAirdropBot.exe --run-once

# Schedule harian jam 7 pagi (URL auto-extract)
./dist/AsyafiraAirdropBot.exe --daily-time "07:00"

# Schedule waktu tertentu (URL auto-extract)
./dist/AsyafiraAirdropBot.exe --run-datetime "2025-09-15 14:30:00"
```

### **Menggunakan Batch File**
```bash
# Double-click run_bot.bat
# Pilih opsi 1 atau 2
# Tidak perlu input URL lagi!
```

## 🔍 **Prioritas URL**

1. **Manual URL** (jika diberikan via `--task-url`)
2. **Environment Variable** (`TASK_URL` di .env)
3. **Auto-Extract dari Cookie** (fitur baru)

## 📋 **Log Output**

### **Sukses Extract URL:**
```
11:16:37 - INFO - No task URL provided, attempting to extract from cookie...
11:16:37 - INFO - Extracted URL from cookie: https://httpbin.org/post
11:16:37 - INFO - Successfully extracted task URL from cookie
11:16:37 - INFO - Target URL: https://httpbin.org/post
```

### **Gagal Extract URL:**
```
11:15:30 - INFO - No task URL provided, attempting to extract from cookie...
11:15:30 - WARNING - Could not extract URL from cookie
11:15:30 - ERROR - Task URL is required. Provide via --task-url, TASK_URL in .env, or ensure URL is available in cookie
```

## 🛠️ **Troubleshooting**

### **Problem: "Could not extract URL from cookie"**
**Solusi:**
1. Pastikan cookie berisi URL atau domain
2. Check format cookie di .env
3. Gunakan pattern yang didukung:
   - `task_url=https://...`
   - `domain=example.com`
   - `claim_url=https://...`

### **Problem: "No cookie found"**
**Solusi:**
1. Set `COOKIE` di file .env
2. Pastikan format: `COOKIE="key1=value1; key2=value2"`
3. Copy dari Chrome Cookie Editor

## 🎯 **Keuntungan Fitur Ini**

✅ **Tidak perlu input URL manual**
✅ **Otomatis detect dari cookie**
✅ **Support multiple pattern**
✅ **Fallback ke manual URL**
✅ **User-friendly untuk client**
✅ **Mengurangi human error**

## 🔧 **Untuk Developer**

### **Fungsi Utama:**
- `extract_url_from_cookie()` di `utils/claimer.py`
- Pattern matching dengan regex
- URL validation dengan `urlparse`
- Domain construction untuk common endpoints

### **Pattern yang Didukung:**
```python
url_patterns = [
    r'url=([^;\s]+)',
    r'task_url=([^;\s]+)',
    r'claim_url=([^;\s]+)',
    r'endpoint=([^;\s]+)',
    r'api_url=([^;\s]+)',
    r'target=([^;\s]+)',
    r'https?://[^;\s]+'
]
```

---

**🚀 Bot sekarang 100% otomatis - tinggal set cookie dan jalankan!**