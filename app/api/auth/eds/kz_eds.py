import base64
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Optional, Union, Tuple

from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, UserStatus

# Create OAuth2 scheme for token authentication
# auto_error=False means it won't automatically raise HTTP 401 
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_STR}/auth/eds/login",
    auto_error=False
)

logger = logging.getLogger(__name__)

class EDSConfig:
    # NCANode API endpoint
    NCANODE_API_ENDPOINT = settings.NCANODE_API_ENDPOINT
    
    # JWT Settings
    JWT_SECRET_KEY = settings.SECRET_KEY
    JWT_ALGORITHM = settings.ALGORITHM
    ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    iin: Optional[str] = None

class KZEDSAuthenticator:
    """
    Class for handling Kazakhstan eGov EDS authentication using NCANode
    """
    @staticmethod
    def verify_xml_signature(signed_xml: str) -> bool:
        """
        Verify the XML digital signature using NCANode
        """
        try:
            # Create request payload for NCANode
            payload = {
                "xml": signed_xml,
                "revocationCheck": ["OCSP"],
            }
            
            # Send request to NCANode with timeout
            response = requests.post(
                f"{EDSConfig.NCANODE_API_ENDPOINT}/xml/verify", 
                json=payload,
                timeout=10  # 10 seconds timeout
            )
            
            # Log the response for debugging
            logger.info(f"NCANode verify response: {response.text}")
            
            # Parse response
            result = response.json()
            
            # Check if verification was successful
            if result.get("status") == 200 and result.get("signers", [{}])[0].get("valid") == True:
                logger.info("XML signature verification successful")
                return True
            else:
                logger.warning(f"XML signature verification failed: {result.get('message')}")
                logger.warning(f"XML signature verification failed: {result}")
                return False
                
        except requests.Timeout:
            logger.error("Timeout while connecting to NCANode")
            return False
        except Exception as e:
            logger.error(f"Error verifying XML signature: {e}")
            return False

    @staticmethod
    def extract_user_info_from_xml(signed_xml: str) -> Dict:
        """
        Extract user information from the signed XML using NCANode
        """
        try:
            # Create request payload for NCANode
            payload = {
                "xml": signed_xml
            }
            
            # Send request to NCANode with timeout
            response = requests.post(
                f"{EDSConfig.NCANODE_API_ENDPOINT}/xml/verify", 
                json=payload,
                timeout=10  # 10 seconds timeout
            )
            
            # Parse response
            result = response.json()
            
            if result.get("status") != 200:
                logger.warning(f"Failed to get certificate info: {result}")
                return {}
            
            # Extract subject info 
            subject = result.get("signers", {})[0].get("subject", {})
            
            # Create user info dictionary
            user_info = {
                "iin": subject.get("iin"),
            }
            
            return user_info
        except requests.Timeout:
            logger.error("Timeout while connecting to NCANode")
            return {}
        except Exception as e:
            logger.error(f"Error extracting user info from XML: {e}")
            return {}

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create JWT token
        
        Args:
            data: Payload data for the token (should include 'iin')
            expires_delta: Optional custom expiration time
        
        Returns:
            Encoded JWT token
        """
        try:
            logger.info(f"Creating token")
            to_encode = data.copy()
            
            if expires_delta:
                expire = datetime.utcnow() + expires_delta
            else:
                expire = datetime.utcnow() + timedelta(minutes=EDSConfig.ACCESS_TOKEN_EXPIRE_MINUTES)
                
            to_encode.update({"exp": expire})
            
            # Ensure IIN is present
            if not data.get("iin"):
                logger.warning("No IIN provided for token creation")
                
            # Create token
            encoded_jwt = jwt.encode(to_encode, EDSConfig.JWT_SECRET_KEY, algorithm=EDSConfig.JWT_ALGORITHM)
            logger.info(f"Token created successfully")
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            # Return a fallback token that will expire quickly
            fallback_payload = {
                "exp": datetime.utcnow() + timedelta(minutes=5),
                "error": "token_creation_failed"
            }
            if "iin" in data:
                fallback_payload["iin"] = data["iin"]
            return jwt.encode(fallback_payload, EDSConfig.JWT_SECRET_KEY, algorithm=EDSConfig.JWT_ALGORITHM)

    @staticmethod
    def get_user_by_iin(db: Session, iin: str) -> Optional[User]:
        """
        Get user by IIN from database
        """
        return db.query(User).filter(User.iin == iin).first()

    @staticmethod
    def create_user_from_eds_data(db: Session, user_data: Dict) -> User:
        """
        Create a new user from EDS data with pending status
        """
        # Create user object based on your User model
        user = User(
            iin=user_data.get("iin"),
            email=None,  # Will be set during registration
            full_name=None,  # Will be set during registration
            is_active=True,
            is_superuser=False,
            status=UserStatus.PENDING.value,  # Use the lowercase value from the enum
            hashed_password=None  # Will be set during registration
        )
        
        try:
            db.add(user)
            db.commit()
            db.refresh(user)
            return user
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating user: {e}")
            raise

    @staticmethod
    def authenticate_eds(signed_xml: str, db: Session, cert_hint: Optional[Dict] = None) -> Optional[Dict]:
        """
        Authenticate user with EDS using NCANode
        
        Args:
            signed_xml: XML document signed with EDS
            db: Database session
            cert_hint: Optional dictionary with certificate hints from SDK
        
        Returns:
            Dictionary with user and login_status if authentication successful, None otherwise
        """
        try:
            # Log authentication attempt (for debugging)
            logger.info(f"EDS authentication attempt received, cert_hint available: {cert_hint is not None}")
            
            # Verify XML signature using NCANode
            logger.info("Starting XML signature verification")
            if not KZEDSAuthenticator.verify_xml_signature(signed_xml):
                logger.warning("EDS signature verification failed")
                return None
            logger.info("XML signature verification completed successfully")
            
            # Extract user info from XML using NCANode
            logger.info("Starting extraction of user info from XML")
            user_info = KZEDSAuthenticator.extract_user_info_from_xml(signed_xml)
            logger.info(f"User info extracted: IIN present: {user_info.get('iin') is not None}")
            
            if not user_info.get("iin"):
                logger.warning("No IIN found in signed XML or certificate hint")
                return None
            
            # Find user in database by IIN
            logger.info(f"Looking up user with IIN: {user_info['iin']}")
            user = KZEDSAuthenticator.get_user_by_iin(db, user_info["iin"])
            logger.info(f"User lookup result: {user is not None}")
            
            # Determine login status
            if not user:
                # Create a new user with pending status if not exists
                logger.info(f"Creating new user with IIN: {user_info['iin']}")
                user = KZEDSAuthenticator.create_user_from_eds_data(db, user_info)
                logger.info(f"New user created with ID: {user.id}")
                return {"user": user, "login_status": "REGISTRATION_REQUIRED"}
            elif user.status == UserStatus.PENDING.value:
                # User exists but registration is incomplete
                logger.info(f"User {user.id} is in PENDING status")
                return {"user": user, "login_status": "REGISTRATION_REQUIRED"}
            elif user.status == UserStatus.INACTIVE.value:
                # User is deactivated
                logger.warning(f"Authentication failed: User with IIN {user_info['iin']} is inactive")
                return None
            else:
                # User is active and fully registered
                logger.info(f"User {user.id} is fully registered and active")
                return {"user": user, "login_status": "AUTHENTICATED"}
                
        except Exception as e:
            logger.error(f"EDS authentication error: {e}")
            return None

def get_current_user_from_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Get current user from JWT token based on IIN
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT
        logger.info(f"Decoding token")
        payload = jwt.decode(token, EDSConfig.JWT_SECRET_KEY, algorithms=[EDSConfig.JWT_ALGORITHM])
        iin: str = payload.get("iin")
        if iin is None:
            logger.error("Token missing required 'iin' claim")
            raise credentials_exception
            
        token_data = TokenData(iin=iin)
        logger.info(f"Token successfully decoded, iin: {iin}")
        
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise credentials_exception
        
    # Get user from database
    user = KZEDSAuthenticator.get_user_by_iin(db, token_data.iin)
    if user is None:
        logger.error(f"No user found with IIN: {token_data.iin}")
        raise credentials_exception
    
    logger.info(f"User authenticated: id={user.id}, iin={user.iin}, status={user.status}")    
    return user 