from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    phone_number: Optional[str] = None
    organization: Optional[str] = None
    position: Optional[str] = None
    iin: Optional[str] = None
    status: Optional[str] = None
    role: Optional[str] = None

class UserCreate(UserBase):
    email: EmailStr
    password: str
    full_name: str

class AdminUserCreate(UserCreate):
    role: str
    phone_number: Optional[str] = None
    organization: Optional[str] = None
    position: Optional[str] = None
    status: Optional[str] = "active"  # Default to active

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserInDBBase(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class User(UserInDBBase):
    pass

# New schema for responding in other models' relationships
class UserResponse(BaseModel):
    id: int
    email: Optional[str] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    organization: Optional[str] = None
    position: Optional[str] = None
    role: Optional[str] = None
    
    class Config:
        from_attributes = True

class UserInDB(UserInDBBase):
    hashed_password: str

# Maintain backward compatibility with OAuth2 
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str | None = None

class TokenPayload(BaseModel):
    sub: Optional[int] = None

# New schema for custom login endpoint
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# New schema for login response with user information
class LoginResponse(BaseModel):
    token: str
    user: User 

# Export all schemas
__all__ = [
    "UserBase", 
    "UserCreate", 
    "AdminUserCreate",
    "UserUpdate", 
    "User", 
    "UserInDB",
    "Token",
    "TokenPayload",
    "LoginRequest",
    "LoginResponse",
    "UserResponse"
] 