from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.schemas.user import UserResponse


# Base Comment Schema
class CommentBase(BaseModel):
    comment: str


# Create Comment Schema
class CommentCreate(CommentBase):
    pass


# Response Comment Schema
class CommentResponse(CommentBase):
    id: int
    request_id: int
    author_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Detailed Comment Response with author information
class CommentDetailResponse(CommentResponse):
    author: Optional[UserResponse] = None
    
    class Config:
        from_attributes = True


# Response for listing comments
class CommentListResponse(BaseModel):
    items: List[CommentDetailResponse]
    
    class Config:
        from_attributes = True 