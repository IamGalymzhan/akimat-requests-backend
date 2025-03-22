from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import BaseModel

class RequestComment(BaseModel):
    __tablename__ = "request_comments"
    
    request_id = Column(ForeignKey("requests.id"), nullable=False)
    author_id = Column(ForeignKey("users.id"), nullable=False)
    comment = Column(Text, nullable=False)
    
    # Relationships
    request = relationship("Request", back_populates="comments")
    author = relationship("User", back_populates="comments")
    
    def __repr__(self):
        return f"<RequestComment(id={self.id}, author_id={self.author_id}, request_id={self.request_id})>" 