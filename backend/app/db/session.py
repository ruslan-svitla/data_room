from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Convert SQLite URL to async format if needed
async_database_url = settings.DATABASE_URL
if async_database_url.startswith("sqlite"):
    async_database_url = async_database_url.replace("sqlite", "sqlite+aiosqlite")

# Create async engine
engine = create_async_engine(
    async_database_url,
    connect_args=(
        {"check_same_thread": False}
        if settings.DATABASE_URL.startswith("sqlite")
        else {}
    ),
)

# Create async session
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


# Async dependency to get DB session
async def get_db():
    async with AsyncSessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()
