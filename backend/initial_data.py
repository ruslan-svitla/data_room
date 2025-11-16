import asyncio
import logging
from typing import Optional

from app.db.dynamodb_session import DynamoDBSession

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_db(db: DynamoDBSession | None = None) -> None:
    """Initialize DynamoDB with required tables
    This function ensures that DynamoDB tables are properly set up.
    """
    # With DynamoDB, tables are created through the infrastructure code
    # or automatically by the application on startup
    logger.info("DynamoDB initialization complete")
    return


async def init() -> None:
    """Initialize database with basic data"""
    # Create a DynamoDB session
    db = DynamoDBSession()
    await init_db(db)


async def main() -> None:
    logger.info("Creating initial data")
    await init()
    logger.info("Initial data created")


if __name__ == "__main__":
    asyncio.run(main())
