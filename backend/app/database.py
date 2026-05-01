"""SQLAlchemy async database setup."""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """Dependency that provides a database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Create all tables and run safe column migrations on startup."""
    from sqlalchemy import text

    async with engine.begin() as conn:
        from app import models  # noqa: F401 — ensure models are imported
        await conn.run_sync(Base.metadata.create_all)

        # Safe migration: add variant_name to products if missing
        try:
            await conn.execute(text(
                "ALTER TABLE products ADD COLUMN variant_name VARCHAR(256)"
            ))
        except Exception:
            pass  # Column already exists

async def get_async_session():
    """Yield a standalone async session (for scripts)."""
    async with async_session() as session:
        yield session

