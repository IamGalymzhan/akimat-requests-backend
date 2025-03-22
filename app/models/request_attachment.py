from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import BaseModel

class RequestAttachment(BaseModel):
    __tablename__ = "request_attachments"
    
    request_id = Column(ForeignKey("requests.id"), nullable=False)
    uploaded_by_id = Column(ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(String, nullable=False)  # Store size as a string, e.g., "1.2 MB"
    mime_type = Column(String, nullable=False)
    
    # Relationships
    request = relationship("Request", back_populates="attachments")
    uploaded_by = relationship("User", back_populates="attachments")
    
    def __repr__(self):
        return f"<RequestAttachment(id={self.id}, filename={self.filename}, request_id={self.request_id})>" 