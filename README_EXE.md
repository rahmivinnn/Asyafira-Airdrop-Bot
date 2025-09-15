# 🚀 Asyafira Airdrop Bot - EXE Version

## 📁 File yang Diperlukan

```
Asyafira Airdrop Bot/
├── dist/
│   └── AsyafiraAirdropBot.exe    # File utama bot (executable)
├── run_bot.bat                   # Script untuk menjalankan bot dengan mudah
├── .env.example                  # Template konfigurasi
├── logs/                         # Folder log otomatis
├── responses/                    # Folder response otomatis
└── README_EXE.md                # Panduan ini
```

## 🎯 Cara Menggunakan Bot (MUDAH!)

### Metode 1: Menggunakan Script Batch (RECOMMENDED)

1. **Double-click** file `run_bot.bat`
2. Pilih opsi yang diinginkan:
   - `1` = Run sekali (langsung claim)
   - `2` = Schedule harian (claim setiap hari)
   - `3` = Schedule waktu tertentu
   - `4` = Test Telegram
   - `5` = Validasi konfigurasi
   - `6` = Help

### Metode 2: Command Line Manual

Buka Command Prompt di folder bot, lalu:

```bash
# Run sekali
dist\AsyafiraAirdropBot.exe --task-url "https://example.com/claim" --run-once

# Schedule harian jam 9 pagi
dist\AsyafiraAirdropBot.exe --task-url "https://example.com/claim" --daily-time "09:00"

# Schedule waktu tertentu
dist\AsyafiraAirdropBot.exe --task-url "https://example.com/claim" --run-datetime "2025-09-15 14:30:00"

# Test Telegram
dist\AsyafiraAirdropBot.exe --test-telegram

# Validasi config
dist\AsyafiraAirdropBot.exe --validate-config
```

## ⚙️ Konfigurasi (Opsional)

### Setup Telegram Notifications

1. Copy `.env.example` menjadi `.env`
2. Edit file `.env` dan isi:
   ```
   TELEGRAM_TOKEN=your_bot_token_here
   CHAT_ID=your_chat_id_here
   ```

### Setup Cookie Authentication (Opsional)

```
COOKIE_VALUE=your_cookie_here
USER_AGENT=your_user_agent_here
```

## 📊 Monitoring

- **Logs**: Cek folder `logs/claimer.log` untuk melihat aktivitas bot
- **Responses**: Cek folder `responses/` untuk melihat response dari server
- **Real-time**: Bot akan menampilkan status di console

## 🔧 Troubleshooting

### Bot tidak jalan?
1. Pastikan file `AsyafiraAirdropBot.exe` ada di folder `dist/`
2. Run `dist\AsyafiraAirdropBot.exe --validate-config` untuk cek konfigurasi
3. Cek file `logs/claimer.log` untuk error details

### Telegram tidak jalan?
1. Run `dist\AsyafiraAirdropBot.exe --test-telegram`
2. Pastikan `TELEGRAM_TOKEN` dan `CHAT_ID` benar di file `.env`

### Claim gagal?
1. Cek URL task apakah benar
2. Cek internet connection
3. Cek logs untuk error details

## 🎉 Fitur Utama

✅ **Auto Claim**: Otomatis claim airdrop
✅ **Scheduling**: Schedule harian atau waktu tertentu
✅ **Retry Logic**: Auto retry jika gagal
✅ **Telegram Notifications**: Notifikasi hasil ke Telegram
✅ **Logging**: Log lengkap semua aktivitas
✅ **Cookie Support**: Login menggunakan cookie
✅ **Easy to Use**: Interface yang mudah digunakan
✅ **No Installation**: Langsung jalan tanpa install Python

## 📞 Support

Jika ada masalah:
1. Cek file `logs/claimer.log`
2. Run validation: `dist\AsyafiraAirdropBot.exe --validate-config`
3. Test basic functionality: `dist\AsyafiraAirdropBot.exe --help`

---

**Selamat menggunakan Asyafira Airdrop Bot! 🚀**