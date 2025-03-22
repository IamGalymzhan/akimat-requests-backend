from sqlalchemy import Column, String, Text, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
import enum
from app.db.base import BaseModel

class RequestType(str, enum.Enum):
    FINANCIAL = "financial"
    HR = "hr"
    IT = "it"
    FACILITY = "facility"

class RequestStatus(str, enum.Enum):
    NEW = "new"
    IN_PROCESS = "in_process"
    AWAITING = "awaiting"
    COMPLETED = "completed"

class Request(BaseModel):
    __tablename__ = "requests"
    
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    # Use String type with check constraints instead of Enum
    request_type = Column(String, nullable=False)
    urgency = Column(Boolean, default=False)
    status = Column(String, nullable=False, default=RequestStatus.NEW.value)
    
    # Foreign keys linking to user and department
    created_by_id = Column(ForeignKey("users.id"), nullable=False)
    assigned_to_id = Column(ForeignKey("users.id"), nullable=True)
    department_id = Column(ForeignKey("departments.id"), nullable=True)
    
    # Check constraints for enums
    __table_args__ = (
        CheckConstraint(
            request_type.in_([t.value for t in RequestType]),
            name='check_valid_request_type'
        ),
        CheckConstraint(
            status.in_([s.value for s in RequestStatus]),
            name='check_valid_request_status'
        ),
    )
    
    # Relationships to link requests with users and departments
    created_by = relationship("User", foreign_keys=[created_by_id], back_populates="created_requests")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], back_populates="assigned_requests")
    department = relationship("Department", back_populates="requests")
    
    # Relationships for comments and attachments
    comments = relationship("RequestComment", back_populates="request", cascade="all, delete-orphan")
    attachments = relationship("RequestAttachment", back_populates="request", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Request(id={self.id}, title={self.title}, status={self.status})>" 