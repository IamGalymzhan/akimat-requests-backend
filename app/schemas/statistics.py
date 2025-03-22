from typing import Dict, List, Optional
from pydantic import BaseModel


class UserRequestCount(BaseModel):
    """User with their request count for top users statistics"""
    id: int
    full_name: str
    email: Optional[str] = None
    request_count: int


class DepartmentStats(BaseModel):
    """Statistics for a department"""
    id: int
    name: str
    request_count: int


class RequestTypeStats(BaseModel):
    """Statistics for a request type"""
    type: str
    request_count: int


class CompletionRateStats(BaseModel):
    """Completion rate statistics"""
    total_requests: int
    completed_requests: int
    completion_rate: float  # Percentage of completed requests


class Statistics(BaseModel):
    """Overall statistics response"""
    total_requests: int
    completion_rate: CompletionRateStats
    department_stats: List[DepartmentStats]
    request_type_stats: List[RequestTypeStats]
    top_users: List[UserRequestCount] 