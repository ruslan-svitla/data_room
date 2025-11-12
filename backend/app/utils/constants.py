"""
Application constants
"""

from enum import Enum


# User related constants
class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class DocumentStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class PermissionType(str, Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


# File size limits (in bytes)
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
MAX_TOTAL_STORAGE_PER_USER = 1024 * 1024 * 1024  # 1GB

# Authentication related
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"
PASSWORD_RESET_TOKEN_EXPIRE_HOURS = 24

# Pagination defaults
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Document versioning
MAX_VERSIONS_PER_DOCUMENT = 100

# Date formats
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
DATETIME_FORMAT_WITH_TZ = "%Y-%m-%dT%H:%M:%S%z"

# Common file mime types
MIME_TYPES = {
    # Documents
    "pdf": "application/pdf",
    "doc": "application/msword",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xls": "application/vnd.ms-excel",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "ppt": "application/vnd.ms-powerpoint",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    # Images
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    # Text
    "txt": "text/plain",
    "csv": "text/csv",
    "html": "text/html",
    "xml": "application/xml",
    "json": "application/json",
    # Archive
    "zip": "application/zip",
    "tar": "application/x-tar",
    "gz": "application/gzip",
}

# Allowed file extensions
ALLOWED_DOCUMENT_EXTENSIONS = {
    # Documents
    "pdf",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "ppt",
    "pptx",
    # Images
    "jpg",
    "jpeg",
    "png",
    "gif",
    # Text
    "txt",
    "csv",
    "html",
    "xml",
    "json",
    # Archive
    "zip",
    "tar",
    "gz",
}
