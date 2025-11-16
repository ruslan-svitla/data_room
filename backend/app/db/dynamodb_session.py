"""
DynamoDB session for the Data Room application.
This provides a compatibility layer similar to SQLAlchemy's AsyncSession but uses DynamoDB as the backend.
Allowing for a smoother transition from SQL to NoSQL.
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.db.base_class import Base

ModelType = TypeVar("ModelType", bound=Base)


class DynamoDBSession:
    """
    Simulates an AsyncSession but uses DynamoDB.
    This is a very simplified implementation for AWS Lambda deployment.
    """

    def __init__(self):
        """Initialize DynamoDB resources"""
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

        # Map tables with their environment variable names
        self.tables = {
            "users": settings.DYNAMODB_USERS_TABLE,
            "documents": settings.DYNAMODB_DOCUMENTS_TABLE,
            "folders": settings.DYNAMODB_FOLDERS_TABLE,
            "integrations": settings.DYNAMODB_INTEGRATIONS_TABLE,
            "document_shares": settings.DYNAMODB_DOCUMENT_SHARES_TABLE,
            "folder_shares": settings.DYNAMODB_FOLDER_SHARES_TABLE,
            "document_versions": settings.DYNAMODB_DOCUMENT_VERSIONS_TABLE,
        }

        # Map model names to table names
        self.model_table_map = {
            "User": "users",
            "Document": "documents",
            "Folder": "folders",
            "ExternalIntegration": "integrations",
            "DocumentShare": "document_shares",
            "FolderShare": "folder_shares",
            "DocumentVersion": "document_versions",
        }

        # Store objects to be committed
        self._to_add = []
        self._to_update = []
        self._to_delete = []

    async def add(self, obj: Base) -> None:
        """Add object to be saved on commit"""
        self._to_add.append(obj)

    async def delete(self, obj: Base) -> None:
        """Add object to be deleted on commit"""
        self._to_delete.append(obj)

    async def commit(self) -> None:
        """Commit changes to DynamoDB"""
        # Process additions
        for obj in self._to_add:
            item = self._model_to_dict(obj)
            table_name = self._get_table_name(obj.__class__.__name__)
            if not table_name:
                continue

            table = self.dynamodb.Table(table_name)
            try:
                table.put_item(Item=item)
            except ClientError as e:
                print(f"Error adding item to DynamoDB: {e}")
                raise

        # Process updates - similar to add but could use update_item for efficiency
        for obj in self._to_update:
            item = self._model_to_dict(obj)
            table_name = self._get_table_name(obj.__class__.__name__)
            if not table_name:
                continue

            table = self.dynamodb.Table(table_name)
            try:
                table.put_item(Item=item)
            except ClientError as e:
                print(f"Error updating item in DynamoDB: {e}")
                raise

        # Process deletions
        for obj in self._to_delete:
            table_name = self._get_table_name(obj.__class__.__name__)
            if not table_name:
                continue

            table = self.dynamodb.Table(table_name)
            try:
                table.delete_item(Key={"id": obj.id})
            except ClientError as e:
                print(f"Error deleting item from DynamoDB: {e}")
                raise

        # Clear saved objects
        self._to_add = []
        self._to_update = []
        self._to_delete = []

    async def rollback(self) -> None:
        """Rollback changes - clear pending operations"""
        self._to_add = []
        self._to_update = []
        self._to_delete = []

    async def get(self, model: type[ModelType], id: Any) -> ModelType | None:
        """Get an item by ID"""
        table_name = self._get_table_name(model.__name__)
        if not table_name:
            return None

        table = self.dynamodb.Table(table_name)
        try:
            response = table.get_item(Key={"id": id})
            item = response.get("Item")
            if item:
                obj = model()
                self._update_from_dict(obj, item)
                return obj
            return None
        except ClientError as e:
            print(f"Error getting item from DynamoDB: {e}")
            raise

    async def refresh(self, obj: Base) -> None:
        """Refresh an object from DynamoDB"""
        if not hasattr(obj, "id"):
            raise ValueError("Object must have an id attribute")

        table_name = self._get_table_name(obj.__class__.__name__)
        if not table_name:
            return

        table = self.dynamodb.Table(table_name)
        try:
            response = table.get_item(Key={"id": obj.id})
            if "Item" in response:
                self._update_from_dict(obj, response["Item"])
        except ClientError as e:
            print(f"Error getting item from DynamoDB: {e}")
            raise

    async def filter(self, model: type[ModelType], **kwargs) -> list[ModelType]:
        """Filter items by attributes"""
        table_name = self._get_table_name(model.__name__)
        if not table_name:
            return []

        table = self.dynamodb.Table(table_name)
        try:
            # Build filter expression
            filter_expression = None
            expression_values = {}
            expression_names = {}

            for key, value in kwargs.items():
                # Handle reserved words if necessary, but for now simple implementation
                placeholder = f":val_{key}"
                name_placeholder = f"#{key}"

                condition = f"{name_placeholder} = {placeholder}"
                if filter_expression:
                    filter_expression += f" AND {condition}"
                else:
                    filter_expression = condition

                expression_values[placeholder] = value
                expression_names[name_placeholder] = key

            if not filter_expression:
                response = table.scan()
            else:
                response = table.scan(
                    FilterExpression=filter_expression,
                    ExpressionAttributeValues=expression_values,
                    ExpressionAttributeNames=expression_names,
                )

            items = response.get("Items", [])
            results = []
            for item in items:
                obj = model()
                self._update_from_dict(obj, item)
                results.append(obj)

            return results

        except ClientError as e:
            print(f"Error filtering items in DynamoDB: {e}")
            raise

    async def execute(self, statement: Any) -> Any:
        """
        Simulate SQLAlchemy's execute method.
        This handles basic SQLAlchemy-style queries and translates them to DynamoDB operations.
        """
        # Convert SQLAlchemy query to DynamoDB operation
        # This is a simplified implementation that handles basic queries

        # Check if this is a select statement
        if hasattr(statement, "whereclause") and hasattr(statement, "froms"):
            # Extract information from SQLAlchemy query
            table_name = self._extract_table_name(statement)
            if not table_name:
                return DynamoDBResult()

            # Extract filter conditions
            filters = self._extract_filters(statement)

            # Get DynamoDB table
            table = self.dynamodb.Table(self.tables.get(table_name))

            # Execute appropriate DynamoDB query based on filters
            try:
                if not filters:
                    # No filters, do a scan
                    response = table.scan()
                    return DynamoDBResult(response.get("Items", []))

                # Check if we can use a key-based get_item
                if "id" in filters and len(filters) == 1:
                    response = table.get_item(Key={"id": filters["id"]})
                    item = response.get("Item")
                    return DynamoDBResult([item] if item else [])

                # For more complex filters, use scan with FilterExpression
                filter_expression = ""
                expression_values = {}

                for key, value in filters.items():
                    if filter_expression:
                        filter_expression += " AND "
                    filter_expression += f"{key} = :val_{key}"
                    expression_values[f":val_{key}"] = value

                if filter_expression:
                    response = table.scan(
                        FilterExpression=filter_expression,
                        ExpressionAttributeValues=expression_values,
                    )
                    return DynamoDBResult(response.get("Items", []))

                # Fallback to full scan
                response = table.scan()
                return DynamoDBResult(response.get("Items", []))

            except ClientError as e:
                print(f"Error executing DynamoDB query: {e}")
                return DynamoDBResult()

        # For other types of statements, return empty result
        return DynamoDBResult()

    def _extract_table_name(self, statement) -> str:
        """Extract table name from SQLAlchemy statement"""
        if hasattr(statement, "froms") and statement.froms:
            for table in statement.froms:
                if hasattr(table, "name"):
                    table_name = table.name
                    # Convert SQLAlchemy table name to our naming convention
                    # Example: convert 'document_shares' to 'document_shares'
                    return table_name.lower()
        return None

    def _extract_filters(self, statement) -> dict:
        """Extract filter conditions from SQLAlchemy statement"""
        filters = {}

        if hasattr(statement, "whereclause"):
            # Process WHERE clause to extract filters
            clause = statement.whereclause
            filters = self._process_where_clause(clause)

        return filters

    def _process_where_clause(self, clause) -> dict:
        """Process SQLAlchemy WHERE clause to extract filters"""
        filters = {}

        # Basic WHERE column=value extraction
        # This is a simplified implementation that only handles basic equality conditions
        if hasattr(clause, "left") and hasattr(clause, "right"):
            if hasattr(clause.left, "name") and hasattr(clause.right, "value"):
                filters[clause.left.name] = clause.right.value

        # Handle AND conditions
        if hasattr(clause, "clauses"):
            for subclause in clause.clauses:
                subfilters = self._process_where_clause(subclause)
                filters.update(subfilters)

        return filters

    def _get_table_name(self, model_name: str) -> str | None:
        """Get DynamoDB table name for a model"""
        if model_name not in self.model_table_map:
            return None

        table_key = self.model_table_map[model_name]
        return self.tables.get(table_key)

    def _model_to_dict(self, obj: Base) -> dict[str, Any]:
        """Convert model object to DynamoDB item dict

        This handles various data types appropriately for DynamoDB
        """
        result = {}

        # Handle objects that came from SQLAlchemy
        if hasattr(obj, "__table__") and hasattr(obj.__table__, "columns"):
            for column in obj.__table__.columns:
                name = column.name
                value = getattr(obj, name)
                if value is not None:
                    # Convert datetime to ISO format string for DynamoDB
                    if isinstance(value, datetime):
                        result[name] = value.isoformat()
                    # Convert boolean to string representation
                    elif isinstance(value, bool):
                        result[name] = str(value).lower()  # 'true' or 'false'
                    else:
                        result[name] = value
        else:
            # For non-SQLAlchemy objects, get all attributes
            for name in dir(obj):
                # Skip special and private attributes
                if not name.startswith("_") and not callable(getattr(obj, name)):
                    value = getattr(obj, name)
                    if value is not None:
                        # Convert datetime to ISO format string
                        if isinstance(value, datetime):
                            result[name] = value.isoformat()
                        # Convert boolean to string representation
                        elif isinstance(value, bool):
                            result[name] = str(value).lower()
                        else:
                            result[name] = value

        # Ensure the record has an id
        if "id" not in result and hasattr(obj, "id"):
            result["id"] = obj.id

        return result

    def _update_from_dict(self, obj: Base, data: dict[str, Any]) -> None:
        """Update model object from DynamoDB item dict"""
        for key, value in data.items():
            if hasattr(obj, key):
                # Handle type conversion
                attr_type = (
                    type(getattr(obj, key)) if getattr(obj, key) is not None else None
                )

                # If the attribute is a datetime and value is a string, parse it
                if attr_type == datetime and isinstance(value, str):
                    try:
                        setattr(obj, key, datetime.fromisoformat(value))
                    except ValueError:
                        # If parsing fails, keep the string value
                        setattr(obj, key, value)
                # If the attribute is a boolean and value is a string, convert it
                elif attr_type == bool and isinstance(value, str):
                    setattr(obj, key, value.lower() == "true")
                else:
                    # Default case: direct assignment
                    setattr(obj, key, value)


class DynamoDBResult:
    """
    Simulates the result of a SQLAlchemy execute call.
    """

    def __init__(self, items: list[dict[str, Any]] = None):
        """Initialize with optional items"""
        self.items = items or []

    def scalars(self) -> "DynamoDBScalars":
        """Return a scalars object"""
        return DynamoDBScalars(self.items)


class DynamoDBScalars:
    """
    Simulates SQLAlchemy's ScalarResult.
    """

    def __init__(self, items: list[dict[str, Any]]):
        """Initialize with items"""
        self.items = items

    def first(self) -> dict[str, Any] | None:
        """Return the first item or None"""
        return self.items[0] if self.items else None

    def all(self) -> list[dict[str, Any]]:
        """Return all items"""
        return self.items


async def get_db() -> DynamoDBSession:
    """Dependency to get DynamoDB session"""
    session = DynamoDBSession()
    try:
        yield session
    finally:
        # Nothing to close in DynamoDB
        pass
