from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.schemas.user import UserResponse


# Response schema for attachment
class AttachmentResponse(BaseModel):
    id: int
    request_id: int
    uploaded_by_id: int
    filename: str
    file_path: str
    file_size: str
    mime_type: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Detailed attachment response with uploader information
class AttachmentDetailResponse(AttachmentResponse):
    uploaded_by: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True


# Response for listing attachments
class AttachmentListResponse(BaseModel):
    items: List[AttachmentDetailResponse]
    
    class Config:
        from_attributes = True 