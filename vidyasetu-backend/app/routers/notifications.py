from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.models import User, Notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/me")
def my_notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(Notification).filter(Notification.user_id == user.id).order_by(
        Notification.created_at.desc()
    ).all()
    return [{"id": n.id, "message": n.message, "is_read": n.is_read, "created_at": n.created_at} for n in rows]


@router.patch("/{notification_id}/read")
def mark_read(notification_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    n = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user.id).first()
    if n:
        n.is_read = True
        db.commit()
    return {"status": "ok"}
