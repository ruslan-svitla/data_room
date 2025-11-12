from datetime import datetime

from pydantic import BaseModel


class DocumentBase(BaseModel):
    """Base schema for document data"""

    name: str | None = None
    description: str | None = None
    folder_id: str | None = None
    is_public: bool | None = False


class DocumentCreate(DocumentBase):
    """Schema for creating a document"""

    name: str


class DocumentUpdate(DocumentBase):
    """Schema for updating a document"""

    pass


class DocumentInDBBase(DocumentBase):
    """Base schema for document data retrieved from DB"""

    id: str
    name: str
    file_path: str
    file_type: str
    file_size: int
    owner_id: str
    created_at: datetime
    updated_at: datetime | None = None
    is_deleted: bool

    class Config:
        from_attributes = True


class Document(DocumentInDBBase):
    """Schema for complete document info (returned to client)"""

    pass


class DocumentWithVersion(Document):
    """Schema for document with version info"""

    current_version: int


# Document Version Schemas
class DocumentVersionBase(BaseModel):
    """Base schema for document version data"""

    document_id: str
    version_number: int


class DocumentVersionCreate(DocumentVersionBase):
    """Schema for creating a document version"""

    pass


class DocumentVersionInDBBase(DocumentVersionBase):
    """Base schema for document version data retrieved from DB"""

    id: str
    file_path: str
    file_size: int
    created_at: datetime
    created_by: str

    class Config:
        from_attributes = True


class DocumentVersion(DocumentVersionInDBBase):
    """Schema for complete document version info"""

    pass


# Document Share Schemas
class DocumentShareBase(BaseModel):
    """Base schema for document share data"""

    document_id: str
    user_id: str
    can_edit: bool | None = False
    can_delete: bool | None = False


class DocumentShareCreate(DocumentShareBase):
    """Schema for creating a document share"""

    pass


class DocumentShareUpdate(BaseModel):
    """Schema for updating document share permissions"""

    can_edit: bool | None = None
    can_delete: bool | None = None


class DocumentShareInDBBase(DocumentShareBase):
    """Base schema for document share data retrieved from DB"""

    id: str
    created_at: datetime
    updated_at: datetime | None = None

    class Config:
        from_attributes = True


class DocumentShare(DocumentShareInDBBase):
    """Schema for complete document share info"""

    pass
