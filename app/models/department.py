from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.db.base import BaseModel

class Department(BaseModel):
    __tablename__ = "departments"

    name = Column(String, nullable=False, index=True, unique=True)
    
    # Relationship for requests
    requests = relationship("Request", back_populates="department") 