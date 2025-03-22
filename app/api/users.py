from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_current_active_user, get_db
from app.models.user import User, UserRole, UserStatus
from app.schemas.user import User as UserSchema, AdminUserCreate
from app import crud

router = APIRouter()

def get_supervisor_or_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency to ensure the current user is a supervisor or administrator.
    Raises an HTTP 403 exception if the user doesn't have the required role.
    """
    if current_user.role not in [UserRole.SUPERVISOR.value, UserRole.ADMINISTRATOR.value]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Only supervisors and administrators can access this endpoint.",
        )
    return current_user

def get_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency to ensure the current user is an administrator.
    Raises an HTTP 403 exception if the user doesn't have the required role.
    """
    if current_user.role != UserRole.ADMINISTRATOR.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions. Only administrators can access this endpoint.",
        )
    return current_user

@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: AdminUserCreate,
    current_user: User = Depends(get_admin_user)
) -> User:
    """
    Create new user.
    
    This endpoint allows administrators to create new users, including both employees and supervisors.
    Only administrators can access this endpoint.
    """
    # Check if email already exists
    user_by_email = crud.user.get_by_email(db, email=user_in.email)
    if user_by_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    
    # Validate role
    if user_in.role not in [role.value for role in UserRole]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Must be one of: {', '.join([role.value for role in UserRole])}"
        )
        
    # Create new user
    user = crud.user.create(db=db, obj_in=user_in)
    return user

@router.get("/", response_model=List[UserSchema])
async def get_all_users(
    db: Session = Depends(get_db),
    _: User = Depends(get_supervisor_or_admin_user),
    skip: int = Query(0, ge=0, description="Skip the first N users"),
    limit: int = Query(100, ge=1, le=100, description="Limit the number of users returned"),
) -> List[User]:
    """
    Get all users with pagination.
    
    This endpoint returns a list of all users in the system.
    Both administrators and supervisors can access this endpoint.
    """
    users = crud.user.get_multi(db=db, skip=skip, limit=limit)
    return users

@router.get("/{user_id}", response_model=UserSchema)
async def get_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_supervisor_or_admin_user),
) -> User:
    """
    Get user information by ID.
    
    This endpoint returns information about a specific user by ID.
    Only supervisors and administrators can access this endpoint.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user 