# Asyafira Airdrop Bot

Enterprise-grade automated airdrop claiming system with advanced scheduling, real-time notifications, and production-ready Windows executable distribution.

## Core Features

**Authentication & Session Management**
- Cookie-based authentication with Chrome integration
- Session persistence and automatic renewal
- Multi-account support through configuration profiles

**Execution Engine**
- Asynchronous HTTP client with connection pooling
- Exponential backoff retry mechanism
- Configurable timeout and rate limiting
- Support for GET/POST with custom payloads

**Scheduling & Automation**
- Cron-like scheduling for recurring tasks
- One-time execution with precise datetime targeting
- Interactive mode with timeout-based auto-execution

**Monitoring & Observability**
- Structured logging with rotation and compression
- Raw response archival for debugging
- Real-time Telegram notifications
- Health check endpoints

**Production Deployment**
- Standalone Windows executable
- Environment-based configuration
- Graceful error handling and recovery

## Architecture

```
asyafira-airdrop-bot/
├── main.py                 # Application entry point
├── utils/
│   ├── claimer.py          # Core claiming logic with retry
│   ├── telegram.py         # Notification service
│   ├── captcha.py          # CAPTCHA solving integration
│   └── cookie_manager.py   # Session management
├── config/
│   ├── database.py         # Configuration persistence
│   ├── accounts/           # Multi-account profiles
│   └── certificates/       # SSL certificates
├── logs/                   # Application logs
├── responses/              # Response archives
├── static/                 # Web interface assets
├── templates/              # HTML templates
└── dist/                   # Production builds
```

## Installation

### Development Setup

```bash
git clone <repository-url>
cd "Asyafira Airdrop Bot"
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Production Deployment

1. Download the latest release executable
2. Configure environment variables
3. Deploy with process manager (PM2, systemd, etc.)

## Configuration

### Environment Variables

Create `.env` from `.env.example`:

```bash
# Core Configuration
COOKIE=session_cookie_string
TASK_URL=https://api.example.com/claim
HTTP_METHOD=POST
JSON_PAYLOAD={"action":"claim","timestamp":"auto"}

# Scheduling
RUN_DATETIME=2025-09-14T13:30:00Z
DAILY_CLAIM_TIME=09:00
TIMEZONE=UTC

# Network Configuration
REQUEST_TIMEOUT=30
MAX_RETRIES=3
RETRY_DELAY=5
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64)

# Telegram Integration
TELEGRAM_TOKEN=bot_token
CHAT_ID=chat_id
NOTIFICATION_LEVEL=INFO

# Security
TWOCAPTCHA_API_KEY=api_key
CAPTCHA_TIMEOUT=300
SSL_VERIFY=true

# Logging
LOG_LEVEL=INFO
MAX_LOG_SIZE=5242880  # 5MB
LOG_BACKUP_COUNT=10
LOG_FORMAT=json
```

### Cookie Extraction

1. Install Chrome Cookie Editor extension
2. Navigate to target application
3. Complete authentication flow
4. Export cookies as string format
5. Configure `COOKIE` environment variable

### Telegram Bot Setup

```bash
# Create bot via BotFather
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://your-domain.com/webhook"}'

# Get chat ID
curl "https://api.telegram.org/bot<TOKEN>/getUpdates"
```

## Usage

### Command Line Interface

```bash
# Immediate execution
python main.py --task-url "https://api.example.com/claim" --run-once

# Scheduled execution
python main.py --run-datetime "2025-09-14T13:30:00Z"

# Daily recurring
python main.py --daily-time "09:00" --timezone "UTC"

# Custom payload
python main.py --payload '{"action":"claim","user_id":123}' --method POST

# Configuration validation
python main.py --validate-config

# Health check
python main.py --health-check
```

### Production Executable

```bash
# Interactive mode with auto-timeout
./AsyafiraAirdropBot.exe

# Direct execution
./AsyafiraAirdropBot.exe --run-once

# Scheduled execution
./AsyafiraAirdropBot.exe --daily-time "09:00"

# Background service
./AsyafiraAirdropBot.exe --daemon --log-file /var/log/airdrop.log
```

### Batch Operations

```bash
# Batch launcher (Windows)
run_interactive.bat

