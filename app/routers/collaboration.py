from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.collaboration import ProjectMemberCreate, ProjectMemberRead


router = APIRouter(prefix="/api/projects/{project_id}/members", tags=["collaboration"])


@router.post("/", response_model=ProjectMemberRead)
def add_member(
    project_id: int,
    payload: ProjectMemberCreate,
    _user: dict = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> ProjectMemberRead:
    return ProjectMemberRead(id=1, email=payload.email, role=payload.role)


@router.delete("/{member_id}")
def remove_member(
    project_id: int,
    member_id: int,
    _user: dict = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> dict:
    return {"ok": True, "project_id": project_id, "removed_member_id": member_id}

