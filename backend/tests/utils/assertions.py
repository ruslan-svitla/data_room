"""Custom assertions for test validation"""

from typing import Any, Optional

import boto3

from app.core.config import settings
from app.models.document import Document


def assert_document_equals(
    actual: Document,
    expected: Document,
    ignore_fields: list[str] | None = None,
) -> None:
    """
    Assert that two document objects are equal

    Args:
        actual: Actual document object
        expected: Expected document object
        ignore_fields: List of field names to ignore in comparison
    """
    ignore_fields = ignore_fields or []

    # Convert to dicts for comparison
    actual_dict = actual.to_dict() if hasattr(actual, "to_dict") else actual.__dict__
    expected_dict = (
        expected.to_dict() if hasattr(expected, "to_dict") else expected.__dict__
    )

    for key in expected_dict:
        if key in ignore_fields:
            continue

        assert key in actual_dict, f"Field '{key}' missing in actual document"
        assert actual_dict[key] == expected_dict[key], (
            f"Field '{key}' mismatch: {actual_dict[key]} != {expected_dict[key]}"
        )


def assert_s3_file_exists(
    file_path: str,
    bucket: str | None = None,
) -> None:
    """
    Assert that a file exists in S3

    Args:
        file_path: Path to file in S3
        bucket: S3 bucket name (uses default if not provided)
    """
    bucket = bucket or settings.S3_BUCKET
    s3_client = boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or "testing",
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or "testing",
    )

    try:
        s3_client.head_object(Bucket=bucket, Key=file_path)
    except s3_client.exceptions.NoSuchKey:
        raise AssertionError(
            f"File '{file_path}' does not exist in S3 bucket '{bucket}'"
        )


def assert_s3_file_deleted(
    file_path: str,
    bucket: str | None = None,
) -> None:
    """
    Assert that a file does NOT exist in S3

    Args:
        file_path: Path to file in S3
        bucket: S3 bucket name (uses default if not provided)
    """
    bucket = bucket or settings.S3_BUCKET
    s3_client = boto3.client(
        "s3",
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID or "testing",
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or "testing",
    )

    try:
        s3_client.head_object(Bucket=bucket, Key=file_path)
        raise AssertionError(f"File '{file_path}' still exists in S3 bucket '{bucket}'")
    except s3_client.exceptions.NoSuchKey:
        # File doesn't exist - this is what we want
        pass


def assert_response_has_keys(
    response_data: dict[str, Any],
    required_keys: list[str],
) -> None:
    """
    Assert that a response dictionary contains all required keys

    Args:
        response_data: Response data dictionary
        required_keys: List of required key names
    """
    for key in required_keys:
        assert key in response_data, f"Required key '{key}' missing from response"


def assert_status_code(
    actual: int,
    expected: int,
    message: str | None = None,
) -> None:
    """
    Assert HTTP status code with custom message

    Args:
        actual: Actual status code
        expected: Expected status code
        message: Optional custom error message
    """
    default_message = f"Expected status code {expected}, got {actual}"
    assert actual == expected, message or default_message
