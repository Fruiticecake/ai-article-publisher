"""用户认证服务"""
import logging
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database import DatabaseManager, UserRecord
from config_new import SETTINGS


logger = logging.getLogger(__name__)


class AuthService:
    """认证服务"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.secret_key = SETTINGS.auth.secret_key
        self.algorithm = SETTINGS.auth.algorithm
        self.token_expires_in = timedelta(days=SETTINGS.auth.token_expires_days)

    async def hash_password(self, password: str) -> str:
        """加密密码"""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    async def verify_password(self, password: str, hashed_password: str) -> bool:
        """验证密码"""
        try:
            return bcrypt.checkpw(password.encode(), hashed_password.encode())
        except Exception as e:
            logger.error(f"密码验证失败: {e}")
            return False

    def generate_token(self, user_id: int, username: str) -> str:
        """生成 JWT Token"""
        payload = {
            "user_id": user_id,
            "username": username,
            "exp": datetime.utcnow() + self.token_expires_in,
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[dict]:
        """验证 JWT Token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token 已过期")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"无效的 Token: {e}")
            return None

    async def register(self, username: str, password: str, email: Optional[str] = None) -> dict:
        """注册用户"""
        async with self.db_manager.session() as session:
            # 检查用户是否已存在
            stmt = select(UserRecord).where(UserRecord.username == username)
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if existing_user:
                raise ValueError("用户名已存在")

            # 创建新用户
            hashed_password = await self.hash_password(password)
            user = UserRecord(
                username=username,
                password=hashed_password,
                email=email,
                is_active=True,
                is_admin=True,  # 默认为管理员
            )
            session.add(user)
            await session.flush()

            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }

    async def login(self, username: str, password: str) -> dict:
        """登录用户"""
        async with self.db_manager.session() as session:
            stmt = select(UserRecord).where(UserRecord.username == username)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                raise ValueError("用户名或密码错误")

            if not user.is_active:
                raise ValueError("用户已被禁用")

            if not await self.verify_password(password, user.password):
                raise ValueError("用户名或密码错误")

            # 生成 Token
            token = self.generate_token(user.id, user.username)

            return {
                "token": token,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_admin": user.is_admin,
                }
            }

    async def get_current_user(self, token: str) -> Optional[dict]:
        """获取当前用户"""
        payload = self.verify_token(token)
        if not payload:
            return None

        async with self.db_manager.session() as session:
            stmt = select(UserRecord).where(UserRecord.id == payload["user_id"])
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user or not user.is_active:
                return None

            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin,
            }
