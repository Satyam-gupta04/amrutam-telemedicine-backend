import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import Base, get_db
from app.models.models import User, Profile, Doctor, AvailabilitySlot
from app.core.security import hash_password, create_access_token

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_patient(db_session):
    user = User(
        email="patient@amrutam.com",
        password_hash=hash_password("Password123!"),
        role="patient",
        is_active=True
    )
    db_session.add(user)
    db_session.flush()

    profile = Profile(
        user_id=user.id,
        full_name="Ramesh Sharma",
        phone="9876543210"
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def patient_token(test_patient):
    return create_access_token({"sub": test_patient.id, "role": test_patient.role, "email": test_patient.email})

@pytest.fixture
def test_doctor(db_session):
    user = User(
        email="doctor@amrutam.com",
        password_hash=hash_password("DoctorPass123!"),
        role="doctor",
        is_active=True
    )
    db_session.add(user)
    db_session.flush()

    profile = Profile(
        user_id=user.id,
        full_name="Dr. Priya Iyer",
        phone="9812345678"
    )
    db_session.add(profile)

    doctor = Doctor(
        user_id=user.id,
        specialization="Ayurveda",
        experience_years=8,
        consultation_fee=750.0,
        bio="Senior Ayurvedic Practitioner"
    )
    db_session.add(doctor)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def doctor_token(test_doctor):
    return create_access_token({"sub": test_doctor.id, "role": test_doctor.role, "email": test_doctor.email})

@pytest.fixture
def test_admin(db_session):
    user = User(
        email="admin@amrutam.com",
        password_hash=hash_password("AdminSecure123!"),
        role="admin",
        is_active=True
    )
    db_session.add(user)
    db_session.flush()

    profile = Profile(
        user_id=user.id,
        full_name="System Administrator",
        phone="9999999999"
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def admin_token(test_admin):
    return create_access_token({"sub": test_admin.id, "role": test_admin.role, "email": test_admin.email})

@pytest.fixture
def doctor_slot(db_session, test_doctor):
    slot = AvailabilitySlot(
        doctor_id=test_doctor.doctor_profile.id,
        start_time=datetime.utcnow() + timedelta(days=1, hours=10),
        end_time=datetime.utcnow() + timedelta(days=1, hours=10, minutes=30),
        is_booked=False
    )
    db_session.add(slot)
    db_session.commit()
    db_session.refresh(slot)
    return slot
