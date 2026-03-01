"""
HealthLoom Database Module
Handles PostgreSQL connections using async SQLAlchemy
"""

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create declarative base for ORM models
Base = declarative_base()

# ==============================================
# DATABASE ENGINE CONFIGURATION
# ==============================================

# Create async engine
engine = create_async_engine(
    settings.get_database_url_async(),
    echo=settings.is_development,  # Log SQL queries in development
    future=True,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ==============================================
# DATABASE SESSION DEPENDENCY
# ==============================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database sessions in FastAPI endpoints
    
    Usage:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context():
    """
    Context manager for database sessions outside of FastAPI
    
    Usage:
        async with get_db_context() as db:
            result = await db.execute(...)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database context error: {e}")
            raise
        finally:
            await session.close()


# ==============================================
# DATABASE LIFECYCLE
# ==============================================

async def init_db():
    """
    Initialize database - create all tables
    Note: In production, use Alembic migrations instead
    """
    async with engine.begin() as conn:
        logger.info("Creating database tables...")
        await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created successfully")


async def close_db():
    """
    Close database connections gracefully
    """
    logger.info("Closing database connections...")
    await engine.dispose()
    logger.info("✅ Database connections closed")


# ==============================================
# DATABASE HEALTH CHECK
# ==============================================

async def check_db_health() -> bool:
    """
    Check if database is accessible and healthy
    
    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


# ==============================================
# TRANSACTION HELPERS
# ==============================================

@asynccontextmanager
async def atomic_transaction():
    """
    Context manager for atomic transactions
    Ensures all-or-nothing database operations
    
    Usage:
        async with atomic_transaction() as db:
            # All operations here are atomic
            await db.execute(...)
            await db.execute(...)
    """
    async with AsyncSessionLocal() as session:
        async with session.begin():
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"Transaction failed and rolled back: {e}")
                raise
