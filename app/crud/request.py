from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.crud.base import CRUDBase
from app.models.request import Request, RequestType
from app.schemas.request import RequestCreate, RequestUpdate


class CRUDRequest(CRUDBase[Request, RequestCreate, RequestUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: RequestCreate, user_id: int
    ) -> Request:
        """Create a new request with the current user as the owner"""
        db_obj = Request(
            **obj_in.dict(),
            created_by_id=user_id,
            # Auto-assign department based on request type
            department_id=self._get_department_id_for_request_type(db, obj_in.request_type)
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def _get_department_id_for_request_type(self, db: Session, request_type: str) -> Optional[int]:
        """Helper method to determine department ID based on request type"""
        # This is a simplistic implementation
        # In a real app, you might have a mapping table for request types to departments
        from app.models.department import Department
        
        # Example mapping logic - can be adjusted based on actual department names
        type_to_dept = {
            RequestType.FINANCIAL.value: "Finance",
            RequestType.HR.value: "Human Resources",
            RequestType.IT.value: "IT Support",
            RequestType.FACILITY.value: "Facilities"
        }
        
        department_name = type_to_dept.get(request_type)
        if not department_name:
            return None
            
        department = db.query(Department).filter(Department.name == department_name).first()
        return department.id if department else None
    
    def get_multi_by_owner(
        self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Request]:
        """Get requests created by a specific user"""
        return (
            db.query(self.model)
            .filter(Request.created_by_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
        
    def get_multi_paginated(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get requests with pagination, filtering and search"""
        query = db.query(self.model)
        
        # Apply filters if provided
        if filters:
            if "status" in filters:
                query = query.filter(Request.status == filters["status"])
            if "request_type" in filters:
                query = query.filter(Request.request_type == filters["request_type"])
            if "department_id" in filters:
                query = query.filter(Request.department_id == filters["department_id"])
            if "created_by_id" in filters:
                query = query.filter(Request.created_by_id == filters["created_by_id"])
            if "assigned_to_id" in filters:
                query = query.filter(Request.assigned_to_id == filters["assigned_to_id"])
            if "urgency" in filters:
                query = query.filter(Request.urgency == filters["urgency"])
                
        # Apply search on title and description if provided
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Request.title.ilike(search_term)) | 
                (Request.description.ilike(search_term))
            )
            
        # Get total count before applying pagination
        total = query.count()
        
        # Apply pagination
        items = query.offset(skip).limit(limit).all()
        
        return {
            "total": total,
            "items": items
        }


request = CRUDRequest(Request) 