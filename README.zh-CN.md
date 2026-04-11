# Auto Publisher

[English](README.md) | [简体中文](README.zh-CN.md)

自动化 GitHub 项目分析报告生成与多平台发布工具。

## 功能特性

- 🔍 **自动抓取** - 从 GitHub 获取热门趋势项目数据
- 🤖 **AI 分析** - 使用 LLM (Claude) 对项目进行深度分析和质量评分
- 📊 **可视化仪表盘** - 完整的 Web 管理界面，支持项目浏览、报告生成、配置管理
- 📝 **多平台发布** - 一键发布到 CSDN、知乎、掘金、Notion、Telegram、小红书
- ⏰ **定时任务** - 支持 Cron 定时自动抓取和发布
- 📄 **文档导出** - 支持 PDF 和 Markdown 格式导出
- 🔐 **安全** - 完整的 JWT 认证，凭据脱敏显示，安全最佳实践

## 技术栈

**后端:**
- Python 3.10+
- FastAPI
- SQLAlchemy (异步)
- APScheduler
- Jinja2

**前端:**
- React 18 + TypeScript
- Vite
- Tailwind CSS
- React Router
- Axios

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/Fruiticecake/auto-publisher.git
cd auto-publisher
```

### 2. 安装后端依赖

```bash
pip install -r requirements.txt
```

### 3. 安装前端依赖

```bash
cd frontend
npm install
```

### 4. 配置环境变量

创建 `.env` 文件：

```env
# JWT 密钥 (必须)
# 生成方式: python -c 'import secrets; print(secrets.token_hex(32))'
JWT_SECRET_KEY=your-generated-secret-key

# GitHub Token (可选，提高 API 速率限制)
GITHUB_TOKEN=your_github_token

# LLM 配置
LLM_API_KEY=your_anthropic_api_key
LLM_MODEL=claude-3-5-sonnet-20241022
LLM_ENABLED=true

# 发布平台配置
NOTION_TOKEN=your_notion_token
NOTION_DATABASE_ID=your_notion_database_id
CSDN_PUBLISH_API=your_csdn_api
CSDN_TOKEN=your_csdn_token
ZHIHU_TOKEN=your_zhihu_token
JUEJIN_TOKEN=your_juejin_token
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
XHS_COOKIE=your_xhs_cookie

# CORS 配置
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:8080
```

### 5. 构建前端

```bash
cd frontend
npm run build
cd ..
```

### 6. 运行

```bash
python main_enhanced.py
```

首次运行会自动创建数据库并生成随机管理员密码，请保存好密码。

## 仪表盘

启动后访问 `http://localhost:8080` 进入仪表盘：

- 项目列表 - 浏览已抓取的 GitHub 项目
- 报告生成 - 使用 AI 生成分析报告
- 发布管理 - 手动发布到选中平台
- 定时任务 - 配置自动发布计划
- 设置 - 配置各个平台的凭据

## 项目结构

```
auto-publisher/
├── application/           # 应用层
│   ├── routes/            # 模块化 API 路由
│   ├── utils.py           # 共享工具函数
│   ├── auth.py           # 认证服务
│   ├── dashboard_enhanced.py  # FastAPI 仪表盘
│   └── ...
├── core/                 # 核心模型
├── infrastructure/       # 基础设施 (数据库、缓存)
├── adapters/             # 外部适配器 (GitHub、发布平台)
├── frontend/             # React 前端
├── templates/            # Jinja2 报告模板
├── tests/                # 单元测试
└── main_enhanced.py       # 入口文件
```

## 安全特性

- ✅ 没有硬编码凭据，所有配置来自环境变量
- ✅ `.env` 正确添加到 `.gitignore`，不会被提交
- ✅ CORS 可配置，不默认允许所有来源
- ✅ API 返回凭据时自动脱敏
- ✅ Jinja2 自动转义启用，防止 XSS
- ✅ 静态文件路径遍历防护
- ✅ 默认绑定 `127.0.0.1`，提高开发环境安全性
- ✅ 首次运行自动生成随机管理员密码

## 开发

### 运行测试

```bash
python -m pytest tests/ -v
```

### 前端开发模式

```bash
cd frontend
npm run dev
```

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎提交 Issue 和 Pull Request!
