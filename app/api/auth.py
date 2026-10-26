from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, Profile, Doctor
from app.schemas.schemas import UserRegister, UserLogin, TokenResponse, UserResponse, MFASetupResponse, MFAVerifyRequest
from app.core.security import hash_password, verify_password, create_access_token, get_current_user, generate_mfa_secret, verify_mfa_code, get_current_mfa_code
from app.services.audit_service import record_audit

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user_in: UserRegister, request: Request, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=400, detail="Email is already registered")

    user = User(email=user_in.email, password_hash=hash_password(user_in.password), role=user_in.role)
    db.add(user)
    db.flush()

    db.add(Profile(user_id=user.id, full_name=user_in.full_name, phone=user_in.phone))

    if user.role == "doctor":
        db.add(Doctor(user_id=user.id, specialization="General Physician", experience_years=1, consultation_fee=500.0))

    db.commit()
    db.refresh(user)

    record_audit(db, "USER_REGISTER", f"user:{user.id}", actor_id=user.id, details=f"role={user.role}", ip_address=request.client.host if request.client else None)
    return user


@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")
    if user.mfa_enabled:
        if not login_data.mfa_code or not verify_mfa_code(user.mfa_secret, login_data.mfa_code):
            raise HTTPException(status_code=401, detail="Invalid or missing MFA code")

    token = create_access_token({"sub": user.id, "role": user.role, "email": user.email})
    record_audit(db, "USER_LOGIN", f"user:{user.id}", actor_id=user.id, ip_address=request.client.host if request.client else None)
    return {"access_token": token, "token_type": "bearer", "user_id": user.id, "email": user.email, "role": user.role}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/mfa/setup", response_model=MFASetupResponse)
def setup_mfa(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    secret = generate_mfa_secret()
    current_user.mfa_secret = secret
    db.commit()
    code = get_current_mfa_code(secret)
    return {"secret": secret, "instructions": f"MFA ready. Current test code: {code}"}


@router.post("/mfa/verify")
def verify_mfa(mfa_in: MFAVerifyRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA not set up. Call /auth/mfa/setup first.")
    if not verify_mfa_code(current_user.mfa_secret, mfa_in.code):
        raise HTTPException(status_code=400, detail="Invalid MFA code")
    current_user.mfa_enabled = True
    db.commit()
    return {"status": "success", "message": "MFA enabled."}


@router.post("/mfa/disable")
def disable_mfa(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    db.commit()
    return {"status": "success", "message": "MFA disabled."}
