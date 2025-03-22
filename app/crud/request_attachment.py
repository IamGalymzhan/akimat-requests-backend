from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import os
import shutil
from pathlib import Path
from datetime import datetime
from fastapi import UploadFile

from app.crud.base import CRUDBase
from app.models.request_attachment import RequestAttachment
from app.core.config import settings


class CRUDRequestAttachment(CRUDBase[RequestAttachment, Dict[str, Any], Dict[str, Any]]):
    def create_with_file(
        self, 
        db: Session, 
        *, 
        file: UploadFile, 
        request_id: int, 
        user_id: int
    ) -> RequestAttachment:
        """Upload a file and create an attachment record"""
        
        # Create uploads directory if it doesn't exist
        uploads_dir = Path(settings.UPLOADS_DIR) / f"request_{request_id}"
        uploads_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate a unique filename to avoid collisions
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = file.filename.replace(" ", "_")
        unique_filename = f"{timestamp}_{safe_filename}"
        file_path = uploads_dir / unique_filename
        
        # Save the file
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        human_file_size = self._get_human_readable_size(file_size)
        
        # Create attachment record
        db_obj = RequestAttachment(
            request_id=request_id,
            uploaded_by_id=user_id,
            filename=file.filename,
            file_path=str(file_path),
            file_size=human_file_size,
            mime_type=file.content_type or "application/octet-stream"
        )
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def _get_human_readable_size(self, size_bytes: int) -> str:
        """Convert bytes to human-readable file size"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"  # If we somehow have petabyte files
    
    def get_multi_by_request(
        self, db: Session, *, request_id: int, skip: int = 0, limit: int = 100
    ) -> List[RequestAttachment]:
        """Get attachments for a specific request"""
        return (
            db.query(self.model)
            .filter(RequestAttachment.request_id == request_id)
            .order_by(RequestAttachment.created_at)
            .offset(skip)
            .limit(limit)
            .all()
        )


request_attachment = CRUDRequestAttachment(RequestAttachment) 