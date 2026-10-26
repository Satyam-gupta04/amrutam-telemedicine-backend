from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.core.middleware import ObservabilityMiddleware, metrics_collector
from app.api import auth, doctors, bookings, consultations, prescriptions, payments, admin

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Amrutam Telemedicine API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(ObservabilityMiddleware)


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "Amrutam Telemedicine API"}


@app.get("/metrics", tags=["Observability"])
def get_metrics():
    return metrics_collector.get_stats()


app.include_router(auth.router, prefix="/api/v1")
app.include_router(doctors.router, prefix="/api/v1")
app.include_router(bookings.router, prefix="/api/v1")
app.include_router(consultations.router, prefix="/api/v1")
app.include_router(prescriptions.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
