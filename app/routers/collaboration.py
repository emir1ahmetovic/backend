import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.collaboration import ProjectMemberCreate, ProjectMemberRead

router = APIRouter(prefix="/api/projects/{project_id}/members", tags=["collaboration"])


@router.post("/", response_model=ProjectMemberRead)
def add_member(
    project_id: uuid.UUID,
    payload: ProjectMemberCreate,
    _user: dict = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> ProjectMemberRead:
    target_user = _db.query(User).filter(User.email == payload.email).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    member = ProjectMember(
        project_id=project_id,
        user_id=target_user.user_id,
        invited_by=_user["user_id"],
        role=payload.role,
    )
    _db.add(member)
    _db.commit()
    _db.refresh(member)

    return ProjectMemberRead(
        project_member_id=member.project_member_id,
        user_id=member.user_id,
        role=member.role,
        email=target_user.email,
    )


@router.delete("/{member_id}")
def remove_member(
    project_id: uuid.UUID,
    member_id: uuid.UUID,
    _user: dict = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> dict:
    member = (
        _db.query(ProjectMember)
        .filter(ProjectMember.project_member_id == member_id, ProjectMember.project_id == project_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    _db.delete(member)
    _db.commit()

    return {"ok": True, "project_id": str(project_id), "removed_member_id": str(member_id)}