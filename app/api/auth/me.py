from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.user import User as UserSchema, UserUpdate
from app import crud

router = APIRouter()

@router.get("/me", response_model=UserSchema)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Get current user information.
    
    This endpoint returns information about the currently authenticated user.
    """
    return current_user

@router.put("/me", response_model=UserSchema)
async def update_me(
    *,
    db: Session = Depends(get_db),
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Update current user profile information.
    
    This endpoint allows users to update their profile information like:
    - full_name
    - email
    - phone_number
    - organization
    - position
    - password
    
    Note: Some fields may have additional validation or restrictions.
    """
    # Update user profile
    updated_user = crud.user.update(db=db, db_obj=current_user, obj_in=user_update)
    return updated_user 