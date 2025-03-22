from sqlalchemy import Boolean, Column, String, Enum, CheckConstraint
import enum
from sqlalchemy.orm import relationship
from app.db.base import BaseModel

class UserStatus(str, enum.Enum):
    ACTIVE = "active"         # Fully registered and active
    PENDING = "pending"       # EDS authenticated but registration incomplete
    INACTIVE = "inactive"     # Deactivated user

class UserRole(str, enum.Enum):
    EMPLOYEE = "employee"
    SUPERVISOR = "supervisor"
    ADMINISTRATOR = "administrator"

class User(BaseModel):
    __tablename__ = "users"

    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    iin = Column(String(12), unique=True, index=True, nullable=True)  # Kazakhstan IIN is 12 digits
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    status = Column(String, nullable=False, default=UserStatus.PENDING.value)
    role = Column(String, nullable=False, default=UserRole.EMPLOYEE.value)
    __table_args__ = (
        CheckConstraint(
            status.in_([status.value for status in UserStatus]),
            name='check_valid_status'
        ),
        CheckConstraint(
            role.in_([role.value for role in UserRole]),
            name='check_valid_role'
        ),
    )
    
    # New fields that might be collected during registration
    phone_number = Column(String, nullable=True)
    organization = Column(String, nullable=True)
    position = Column(String, nullable=True)
    
    # Relationships for requests
    created_requests = relationship("Request", foreign_keys="Request.created_by_id", back_populates="created_by")
    assigned_requests = relationship("Request", foreign_keys="Request.assigned_to_id", back_populates="assigned_to")
    
    # Relationship for comments and attachments
    comments = relationship("RequestComment", back_populates="author")
    attachments = relationship("RequestAttachment", back_populates="uploaded_by")