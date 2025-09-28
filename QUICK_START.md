# 🚀 QUICK START - Zealy.io Bot

**Panduan cepat untuk menjalankan bot dalam 5 menit!**

## ⚡ Langkah Cepat (5 Menit)

### 1️⃣ Download & Install
```bash
# Download dari GitHub
git clone https://github.com/rahmivinnn/Asyafira-Airdrop-Bot.git
cd Asyafira-Airdrop-Bot

# Install dependencies
pip install requests python-dotenv
```

### 2️⃣ Dapatkan Cookie
1. Buka [zealy.io](https://zealy.io) dan **LOGIN**
2. Tekan **F12** → Tab **Application** → **Cookies** → **zealy.io**
3. **COPY** semua cookie (yang panjang-panjang)

### 3️⃣ Setup Bot
```bash
# Copy config
cp simple_.env.example .env

# Edit .env (ganti COOKIE dengan yang di-copy)
nano .env
```

**Isi .env:**
```env
COOKIE=cookie_yang_di_copy_dari_browser
```

### 4️⃣ Jalankan Bot
```bash
# Test dulu
python simple_main.py --run-once
```

## ✅ Selesai!

Bot akan otomatis:
- ✅ Deteksi URL claim dari cookie
- ✅ Kirim request ke zealy.io
- ✅ Retry jika gagal
- ✅ Tampilkan hasil

## 🆘 Jika Error

**"Missing COOKIE"** → Pastikan sudah set di .env
**"Could not extract URL"** → Coba: `python simple_main.py --task-url "https://zealy.io/api/claim" --run-once`
**"Client error 401/403"** → Cookie expired, ambil yang baru

## 📱 Notifikasi Telegram (Opsional)

1. Chat [@BotFather](https://t.me/botfather) → `/newbot`
2. Simpan token
3. Chat dengan bot → Kirim pesan
4. Buka: `https://api.telegram.org/bot<TOKEN>/getUpdates`
5. Copy chat ID
6. Update .env:
```env
COOKIE=cookie_anda
TELEGRAM_TOKEN=token_dari_botfather
CHAT_ID=chat_id_yang_di_copy
```

## 🎯 Command Lengkap

```bash
# Basic
python simple_main.py --run-once

# Dengan URL spesifik
python simple_main.py --task-url "https://zealy.io/api/claim" --run-once

# Dengan payload
python simple_main.py --payload '{"action":"claim"}' --run-once

# Test Telegram
python simple_main.py --test-telegram
```

**Happy claiming! 🚀**