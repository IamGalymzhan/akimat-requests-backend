from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.auth.eds.kz_eds import KZEDSAuthenticator
from app.db.session import get_db

router = APIRouter()

class EDSLoginRequest(BaseModel):
    """
    EDS Login Request structure
    
    This model defines the structure for EDS authentication requests.
    The signed_xml field is required and contains the XML signed by NCALayer.
    """
    signed_xml: str = Field(..., description="XML document signed using EDS via NCALayer")
    
    class Config:
        json_schema_extra = {
            "example": {
                "signed_xml": "<ds:Signature xmlns:ds='http://www.w3.org/2000/09/xmldsig#'>...</ds:Signature>"
            }
        }

class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str
    is_new_user: bool
    role: str

@router.post("/login", response_model=TokenResponse, summary="Authenticate with EDS")
async def login_with_eds(
    request: EDSLoginRequest, 
    db: Session = Depends(get_db)
):
    """
    Authenticate using Kazakhstan electronic digital signature (EDS)
    
    This endpoint handles authentication using Kazakhstan EDS through NCALayer.
    If the user doesn't exist, a new account will be created automatically.
    
    Parameters:
    - **signed_xml**: XML document signed using NCALayer
    
    Returns:
    - **access_token**: JWT token for API access
    - **token_type**: Token type (bearer)
    - **is_new_user**: True if this is the user's first login
    - **role**: User's role
    
    Raises:
    - **401**: Invalid signature
    - **400**: Invalid request format
    """
    
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Login with EDS request received")
        
        # Check if signed_xml is present
        if not request.signed_xml:
            logger.warning("Login failed: Missing signed_xml data")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing signed XML document",
            )
        
        # Log XML length for debugging (not the content for security)
        logger.info(f"Received signed XML with length: {len(request.signed_xml)}")
        
        # Authenticate with EDS
        logger.info("Starting EDS authentication")
        auth_result = KZEDSAuthenticator.authenticate_eds(
            request.signed_xml, 
            db
        )
        
        logger.info(f"Authentication result: {auth_result is not None}")
        
        if not auth_result:
            logger.warning("Login failed: Invalid EDS signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid EDS signature or user information",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = auth_result["user"]
        is_new_user = auth_result["login_status"] == "REGISTRATION_REQUIRED"
        
        # Create access token with IIN
        logger.info(f"Creating token for user with IIN: {user.iin}, status: {user.status}")
        access_token = KZEDSAuthenticator.create_access_token(
            data={"iin": user.iin}
        )
        logger.info("Token created successfully")
        
        logger.info("Login successful")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "is_new_user": is_new_user,
            "role": user.role
        }
    except HTTPException:
        # Re-raise HTTP exceptions as they are already properly formatted
        raise
    except Exception as e:
        # Log any unexpected errors and return a generic error message
        logger.error(f"Unexpected error during login: {str(e)}", exc_info=True)
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during authentication: {str(e)}"
        ) 