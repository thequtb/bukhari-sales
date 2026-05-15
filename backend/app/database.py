"""SQLAlchemy async database setup."""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)
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

        # Safe migrations — PostgreSQL supports ADD COLUMN IF NOT EXISTS
        for stmt in [
            "ALTER TABLE products ADD COLUMN IF NOT EXISTS variant_name VARCHAR(256)",
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS telegram_conversation_id INTEGER REFERENCES telegram_conversations(id)",
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS telegram_user_id VARCHAR(128)",
            "ALTER TABLE orders ADD COLUMN IF NOT EXISTS channel VARCHAR(20) DEFAULT 'instagram'",
        ]:
            await conn.execute(text(stmt))

async def get_async_session():
    """Yield a standalone async session (for scripts)."""
    async with async_session() as session:
        yield session

