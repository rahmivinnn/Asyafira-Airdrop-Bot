# 🤖 Simple Zealy.io Task Claimer Bot

**Bot sederhana untuk klaim task otomatis di zealy.io**

Bot yang disederhanakan dengan fokus pada fungsi utama untuk mengklaim task di zealy.io dengan mudah dan cepat.

## ✨ Fitur Utama

- **Setup Mudah**: Hanya perlu konfigurasi cookie dan langsung jalan
- **Auto URL Detection**: Otomatis mendeteksi URL claim dari cookie
- **Retry Logic**: 3 kali percobaan dengan delay 5 detik
- **Notifikasi Telegram**: Optional notifikasi sukses/gagal
- **Dependencies Minimal**: Hanya butuh `requests` dan `python-dotenv`

## 🚀 Cara Install & Running (Step by Step)

### Langkah 1: Download/Clone Repository

```bash
# Download dari GitHub
git clone https://github.com/rahmivinnn/Asyafira-Airdrop-Bot.git
cd Asyafira-Airdrop-Bot

# ATAU download ZIP dari GitHub dan extract
```

### Langkah 2: Install Python Dependencies

```bash
# Install requirements
pip install -r simple_requirements.txt

# Jika error, coba:
pip install requests python-dotenv
```

### Langkah 3: Dapatkan Cookie dari zealy.io

1. **Buka zealy.io** di browser dan **login**
2. **Tekan F12** untuk buka Developer Tools
3. **Klik tab "Application"** (Chrome) atau "Storage" (Firefox)
4. **Klik "Cookies"** di sidebar kiri
5. **Pilih domain zealy.io**
6. **Copy semua cookie** (biasanya yang panjang dengan session/auth)
7. **Simpan cookie** untuk langkah berikutnya

### Langkah 4: Konfigurasi Bot

```bash
# Copy file konfigurasi
cp simple_.env.example .env

# Edit file .env dengan text editor
nano .env
# ATAU
notepad .env
```

**Isi file .env seperti ini:**
```env
# WAJIB: Cookie dari zealy.io
COOKIE=session_cookie_yang_di_copy_dari_browser

# OPSIONAL: URL spesifik (biasanya auto-detect)
TASK_URL=https://zealy.io/api/claim

# OPSIONAL: Notifikasi Telegram
TELEGRAM_TOKEN=bot_token_telegram_anda
CHAT_ID=chat_id_telegram_anda
```

### Langkah 5: Test Bot

```bash
# Test notifikasi Telegram (jika sudah setup)
python simple_main.py --test-telegram

# Test claim sekali
python simple_main.py --run-once
```

### Langkah 6: Running Bot

```bash
# Klaim sekali langsung
python simple_main.py --run-once

# Klaim dengan URL spesifik
python simple_main.py --task-url "https://zealy.io/api/claim" --run-once

# Klaim dengan payload custom
python simple_main.py --payload '{"action":"claim"}' --run-once
```

## 📋 Konfigurasi Lengkap

### Wajib Diisi
- `COOKIE`: Cookie session dari zealy.io (WAJIB!)

### Opsional
- `TASK_URL`: URL spesifik untuk claim (auto-detect jika tidak diisi)
- `HTTP_METHOD`: GET atau POST (default: POST)
- `JSON_PAYLOAD`: Data JSON untuk request POST
- `TELEGRAM_TOKEN`: Token bot Telegram untuk notifikasi
- `CHAT_ID`: ID chat Telegram untuk notifikasi

## 💡 Contoh Penggunaan

```bash
# Klaim dasar
python simple_main.py --run-once

# Klaim dengan payload custom
python simple_main.py --payload '{"action":"claim","questId":"123"}' --run-once

# Klaim dengan URL spesifik
python simple_main.py --task-url "https://zealy.io/api/quests/claim" --run-once

# Test notifikasi Telegram
python simple_main.py --test-telegram
```

## 🔧 Cara Kerja Bot

1. **Ekstraksi Cookie**: Otomatis mengambil URL claim dari cookie
2. **Buat Request**: Membuat header dengan session cookie
3. **Eksekusi Claim**: Mengirim request POST/GET ke zealy.io
4. **Retry Logic**: Coba ulang sampai 3 kali jika gagal
5. **Notifikasi**: Kirim notifikasi Telegram (jika dikonfigurasi)

