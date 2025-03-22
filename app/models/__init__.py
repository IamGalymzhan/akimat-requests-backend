from app.models.user import User, UserStatus, UserRole
from app.models.department import Department
from app.models.request import Request, RequestType, RequestStatus
from app.models.request_comment import RequestComment
from app.models.request_attachment import RequestAttachment

# For alembic to detect models
__all__ = [
    "User", "UserStatus", "UserRole", 
    "Department", 
    "Request", "RequestType", "RequestStatus", 
    "RequestComment",
    "RequestAttachment"
] 