from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, Profile, Doctor
from app.schemas.schemas import (
    UserRegister,
    UserLogin,
    TokenResponse,
    UserResponse,
    MFASetupResponse,
    MFAVerifyRequest
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    generate_mfa_secret,
    verify_mfa_code,
    get_current_mfa_code
)
from app.services.audit_service import record_audit

router = APIRouter(prefix="/auth", tags=["Authentication & User Lifecycle"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, request: Request, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )

    user = User(
        email=user_in.email,
        password_hash=hash_password(user_in.password),
        role=user_in.role
    )
    db.add(user)
    db.flush()

    profile = Profile(
        user_id=user.id,
        full_name=user_in.full_name,
        phone=user_in.phone
    )
    db.add(profile)

    if user.role == "doctor":
        doctor = Doctor(
            user_id=user.id,
            specialization="General Physician",
            experience_years=1,
            consultation_fee=500.0,
            bio="Ayurvedic & Telemedicine Practitioner"
        )
        db.add(doctor)

    db.commit()
    db.refresh(user)

    client_ip = request.client.host if request.client else None
    record_audit(
        db=db,
        action="USER_REGISTER",
        resource=f"user:{user.id}",
        actor_id=user.id,
        details=f"User registered with role {user.role}",
        ip_address=client_ip
    )

    return user

@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )

    if user.mfa_enabled:
        if not login_data.mfa_code or not verify_mfa_code(user.mfa_secret, login_data.mfa_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing MFA code"
            )

    token = create_access_token(data={"sub": user.id, "role": user.role, "email": user.email})

    client_ip = request.client.host if request.client else None
    record_audit(
        db=db,
        action="USER_LOGIN",
        resource=f"user:{user.id}",
        actor_id=user.id,
        details="User logged in successfully",
        ip_address=client_ip
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
        "role": user.role
    }

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/mfa/setup", response_model=MFASetupResponse)
def setup_mfa(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    secret = generate_mfa_secret()
    current_user.mfa_secret = secret
    db.commit()
    sample_code = get_current_mfa_code(secret)
    return {
        "secret": secret,
        "instructions": f"MFA Secret initialized. For instant verification in testing, use current OTP code: {sample_code}"
    }

@router.post("/mfa/verify")
def verify_mfa(
    mfa_in: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA has not been set up. Call /auth/mfa/setup first."
        )

    if not verify_mfa_code(current_user.mfa_secret, mfa_in.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MFA verification code"
        )

    current_user.mfa_enabled = True
    db.commit()
    return {"status": "success", "message": "MFA has been successfully activated."}

@router.post("/mfa/disable")
def disable_mfa(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    db.commit()
    return {"status": "success", "message": "MFA has been disabled."}
