from datetime import datetime
from typing import Any, ClassVar, Dict


class Base:
    """Base class for all models using DynamoDB

    This replaces the SQLAlchemy declarative base with a simple class
    that provides similar functionality for our DynamoDB models.
    """

    id: Any
    __name__: str

    # Allow defining indexes at the class level
    __indexes__: ClassVar[dict[str, str]] = {}

    @classmethod
    def get_table_name(cls) -> str:
        """Get the DynamoDB table name for this model"""
        return cls.__name__.lower()

    def to_dict(self) -> dict:
        """Convert the model to a dictionary for DynamoDB storage

        Handles special data types like datetime and bool values
        """
        result = {}
        # Skip private attributes and methods
        for attr in dir(self):
            if not attr.startswith("_") and not callable(getattr(self, attr)):
                value = getattr(self, attr)
                if value is not None:
                    # Handle datetime conversion to ISO format string
                    if isinstance(value, datetime):
                        result[attr] = value.isoformat()
                    # Handle boolean conversion (some DynamoDB implementations expect strings)
                    elif isinstance(value, bool):
                        result[attr] = str(value).lower()
                    # Use the value as is for other types
                    else:
                        result[attr] = value
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "Base":
        """Create a model instance from a dictionary

        Handles conversion from DynamoDB types to Python types
        """
        instance = cls()

        # If data is None, return empty instance
        if not data:
            return instance

        for key, value in data.items():
            if hasattr(instance, key):
                # Get the expected type for this attribute if possible
                attr_type = None
                current_val = getattr(instance, key, None)
                if current_val is not None:
                    attr_type = type(current_val)

                # Handle type conversions
                if attr_type == datetime and isinstance(value, str):
                    # Try to parse datetime from ISO format
                    try:
                        value = datetime.fromisoformat(value)
                    except ValueError:
                        # If parsing fails, keep the string value
                        pass
                elif attr_type == bool and isinstance(value, str):
                    # Convert 'true'/'false' strings to bool
                    value = value.lower() == "true"

                # Set the attribute with the converted value
                setattr(instance, key, value)

        return instance
