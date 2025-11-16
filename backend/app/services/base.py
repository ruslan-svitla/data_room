from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel

from app.db.base_class import Base
from app.db.dynamodb_session import DynamoDBSession

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base service class providing basic CRUD operations compatible with DynamoDB.
    """

    def __init__(self, model: type[ModelType]):
        """Initialize the service with the model class."""
        self.model = model

    async def get(self, db: DynamoDBSession, id: str) -> ModelType | None:
        """Get an object by ID."""
        table = db.dynamodb.Table(
            db.tables.get(db.model_table_map[self.model.__name__])
        )
        response = table.get_item(Key={"id": id})
        item = response.get("Item")
        if not item:
            return None
        return self.model(**item)

    async def get_multi(
        self, db: DynamoDBSession, *, skip: int = 0, limit: int = 100
    ) -> list[ModelType]:
        """Get multiple objects with pagination."""
        table = db.dynamodb.Table(
            db.tables.get(db.model_table_map[self.model.__name__])
        )
        response = table.scan()
        items = response.get("Items", [])

        # Apply skip and limit
        items = items[skip : skip + limit]
        return [self.model(**item) for item in items]

    async def create(
        self, db: DynamoDBSession, *, obj_in: CreateSchemaType
    ) -> ModelType:
        """Create a new object."""
        obj_in_data = (
            obj_in.model_dump() if hasattr(obj_in, "model_dump") else obj_in.dict()
        )
        db_obj = self.model(**obj_in_data)
        await db.add(db_obj)
        await db.commit()
        return db_obj

    async def create_with_id(
        self,
        db: DynamoDBSession,
        *,
        obj_in: CreateSchemaType | dict[str, Any],
        id: str,
        user_id: str | None = None,
    ) -> ModelType:
        """Create a new object with a specific ID."""
        if isinstance(obj_in, dict):
            obj_in_data = obj_in.copy()
        else:
            obj_in_data = (
                obj_in.model_dump() if hasattr(obj_in, "model_dump") else obj_in.dict()
            )

        obj_in_data["id"] = id
        if user_id:
            obj_in_data["user_id"] = user_id

        db_obj = self.model(**obj_in_data)
        await db.add(db_obj)
        await db.commit()
        return db_obj

    async def update(
        self,
        db: DynamoDBSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any],
    ) -> ModelType:
        """Update an object."""
        update_data = (
            obj_in.model_dump(exclude_unset=True)
            if hasattr(obj_in, "model_dump")
            else obj_in
        )

        # Update object attributes
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])

        # Update the timestamp if applicable
        if hasattr(db_obj, "update_timestamp"):
            db_obj.update_timestamp()

        await db.add(db_obj)  # In DynamoDB this will be an overwrite
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: DynamoDBSession, *, id: str) -> ModelType:
        """Remove an object."""
        obj = await self.get(db, id=id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj
