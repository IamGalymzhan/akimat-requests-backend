from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt
import uuid
import logging

from app.db.session import get_db
from app.models.user import User, UserRole, UserStatus
from app.core.config import settings
from app.api.auth.eds.kz_eds import KZEDSAuthenticator

router = APIRouter()
logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone_number: str
    organization: str | None = None
    position: str | None = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str

class EmailPasswordForm(BaseModel):
    email: EmailStr
    password: str

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()

def generate_pseudo_iin() -> str:
    """Generate a unique identifier to be used as IIN for email-based users"""
    # Use uuid4 to generate a random string and take first 12 characters
    # Real IINs are 12-digit numbers, but this is just a placeholder for email users
    return f"E{uuid.uuid4().hex[:11]}"

@router.post("/register", response_model=TokenResponse)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user with email and password
    """
    # Check if user already exists
    db_user = get_user_by_email(db, user_data.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Generate a pseudo-IIN for email-based users
    pseudo_iin = generate_pseudo_iin()
    logger.info(f"Generated pseudo-IIN {pseudo_iin} for new email user")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        phone_number=user_data.phone_number,
        organization=user_data.organization,
        position=user_data.position,
        status=UserStatus.ACTIVE.value,
        role=UserRole.ADMINISTRATOR.value,
        is_active=True,
        iin=pseudo_iin  # Add the pseudo-IIN
    )
    
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user"
        )
    
    logger.info(f"User registered successfully: id={user.id}, email={user.email}, iin={user.iin}")
    
    # Create access token using KZEDSAuthenticator for consistency
    access_token = KZEDSAuthenticator.create_access_token(
        data={"iin": user.iin}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role
    }

@router.post("/login", response_model=TokenResponse)
async def login_user(
    form_data: EmailPasswordForm,
    db: Session = Depends(get_db)
):
    """
    Login with email and password
    """
    user = get_user_by_email(db, form_data.email)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Check if user has an IIN, if not, generate one
    if not user.iin:
        user.iin = generate_pseudo_iin()
        db.commit()
        db.refresh(user)
        logger.info(f"Generated pseudo-IIN {user.iin} for existing email user id={user.id}")
    
    logger.info(f"User logged in successfully: id={user.id}, email={user.email}, iin={user.iin}")
    
    # Create access token using KZEDSAuthenticator for consistency
    access_token = KZEDSAuthenticator.create_access_token(
        data={"iin": user.iin}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role
    }

# Keep the original OAuth2 endpoint for compatibility with standard OAuth clients
@router.post("/oauth/token", response_model=TokenResponse)
async def login_oauth(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Standard OAuth2 login endpoint that accepts username as email
    """
    user = get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Check if user has an IIN, if not, generate one
    if not user.iin:
        user.iin = generate_pseudo_iin()
        db.commit()
        db.refresh(user)
        logger.info(f"Generated pseudo-IIN {user.iin} for existing email user in OAuth flow, id={user.id}")
    
    logger.info(f"User authenticated via OAuth: id={user.id}, email={user.email}, iin={user.iin}")
    
    # Create access token using KZEDSAuthenticator for consistency
    access_token = KZEDSAuthenticator.create_access_token(
        data={"iin": user.iin}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role
    } 