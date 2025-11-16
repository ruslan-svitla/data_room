"""
Storage factory module for creating storage providers.
Supports both local filesystem storage and S3 storage.
"""

import logging
import os
from typing import Optional, Union

import boto3
from fastapi import UploadFile

from app.core.config import settings

# Configure logger
logger = logging.getLogger(__name__)


class StorageProvider:
    """Base storage provider interface"""

    async def save_file(self, file: UploadFile, filename: str | None = None) -> str:
        """Save a file and return the path"""
        raise NotImplementedError()

    async def save_content(
        self, content: bytes, filename: str, content_type: str = None
    ) -> str:
        """Save bytes content and return the path"""
        raise NotImplementedError()

    async def delete_file(self, filename: str) -> bool:
        """Delete a file and return success status"""
        raise NotImplementedError()

    def get_presigned_url(self, filename: str, expiration: int = 3600) -> str | None:
        """Get a presigned URL for downloading the file"""
        return None


class FileSystemStorage(StorageProvider):
    """Local filesystem storage provider"""

    def __init__(self, upload_folder: str = None):
        """Initialize with upload folder path"""
        self.upload_folder = upload_folder or settings.get_upload_path()
        # Ensure upload folder exists
        os.makedirs(self.upload_folder, exist_ok=True)
        logger.info(
            f"FileSystemStorage initialized with upload folder: {self.upload_folder}"
        )

    async def save_file(self, file: UploadFile, filename: str | None = None) -> str:
        """Save file to local filesystem"""
        if not filename:
            filename = file.filename

        file_path = os.path.join(self.upload_folder, filename)

        # Save file to disk
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        return file_path

    async def save_content(
        self, content: bytes, filename: str, content_type: str = None
    ) -> str:
        """Save bytes content to local filesystem"""
        file_path = os.path.join(self.upload_folder, filename)

        # Save file to disk
        with open(file_path, "wb") as f:
            f.write(content)

        return file_path

    async def delete_file(self, filename: str) -> bool:
        """Delete file from local filesystem"""
        if not filename:
            return False

        # If it's a full path, extract just the filename
        if os.path.sep in filename:
            filename = os.path.basename(filename)

        file_path = os.path.join(self.upload_folder, filename)

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
                return True
            else:
                logger.warning(f"File not found during deletion: {file_path}")
                return True  # Return True if file doesn't exist (already deleted)
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            return False


class S3Storage(StorageProvider):
    """AWS S3 storage provider"""

    def __init__(self, bucket_name: str = None):
        """Initialize with bucket name"""
        self.bucket_name = bucket_name or settings.S3_BUCKET

        if not self.bucket_name:
            raise ValueError("S3 bucket name not configured")

        # Initialize S3 client
        s3_kwargs = {"region_name": settings.AWS_REGION}

        # Add AWS credentials if provided
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            s3_kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
            s3_kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
            if settings.AWS_SESSION_TOKEN:
                s3_kwargs["aws_session_token"] = settings.AWS_SESSION_TOKEN

        # Add endpoint URL if provided (for local S3)
        if settings.AWS_ENDPOINT_URL:
            s3_kwargs["endpoint_url"] = settings.AWS_ENDPOINT_URL

        self.s3 = boto3.client("s3", **s3_kwargs)
        logger.info(f"S3Storage initialized with bucket: {self.bucket_name}")

    async def save_file(self, file: UploadFile, filename: str | None = None) -> str:
        """Save file to S3"""
        if not filename:
            filename = file.filename

        # Read file content
        content = await file.read()

        return await self.save_content(content, filename, file.content_type)

    async def save_content(
        self, content: bytes, filename: str, content_type: str = None
    ) -> str:
        """Save bytes content to S3"""
        try:
            # Upload to S3
            extra_args = {}
            if content_type:
                extra_args["ContentType"] = content_type

            self.s3.put_object(
                Bucket=self.bucket_name, Key=filename, Body=content, **extra_args
            )

            # Return S3 path (not a URL - just the key)
            return filename
        except Exception as e:
            logger.error(f"Error saving file to S3: {str(e)}")
            raise

    async def delete_file(self, filename: str) -> bool:
        """Delete file from S3"""
        if not filename:
            return False

        # S3 uses forward slashes, so convert if needed
        if os.path.sep in filename and os.path.sep != "/":
            filename = filename.replace(os.path.sep, "/")

        # If it's a full path with multiple components, keep only relevant parts
        if filename.startswith("/"):
            filename = filename[1:]

        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=filename)
            logger.info(f"Deleted file from S3: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file from S3: {str(e)}")
            return False

    def get_presigned_url(self, filename: str, expiration: int = 3600) -> str | None:
        """Get a presigned URL for downloading the file"""
        original_filename = filename.split("-")[-1]
        try:
            response = self.s3.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": filename,
                    "ResponseContentDisposition": f'attachment; filename="{original_filename}"',
                },
                ExpiresIn=expiration,
            )
            return response
        except Exception as e:
            logger.error(f"Error generating presigned URL: {str(e)}")
            return None


def get_storage_provider() -> FileSystemStorage | S3Storage:
    """Get the appropriate storage provider based on configuration"""
    # Use S3 if bucket is configured
    if settings.S3_BUCKET:
        logger.info("Using S3 storage provider")
        return S3Storage()

    # Otherwise use filesystem
    logger.info("Using FileSystem storage provider")
    return FileSystemStorage()
