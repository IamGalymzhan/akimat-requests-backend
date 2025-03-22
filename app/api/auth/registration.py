from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from typing import Optional
from jose import jwt
import logging

from app.db.session import get_db
from app.models.user import User, UserStatus
from app.api.auth.eds.kz_eds import get_current_user_from_token, KZEDSAuthenticator, EDSConfig
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

class RegistrationData(BaseModel):
    """Registration data for completing user profile"""
    email: EmailStr
    phone_number: str = Field(..., min_length=10, max_length=15)
    organization: Optional[str] = Field(None, max_length=100)
    position: Optional[str] = Field(None, max_length=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "phone_number": "+77771234567",
                "organization": "Example Company",
                "position": "Manager"
            }
        }

class RegistrationResponse(BaseModel):
    """Registration completion response"""
    message: str
    access_token: str
    token_type: str
    role: str

async def verify_registration_token(request: Request, user: User = Depends(get_current_user_from_token)):
    """
    Verify that the user is eligible for registration completion based on status
    """
    # Set up logging
    logger.info(f"Verifying user eligibility for registration: id={user.id}, iin={user.iin}, status={user.status}")
    
    # Only users in PENDING status can complete registration
    if user.status != UserStatus.PENDING.value:
        logger.warning(f"Access denied: User is not in PENDING status. User status: {user.status}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only users in PENDING status can complete registration"
        )
    
    logger.info(f"User is eligible for registration completion: id={user.id}")
    return user

@router.put("/complete", response_model=RegistrationResponse)
async def complete_registration(
    registration_data: RegistrationData,
    user: User = Depends(verify_registration_token),
    db: Session = Depends(get_db)
):
    """
    ## Complete User Registration
    
    This endpoint allows users who have authenticated with EDS to complete their registration
    by providing additional information.
    
    ### Request
    - **email**: User's email address
    - **phone_number**: User's phone number
    - **organization**: (Optional) User's organization
    - **position**: (Optional) User's position
    
    ### Response
    - **message**: Success message
    - **access_token**: New JWT token with full access
    - **token_type**: Token type (bearer)
    - **role**: User's role
    
    ### Errors
    - **401 Unauthorized**: Invalid or expired token
    - **403 Forbidden**: User is not in pending status
    - **400 Bad Request**: Invalid registration data
    
    ### Notes
    - Requires a valid registration token obtained from EDS login
    - After successful registration, the user's status will be updated to ACTIVE
    """
    # Update user information
    user.email = registration_data.email
    user.phone_number = registration_data.phone_number
    user.organization = registration_data.organization
    user.position = registration_data.position
    user.status = UserStatus.ACTIVE.value
    
    # Save changes
    db.commit()
    db.refresh(user)
    
    # Create a new access token
    access_token = KZEDSAuthenticator.create_access_token(
        data={"iin": user.iin}
    )
    
    logger.info(f"Registration completed successfully for user id: {user.id}, iin: {user.iin}")
    
    return {
        "message": "Registration completed successfully",
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role
    } 