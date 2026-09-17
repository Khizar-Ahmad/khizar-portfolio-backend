from fastapi import HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.config import settings

security = HTTPBearer()

ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24


def create_admin_token() -> str:
    payload = {
        "sub": "admin",
        "role": "admin",
        "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)


def verify_admin_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Not authorized")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# Dependency alias
AdminRequired = Depends(verify_admin_token)
