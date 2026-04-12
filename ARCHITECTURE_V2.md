# GitThink Pulse v2.0 架构文档

## 概述

GitThink Pulse v2.0 是一个全面升级的 GitHub 项目分析与多平台发布系统，在 v1.0 的基础上增加了现代化的前端 UI、用户认证、任务队列等功能。

## 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端层 (Frontend)                     │
│  React 18 + TypeScript + Vite + Tailwind CSS                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Dashboard │  │ Projects │  │ Reports  │  │ Settings │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────────┘
                          ↓ REST API
┌─────────────────────────────────────────────────────────────────┐
│                      API 网关层 (FastAPI)                      │
│ 2.0.0 版本 - CORS、认证中间件、Swagger 文档                    │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                        应用层 (Application)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Auth        │  │ Project      │  │ Notifications │      │
│  │  Service     │  │ Manager      │  │ Service      │      │
│  └──────────────┘  └──────────────┘  └────────────┘       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Task Queue   │  │ LLM Service  │  │ Quality      │      │
│  │              │  │              │  │ Service      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                        核心层 (Core)                          │
│  ┌──────────────┐  ┌──────────────┐                          │
│  │ Domain       │  │ Repository   │                          │
│  │ Models       │  │ Interfaces   │                          │
│  └──────────────┘  └──────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                    基础设施层 (Infrastructure)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Database     │  │ Cache        │  │ Resilience   │      │
│  │ (SQLite/PG) │  │ (Memory)     │  │ (Retry/CB)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                          │
│  │ GitHub       │  │ Publishers   │                          │
│  │ Adapter      │  │ (Multi)      │                          │
│  └──────────────┘  └──────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

## v2.0 新增功能详解

### 1. 现代化前端 UI

#### 技术栈
- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **样式**: Tailwind CSS
- **路由**: React Router v6
- **状态管理**: Zustand
- **数据获取**: TanStack Query
- **UI 组件**: Lucide Icons
- **图表**: Recharts

#### 页面结构
```
frontend/src/
├── components/
│   ├── Layout.tsx          # 主布局（侧边栏 + 内容区）
│   └── ui/                # UI 组件库
│       ├── Card.tsx
│       ├── Button.tsx
│       ├── Badge.tsx
│       ├── Input.tsx
│       ├── Select.tsx
│       └── Loading.tsx
├── pages/
│   ├── Dashboard.tsx       # 仪表盘（统计概览）
│   ├── Projects.tsx        # 项目列表
│   ├── Reports.tsx         # 报告列表
│   ├── Settings.tsx        # 设置页面
│   └── Login.tsx          # 登录页面
├── hooks/
│   ├── useProjects.ts      # 项目数据 hook
│   ├── useReports.ts       # 报告数据 hook
│   └── useStats.ts         # 统计数据 hook
├── api/
│   └── client.ts           # HTTP 客户端（axios）
├── types/
│   └── index.ts           # TypeScript 类型定义
└── lib/
    └── utils.ts           # 工具函数
```

#### 特性
- 响应式设计，支持移动端
- 自动数据刷新（TanStack Query）
- 深色模式支持
- Toast 通知
- 加载状态处理
- 错误边界

### 2. 用户认证系统

#### 认证服务 (`application/auth.py`)

**功能**:
- 用户注册（密码 bcrypt 加密）
- 用户登录（JWT Token 生成）
- Token 验证
- 密码验证

**API 端点**:
- `POST /api/auth/register` - 注册
- `POST /api/auth/login` - 登录
- `POST /api/auth/logout` - 登出
- `GET /api/auth/me` - 获取当前用户

**默认管理员**:
- 用户名: `admin`
- 密码: `admin123`
- 首次运行时自动创建

**JWT 配置**:
```python
{
    "algorithm": "HS256",
    "expires_in": 7 days,
    "secret_key": "from-config"
}
```

### 3. 项目管理

#### 项目管理器 (`application/project_manager.py`)

**功能**:
- 添加项目（自动去重）
- 删除项目
- 查询单个项目
- 搜索项目（关键字、语言、最低 Stars）
- 获取项目统计

**API 端点**:
- `GET /api/projects` - 列表（支持搜索和过滤）
- `GET /api/projects/{id}` - 详情
- `POST /api/projects` - 创建（需要管理员）
- `DELETE /api/projects/{id}` - 删除（需要管理员）

**搜索参数**:
```typescript
{
    keyword?: string;    // 关键字搜索
    language?: string;   // 语言过滤
    min_stars?: number; // 最低 Stars
    limit?: number;      // 分页限制
    offset?: number;     // 分页偏移
}
```

### 4. 通知服务

#### 通知服务 (`application/notifications.py`)

**支持的通知类型**:
1. **邮件通知**
   - SMTP 协议
   - 支持 TLS
   - HTML 格式支持

