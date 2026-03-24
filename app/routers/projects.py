from datetime import datetime
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.project import Project
from app.models.enums import ProjectStatus
from app.schemas.project import ProjectCreate, ProjectRead


router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectRead])
def list_projects(
    _user: dict = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> list[ProjectRead]:
    return (
        _db.query(Project)
        .filter(Project.deleted_at.is_(None))
        .order_by(Project.created_at.desc())
        .all()
    )


@router.post("/", response_model=ProjectRead)
def create_project(
    payload: ProjectCreate,
    _user: dict = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> ProjectRead:
    project = Project(
        project_name=payload.project_name,
        project_description=payload.project_description,
        owner_id=_user["user_id"],
        status=ProjectStatus.ACTIVE,
    )
    _db.add(project)
    _db.commit()
    _db.refresh(project)
    return project


@router.delete("/{project_id}")
def delete_project(
    project_id: uuid.UUID,
    _user: dict = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> dict:
    project = (
        _db.query(Project)
        .filter(Project.project_id == project_id, Project.deleted_at.is_(None))
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.deleted_at = datetime.utcnow()
    _db.commit()

    return {"ok": True, "deleted_project_id": str(project_id)}