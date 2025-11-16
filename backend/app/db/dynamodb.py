"""
DynamoDB adapter for database operations.
This file provides an alternative implementation for the database operations
that work with DynamoDB instead of SQLite when running in AWS Lambda.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar

import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel

from app.core.config import settings
from app.db.base_class import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class DynamoDBCrud:
    """
    Generic CRUD operations using DynamoDB.
    """

    def __init__(self, table_name: str):
        """Initialize with table name."""
        self.table_name = table_name

        # Configure DynamoDB client with optional credentials
        dynamodb_kwargs = {"region_name": settings.AWS_REGION}

        # Add AWS credentials if provided
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            dynamodb_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            dynamodb_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
            if settings.AWS_SESSION_TOKEN:
                dynamodb_kwargs["aws_session_token"] = settings.AWS_SESSION_TOKEN

        # Add endpoint URL if provided (for local DynamoDB)
        if settings.AWS_ENDPOINT_URL:
            dynamodb_kwargs["endpoint_url"] = settings.AWS_ENDPOINT_URL

        self.dynamodb = boto3.resource("dynamodb", **dynamodb_kwargs)
        self.table = self.dynamodb.Table(table_name)

    async def create(self, obj_in: CreateSchemaType) -> dict[str, Any]:
        """Create a new item."""
        item = obj_in.model_dump()
        try:
            self.table.put_item(Item=item)
            return item
        except ClientError as e:
            print(f"Error creating item in DynamoDB: {e}")
            raise

    async def get(self, id: str) -> dict[str, Any] | None:
        """Get item by ID."""
        try:
            response = self.table.get_item(Key={"id": id})
            return response.get("Item")
        except ClientError as e:
            print(f"Error retrieving item from DynamoDB: {e}")
            raise

    async def get_multi(self, skip: int = 0, limit: int = 100) -> list[dict[str, Any]]:
        """Get multiple items with pagination."""
        try:
            response = self.table.scan(Limit=limit)
            items = response.get("Items", [])

            # Apply skip manually since DynamoDB doesn't have direct offset
            if skip > 0:
                items = items[skip:] if skip < len(items) else []

            return items
        except ClientError as e:
            print(f"Error scanning items from DynamoDB: {e}")
            raise

    async def update(self, id: str, obj_in: UpdateSchemaType) -> dict[str, Any]:
        """Update an item."""
        update_data = obj_in.model_dump(exclude_unset=True)

        # Prepare update expression
        update_expression = "SET "
        expression_attribute_values = {}

        for key, value in update_data.items():
            if key != "id":  # Don't update the primary key
                update_expression += f"{key} = :{key}, "
                expression_attribute_values[f":{key}"] = value

        update_expression = update_expression[:-2]  # Remove trailing comma and space

        try:
            response = self.table.update_item(
                Key={"id": id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="ALL_NEW",
            )
            return response.get("Attributes", {})
        except ClientError as e:
            print(f"Error updating item in DynamoDB: {e}")
            raise

    async def delete(self, id: str) -> dict[str, Any]:
        """Delete an item."""
        try:
            response = self.table.delete_item(Key={"id": id}, ReturnValues="ALL_OLD")
            return response.get("Attributes", {})
        except ClientError as e:
            print(f"Error deleting item from DynamoDB: {e}")
            raise

    async def get_by_field(
        self, field_name: str, field_value: Any
    ) -> list[dict[str, Any]]:
        """Get items by a specific field value."""
        try:
            response = self.table.scan(
                FilterExpression=f"{field_name} = :value",
                ExpressionAttributeValues={":value": field_value},
            )
            return response.get("Items", [])
        except ClientError as e:
            print(f"Error searching items by field in DynamoDB: {e}")
            raise
