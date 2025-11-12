from typing import Any, Generic, TypeVar

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.base_class import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base class for CRUD operations on a specific model
    """

    def __init__(self, model: type[ModelType]):
        """
        Initialize BaseService with the model class
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> ModelType | None:
        """
        Get a record by ID
        """
        result = await db.execute(select(self.model).filter(self.model.id == id))
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[ModelType]:
        """
        Get multiple records with pagination
        """
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()

    async def create(
        self, db: AsyncSession, *, obj_in: CreateSchemaType, **kwargs
    ) -> ModelType:
        """
        Create a new record
        """
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, **kwargs)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def create_with_id(
        self, db: AsyncSession, *, obj_in: CreateSchemaType | dict, id: str, **kwargs
    ) -> ModelType:
        """
        Create a new record with a specific ID
        """
        try:
            # For debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Creating object with ID {id}, data type: {type(obj_in)}")
    
            # Handle both Pydantic models and dictionaries
            if hasattr(obj_in, "model_dump"):
                # It's a Pydantic model
                obj_in_data = jsonable_encoder(obj_in)
            else:
                # It's already a dict
                obj_in_data = obj_in
    
            # For debugging
            if "token_expiry" in obj_in_data:
                logger.info(f"Token expiry before model creation: {type(obj_in_data['token_expiry'])}")
    
            # Create the model instance
            db_obj = self.model(id=id, **obj_in_data, **kwargs)
    
            # For debugging
            if hasattr(db_obj, "token_expiry"):
                logger.info(f"Token expiry after model creation: {type(db_obj.token_expiry)}")
    
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            return db_obj
        except Exception as e:
            logger.error(f"Error in create_with_id: {str(e)}")
            raise

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any],
    ) -> ModelType:
        """
        Update a record
        """
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, *, id: Any) -> ModelType:
        """
        Remove a record (soft delete or hard delete based on model)
        """
        result = await db.execute(select(self.model).filter(self.model.id == id))
        obj = result.scalars().first()
        if hasattr(obj, "is_deleted"):
            # Soft delete if model has is_deleted field
            obj.is_deleted = True
            db.add(obj)
        else:
            # Hard delete otherwise
            await db.delete(obj)
        await db.commit()
        await db.refresh(obj)
        return obj
