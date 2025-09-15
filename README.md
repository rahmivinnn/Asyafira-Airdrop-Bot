# Asyafira Airdrop Bot 🚀

Bot auto-claim airdrop yang canggih dengan fitur scheduling, notifikasi Telegram, dan dapat di-build menjadi executable Windows (.exe).

## ✨ Fitur Utama

- 🍪 **Login via Cookie** - Menggunakan cookie dari Chrome Cookie Editor
- ⏰ **Scheduling Fleksibel** - Run sekali, datetime tertentu, atau harian
- 📱 **Notifikasi Telegram** - Update real-time ke Telegram
- 🔄 **Retry Logic** - Exponential backoff dengan retry otomatis
- 🤖 **Captcha Handling** - Support manual input dan API solver
- 📝 **Logging Lengkap** - Rotating logs dan raw response storage
- 🎯 **HTTP Flexible** - Support GET/POST dengan custom payload
- 💻 **Windows EXE** - Build menjadi executable standalone

## 📁 Struktur Proyek

```
Asyafira Airdrop Bot/
├── main.py                 # Entry point utama
├── utils/
│   ├── claimer.py          # Fungsi claim dengan retry logic
│   ├── telegram.py         # Notifikasi Telegram
│   └── captcha.py          # Handling captcha
├── logs/                   # Folder log (auto-created)
├── responses/              # Raw response files (auto-created)
├── .env.example            # Template konfigurasi
├── requirements.txt        # Dependencies
└── README.md              # Dokumentasi ini
```

## 🛠️ Setup & Instalasi

### 1. Clone/Download Project

```bash
# Download atau clone project ini
cd "Asyafira Airdrop Bot"
```

### 2. Install Dependencies

```bash
# Install semua dependencies
pip install -r requirements.txt
```

### 3. Konfigurasi Environment

```bash
# Copy template konfigurasi
copy .env.example .env

# Edit .env dengan text editor favorit
notepad .env
```

#### Konfigurasi Wajib:

```env
# Cookie dari Chrome (wajib)
COOKIE=your_cookie_string_here

# URL target claim
TASK_URL=https://example.com/api/claim
```

#### Konfigurasi Opsional:

```env
# Telegram Notifications
TELEGRAM_TOKEN=your_bot_token
CHAT_ID=your_chat_id

# Scheduling
RUN_DATETIME=2025-09-14 13:30:00
DAILY_CLAIM_TIME=09:00

# HTTP Settings
HTTP_METHOD=POST
JSON_PAYLOAD={"action":"claim"}
REQUEST_TIMEOUT=30

# Retry Settings
MAX_RETRIES=3
RETRY_DELAY=5

# Captcha (opsional)
TWOCAPTCHA_API_KEY=your_2captcha_key
CAPTCHA_TIMEOUT=300
```

### 4. Cara Mendapatkan Cookie

1. Install **Cookie Editor** extension di Chrome
2. Login ke website target airdrop
3. Buka Cookie Editor → Export → Copy sebagai string
4. Paste ke file `.env` di bagian `COOKIE=`

### 5. Setup Telegram Bot (Opsional)

1. Chat dengan [@BotFather](https://t.me/botfather) di Telegram
2. Buat bot baru dengan `/newbot`
3. Copy token yang diberikan ke `TELEGRAM_TOKEN`
4. Untuk mendapatkan `CHAT_ID`:
   - Chat dengan bot Anda
   - Buka: `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - Copy `chat.id` dari response

## 🚀 Cara Penggunaan

### Mode CLI (Command Line)

```bash
# Run sekali langsung
python main.py --task-url "https://example.com/claim" --run-once

# Schedule untuk datetime tertentu
python main.py --task-url "https://example.com/claim" --run-datetime "2025-09-14 13:30:00"

# Schedule harian pada jam tertentu
python main.py --task-url "https://example.com/claim" --daily-time "09:00"

# Dengan custom payload
python main.py --task-url "https://example.com/claim" --run-once --payload '{"action":"claim"}'

# Menggunakan method GET
python main.py --task-url "https://example.com/claim" --run-once --method GET
```

### Mode Environment (.env)

```bash
# Set konfigurasi di .env, lalu jalankan
python main.py
```

### Utility Commands

```bash
# Test konfigurasi
python main.py --validate-config

# Test notifikasi Telegram
python main.py --test-telegram

# Lihat help
python main.py --help
```

## 🔧 Build ke Windows EXE

### 1. Install PyInstaller

```bash
pip install pyinstaller
```

### 2. Build EXE

```bash
# Build dengan semua dependencies
pyinstaller --onefile --console --name "AsyafiraAirdropBot" main.py

# Atau dengan icon (jika ada)
pyinstaller --onefile --console --icon=icon.ico --name "AsyafiraAirdropBot" main.py
```

### 3. Build Advanced (Recommended)

```bash
# Build dengan optimasi dan hidden imports
pyinstaller --onefile --console \
  --name "AsyafiraAirdropBot" \
  --hidden-import="utils.claimer" \
  --hidden-import="utils.telegram" \
  --hidden-import="utils.captcha" \
  --add-data ".env.example;." \
  main.py
```

### 4. Distribusi

Setelah build berhasil:

1. File EXE akan ada di folder `dist/`
2. Copy file `.env.example` ke folder yang sama dengan EXE
3. Rename `.env.example` menjadi `.env`
4. Edit `.env` dengan konfigurasi yang benar
5. Jalankan EXE

```
folder_distribusi/
├── AsyafiraAirdropBot.exe
├── .env
└── logs/                    # akan dibuat otomatis
```

## 📋 Format Datetime

Bot mendukung berbagai format datetime:

```
2025-09-14 13:30:00
2025-09-14 13:30
2025/09/14 13:30:00
2025/09/14 13:30
14-09-2025 13:30:00
14-09-2025 13:30
14/09/2025 13:30:00
14/09/2025 13:30
```

## 📊 Logging & Monitoring

### Log Files

- **logs/claimer.log** - Log utama dengan rotating (5MB per file, keep 10 files)
- **responses/timestamp.json** - Raw response dari server
- **responses/timestamp.txt** - Raw response text format

### Log Levels

Set di `.env`:

```env
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
MAX_LOG_SIZE=5          # MB per file
LOG_BACKUP_COUNT=10     # Jumlah backup files
```

## 🔍 Troubleshooting

### Error: "Missing required environment variables"

- Pastikan file `.env` ada di folder yang sama dengan script/EXE
- Pastikan `COOKIE` sudah diisi dengan benar

### Error: "Invalid datetime format"

- Gunakan format yang didukung (lihat section Format Datetime)
- Pastikan datetime di masa depan, bukan masa lalu

### Error: "Telegram test failed"

- Periksa `TELEGRAM_TOKEN` dan `CHAT_ID`
- Pastikan bot sudah di-start dengan mengirim `/start`
- Test manual: `https://api.telegram.org/bot<TOKEN>/getMe`

### Error: "Request failed"

- Periksa cookie masih valid (login ulang jika perlu)
- Periksa URL target masih benar
- Cek log detail di `logs/claimer.log`

### Build EXE Error

- Pastikan semua dependencies terinstall
- Gunakan virtual environment yang bersih
- Tambahkan `--hidden-import` untuk module yang missing

## 🛡️ Security Notes

- **Jangan commit file `.env`** ke repository
- **Cookie bersifat sensitif** - jangan share ke orang lain
- **Telegram token** harus dijaga kerahasiaannya
- **Gunakan HTTPS** untuk semua request

## 🔄 Update & Maintenance

### Update Dependencies

```bash
pip install --upgrade -r requirements.txt
```

### Clean Logs

```bash
# Hapus log lama (opsional)
rmdir /s logs
rmdir /s responses
```

### Backup Configuration

```bash
# Backup konfigurasi penting
copy .env .env.backup
```

## 📞 Support

Jika mengalami masalah:

1. Periksa log di `logs/claimer.log`
2. Jalankan `python main.py --validate-config`
3. Test dengan `python main.py --test-telegram`
4. Periksa format datetime dan URL

## 📄 License

MIT License - Bebas digunakan untuk keperluan pribadi dan komersial.

---

**Happy Claiming! 🎉**