"""配置管理 - 升级版"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


load_dotenv()


@dataclass
class DatabaseConfig:
    """数据库配置"""
    url: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./auto_publisher.db")
    pool_size: int = int(os.getenv("DB_POOL_SIZE", "10"))
    max_overflow: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))


@dataclass
class GitHubConfig:
    """GitHub 配置"""
    token: str = os.getenv("GITHUB_TOKEN", "")
    fetch_count: int = int(os.getenv("GITHUB_FETCH_COUNT", "100"))
    days_window: int = int(os.getenv("GITHUB_DAYS_WINDOW", "30"))


@dataclass
class LLMConfig:
    """LLM 配置"""
    api_key: str = os.getenv("LLM_API_KEY", "")
    model: str = os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022")
    enabled: bool = bool(os.getenv("LLM_ENABLED", "false").lower() == "true")


@dataclass
class PublisherConfig:
    """发布平台配置"""
    notion_token: str = os.getenv("NOTION_TOKEN", "")
    notion_database_id: str = os.getenv("NOTION_DATABASE_ID", "")
    csdn_api: str = os.getenv("CSDN_PUBLISH_API", "")
    csdn_token: str = os.getenv("CSDN_TOKEN", "")
    zhihu_token: str = os.getenv("ZHIHU_TOKEN", "")
    juejin_token: str = os.getenv("JUEJIN_TOKEN", "")
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")


@dataclass
class MonitoringConfig:
    """监控配置"""
    enabled: bool = bool(os.getenv("MONITORING_ENABLED", "true").lower() == "true")
    metrics_port: int = int(os.getenv("METRICS_PORT", "8000"))
    dashboard_port: int = int(os.getenv("DASHBOARD_PORT", "8080"))


@dataclass
class ScheduleConfig:
    """调度配置"""
    cron: str = os.getenv("SCHEDULE_CRON", "0 9 * * *")
    timezone: str = os.getenv("TIMEZONE", "Asia/Shanghai")


@dataclass
class TemplateConfig:
    """模板配置"""
    template_dir: Path = Path(os.getenv("TEMPLATE_DIR", "templates"))
    default_template: str = os.getenv("DEFAULT_TEMPLATE", "default.md.j2")


@dataclass
class AuthConfig:
    """认证配置"""
    secret_key: str = os.getenv("JWT_SECRET_KEY", "auto-publisher-secret-key-change-in-production")
    algorithm: str = "HS256"
    token_expires_days: int = int(os.getenv("JWT_TOKEN_EXPIRES_DAYS", "7"))


@dataclass
class Settings:
    """主配置"""
    # 子配置
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    github: GitHubConfig = field(default_factory=GitHubConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    publisher: PublisherConfig = field(default_factory=PublisherConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    schedule: ScheduleConfig = field(default_factory=ScheduleConfig)
    template: TemplateConfig = field(default_factory=TemplateConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)

    # 路径配置
    reports_dir: Path = Path(os.getenv("REPORTS_DIR", "reports"))
    state_file: Path = Path(os.getenv("STATE_FILE", "state/selection_state.json"))

    # 其他
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    debug: bool = bool(os.getenv("DEBUG", "false").lower() == "true")


SETTINGS = Settings()
