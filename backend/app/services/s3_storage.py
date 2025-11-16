"""
AWS S3 adapter for file storage.
Used when running in AWS Lambda to store files in S3 instead of local filesystem.
"""

import os
import tempfile
import uuid
from pathlib import Path
from typing import BinaryIO, Optional

import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile

from app.core.config import settings


class S3Storage:
    """
    S3 storage adapter for file operations.
    """

    def __init__(self):
        """Initialize S3 client."""
        self.s3_client = boto3.client("s3", region_name=settings.AWS_REGION)
        self.bucket_name = settings.S3_BUCKET

        # Create temp directory if it doesn't exist
        if settings.IS_LAMBDA:
            os.makedirs("/tmp/uploads", exist_ok=True)

    async def save_file(self, file: UploadFile, filename: str | None = None) -> str:
        """
        Save a file to S3 bucket.
        Returns the S3 object key.
        """
        if not self.bucket_name:
            raise ValueError("S3_BUCKET setting is not configured")

        if not filename:
            filename = f"{uuid.uuid4()}-{file.filename}"

        # Create a temp file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Write uploaded file to temp file
            content = await file.read()
            temp_file.write(content)
            temp_file.flush()

            # Upload to S3
            try:
                self.s3_client.upload_file(
                    temp_file.name,
                    self.bucket_name,
                    filename,
                    ExtraArgs={"ContentType": file.content_type},
                )
            except ClientError as e:
                # Clean up temp file
                os.unlink(temp_file.name)
                raise ValueError(f"Failed to upload file to S3: {str(e)}")

            # Clean up temp file
            os.unlink(temp_file.name)

        return filename

    async def get_file(self, filename: str) -> Path:
        """
        Get a file from S3 bucket.
        Downloads to local temp storage and returns the path.
        """
        if not self.bucket_name:
            raise ValueError("S3_BUCKET setting is not configured")

        # Create temp file path
        local_path = Path(f"/tmp/uploads/{filename}")

        # Download from S3
        try:
            self.s3_client.download_file(self.bucket_name, filename, str(local_path))
        except ClientError as e:
            raise ValueError(f"Failed to download file from S3: {str(e)}")

        return local_path

    async def delete_file(self, filename: str) -> bool:
        """
        Delete a file from S3 bucket.
        Returns True if successful.
        """
        if not self.bucket_name:
            raise ValueError("S3_BUCKET setting is not configured")

        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=filename)
            return True
        except ClientError:
            return False
