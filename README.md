# GitThink Pulse

[English](README.md) | [简体中文](README.zh-CN.md)

Automated GitHub project analysis, report generation, and multi-platform publishing tool.

## Features

- 🔍 **Auto Fetching** - Get trending project data from GitHub automatically
- 🤖 **AI Analysis** - Deep project analysis and quality scoring using LLM (Claude)
- 📊 **Visual Dashboard** - Complete web management interface with project browsing, report generation, and configuration management
- 📝 **Multi-platform Publishing** - One-click publishing to CSDN, Zhihu, Juejin, Notion, Telegram, Xiaohongshu
- ⏰ **Scheduled Tasks** - Cron-based automatic fetching and publishing
- 📄 **Document Export** - Support PDF and Markdown export formats
- 🔐 **Security** - Complete JWT authentication, credential masking, security best practices

## Tech Stack

**Backend:**
- Python 3.10+
- FastAPI
- SQLAlchemy (Async)
- APScheduler
- Jinja2

**Frontend:**
- React 18 + TypeScript
- Vite
- Tailwind CSS
- React Router
- Axios

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/Fruiticecake/githink-pulse.git
cd githink-pulse
```

### 2. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 3. Install frontend dependencies

```bash
cd frontend
npm install
```

### 4. Configure environment variables

Create `.env` file:

```env
# JWT Secret (required)
# Generate with: python -c 'import secrets; print(secrets.token_hex(32))'
JWT_SECRET_KEY=your-generated-secret-key

# GitHub Token (optional, increases API rate limit)
GITHUB_TOKEN=your_github_token

# LLM Configuration
LLM_API_KEY=your_anthropic_api_key
LLM_MODEL=claude-3-5-sonnet-20241022
LLM_ENABLED=true

# Publishing Platforms
NOTION_TOKEN=your_notion_token
NOTION_DATABASE_ID=your_notion_database_id
CSDN_PUBLISH_API=your_csdn_api
CSDN_TOKEN=your_csdn_token
ZHIHU_TOKEN=your_zhihu_token
JUEJIN_TOKEN=your_juejin_token
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
XHS_COOKIE=your_xhs_cookie

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8080
```

### 5. Build frontend

```bash
cd frontend
npm run build
cd ..
```

### 6. Run

```bash
python main_enhanced.py
```

On first run, the database will be created automatically and a random admin password will be generated. **Make sure to save this password.**

## Dashboard

After starting, visit `http://localhost:8080` to access the dashboard:

- Project List - Browse fetched GitHub projects
- Report Generation - Generate AI analysis reports
- Publish Management - Manually publish to selected platforms
- Scheduled Tasks - Configure automatic publishing schedule
- Settings - Configure credentials for all platforms

## Project Structure

```
githink-pulse/
├── application/           # Application layer
│   ├── routes/            # Modular API routes
│   ├── utils.py           # Shared utilities
│   ├── auth.py            # Authentication service
│   ├── dashboard_enhanced.py  # FastAPI dashboard
│   └── ...
├── core/                 # Core models
├── infrastructure/       # Infrastructure (database, cache)
├── adapters/             # External adapters (GitHub, publishers)
├── frontend/             # React frontend
├── templates/            # Jinja2 report templates
├── tests/                # Unit tests
└── main_enhanced.py       # Entry point
```

## Security Features

- ✅ No hardcoded credentials, all configuration from environment variables
- ✅ `.env` properly added to `.gitignore`, won't be committed
- ✅ Configurable CORS, doesn't allow all origins by default
- ✅ Automatic credential masking in API responses
- ✅ Jinja2 auto-escaping enabled, prevents XSS
- ✅ Path traversal protection for static files
- ✅ Default binding to `127.0.0.1` for better development security
- ✅ Random admin password generated automatically on first run

## Development

### Run tests

```bash
python -m pytest tests/ -v
```

### Frontend development mode

```bash
cd frontend
npm run dev
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contributing

Issues and Pull Requests are welcome!
