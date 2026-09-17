from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.auth import create_admin_token
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


class AdminLogin(BaseModel):
    secret_key: str


@router.post("/admin/login")
def admin_login(data: AdminLogin):
    if data.secret_key != settings.ADMIN_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin key")
    token = create_admin_token()
    return {"token": token, "message": "Welcome back, Admin!"}
