"""
DynamoDB service for handling data access operations.
This replaces the SQLAlchemy-based service classes with ones that use DynamoDB.
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.security import generate_uuid
from app.db.base_class import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class DynamoDBService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Base class for DynamoDB services that provides CRUD operations.
    """

    def __init__(
        self,
        model_class: type[ModelType],
        table_name: str,
    ):
        """
        Initialize the service with model class and table name.

        Args:
            model_class: The model class this service manages
            table_name: The DynamoDB table name
        """
        self.model_class = model_class
        self.table_name = table_name
        self.dynamodb = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
        self.table = self.dynamodb.Table(table_name)

    async def get(self, id: str) -> ModelType | None:
        """
        Get an item by ID.

        Args:
            id: The item ID

        Returns:
            The model instance if found, or None
        """
        try:
            response = self.table.get_item(Key={"id": id})
            item = response.get("Item")
            if item:
                return self.model_class.from_dict(item)
            return None
        except ClientError as e:
            print(f"Error getting item from DynamoDB: {e}")
            return None

    async def get_multi(
        self, skip: int = 0, limit: int = 100, filters: dict[str, Any] = None
    ) -> list[ModelType]:
        """
        Get multiple items with optional filters.

        Args:
            skip: Items to skip (pagination)
            limit: Maximum items to return
            filters: Filter conditions

        Returns:
            List of model instances
        """
        try:
            if not filters:
                # Simple scan
                response = self.table.scan(Limit=limit)
            else:
                # Build filter expression
                filter_expression = ""
                expression_values = {}

                for i, (key, value) in enumerate(filters.items()):
                    if filter_expression:
                        filter_expression += " AND "
                    filter_expression += f"{key} = :val{i}"
                    expression_values[f":val{i}"] = value

                response = self.table.scan(
                    FilterExpression=filter_expression,
                    ExpressionAttributeValues=expression_values,
                    Limit=limit,
                )

            items = response.get("Items", [])

            # Apply skip manually
            if skip > 0:
                items = items[skip:] if skip < len(items) else []

            # Convert to model instances
            return [self.model_class.from_dict(item) for item in items]
        except ClientError as e:
            print(f"Error scanning items from DynamoDB: {e}")
            return []

    async def get_by_index(
        self,
        index_name: str,
        key_name: str,
        key_value: Any,
        range_key_name: str = None,
        range_key_value: Any = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[ModelType]:
        """
        Query items using a GSI.

        Args:
            index_name: GSI name
            key_name: Hash key name
            key_value: Hash key value
            range_key_name: Optional range key name
            range_key_value: Optional range key value
            skip: Items to skip
            limit: Maximum items to return

        Returns:
            List of model instances
        """
        try:
            key_condition = f"{key_name} = :hashval"
            expression_values = {":hashval": key_value}

            # Add range key condition if provided
            if range_key_name and range_key_value is not None:
                key_condition += f" AND {range_key_name} = :rangeval"
                expression_values[":rangeval"] = range_key_value

            response = self.table.query(
                IndexName=index_name,
                KeyConditionExpression=key_condition,
                ExpressionAttributeValues=expression_values,
                Limit=limit,
            )

            items = response.get("Items", [])

            # Apply skip manually
            if skip > 0:
                items = items[skip:] if skip < len(items) else []

            # Convert to model instances
            return [self.model_class.from_dict(item) for item in items]
        except ClientError as e:
            print(f"Error querying by index in DynamoDB: {e}")
            return []

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        """
        Create a new item.

        Args:
            obj_in: Create schema with data

        Returns:
            Created model instance
        """
        # Generate a new ID if not provided
        if isinstance(obj_in, dict):
            data = obj_in
        elif hasattr(obj_in, "model_dump"):
            data = obj_in.model_dump()
        else:
            data = obj_in.dict()
        if "id" not in data or not data["id"]:
            data["id"] = generate_uuid()

        # Set timestamps
        now = datetime.now().isoformat()
        if "created_at" not in data:
            data["created_at"] = now
        if "updated_at" not in data:
            data["updated_at"] = now

        # Create model instance and put in DynamoDB
        obj = self.model_class.from_dict(data)
        try:
            self.table.put_item(Item=obj.to_dict())
            return obj
        except ClientError as e:
            print(f"Error creating item in DynamoDB: {e}")
            raise

    async def update(
        self, id: str, obj_in: UpdateSchemaType | dict[str, Any]
    ) -> ModelType | None:
        """
        Update an item by ID.

        Args:
            id: Item ID
            obj_in: Update schema or dict with fields to update

        Returns:
            Updated model instance or None if not found
        """
        try:
            # Get current item
            current = await self.get(id)
            if not current:
                return None

            # Convert input to dict if it's a schema
            if hasattr(obj_in, "model_dump"):
                update_data = obj_in.model_dump(exclude_unset=True)
            elif hasattr(obj_in, "dict"):
                update_data = obj_in.dict(exclude_unset=True)
            else:
                update_data = obj_in

            # Prepare update expression
            update_expression = "SET "
            expression_attr_values = {}
            expression_attr_names = {}

            # Add updated_at timestamp
            update_data["updated_at"] = datetime.now().isoformat()

            # Build expressions
            for i, (key, value) in enumerate(update_data.items()):
                if key != "id":  # Don't update primary key
                    # Handle boolean conversion to match Base.to_dict()
                    if isinstance(value, bool):
                        value = str(value).lower()

                    attr_name = f"#attr{i}"
                    attr_val = f":val{i}"
                    update_expression += f"{attr_name} = {attr_val}, "
                    expression_attr_names[attr_name] = key
                    expression_attr_values[attr_val] = value

            # Remove trailing comma and space
            update_expression = update_expression[:-2]

            # Execute update
            response = self.table.update_item(
                Key={"id": id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attr_names,
                ExpressionAttributeValues=expression_attr_values,
                ReturnValues="ALL_NEW",
            )

            # Convert result to model
            updated_item = response.get("Attributes", {})
            if updated_item:
                return self.model_class.from_dict(updated_item)
            return None

        except ClientError as e:
            print(f"Error updating item in DynamoDB: {e}")
            return None

    async def delete(self, id: str) -> bool:
        """
        Delete an item by ID.

        Args:
            id: Item ID

        Returns:
            True if deleted, False otherwise
        """
        try:
            self.table.delete_item(Key={"id": id})
            return True
        except ClientError as e:
            print(f"Error deleting item from DynamoDB: {e}")
            return False

    async def delete_all(self) -> bool:
        """
        Delete all items from the table. DANGEROUS!
        Only use for testing.

        Returns:
            True if successful
        """
        try:
            # Scan all items
            response = self.table.scan(ProjectionExpression="id")
            items = response.get("Items", [])

            # Delete each item
            with self.table.batch_writer() as batch:
                for item in items:
                    batch.delete_item(Key={"id": item["id"]})

            return True
        except ClientError as e:
            print(f"Error deleting all items from DynamoDB: {e}")
            return False
