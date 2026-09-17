from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Text, Boolean, DateTime, Integer, JSON
from datetime import datetime
import uuid
from app.config import settings

# Convert postgres:// or postgresql:// → postgresql+asyncpg://
_db_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://").replace("postgres://", "postgresql+asyncpg://")

engine = create_async_engine(_db_url, pool_pre_ping=True, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


class HeroProfile(Base):
    __tablename__ = "hero_profile"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    title = Column(String(300), nullable=False)
    tagline = Column(Text)
    bio = Column(Text)
    email = Column(String(200))
    github_url = Column(String(500))
    linkedin_url = Column(String(500))
    resume_url = Column(String(500))
    profile_picture = Column(Text)  # base64 or URL
    location = Column(String(200))
    years_experience = Column(String(50))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Experience(Base):
    __tablename__ = "experiences"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    company = Column(String(200), nullable=False)
    company_url = Column(String(500))
    role = Column(String(200), nullable=False)
    start_date = Column(String(50), nullable=False)
    end_date = Column(String(50))  # None = current
    is_current = Column(Boolean, default=False)
    description = Column(Text)
    technologies = Column(JSON, default=list)
    location = Column(String(200))
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    long_description = Column(Text)
    technologies = Column(JSON, default=list)
    live_url = Column(String(500))
    github_url = Column(String(500))
    images = Column(JSON, default=list)  # list of base64 or URLs
    is_featured = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Skill(Base):
    __tablename__ = "skills"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    category = Column(String(100), nullable=False)
    name = Column(String(100), nullable=False)
    proficiency = Column(Integer, default=80)  # 0-100
    order_index = Column(Integer, default=0)
