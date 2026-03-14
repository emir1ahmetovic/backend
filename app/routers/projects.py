from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.project import ProjectCreate, ProjectRead


router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectRead])
def list_projects(
    _user: dict = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> list[ProjectRead]:
    return []


@router.post("/", response_model=ProjectRead)
def create_project(
    payload: ProjectCreate,
    _user: dict = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> ProjectRead:
    return ProjectRead(id=1, name=payload.name)


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    _user: dict = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> dict:
    return {"ok": True, "deleted_project_id": project_id}

