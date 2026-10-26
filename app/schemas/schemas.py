from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = Field(default="patient", pattern="^(patient|doctor|admin)$")
    full_name: str = Field(..., min_length=2)
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    mfa_code: Optional[str] = None

class MFASetupResponse(BaseModel):
    secret: str
    instructions: str

class MFAVerifyRequest(BaseModel):
    code: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str

class ProfileResponse(BaseModel):
    id: str
    full_name: str
    phone: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    is_active: bool
    mfa_enabled: bool
    created_at: datetime
    profile: Optional[ProfileResponse] = None

    class Config:
        from_attributes = True

class DoctorCreate(BaseModel):
    specialization: str
    experience_years: int = Field(default=0, ge=0)
    consultation_fee: float = Field(default=500.0, ge=0)
    bio: Optional[str] = None

class DoctorResponse(BaseModel):
    id: str
    user_id: str
    full_name: str
    email: str
    specialization: str
    experience_years: int
    consultation_fee: float
    bio: Optional[str] = None
    rating: float

    class Config:
        from_attributes = True

class SlotCreate(BaseModel):
    start_time: datetime
    end_time: datetime

class SlotResponse(BaseModel):
    id: str
    doctor_id: str
    start_time: datetime
    end_time: datetime
    is_booked: bool

    class Config:
        from_attributes = True

class BookingCreate(BaseModel):
    doctor_id: str
    slot_id: str
    notes: Optional[str] = None

class PrescriptionCreate(BaseModel):
    diagnosis: str
    medicines: str
    instructions: Optional[str] = None

class PrescriptionResponse(BaseModel):
    id: str
    consultation_id: str
    diagnosis: str
    medicines: str
    instructions: Optional[str] = None
    issued_at: datetime

    class Config:
        from_attributes = True

class PaymentResponse(BaseModel):
    id: str
    consultation_id: str
    amount: float
    currency: str
    status: str
    transaction_ref: str
    created_at: datetime

    class Config:
        from_attributes = True

class ConsultationResponse(BaseModel):
    id: str
    patient_id: str
    doctor_id: str
    slot_id: str
    status: str
    notes: Optional[str] = None
    meet_link: Optional[str] = None
    created_at: datetime
    prescription: Optional[PrescriptionResponse] = None
    payment: Optional[PaymentResponse] = None

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    id: str
    actor_id: Optional[str] = None
    action: str
    resource: str
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class AnalyticsSummary(BaseModel):
    total_users: int
    total_patients: int
    total_doctors: int
    total_consultations: int
    completed_consultations: int
    cancelled_consultations: int
    total_revenue: float
