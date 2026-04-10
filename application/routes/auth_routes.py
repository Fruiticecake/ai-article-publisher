"""Authentication routes"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from .dependencies import auth_service, get_current_user
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

router = APIRouter(tags=["认证"])
security = HTTPBearer()


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: str | None = None


@router.post("/api/auth/register")
async def register(request: RegisterRequest) -> dict:
    """Register a new user"""
    try:
        user = await auth_service.register(
            username=request.username,
            password=request.password,
            email=request.email,
        )
        return {"success": True, "user": user}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/auth/login")
async def login(request: LoginRequest) -> dict:
    """Login a user"""
    try:
        result = await auth_service.login(
            username=request.username,
            password=request.password,
        )
        return {"success": True, **result}
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/api/auth/logout")
async def logout() -> dict:
    """Logout current user"""
    return {"success": True}


@router.get("/api/auth/me")
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Get current authenticated user info"""
    user = await auth_service.get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="无效的 Token")
    return {"success": True, "user": user}
