from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.models import User, RoleEnum, StudentProfile, FacultyProfile, Institution, Company
from app.schemas.schemas import RegisterRequest, LoginRequest, TokenResponse, CurrentUserResponse
from app.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if payload.role not in [r.value for r in RoleEnum]:
        raise HTTPException(400, f"Invalid role. Must be one of {[r.value for r in RoleEnum]}")
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(400, "An account with this email already exists.")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
    )
    db.add(user)
    db.flush()  # get user.id before creating dependent profile rows

    if payload.role == RoleEnum.student:
        institution = None
        if payload.institution_name:
            institution = db.query(Institution).filter(Institution.name == payload.institution_name).first()
            if not institution:
                institution = Institution(name=payload.institution_name)
                db.add(institution)
                db.flush()
        db.add(StudentProfile(user_id=user.id, institution_id=institution.id if institution else None))

    elif payload.role == RoleEnum.faculty:
        institution = None
        if payload.institution_name:
            institution = db.query(Institution).filter(Institution.name == payload.institution_name).first()
            if not institution:
                institution = Institution(name=payload.institution_name)
                db.add(institution)
                db.flush()
        db.add(FacultyProfile(user_id=user.id, institution_id=institution.id if institution else None))

    elif payload.role == RoleEnum.institution:
        if payload.institution_name and not db.query(Institution).filter(
            Institution.name == payload.institution_name
        ).first():
            db.add(Institution(name=payload.institution_name))

    elif payload.role == RoleEnum.industry:
        if payload.company_name:
            db.add(Company(name=payload.company_name, user_id=user.id))

    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.id, role=user.role.value)
    return TokenResponse(access_token=token, role=user.role.value, user_id=user.id, full_name=user.full_name)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect email or password.")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been deactivated.")
    token = create_access_token(subject=user.id, role=user.role.value)
    return TokenResponse(access_token=token, role=user.role.value, user_id=user.id, full_name=user.full_name)


@router.get("/me", response_model=CurrentUserResponse)
def me(user: User = Depends(get_current_user)):
    return CurrentUserResponse(id=user.id, email=user.email, full_name=user.full_name, role=user.role.value)
