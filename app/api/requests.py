from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, UploadFile, File, Form
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.models.user import User, UserRole
from app.models.request import RequestStatus
from app.core.config import settings

router = APIRouter()


@router.post("/", response_model=schemas.RequestResponse, status_code=201)
def create_request(
    *,
    db: Session = Depends(deps.get_db),
    request_in: schemas.RequestCreate,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Create a new request.
    """
    request = crud.request.create_with_owner(
        db=db, obj_in=request_in, user_id=current_user.id
    )
    return request


@router.get("/", response_model=schemas.RequestListResponse)
def read_requests(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = Query(0, ge=0, description="Skip the first N items"),
    limit: int = Query(100, ge=1, le=100, description="Limit the number of items"),
    status: Optional[str] = Query(None, description="Filter by status"),
    request_type: Optional[str] = Query(None, description="Filter by request type"),
    department_id: Optional[int] = Query(None, description="Filter by department ID"),
    created_by_id: Optional[int] = Query(None, description="Filter by creator user ID"),
    search: Optional[str] = Query(None, description="Search term for title and description")
) -> Any:
    """
    Retrieve requests with filtering, pagination and search.
    """
    # Initialize filters
    filters = {}
    
    # Apply filters based on query parameters
    if status:
        filters["status"] = status
    if request_type:
        filters["request_type"] = request_type
    if department_id:
        filters["department_id"] = department_id
    
    # Handle created_by_id filter
    if created_by_id:
        # Only administrators and supervisors can filter by other users
        if current_user.role in [UserRole.ADMINISTRATOR.value, UserRole.SUPERVISOR.value]:
            filters["created_by_id"] = created_by_id
        else:
            # For employees, ignore the created_by_id parameter and only show their own requests
            pass
    
    # Apply role-based access control
    if current_user.role == UserRole.EMPLOYEE.value:
        # Regular employees can only see their own requests
        filters["created_by_id"] = current_user.id
    elif current_user.role == UserRole.SUPERVISOR.value and "department_id" not in filters and "created_by_id" not in filters:
        # Supervisors can see all requests in their department
        # This assumes supervisors have a department assigned (not implemented here)
        pass
    # Administrators can see all requests (no additional filters)
    
    # Get paginated requests
    result = crud.request.get_multi_paginated(
        db, skip=skip, limit=limit, filters=filters, search=search
    )
    
    return result


@router.get("/{id}", response_model=schemas.RequestDetailResponse)
def read_request(
    *,
    db: Session = Depends(deps.get_db),
    id: int = Path(..., title="The ID of the request to get", ge=1),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get request by ID.
    """
    request = crud.request.get(db=db, id=id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Check permissions
    if (current_user.role == UserRole.EMPLOYEE.value and 
        request.created_by_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return request


@router.put("/{id}", response_model=schemas.RequestResponse)
def update_request(
    *,
    db: Session = Depends(deps.get_db),
    id: int = Path(..., title="The ID of the request to update", ge=1),
    request_in: schemas.RequestUpdate,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Update a request.
    """
    request = crud.request.get(db=db, id=id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Check permissions based on user role
    if current_user.role == UserRole.EMPLOYEE.value:
        # Employees can only update their own requests and only certain fields
        if request.created_by_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        
        # Employees cannot change the status to COMPLETED
        if (request_in.status and 
            request_in.status == RequestStatus.COMPLETED.value and
            request.status != RequestStatus.COMPLETED.value):
            raise HTTPException(
                status_code=403, 
                detail="Employees cannot mark requests as completed"
            )
            
        # Employees cannot change assigned_to_id or department_id
        if request_in.assigned_to_id is not None or request_in.department_id is not None:
            raise HTTPException(
                status_code=403, 
                detail="Employees cannot change assignment or department"
            )
    
    # Update the request
    request = crud.request.update(db=db, db_obj=request, obj_in=request_in)
    return request


# Comments endpoints

@router.post("/{id}/comments", response_model=schemas.CommentResponse, status_code=201)
def create_comment(
    *,
    db: Session = Depends(deps.get_db),
    id: int = Path(..., title="The ID of the request to add a comment to", ge=1),
    comment_in: schemas.CommentCreate,
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Add a new comment to a specific request.
    """
    # Check if the request exists
    request = crud.request.get(db=db, id=id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Create the comment
    comment = crud.request_comment.create_with_request_and_author(
        db=db, 
        obj_in=comment_in, 
        request_id=id, 
        author_id=current_user.id
    )
    
    return comment


@router.get("/{id}/comments", response_model=schemas.CommentListResponse)
def read_comments(
    *,
    db: Session = Depends(deps.get_db),
    id: int = Path(..., title="The ID of the request to get comments for", ge=1),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = Query(0, ge=0, description="Skip the first N items"),
    limit: int = Query(100, ge=1, le=100, description="Limit the number of items")
) -> Any:
    """
    Get all comments for a specific request.
    """
    # Check if the request exists
    request = crud.request.get(db=db, id=id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Check permissions
    if (current_user.role == UserRole.EMPLOYEE.value and 
        request.created_by_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get comments
    comments = crud.request_comment.get_multi_by_request(
        db=db, request_id=id, skip=skip, limit=limit
    )
    
    return {"items": comments}


# File attachment endpoints

@router.post("/{id}/attachments", response_model=schemas.AttachmentResponse, status_code=201)
def upload_attachment(
    *,
    db: Session = Depends(deps.get_db),
    id: int = Path(..., title="The ID of the request to add an attachment to", ge=1),
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Upload a file attachment for a specific request.
    """
    # Check if the request exists
    request = crud.request.get(db=db, id=id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Check if user has permission (can only attach files to their own requests or if supervisor/admin)
    if (current_user.role == UserRole.EMPLOYEE.value and 
        request.created_by_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Check file size
    if file.size and file.size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413, 
            detail=f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE / (1024 * 1024):.1f} MB"
        )
    
    try:
        # Upload file and create attachment record
        attachment = crud.request_attachment.create_with_file(
            db=db, 
            file=file, 
            request_id=id, 
            user_id=current_user.id
        )
        return attachment
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file: {str(e)}"
        )


@router.get("/{id}/attachments", response_model=schemas.AttachmentListResponse)
def read_attachments(
    *,
    db: Session = Depends(deps.get_db),
    id: int = Path(..., title="The ID of the request to get attachments for", ge=1),
    current_user: User = Depends(deps.get_current_active_user),
    skip: int = Query(0, ge=0, description="Skip the first N items"),
    limit: int = Query(100, ge=1, le=100, description="Limit the number of items")
) -> Any:
    """
    Get all attachments for a specific request.
    """
    # Check if the request exists
    request = crud.request.get(db=db, id=id)
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Check permissions
    if (current_user.role == UserRole.EMPLOYEE.value and 
        request.created_by_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Get attachments
    attachments = crud.request_attachment.get_multi_by_request(
        db=db, request_id=id, skip=skip, limit=limit
    )
    
    return {"items": attachments} 