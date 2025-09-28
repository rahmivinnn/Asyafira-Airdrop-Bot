# Simple Zealy.io Task Claimer

A simplified bot focused on the essential functionality of claiming tasks on zealy.io.

## Features

- **Simple Setup**: Just configure your cookie and run
- **Auto URL Detection**: Automatically extracts claim URL from cookie
- **Basic Retry Logic**: 3 attempts with 5-second delays
- **Telegram Notifications**: Optional success/failure notifications
- **Minimal Dependencies**: Only requires `requests` and `python-dotenv`

## Quick Start

### 1. Install Dependencies

```bash
pip install -r simple_requirements.txt
```

### 2. Get Your Cookie

1. Go to [zealy.io](https://zealy.io) and log in
2. Open Developer Tools (F12)
3. Go to Application/Storage > Cookies
4. Copy the cookie string (look for session or auth cookies)

### 3. Configure

Copy the example configuration:

```bash
cp simple_.env.example .env
```

Edit `.env` and add your cookie:

```env
COOKIE=your_session_cookie_here
TELEGRAM_TOKEN=your_bot_token_here  # Optional
CHAT_ID=your_chat_id_here           # Optional
```

### 4. Run

```bash
# Run once immediately
python simple_main.py --run-once

# Run with specific URL
python simple_main.py --task-url "https://zealy.io/api/claim" --run-once

# Test Telegram notifications
python simple_main.py --test-telegram
```

## Configuration

### Required

- `COOKIE`: Your session cookie from zealy.io

### Optional

- `TASK_URL`: Specific claim URL (auto-detected if not provided)
- `HTTP_METHOD`: GET or POST (default: POST)
- `JSON_PAYLOAD`: JSON payload for POST requests
- `TELEGRAM_TOKEN`: Bot token for notifications
- `CHAT_ID`: Telegram chat ID for notifications

## Usage Examples

```bash
# Basic claim
python simple_main.py --run-once

# With custom payload
python simple_main.py --payload '{"action":"claim","questId":"123"}' --run-once

# With specific URL
python simple_main.py --task-url "https://zealy.io/api/quests/claim" --run-once
```

## How It Works

1. **Cookie Extraction**: Automatically extracts the claim URL from your cookie
2. **Request Building**: Creates proper headers with your session cookie
3. **Claim Execution**: Sends POST/GET request to zealy.io
4. **Retry Logic**: Retries up to 3 times on failure
5. **Notifications**: Sends Telegram notifications (if configured)

## Troubleshooting

### Common Issues

**"Missing required environment variables: COOKIE"**
- Make sure you've set the COOKIE in your .env file
- Ensure the cookie is valid and not expired

**"Could not extract Zealy.io URL from cookie"**
- Try providing the URL manually with `--task-url`
- Check that your cookie contains zealy.io domain

**"Client error (401/403)"**
- Your cookie might be expired - get a fresh one
- Make sure you're logged into zealy.io

**"Telegram test failed"**
- Check your TELEGRAM_TOKEN and CHAT_ID
- Make sure the bot is added to your chat

### Getting Help

1. Check the logs in `zealy_claimer.log`
2. Test your cookie by visiting zealy.io in the same browser
3. Verify your Telegram bot setup

## File Structure

```
simple_zealy_claimer/
├── simple_main.py              # Main script
├── utils/
│   ├── simple_claimer.py       # Core claiming logic
│   └── simple_telegram.py      # Telegram notifications
├── simple_requirements.txt     # Dependencies
├── simple_.env.example         # Configuration template
└── SIMPLE_README.md           # This file
```

## Security Note

- Keep your `.env` file secure and never commit it to version control
- Your cookie contains session information - treat it like a password
- Consider using environment variables in production

---

**Simple, focused, and effective - just what you need for zealy.io task claiming!**