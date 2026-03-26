"""
database.py - Neon PostgreSQL async connection using SQLAlchemy
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# Create async engine pointing to Neon
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,           # Set True to log SQL (dev only)
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,   # Verify connections before use
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


async def get_db() -> AsyncSession:
    """FastAPI dependency: yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """Create all tables in the database (run once at startup)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
