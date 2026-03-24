from datetime import datetime
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.material import Material
from app.schemas.material import MaterialCreate, MaterialRead

router = APIRouter(prefix="/api/projects/{project_id}/materials", tags=["materials"])


@router.get("/", response_model=list[MaterialRead])
def list_materials(
    project_id: uuid.UUID,
    _user: dict = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> list[MaterialRead]:
    return (
        _db.query(Material)
        .filter(Material.project_id == project_id, Material.deleted_at.is_(None))
        .order_by(Material.created_at.desc())
        .all()
    )


@router.post("/", response_model=MaterialRead)
def create_material(
    project_id: uuid.UUID,
    payload: MaterialCreate,
    _user: dict = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> MaterialRead:
    material = Material(
        project_id=project_id,
        uploaded_by=_user["user_id"],
        original_file_name=payload.original_file_name,
        file_type=payload.file_type,
        s3_bucket=payload.s3_bucket,
        s3_key=payload.s3_key,
    )
    _db.add(material)
    _db.commit()
    _db.refresh(material)
    return material


@router.delete("/{material_id}")
def delete_material(
    project_id: uuid.UUID,
    material_id: uuid.UUID,
    _user: dict = Depends(get_current_user),
    _db: Session = Depends(get_db),
) -> dict:
    material = (
        _db.query(Material)
        .filter(Material.material_id == material_id, Material.project_id == project_id, Material.deleted_at.is_(None))
        .first()
    )
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    material.deleted_at = datetime.utcnow()
    _db.commit()

    return {"ok": True, "deleted_material_id": str(material_id)}