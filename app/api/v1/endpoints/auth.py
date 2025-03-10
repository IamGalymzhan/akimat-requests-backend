from datetime import timedelta
from typing import Any, Optional
from fastapi import APIRouter, Body, Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app import crud, schemas
from app.api import deps
from app.core import security
from app.core.config import settings

router = APIRouter()

class LoginModel(BaseModel):
    email: str
    password: str

# Standard OAuth2 endpoint for compatibility with OAuth2 clients
@router.post("/oauth-token", response_model=schemas.Token)
def login_for_access_token(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    
    Note: After obtaining the token, you can get user information by:
    1. Using the /api/v1/users/me endpoint with the token
    2. Or by using the /api/v1/auth/login endpoint instead, which returns both token and user info
    """
    user = crud.user.authenticate(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return {
        "access_token": security.create_access_token(
            user.id, expires_delta=access_token_expires
        ),
        "token_type": "bearer",
    }

@router.post("/login", response_model=schemas.LoginResponse)
async def login(
    request: Request,
    db: Session = Depends(deps.get_db),
) -> Any:
    """
    Login endpoint that accepts both OAuth2 form data and direct JSON with email/password
    Returns a token and user information
    """
    content_type = request.headers.get("Content-Type", "")
    
    # Handle form data (OAuth2 standard approach)
    if "form" in content_type.lower() or "x-www-form-urlencoded" in content_type.lower():
        try:
            form = await request.form()
            username = form.get("username")
            password = form.get("password")
            
            if not username or not password:
                raise HTTPException(
                    status_code=400, 
                    detail="Username and password required in form data"
                )
                
            # Use the form data for authentication
            auth_email = username
            auth_password = password
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Error processing form data: {str(e)}"
            )
    # Handle JSON body
    else:
        try:
            body = await request.json()
            auth_email = body.get("email")
            auth_password = body.get("password")
            
            if not auth_email or not auth_password:
                raise HTTPException(
                    status_code=400, 
                    detail="Email and password required in JSON body"
                )
        except Exception as e:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid JSON request format: {str(e)}"
            )
    
    # Authenticate user
    user = crud.user.authenticate(
        db, email=auth_email, password=auth_password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    # Generate token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.id, expires_delta=access_token_expires
    )
    
    # Return token and user information
    return {
        "token": access_token,
        "user": user
    }

@router.post("/signup", response_model=schemas.User)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
) -> Any:
    """
    Create new user.
    """
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = crud.user.create(db, obj_in=user_in)
    return user 