2. **Telegram 通知**
   - Bot API
   - 支持 HTML 格式
   - Parse Mode

3. **Webhook 通知**
   - 任意 URL
   - JSON Payload

**使用示例**:
```python
# 发送新报告通知
await notification_service.notify_new_report(
    title="项目分析报告",
    project_url="https://github.com/user/repo",
    score=0.85
)

# 发送错误通知
await notification_service.notify_error(
    error="任务执行失败",
    context={"task": "daily_analysis"}
)
```

### 5. 任务队列

#### 任务队列 (`application/task_queue.py`)

**架构**:
- 基于 Redis 的优先级队列
- Redis 不可用时降级到内存队列
- 支持异步任务工作器

**功能**:
- 任务入队（支持优先级）
- 任务出队
- 队列大小查询
- 队列清空
- 任务处理器注册

**使用示例**:
```python
# 创建队列
queue = TaskQueue(
    redis_url="redis://localhost:6379/0",
    queue_name="auto_publisher_tasks"
)

# 创建工作器
worker = TaskWorker(
    task_queue=queue,
    task_handlers={
        "analyze_project": analyze_project_handler,
        "generate_report": generate_report_handler,
    }
)

# 启动工作器
worker.start()
```

### 6. Swagger/OpenAPI 文档

#### FastAPI 自动文档

**访问地址**:
- Swagger UI: `http://localhost:8080/docs`
- ReDoc: `http://localhost:8080/redoc`
- OpenAPI JSON: `http://localhost:8080/openapi.json`

**特性**:
- 自动生成 API 文档
- 交互式 API 测试
- 请求/响应 Schema
- 认证集成

## 数据库模式变更

### 新增表: `users`

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| username | VARCHAR(100) | 用户名，唯一 |
| password | VARCHAR(200) | bcrypt 加密密码 |
| email | VARCHAR(200) | 邮箱 |
| is_active | BOOLEAN | 是否激活 |
| is_admin | BOOLEAN | 是否管理员 |
| created_at | DATETIME | 创建时间 |

### 更新表: `reports`

无结构性变更，保持向后兼容。

## API 端点清单

### 认证

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/auth/register` | 注册用户 | 否 |
| POST | `/api/auth/login` | 登录 | 否 |
| POST | `/api/auth/logout` | 登出 | 是 |
| GET | `/api/auth/me` | 获取当前用户 | 是 |

### 项目

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/projects` | 项目列表 | 否 |
| GET | `/api/projects/{id}` | 项目详情 | 否 |
| POST | `/api/projects` | 创建项目 | 是（管理员） |
| DELETE | `/api/projects/{id}` | 删除项目 | 是（管理员） |

### 报告

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/reports` | 报告列表 | 否 |
| GET | `/api/reports/{id}` | 报告详情 | 否 |

### 统计

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/stats` | 基本统计 | 否 |
| GET | `/api/stats/project` | 项目统计 | 否 |

### 系统

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| GET | `/health` | 健康检查 | 否 |

## 运行方式

### 开发模式

```bash
# 后端
python main_enhanced.py --dashboard

# 前端
cd frontend
npm run dev
```

### 生产模式

```bash
# 后端
python main_enhanced.py

# 前端构建
cd frontend
npm run build

# 前端部署
# 将 frontend/dist 部署到 Nginx 或其他静态服务器
```

## 部署建议

### Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build: .
    command: python main_enhanced.py
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/auto_publisher
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    ports:
      - "3000:80"

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: auto_publisher
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass

  redis:
    image: redis:7
```

## 安全建议

1. **修改默认管理员密码**
   ```python
   # 首次登录后立即修改
   ```

2. **使用环境变量存储敏感信息**
   ```bash
   # .env 文件不要提交到版本控制
   JWT_SECRET_KEY=your-secret-key
   ```

3. **启用 HTTPS**
   - 生产环境使用 HTTPS
   - 配置 CORS 白名单

4. **定期更新依赖**
   ```bash
   pip install --upgrade -r requirements_new.txt
   npm update
   ```

## 性能优化

### 已实现的优化

1. **异步架构**
   - 全异步数据库操作
   - 并发 HTTP 请求

2. **缓存**
   - 内存缓存装饰器
   - Redis 支持

3. **熔断器**
   - 防止级联故障
   - 自动恢复

4. **重试策略**
   - 指数退避
   - 可配置重试次数

### 未来优化方向

1. 引入 CDN 加速静态资源
2. 数据库查询优化（索引）
3. 前端代码分割
4. 图片懒加载

## 监控和告警

### Prometheus 指标

- 请求计数
- 请求延迟
- 错误率
- 队列大小

### 健康检查

```bash
curl http://localhost:8080/health
```

## 测试

### 后端测试

```bash
pytest tests/ -v
pytest --cov=. --cov-report=html
```

### 前端测试

```bash
cd frontend
npm test
```

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

MIT License
