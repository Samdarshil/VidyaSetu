from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_role
from app.models.models import User, CollaborationRequest, CollaborationStatus
from app.schemas.schemas import CollaborationCreate, CollaborationOut

router = APIRouter(prefix="/collaborations", tags=["collaboration"])


@router.get("", response_model=list[CollaborationOut])
def list_collaborations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(CollaborationRequest).order_by(CollaborationRequest.created_at.desc()).all()


@router.post("", response_model=CollaborationOut, status_code=201)
def create_collaboration(
    payload: CollaborationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("industry", "institution", "faculty")),
):
    row = CollaborationRequest(
        title=payload.title, description=payload.description,
        from_type=payload.from_type, from_id=user.id,
        to_type=payload.to_type, to_id=payload.to_id,
        status=CollaborationStatus.requested,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/{collab_id}/status", response_model=CollaborationOut)
def update_collaboration_status(
    collab_id: str, new_status: str,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("industry", "institution", "faculty", "admin")),
):
    if new_status not in [s.value for s in CollaborationStatus]:
        raise HTTPException(400, f"Invalid status. Must be one of {[s.value for s in CollaborationStatus]}")
    row = db.query(CollaborationRequest).filter(CollaborationRequest.id == collab_id).first()
    if not row:
        raise HTTPException(404, "Collaboration request not found.")
    row.status = new_status
    if new_status in ("Accepted", "Active"):
        row.participants_count = row.participants_count or 1
    db.commit()
    db.refresh(row)
    return row
