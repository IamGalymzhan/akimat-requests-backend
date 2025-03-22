from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.request_comment import RequestComment
from app.schemas.request_comment import CommentCreate


class CRUDRequestComment(CRUDBase[RequestComment, CommentCreate, CommentCreate]):
    def create_with_request_and_author(
        self, db: Session, *, obj_in: CommentCreate, request_id: int, author_id: int
    ) -> RequestComment:
        """Create a new comment with the specific request and author"""
        db_obj = RequestComment(
            **obj_in.dict(),
            request_id=request_id,
            author_id=author_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_multi_by_request(
        self, db: Session, *, request_id: int, skip: int = 0, limit: int = 100
    ) -> List[RequestComment]:
        """Get comments for a specific request"""
        return (
            db.query(self.model)
            .filter(RequestComment.request_id == request_id)
            .order_by(RequestComment.created_at)
            .offset(skip)
            .limit(limit)
            .all()
        )


request_comment = CRUDRequestComment(RequestComment) 