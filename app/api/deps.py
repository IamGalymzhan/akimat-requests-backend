from typing import Generator, Optional, Union
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError, BaseModel
from sqlalchemy.orm import Session
import re
import logging

from app.core import security
from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.user import TokenPayload

logger = logging.getLogger(__name__)

# Update OAuth2 configuration to use the dedicated OAuth2 endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_STR}/auth/email/oauth/token")

class IINTokenData(BaseModel):
    iin: str

def get_db() -> Generator:
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

# Custom token extractor that can handle both formats
async def get_token_from_request(request: Request) -> Optional[str]:
    authorization = request.headers.get("Authorization")
    if not authorization:
        return None
        
    # Extract token from "Bearer {token}" format
    token_match = re.match(r"Bearer\s+(.+)", authorization)
    if token_match:
        return token_match.group(1)
    
    return None

# Primary token validation - uses IIN to identify users
def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    try:
        logger.info("Validating token in get_current_user")
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        
        # Get IIN from token
        iin: str = payload.get("iin")
        if iin is None:
            logger.warning("Token missing required 'iin' claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials - missing IIN",
            )
            
        token_data = IINTokenData(iin=iin)
    except (JWTError, ValidationError) as e:
        logger.error(f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
        
    # Find user by IIN
    user = db.query(User).filter(User.iin == token_data.iin).first()
    if not user:
        logger.warning(f"No user found with IIN: {token_data.iin}")
        raise HTTPException(status_code=404, detail="User not found")
        
    logger.info(f"User authenticated via token: id={user.id}, iin={user.iin}")
    return user

# Helper dependency to ensure user is active
def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user 