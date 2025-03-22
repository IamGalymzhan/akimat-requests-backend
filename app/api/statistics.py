from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app import schemas
from app.api import deps
from app.models.user import User, UserRole
from app.models.request import Request, RequestStatus
from app.models.department import Department

router = APIRouter()


@router.get("/", response_model=schemas.Statistics)
def get_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get system usage statistics.
    Only administrators can access this endpoint.
    """
    # Check if user is an administrator
    if current_user.role != UserRole.ADMINISTRATOR.value:
        raise HTTPException(
            status_code=403,
            detail="Not enough permissions to access statistics"
        )
    
    # Total number of requests
    total_requests = db.query(func.count(Request.id)).scalar()
    
    # Completion rate stats
    completed_requests = db.query(func.count(Request.id)).filter(
        Request.status == RequestStatus.COMPLETED.value
    ).scalar()
    
    completion_rate = 0.0
    if total_requests > 0:
        completion_rate = (completed_requests / total_requests) * 100.0
    
    completion_stats = schemas.CompletionRateStats(
        total_requests=total_requests,
        completed_requests=completed_requests,
        completion_rate=completion_rate
    )
    
    # Department stats
    department_stats_query = (
        db.query(
            Department.id,
            Department.name,
            func.count(Request.id).label("request_count")
        )
        .outerjoin(Request, Department.id == Request.department_id)
        .group_by(Department.id)
        .order_by(desc("request_count"))
    )
    
    department_stats = [
        schemas.DepartmentStats(
            id=dept.id,
            name=dept.name,
            request_count=dept.request_count
        )
        for dept in department_stats_query
    ]
    
    # Request type stats
    request_type_stats_query = (
        db.query(
            Request.request_type,
            func.count(Request.id).label("request_count")
        )
        .group_by(Request.request_type)
        .order_by(desc("request_count"))
    )
    
    request_type_stats = [
        schemas.RequestTypeStats(
            type=req_type.request_type,
            request_count=req_type.request_count
        )
        for req_type in request_type_stats_query
    ]
    
    # Top 5 users with most created requests
    top_users_query = (
        db.query(
            User.id,
            User.full_name,
            User.email,
            func.count(Request.id).label("request_count")
        )
        .join(Request, User.id == Request.created_by_id)
        .group_by(User.id)
        .order_by(desc("request_count"))
        .limit(5)
    )
    
    top_users = [
        schemas.UserRequestCount(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            request_count=user.request_count
        )
        for user in top_users_query
    ]
    
    # Construct the final statistics response
    return schemas.Statistics(
        total_requests=total_requests,
        completion_rate=completion_stats,
        department_stats=department_stats,
        request_type_stats=request_type_stats,
        top_users=top_users
    ) 