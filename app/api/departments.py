from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.api.users import get_supervisor_or_admin_user
from app.models.user import User
from app.schemas.department import Department, DepartmentCreate
from app.crud.department import department

router = APIRouter()

@router.get("/", response_model=List[Department])
def get_departments(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    _: User = Depends(get_current_active_user),
) -> List[Department]:
    """
    Retrieve departments.
    
    Any authenticated user can access this endpoint.
    """
    departments = department.get_multi(db, skip=skip, limit=limit)
    return departments

@router.post("/", response_model=Department, status_code=status.HTTP_201_CREATED)
def create_department(
    *,
    db: Session = Depends(get_db),
    department_in: DepartmentCreate,
    _: User = Depends(get_supervisor_or_admin_user),
) -> Department:
    """
    Create a new department.
    
    Only supervisors and administrators can create departments.
    """
    return department.create(db, obj_in=department_in)

@router.get("/{department_id}", response_model=Department)
def get_department(
    department_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> Department:
    """
    Get department by ID.
    
    Any authenticated user can access this endpoint.
    """
    db_department = department.get(db, id=department_id)
    if db_department is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )
    return db_department 