# Service management
run_bot.bat
```

## Build Process

### Development Build

```bash
pyinstaller --onefile --console main.py
```

### Production Build

```bash
pyinstaller AsyafiraAirdropBot.spec
```

### Spec Configuration

```python
# AsyafiraAirdropBot.spec
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('.env.example', '.'), ('static', 'static')],
    hiddenimports=[
        'utils.claimer',
        'utils.telegram',
        'utils.captcha',
        'utils.cookie_manager'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AsyafiraAirdropBot',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
```

## Monitoring

### Log Analysis

```bash
# Real-time monitoring
tail -f logs/claimer.log

# Error analysis
grep "ERROR" logs/claimer.log | jq .

# Performance metrics
awk '/Response time/ {sum+=$3; count++} END {print "Avg:", sum/count}' logs/claimer.log
```

### Health Checks

```bash
# Application health
curl http://localhost:8080/health

# Telegram connectivity
curl "https://api.telegram.org/bot<TOKEN>/getMe"

# Target endpoint validation
curl -I "https://api.example.com/claim"
```

## Error Handling

### Common Issues

**Authentication Failures**
```
ERROR: Invalid session cookie
SOLUTION: Re-extract cookie after fresh login
```

**Network Timeouts**
```
ERROR: Request timeout after 30s
SOLUTION: Increase REQUEST_TIMEOUT or check network connectivity
```

**Rate Limiting**
```
ERROR: HTTP 429 Too Many Requests
SOLUTION: Implement exponential backoff or reduce request frequency
```

**CAPTCHA Challenges**
```
ERROR: CAPTCHA required
SOLUTION: Configure 2CAPTCHA_API_KEY or implement manual solving
```

### Debug Mode

```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG
python main.py --debug

# Network debugging
export PYTHONHTTPSVERIFY=0
export REQUESTS_CA_BUNDLE=""
```

## Security Considerations

### Credential Management
- Store sensitive data in environment variables
- Use encrypted configuration files for production
- Implement credential rotation policies
- Monitor for credential leakage in logs

### Network Security
- Enforce HTTPS for all external communications
- Validate SSL certificates
- Implement request signing for API calls
- Use proxy servers for IP rotation

### Operational Security
- Run with minimal privileges
- Implement process isolation
- Monitor for suspicious activity
- Regular security updates

## Performance Optimization

### Connection Pooling
```python
# Configure in utils/claimer.py
session = requests.Session()
adapter = HTTPAdapter(
    pool_connections=10,
    pool_maxsize=20,
    max_retries=3
)
session.mount('https://', adapter)
```

### Memory Management
```python
# Implement response streaming for large payloads
with session.get(url, stream=True) as response:
    for chunk in response.iter_content(chunk_size=8192):
        process_chunk(chunk)
```

### Async Operations
```python
# Concurrent execution for multiple accounts
import asyncio
import aiohttp

async def claim_async(session, account):
    async with session.post(url, json=payload) as response:
        return await response.json()
```

## Deployment

### Docker Container

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: asyafira-airdrop-bot
spec:
  replicas: 1
  selector:
    matchLabels:
      app: asyafira-airdrop-bot
  template:
    metadata:
      labels:
        app: asyafira-airdrop-bot
    spec:
      containers:
      - name: bot
        image: asyafira-airdrop-bot:latest
        env:
        - name: COOKIE
          valueFrom:
            secretKeyRef:
              name: bot-secrets
              key: cookie
```

### Process Management

```bash
# PM2 configuration
pm2 start ecosystem.config.js

# Systemd service
sudo systemctl enable asyafira-airdrop-bot
sudo systemctl start asyafira-airdrop-bot
```

## Contributing

### Development Workflow

1. Fork repository
2. Create feature branch
3. Implement changes with tests
4. Submit pull request
5. Code review and merge

### Code Standards

- Follow PEP 8 style guidelines
- Implement comprehensive error handling
- Add type hints for all functions
- Write unit tests for core functionality
- Document API changes

### Testing

```bash
# Unit tests
python -m pytest tests/

# Integration tests
python -m pytest tests/integration/

# Performance tests
python -m pytest tests/performance/ --benchmark
```

## License

MIT License - See LICENSE file for details.

---

**Production-ready airdrop automation for Web3 ecosystems.**