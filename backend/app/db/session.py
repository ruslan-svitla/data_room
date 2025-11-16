from app.core.config import settings
from app.db.dynamodb_session import DynamoDBSession


# Async dependency to get DB session
async def get_db():
    """Get a database session

    This now returns a DynamoDB session instead of SQLAlchemy
    """
    session = DynamoDBSession()
    try:
        yield session
    finally:
        # DynamoDB doesn't have explicit connections to close
        pass
