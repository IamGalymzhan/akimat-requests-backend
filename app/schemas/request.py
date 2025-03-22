from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from enum import Enum

from app.models.request import RequestType, RequestStatus
from app.schemas.user import UserResponse
from app.schemas.department import DepartmentResponse


# Reuse the enums from models for consistency
class RequestTypeEnum(str, Enum):
    FINANCIAL = RequestType.FINANCIAL.value
    HR = RequestType.HR.value
    IT = RequestType.IT.value
    FACILITY = RequestType.FACILITY.value


class RequestStatusEnum(str, Enum):
    NEW = RequestStatus.NEW.value
    IN_PROCESS = RequestStatus.IN_PROCESS.value
    AWAITING = RequestStatus.AWAITING.value
    COMPLETED = RequestStatus.COMPLETED.value


# Base Request Schema
class RequestBase(BaseModel):
    title: str
    description: str
    request_type: RequestTypeEnum
    urgency: bool = False


# Create Request Schema
class RequestCreate(RequestBase):
    pass


# Update Request Schema - all fields are optional for updates
class RequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    request_type: Optional[RequestTypeEnum] = None
    urgency: Optional[bool] = None
    status: Optional[RequestStatusEnum] = None
    assigned_to_id: Optional[int] = None
    department_id: Optional[int] = None


# Response Request Schema
class RequestResponse(RequestBase):
    id: int
    status: RequestStatusEnum
    created_at: datetime
    updated_at: datetime
    created_by_id: int
    assigned_to_id: Optional[int] = None
    department_id: Optional[int] = None
    
    class Config:
        orm_mode = True


# Detailed Response including related entities
class RequestDetailResponse(RequestResponse):
    created_by: Optional[UserResponse] = None
    assigned_to: Optional[UserResponse] = None
    department: Optional[DepartmentResponse] = None
    
    class Config:
        orm_mode = True


# Response for paginated requests
class RequestListResponse(BaseModel):
    total: int
    items: List[RequestResponse]
    
    class Config:
        orm_mode = True 