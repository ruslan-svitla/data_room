import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.db.session import engine
from app.schemas.user import UserCreate
from app.services.user import user_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db(db: AsyncSession) -> None:
    """Initialize database with required initial data"""

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    # Check if we have users
    user = await user_service.get_by_email(db, email="admin@example.com")

    # Create admin user if it doesn't exist
    if not user:
        user_in = UserCreate(
            email="admin@example.com",
            username="admin",
            password="password",  # Using a simple password that won't exceed bcrypt's 72-byte limit
            full_name="Administrator",
        )
        user = await user_service.create(db, obj_in=user_in)
        logger.info("Admin user created")

        user_in = UserCreate(
            email="user1@example.com",
            username="user1",
            password="password1",  # Using a simple password that won't exceed bcrypt's 72-byte limit
            full_name="User 01",
        )
        user = await user_service.create(db, obj_in=user_in)
        logger.info("Admin user created")

        # Set user as superuser
        user.is_superuser = True
        db.add(user)
        await db.commit()
        logger.info("Admin user set as superuser")