## 🚨 Troubleshooting (Pemecahan Masalah)

### Masalah Umum & Solusinya

**❌ "Missing required environment variables: COOKIE"**
- ✅ Pastikan sudah set COOKIE di file .env
- ✅ Pastikan cookie masih valid dan tidak expired

**❌ "Could not extract Zealy.io URL from cookie"**
- ✅ Coba berikan URL manual dengan `--task-url`
- ✅ Pastikan cookie mengandung domain zealy.io

**❌ "Client error (401/403)"**
- ✅ Cookie mungkin expired - ambil yang baru
- ✅ Pastikan masih login di zealy.io

**❌ "Telegram test failed"**
- ✅ Cek TELEGRAM_TOKEN dan CHAT_ID
- ✅ Pastikan bot sudah ditambahkan ke chat

**❌ "Module not found"**
- ✅ Install dependencies: `pip install -r simple_requirements.txt`

**❌ "Permission denied"**
- ✅ Pastikan file .env bisa dibaca
- ✅ Cek permission file

### Cara Debug

1. **Cek log file**: `zealy_claimer.log`
2. **Test cookie**: Buka zealy.io di browser yang sama
3. **Test Telegram**: Jalankan `python simple_main.py --test-telegram`
4. **Cek konfigurasi**: Pastikan file .env sudah benar

## 📱 Setup Telegram (Opsional)

### Langkah 1: Buat Bot Telegram
1. Chat dengan [@BotFather](https://t.me/botfather)
2. Ketik `/newbot`
3. Ikuti instruksi untuk buat bot
4. **Simpan token** yang diberikan

### Langkah 2: Dapatkan Chat ID
1. Chat dengan bot yang baru dibuat
2. Kirim pesan apapun
3. Buka: `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. **Copy chat ID** dari response

### Langkah 3: Update .env
```env
TELEGRAM_TOKEN=bot_token_dari_botfather
CHAT_ID=chat_id_yang_di_copy
```

## 🎯 Tips & Trik

### Untuk Pemula
- **Mulai simple**: Coba dulu tanpa Telegram
- **Test dulu**: Selalu test dengan `--run-once`
- **Backup cookie**: Simpan cookie di tempat aman

### Untuk Advanced
- **Custom payload**: Sesuaikan dengan API zealy.io
- **Scheduling**: Gunakan cron job atau task scheduler
- **Multiple accounts**: Buat beberapa file .env

## 📁 Struktur File

```
Asyafira-Airdrop-Bot/
├── simple_main.py              # Script utama
├── utils/
│   ├── simple_claimer.py       # Logic klaim
│   └── simple_telegram.py      # Notifikasi
├── simple_requirements.txt     # Dependencies
├── simple_.env.example         # Template konfigurasi
├── .env                        # Konfigurasi Anda (buat sendiri)
└── zealy_claimer.log          # Log file (auto-generated)
```

## 🔒 Keamanan & Privasi

### ⚠️ PENTING!
- **Jangan share file .env** - berisi cookie session Anda
- **Cookie = Password** - jangan kasih ke orang lain
- **Backup aman** - simpan cookie di tempat yang aman
- **Jangan commit .env** ke GitHub

### 🛡️ Tips Keamanan
- Gunakan environment variables di production
- Ganti cookie secara berkala
- Monitor log untuk aktivitas mencurigakan

## 🆘 Support & Bantuan

### Jika Ada Masalah
1. **Baca troubleshooting** di atas dulu
2. **Cek log file** `zealy_claimer.log`
3. **Test step by step** sesuai panduan
4. **Pastikan cookie valid** dan tidak expired

### Kontak
- **GitHub Issues**: [Buat issue di repository](https://github.com/rahmivinnn/Asyafira-Airdrop-Bot/issues)
- **Documentation**: Baca README ini dengan teliti

## 🎉 Selamat!

Bot sudah siap digunakan! Ikuti langkah-langkah di atas dengan teliti, dan Anda akan bisa mengklaim task di zealy.io secara otomatis.

**Happy claiming! 🚀**

---

**Simple, focused, and effective - just what you need for zealy.io task claiming!**