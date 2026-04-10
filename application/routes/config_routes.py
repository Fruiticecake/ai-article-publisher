"""Configuration routes"""
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends

from .dependencies import get_current_admin
from application.utils import mask_secret
from config_new import SETTINGS

# Get project root directory based on this file's location
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

logger = logging.getLogger(__name__)
router = APIRouter(tags=["配置"])

def _mask_secret(value: str | None, keep_start: int = 3, keep_end: int = 4) -> str:
    """Deprecated: use mask_secret from application.utils instead"""
    return mask_secret(value, keep_start, keep_end)


@router.get("/api/config/publishers")
async def get_publisher_config(
    _: dict = Depends(get_current_admin),
):
    """Get publishing platform configuration (credentials are masked)"""
    return {
        "notion_token": _mask_secret(SETTINGS.publisher.notion_token),
        "notion_database_id": _mask_secret(SETTINGS.publisher.notion_database_id, 4, 4),
        "csdn_api": _mask_secret(SETTINGS.publisher.csdn_api),
        "csdn_token": _mask_secret(SETTINGS.publisher.csdn_token),
        "zhihu_token": _mask_secret(SETTINGS.publisher.zhihu_token),
        "juejin_token": _mask_secret(SETTINGS.publisher.juejin_token),
        "telegram_bot_token": _mask_secret(SETTINGS.publisher.telegram_bot_token, 4, 4),
        "telegram_chat_id": _mask_secret(SETTINGS.publisher.telegram_chat_id, 4, 4),
        "xhs_cookie": _mask_secret(SETTINGS.publisher.xhs_cookie, 4, 0),
    }


@router.post("/api/config/publishers")
async def update_publisher_config(
    notion_token: str = None,
    notion_database_id: str = None,
    csdn_api: str = None,
    csdn_token: str = None,
    zhihu_token: str = None,
    juejin_token: str = None,
    telegram_bot_token: str = None,
    telegram_chat_id: str = None,
    xhs_cookie: str = None,
    _: dict = Depends(get_current_admin),
):
    """Update publishing platform configuration"""
    try:
        # Read existing .env file
        env_content = {}
        if ENV_PATH.exists():
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_content[key.strip()] = value.strip()

        # Update fields
        if notion_token is not None:
            env_content["NOTION_TOKEN"] = notion_token
            SETTINGS.publisher.notion_token = notion_token
        if notion_database_id is not None:
            env_content["NOTION_DATABASE_ID"] = notion_database_id
            SETTINGS.publisher.notion_database_id = notion_database_id
        if csdn_api is not None:
            env_content["CSDN_PUBLISH_API"] = csdn_api
            SETTINGS.publisher.csdn_api = csdn_api
        if csdn_token is not None:
            env_content["CSDN_TOKEN"] = csdn_token
            SETTINGS.publisher.csdn_token = csdn_token
        if zhihu_token is not None:
            env_content["ZHIHU_TOKEN"] = zhihu_token
            SETTINGS.publisher.zhihu_token = zhihu_token
        if juejin_token is not None:
            env_content["JUEJIN_TOKEN"] = juejin_token
            SETTINGS.publisher.juejin_token = juejin_token
        if telegram_bot_token is not None:
            env_content["TELEGRAM_BOT_TOKEN"] = telegram_bot_token
            SETTINGS.publisher.telegram_bot_token = telegram_bot_token
        if telegram_chat_id is not None:
            env_content["TELEGRAM_CHAT_ID"] = telegram_chat_id
            SETTINGS.publisher.telegram_chat_id = telegram_chat_id
        if xhs_cookie is not None:
            env_content["XHS_COOKIE"] = xhs_cookie
            SETTINGS.publisher.xhs_cookie = xhs_cookie

        # Write back to .env file
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            for key, value in env_content.items():
                f.write(f"{key}={value}\n")

        return {
            "success": True,
            "message": "配置已保存，部分配置可能需要重启服务器后生效",
        }
    except Exception as e:
        logger.error(f"保存配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="保存配置失败，请查看服务器日志了解详情")


@router.get("/api/config/llm")
async def get_llm_config(
    _: dict = Depends(get_current_admin),
):
    """Get LLM configuration (api_key is masked)"""
    return {
        "api_key": _mask_secret(SETTINGS.llm.api_key),
        "model": SETTINGS.llm.model,
        "enabled": SETTINGS.llm.enabled,
    }


@router.post("/api/config/llm")
async def update_llm_config(
    api_key: str = None,
    model: str = None,
    enabled: bool = None,
    _: dict = Depends(get_current_admin),
):
    """Update LLM configuration"""
    try:
        env_content = {}
        if ENV_PATH.exists():
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_content[key.strip()] = value.strip()

        if api_key is not None:
            env_content["LLM_API_KEY"] = api_key
            SETTINGS.llm.api_key = api_key
        if model is not None:
            env_content["LLM_MODEL"] = model
            SETTINGS.llm.model = model
        if enabled is not None:
            env_content["LLM_ENABLED"] = str(enabled).lower()
            SETTINGS.llm.enabled = enabled

        with open(ENV_PATH, "w", encoding="utf-8") as f:
            for key, value in env_content.items():
                f.write(f"{key}={value}\n")

        return {
            "success": True,
            "message": "LLM 配置已保存",
        }
    except Exception as e:
        logger.error(f"保存 LLM 配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="保存 LLM 配置失败，请查看服务器日志了解详情")


@router.get("/api/config/github")
async def get_github_config(
    _: dict = Depends(get_current_admin),
):
    """Get GitHub configuration (token is masked)"""
    return {
        "token": _mask_secret(SETTINGS.github.token),
        "fetch_count": SETTINGS.github.fetch_count,
        "days_window": SETTINGS.github.days_window,
    }


@router.post("/api/config/github")
async def update_github_config(
    token: str = None,
    fetch_count: int = None,
    days_window: int = None,
    _: dict = Depends(get_current_admin),
):
    """Update GitHub configuration"""
    try:
        env_content = {}
        if ENV_PATH.exists():
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        env_content[key.strip()] = value.strip()

        if token is not None:
            env_content["GITHUB_TOKEN"] = token
            SETTINGS.github.token = token
        if fetch_count is not None:
            env_content["GITHUB_FETCH_COUNT"] = str(fetch_count)
            SETTINGS.github.fetch_count = fetch_count
        if days_window is not None:
            env_content["GITHUB_DAYS_WINDOW"] = str(days_window)
            SETTINGS.github.days_window = days_window

        with open(ENV_PATH, "w", encoding="utf-8") as f:
            for key, value in env_content.items():
                f.write(f"{key}={value}\n")

        return {
            "success": True,
            "message": "GitHub 配置已保存",
        }
    except Exception as e:
        logger.error(f"保存 GitHub 配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="保存 GitHub 配置失败，请查看服务器日志了解详情")
