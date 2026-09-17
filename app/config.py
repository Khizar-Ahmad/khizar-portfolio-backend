from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # No defaults for secrets — pydantic will raise an error at startup
    # if these aren't provided via environment / .env file
    ADMIN_SECRET_KEY: str
    JWT_SECRET_KEY: str
    DATABASE_URL: str
    GROQ_API_KEY: str

    # Non-sensitive defaults are fine to keep
    CHROMA_PERSIST_DIR: str = "./chroma_store"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        extra = "ignore"
