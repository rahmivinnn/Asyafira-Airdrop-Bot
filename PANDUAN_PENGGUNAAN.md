# 🚀 PANDUAN LENGKAP ASYAFIRA AIRDROP BOT

## ✅ BOT SUDAH BERJALAN!

**Status**: Bot sedang berjalan dengan schedule harian jam 07:00 UTC
**Target**: https://api.example-airdrop.com/claim
**Mode**: Production (Real, No Mock)
**Fitur Baru**: Auto-extract URL dari Cookie 🆕

---

## 🆕 **FITUR BARU: Auto-Extract URL dari Cookie**

**Bot sekarang TIDAK PERLU input URL manual!** 
URL akan otomatis diambil dari cookie yang sudah dikonfigurasi.

### **Setup Cookie di .env:**
```bash
# Contoh cookie dengan URL embedded
COOKIE="session_id=abc123; task_url=https://api.airdrop.com/claim; user_token=xyz789"

# Atau dengan domain (bot akan construct URL)
COOKIE="session_id=abc123; domain=airdrop.com; auth_token=xyz789"
```

## 🎯 CARA MENGGUNAKAN BOT

### 1. SCHEDULE HARIAN (RECOMMENDED)

```bash
# Schedule claim setiap hari jam 7 pagi (URL auto-extract dari cookie)
./dist/AsyafiraAirdropBot.exe --daily-time "07:00"

# Schedule claim setiap hari jam 9 malam (URL auto-extract dari cookie)
./dist/AsyafiraAirdropBot.exe --daily-time "21:00"
```

### 2. SCHEDULE WAKTU TERTENTU

```bash
# Schedule untuk tanggal dan waktu spesifik (URL auto-extract dari cookie)
./dist/AsyafiraAirdropBot.exe --run-datetime "2025-09-16 14:30:00"
```

### 3. RUN SEKALI (IMMEDIATE)

```bash
# Langsung claim sekarang (URL auto-extract dari cookie)
./dist/AsyafiraAirdropBot.exe --run-once
```

### 4. DENGAN CUSTOM PAYLOAD

```bash
# Untuk airdrop yang butuh data khusus (URL auto-extract dari cookie)
./dist/AsyafiraAirdropBot.exe --run-once --payload '{"wallet":"0x123...","action":"claim"}'

# Override manual URL (jika diperlukan)
./dist/AsyafiraAirdropBot.exe --task-url "https://your-real-airdrop-url.com/claim" --run-once
```

---

## 🔧 SETUP UNTUK PRODUCTION

### 1. Ganti URL dengan URL Real Airdrop

**PENTING**: Ganti `https://api.example-airdrop.com/claim` dengan URL airdrop yang sebenarnya!

Contoh URL real airdrop:
- `https://api.layerzero.foundation/claim`
- `https://claim.arbitrum.foundation/api/claim`
- `https://airdrop.optimism.io/api/claim`
- `https://claim.polygon.technology/api/claim`

### 2. Setup Cookie Authentication (Jika Diperlukan)

Edit file `.env`:
```
COOKIE_VALUE=your_session_cookie_here
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
```

### 3. Setup Telegram Notifications

Edit file `.env`:
```
TELEGRAM_TOKEN=your_bot_token
CHAT_ID=your_chat_id
```

---

## 📊 MONITORING & LOGS

### Real-time Monitoring
- Bot menampilkan status di console
- Tekan `Ctrl+C` untuk stop bot

### Log Files
- **Main Log**: `logs/claimer.log`
- **Responses**: `responses/` folder

### Check Status
```bash
# Validasi konfigurasi
./dist/AsyafiraAirdropBot.exe --validate-config

# Test Telegram
./dist/AsyafiraAirdropBot.exe --test-telegram
```

---

## 🎯 CONTOH PENGGUNAAN REAL

### Scenario 1: LayerZero Airdrop
```bash
./dist/AsyafiraAirdropBot.exe --task-url "https://api.layerzero.foundation/claim" --daily-time "07:00" --payload '{"address":"0x123..."}'
```

### Scenario 2: Arbitrum Airdrop
```bash
./dist/AsyafiraAirdropBot.exe --task-url "https://claim.arbitrum.foundation/api/claim" --daily-time "08:00"
```

### Scenario 3: One-time Claim
```bash
./dist/AsyafiraAirdropBot.exe --task-url "https://airdrop.optimism.io/api/claim" --run-once
```

---

## 🚨 TROUBLESHOOTING

### Bot tidak claim?
1. **Cek URL**: Pastikan URL airdrop benar dan aktif
2. **Cek Network**: Pastikan internet stabil
3. **Cek Logs**: Lihat `logs/claimer.log` untuk error details
4. **Cek Time**: Pastikan waktu sistem benar

### Claim gagal?
1. **Cek Response**: Lihat folder `responses/` untuk response dari server
2. **Cek Cookie**: Pastikan cookie masih valid (jika diperlukan)
3. **Cek Payload**: Pastikan format JSON payload benar

### Telegram tidak jalan?
1. Run: `./dist/AsyafiraAirdropBot.exe --test-telegram`
2. Cek token dan chat ID di file `.env`

---

## ⚡ TIPS UNTUK SUKSES

1. **Gunakan URL Real**: Jangan gunakan URL mock/test
2. **Set Schedule Tepat**: Sesuaikan dengan waktu airdrop
3. **Monitor Logs**: Selalu cek logs untuk memastikan berjalan
4. **Backup Config**: Simpan file `.env` sebagai backup
5. **Update Cookie**: Perbarui cookie jika expired

---

## 🎉 BOT FEATURES

✅ **Real Production Ready**: Tidak ada mock, semua real
✅ **Auto Retry**: Retry otomatis jika gagal
✅ **Schedule Flexible**: Harian, waktu tertentu, atau immediate
✅ **Cookie Support**: Login menggunakan cookie
✅ **Telegram Alerts**: Notifikasi hasil ke Telegram
✅ **Comprehensive Logs**: Log lengkap semua aktivitas
✅ **Error Handling**: Handle error dengan baik
✅ **Windows EXE**: Tidak perlu install Python

---

**🚀 Selamat menggunakan Asyafira Airdrop Bot untuk claim airdrop real!**

**Current Status**: ✅ Running with daily schedule at 07:00 UTC