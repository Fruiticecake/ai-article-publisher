"""通知服务"""
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any

import aiohttp
from config_new import SETTINGS


logger = logging.getLogger(__name__)


class NotificationService:
    """通知服务"""

    def __init__(
        self,
        email_config: dict | None = None,
        telegram_config: dict | None = None,
    ):
        self.email_config = email_config or {}
        self.telegram_config = telegram_config or {
            "bot_token": SETTINGS.publisher.telegram_bot_token,
            "chat_id": SETTINGS.publisher.telegram_chat_id,
        }

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html: bool = False,
    ) -> bool:
        """发送邮件"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config.get('from_email', '')
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'html' if html else 'plain'))

            with smtplib.SMTP(
                self.email_config.get('smtp_host', 'localhost'),
                self.email_config.get('smtp_port', 587),
            ) as server:
                if self.email_config.get('use_tls', True):
                    server.starttls()
                if self.email_config.get('username'):
                    server.login(
                        self.email_config['username'],
                        self.email_config.get('password', ''),
                    )
                server.send_message(msg)

            logger.info(f"邮件已发送: {to_email}")
            return True
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False

    async def send_telegram(
        self,
        message: str,
        parse_mode: str = "HTML",
    ) -> bool:
        """发送 Telegram 消息"""
        if not self.telegram_config.get('bot_token'):
            logger.warning("Telegram Bot Token 未配置")
            return False

        try:
            url = f"https://api.telegram.org/bot{self.telegram_config['bot_token']}/sendMessage"
            payload = {
                "chat_id": self.telegram_config.get('chat_id'),
                "text": message,
                "parse_mode": parse_mode,
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        logger.info("Telegram 消息已发送")
                        return True
                    else:
                        error = await response.text()
                        logger.error(f"Telegram 发送失败: {error}")
                        return False
        except Exception as e:
            logger.error(f"Telegram 发送失败: {e}")
            return False

    async def send_webhook(
        self,
        url: str,
        data: dict[str, Any],
    ) -> bool:
        """发送 Webhook"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        logger.info(f"Webhook 已发送: {url}")
                        return True
                    else:
                        logger.error(f"Webhook 发送失败: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Webhook 发送失败: {e}")
            return False

    async def notify_new_report(
        self,
        title: str,
        project_url: str,
        score: float,
    ) -> None:
        """通知新报告生成"""
        message = f"""
📊 <b>新报告生成</b>

标题: {title}
项目: {project_url}
质量评分: {score:.2f}

详情请查看 Dashboard。
        """.strip()

        await self.send_telegram(message)

    async def notify_error(
        self,
        error: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """通知错误"""
        context_text = "\n".join([f"{k}: {v}" for k, v in (context or {}).items()])
        message = f"""
⚠️ <b>系统错误</b>

错误信息: {error}

{context_text}
        """.strip()

        await self.send_telegram(message)
